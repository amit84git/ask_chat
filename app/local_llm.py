"""
Local LLM Integration using Ollama for open-source models.
Provides a drop-in replacement for AWS Bedrock that works with local models
running via Ollama, or via Floci's compatible endpoint.

Supported models (via Ollama):
- llama3, llama3.1 (8B, 70B, 400B)
- mistral, mixtral
- phi3, phi3:mini, phi3:medium
- gemma, gemma2
- qwen2, qwen2.5
- codellama
- neural-chat
- deepseek-coder
"""
import json
import logging
from typing import Any, Dict, Optional
import requests

from app.config import settings

logger = logging.getLogger(__name__)


class LocalLLM:
    """
    Local LLM provider that connects to Ollama or any OpenAI-compatible local endpoint.
    
    For PoC purposes, this enables fully offline, zero-cost LLM query generation
    without any AWS dependency.
    
    Ollama default endpoint: http://localhost:11434
    Compatible with any OpenAI-compatible API format.
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or settings.local_llm_endpoint or "http://localhost:11434"
        self.model = model or settings.local_llm_model or "llama3.1:8b"
        self._available = None

    @property
    def is_available(self) -> bool:
        """Check if the local LLM endpoint is reachable."""
        if self._available is not None:
            return self._available
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            self._available = response.status_code == 200
            if self._available:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                logger.info(f"Local LLM available. Models: {', '.join(model_names[:5])}")
            return self._available
        except Exception as e:
            logger.warning(f"Local LLM not available at {self.base_url}: {e}")
            self._available = False
            return False

    def generate(self, prompt: str, max_tokens: int = 500, temperature: float = 0.1) -> Optional[str]:
        """
        Generate text using the local Ollama model.
        
        Args:
            prompt: The prompt to send to the model
            max_tokens: Maximum tokens to generate
            temperature: Temperature for sampling (0.0-1.0)
            
        Returns:
            Generated text string, or None on failure
        """
        if not self.is_available:
            logger.warning("Local LLM not available, cannot generate")
            return None

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "stop": ["\n\n", "Human:", "Assistant:"],
                },
                "stream": False,
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Local LLM request timed out after 60s")
            return None
        except Exception as e:
            logger.error(f"Local LLM generation failed: {e}")
            return None

    def generate_chat(self, messages: list, max_tokens: int = 500) -> Optional[str]:
        """
        Generate text using chat completion format (OpenAI-compatible).
        
        Args:
            messages: List of {"role": "user"/"system"/"assistant", "content": "..."}
            max_tokens: Maximum tokens to generate
        """
        if not self.is_available:
            return None

        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.1,
                },
                "stream": False,
            }

            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("message", {}).get("content", "").strip()
            else:
                logger.error(f"Ollama chat API error: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Local LLM chat failed: {e}")
            return None

    def list_models(self) -> list:
        """List available models from Ollama."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return [m["name"] for m in response.json().get("models", [])]
            return []
        except Exception:
            return []

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama's registry."""
        try:
            payload = {"name": model_name, "stream": False}
            response = requests.post(
                f"{self.base_url}/api/pull",
                json=payload,
                timeout=300,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False


# Factory function to get the appropriate LLM provider
def get_llm_provider() -> Any:
    """
    Get the appropriate LLM provider based on configuration.
    
    Priority:
    1. Local LLM (Ollama) if configured and available
    2. AWS Bedrock if configured and FEATURE_BEDROCK is true
    3. None (heuristic-only fallback)
    """
    provider_name = settings.llm_provider.lower()

    if provider_name in ("local", "ollama", "llama", "mistral", "phi", "gemma"):
        local_llm = LocalLLM()
        if local_llm.is_available:
            logger.info(f"Using local LLM provider: {local_llm.model}")
            return local_llm
        else:
            logger.warning(f"Local LLM configured but not available at {settings.local_llm_endpoint}")
            # Try falling back to Bedrock if available
            if settings.feature_bedrock:
                from app.aws_utils import BedrockRuntime
                logger.info("Falling back to AWS Bedrock")
                return BedrockRuntime()
            return None

    elif provider_name in ("bedrock", "claude", "titan") and settings.feature_bedrock:
        from app.aws_utils import BedrockRuntime
        logger.info(f"Using AWS Bedrock provider: {provider_name}")
        return BedrockRuntime()

    else:
        logger.info("No LLM provider configured, using heuristic-only mode")
        return None
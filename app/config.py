"""
Application Configuration using Pydantic Settings.
Reads from environment variables with sensible defaults for local Floci deployment.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    app_name: str = "AskChat"
    app_env: str = "local"
    app_debug: bool = True
    app_port: int = 8000
    log_level: str = "INFO"

    # AWS
    aws_endpoint_url: Optional[str] = "http://localhost:4566"
    aws_region: str = "us-east-1"
    aws_access_key_id: str = "dummy"
    aws_secret_access_key: str = "dummy"

    # Bedrock (used only if llm_provider is bedrock/claude/titan)
    bedrock_endpoint_url: Optional[str] = "http://localhost:4566/bedrock"
    bedrock_claude_model_id: str = "anthropic.claude-v2"
    bedrock_titan_model_id: str = "amazon.titan-tg1-large"
    llm_fallback_to_heuristics: bool = True

    # S3
    s3_bucket_name: str = "askchat-artifacts"

    # Database
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "askchat"
    db_user: str = "askchat"
    db_password: str = "askchat_secret_2024"
    db_secret_name: str = "askchat/db-credentials"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Feature Flags
    feature_rules_engine: bool = True
    feature_fuzzy_matching: bool = True
    feature_semantic_graph: bool = True
    feature_bedrock: bool = True

    # CORS
    cors_origins: str = "*"

    # Visualization
    vis_output_dir: str = "./output/visualizations"

    # Local LLM (Ollama) - for fully local, zero-cost operation
    local_llm_endpoint: str = "http://localhost:11434"
    local_llm_model: str = "llama3.1:8b"
    # LLM Provider selection:
    #   local/ollama/llama/mistral/phi/gemma = use Ollama with local open-source models
    #   bedrock/claude/titan = use AWS Bedrock
    #   none = heuristic-only mode
    llm_provider: str = "ollama"

    # spaCy
    spacy_model: str = "en_core_web_sm"

    # Is this a real AWS deployment (no endpoint override)?
    @property
    def is_real_aws(self) -> bool:
        return not self.aws_endpoint_url or "localhost" in self.aws_endpoint_url

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
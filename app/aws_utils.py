"""
AWS Integration Utilities.
Provides configurable boto3 client factories that work with both Floci and real AWS.
"""
import json
import logging
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


def get_boto3_config() -> BotoConfig:
    """Create a boto3 Config with appropriate settings."""
    return BotoConfig(
        region_name=settings.aws_region,
        retries={"max_attempts": 3, "mode": "adaptive"},
        connect_timeout=10,
        read_timeout=30,
    )


def get_client(service_name: str, endpoint_url: Optional[str] = None) -> Any:
    """
    Get a boto3 client with configurable endpoint.
    - For Floci: endpoint_url points to local Floci instance
    - For real AWS: endpoint_url is None, uses default AWS endpoints
    """
    actual_endpoint = endpoint_url or (settings.aws_endpoint_url if not settings.is_real_aws else None)

    client_kwargs = {
        "service_name": service_name,
        "config": get_boto3_config(),
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }

    # For Bedrock, the endpoint is different
    if service_name == "bedrock-runtime":
        actual_endpoint = settings.bedrock_endpoint_url or actual_endpoint

    if actual_endpoint:
        client_kwargs["endpoint_url"] = actual_endpoint
        logger.debug(f"Creating {service_name} client with endpoint: {actual_endpoint}")
    else:
        logger.debug(f"Creating {service_name} client with default AWS endpoint")

    return boto3.client(**client_kwargs)


class S3Manager:
    """S3 operations with Floci compatibility."""

    def __init__(self):
        self.client = get_client("s3")
        self.bucket = settings.s3_bucket_name

    def ensure_bucket_exists(self) -> bool:
        """Create bucket if it doesn't exist (Floci compatible)."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
            logger.info(f"Bucket {self.bucket} already exists")
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchBucket"):
                try:
                    if settings.aws_region == "us-east-1":
                        self.client.create_bucket(Bucket=self.bucket)
                    else:
                        self.client.create_bucket(
                            Bucket=self.bucket,
                            CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
                        )
                    logger.info(f"Created bucket: {self.bucket}")
                    return True
                except Exception as create_err:
                    logger.error(f"Failed to create bucket: {create_err}")
                    return False
            logger.error(f"Error checking bucket: {e}")
            return False

    def upload_file(self, key: str, data: bytes, content_type: Optional[str] = None) -> bool:
        """Upload bytes to S3."""
        try:
            kwargs = {"Bucket": self.bucket, "Key": key, "Body": data}
            if content_type:
                kwargs["ContentType"] = content_type
            self.client.put_object(**kwargs)
            logger.info(f"Uploaded s3://{self.bucket}/{key}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            return False

    def download_file(self, key: str) -> Optional[bytes]:
        """Download bytes from S3."""
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except Exception as e:
            logger.error(f"Failed to download from S3: {e}")
            return None

    def list_files(self, prefix: str = "") -> list:
        """List files in bucket with given prefix."""
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]
        except Exception as e:
            logger.error(f"Failed to list S3 objects: {e}")
            return []


class SecretsManager:
    """Secrets Manager operations."""

    def __init__(self):
        self.client = get_client("secretsmanager")

    def get_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a secret as a dictionary."""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_str = response.get("SecretString", "{}")
            return json.loads(secret_str)
        except ClientError as e:
            logger.warning(f"Failed to get secret {secret_name}: {e}")
            # Fallback to env vars for PoC
            return None

    def create_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        """Create a new secret. Floci compatible."""
        try:
            self.client.create_secret(
                Name=secret_name,
                SecretString=json.dumps(secret_value),
            )
            logger.info(f"Created secret: {secret_name}")
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceExistsException":
                logger.info(f"Secret {secret_name} already exists")
                return True
            logger.error(f"Failed to create secret: {e}")
            return False


class BedrockRuntime:
    """AWS Bedrock Runtime integration for LLM calls."""
    
    def __init__(self):
        self.client = get_client("bedrock-runtime")
        self.provider = settings.llm_provider

    def invoke_claude(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Invoke Anthropic Claude via Bedrock."""
        try:
            body = {
                "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                "max_tokens_to_sample": max_tokens,
                "temperature": 0.1,
                "top_p": 0.9,
            }
            response = self.client.invoke_model(
                modelId=settings.bedrock_claude_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            result = json.loads(response["body"].read().decode())
            return result.get("completion", "").strip()
        except Exception as e:
            logger.error(f"Claude invocation failed: {e}")
            return None

    def invoke_titan(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Invoke Amazon Titan via Bedrock."""
        try:
            body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": 0.1,
                    "topP": 0.9,
                },
            }
            response = self.client.invoke_model(
                modelId=settings.bedrock_titan_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body),
            )
            result = json.loads(response["body"].read().decode())
            return result.get("results", [{}])[0].get("outputText", "").strip()
        except Exception as e:
            logger.error(f"Titan invocation failed: {e}")
            return None

    def generate(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Generate text using the configured LLM provider."""
        if self.provider == "claude":
            return self.invoke_claude(prompt, max_tokens)
        elif self.provider == "titan":
            return self.invoke_titan(prompt, max_tokens)
        else:
            logger.warning(f"Unknown LLM provider: {self.provider}")
            return None
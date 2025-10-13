"""
Shared AWS service clients for DataMorph agents.
Provides reusable clients for Bedrock, S3, Secrets Manager, and DynamoDB.
"""
import boto3
import json
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from botocore.config import Config as BotocoreConfig


class AWSClients:
    """Singleton class for AWS service clients."""
    
    _instance = None
    _clients = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AWSClients, cls).__new__(cls)
        return cls._instance
    
    def get_bedrock_client(self, region: str = "us-east-1"):
        """Get or create Bedrock Runtime client."""
        if "bedrock" not in self._clients:
            self._clients["bedrock"] = boto3.client(
                "bedrock-runtime",
                region_name=region
            )
        return self._clients["bedrock"]
    
    def get_s3_client(self, region: str = "us-east-1"):
        """Get or create S3 client."""
        if "s3" not in self._clients:
            self._clients["s3"] = boto3.client("s3", region_name=region)
        return self._clients["s3"]
    
    def get_secrets_manager_client(self, region: str = "us-east-1"):
        """Get or create Secrets Manager client."""
        if "secrets" not in self._clients:
            self._clients["secrets"] = boto3.client(
                "secretsmanager",
                region_name=region
            )
        return self._clients["secrets"]
    
    def get_dynamodb_client(self, region: str = "us-east-1"):
        """Get or create DynamoDB client."""
        if "dynamodb" not in self._clients:
            self._clients["dynamodb"] = boto3.client(
                "dynamodb",
                region_name=region
            )
        return self._clients["dynamodb"]
    
    def get_lambda_client(self, region: str = "us-east-1"):
        """Get or create Lambda client."""
        if "lambda" not in self._clients:
            self._clients["lambda"] = boto3.client("lambda", region_name=region)
        return self._clients["lambda"]
    
    def get_glue_client(self, region: str = "us-east-1"):
        """Get or create Glue client."""
        if "glue" not in self._clients:
            self._clients["glue"] = boto3.client("glue", region_name=region)
        return self._clients["glue"]


def invoke_bedrock(
    prompt: str,
    model_id: str = "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    max_tokens: int = 4096,
    temperature: float = 0.5,
    region: str = "us-east-1"
) -> str:
    """
    Invoke AWS Bedrock with Claude model.
    
    Args:
        prompt: The prompt to send to the model
        model_id: Bedrock model ID
        max_tokens: Maximum tokens in response
        temperature: Model temperature
        region: AWS region
        
    Returns:
        Response text from the model
        
    Raises:
        ClientError: If Bedrock invocation fails
    """
    client = AWSClients().get_bedrock_client(region)
    
    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    }
    
    request = json.dumps(native_request)
    
    response = client.invoke_model(modelId=model_id, body=request)
    model_response = json.loads(response["body"].read())
    response_text = model_response["content"][0]["text"]
    
    return response_text


def upload_to_s3(bucket: str, key: str, content: str, region: str = "us-east-1") -> str:
    """
    Upload content to S3.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        content: Content to upload
        region: AWS region
        
    Returns:
        S3 path (s3://bucket/key)
        
    Raises:
        ClientError: If S3 upload fails
    """
    client = AWSClients().get_s3_client(region)
    client.put_object(Bucket=bucket, Key=key, Body=content)
    return f"s3://{bucket}/{key}"


def download_from_s3(bucket: str, key: str, region: str = "us-east-1") -> str:
    """
    Download content from S3.
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
        region: AWS region
        
    Returns:
        Content as string
        
    Raises:
        ClientError: If S3 download fails
    """
    client = AWSClients().get_s3_client(region)
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read().decode("utf-8")


def invoke_lambda(
    function_name: str,
    payload: Dict[str, Any],
    region: str = "us-east-1"
) -> Dict[str, Any]:
    """
    Invoke another Lambda function.
    
    Args:
        function_name: Name of Lambda function to invoke
        payload: Payload to send
        region: AWS region
        
    Returns:
        Response payload from Lambda
        
    Raises:
        ClientError: If Lambda invocation fails
    """
    # Use custom config with longer read timeout for long-running Lambda functions
    # Glue Executor can take 80-130 seconds, so we need at least 180 seconds
    lambda_config = BotocoreConfig(
        read_timeout=900,  # 15 minutes - matches Lambda max timeout
        connect_timeout=10,
        retries={'max_attempts': 1, 'mode': 'standard'}  # No retries
    )
    
    client = boto3.client('lambda', region_name=region, config=lambda_config)
    
    response = client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload)
    )
    
    response_payload = json.loads(response["Payload"].read())
    return response_payload

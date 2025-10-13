"""
Configuration loader for DataMorph.
Loads configuration from AWS Secrets Manager.
"""
import json
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from .aws_clients import AWSClients


class Config:
    """Configuration manager that loads from Secrets Manager."""
    
    _instance = None
    _config: Optional[Dict[str, Any]] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def load(self, secret_name: str = "datamorph/config", region: str = "us-east-1") -> Dict[str, Any]:
        """
        Load configuration from Secrets Manager.
        
        Args:
            secret_name: Name of the secret in Secrets Manager
            region: AWS region
            
        Returns:
            Configuration dictionary
            
        Raises:
            ClientError: If secret cannot be retrieved
        """
        if self._config is not None:
            return self._config
        
        client = AWSClients().get_secrets_manager_client(region)
        
        try:
            response = client.get_secret_value(SecretId=secret_name)
            self._config = json.loads(response["SecretString"])
            return self._config
        except ClientError as e:
            raise Exception(f"Failed to load configuration from Secrets Manager: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        if self._config is None:
            self.load()
        return self._config.get(key, default)
    
    @property
    def specs_path(self) -> str:
        """Get S3 path for specs."""
        return self.get("SPECS_PATH", "s3://your-bucket/specs")
    
    @property
    def glue_code_path(self) -> str:
        """Get S3 path for Glue code."""
        return self.get("GLUE_CODE_PATH", "s3://your-bucket/glue/codes")
    
    @property
    def glue_config_path(self) -> str:
        """Get S3 path for Glue configs."""
        return self.get("GLUE_CONFIG_PATH", "s3://your-bucket/glue/configs")
    
    @property
    def glue_others_path(self) -> str:
        """Get S3 path for other Glue files."""
        return self.get("GLUE_OTHERS_PATH", "s3://your-bucket/glue/others")
    
    @property
    def rds_endpoint(self) -> str:
        """Get RDS endpoint."""
        return self.get("RDS_ENDPOINT", "your-rds-endpoint.region.rds.amazonaws.com")
    
    @property
    def rds_port(self) -> int:
        """Get RDS port."""
        return int(self.get("RDS_PORT", 5432))
    
    @property
    def rds_username(self) -> str:
        """Get RDS username."""
        return self.get("RDS_USERNAME", "your_username")
    
    @property
    def rds_password(self) -> str:
        """Get RDS password."""
        return self.get("RDS_PASSWORD", "your_password")
    
    @property
    def rds_dbname(self) -> str:
        """Get RDS database name."""
        return self.get("RDS_DBNAME", "your_database")
    
    @property
    def dynamodb_table(self) -> str:
        """Get DynamoDB table name."""
        return self.get("DYNAMODB_TABLE", "datamorph_logs")
    
    @property
    def dynamodb_partition_key(self) -> str:
        """Get DynamoDB partition key."""
        return self.get("DYNAMODB_PARTITION_KEY", "run_id")
    
    @property
    def bedrock_model_id(self) -> str:
        """Get Bedrock model ID."""
        return self.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
    
    @property
    def bedrock_region(self) -> str:
        """Get Bedrock region."""
        return self.get("BEDROCK_REGION", "us-east-1")
    
    @property
    def aws_region(self) -> str:
        """Get AWS region."""
        return self.get("AWS_REGION", "us-east-1")
    
    @property
    def flask_app_url(self) -> str:
        """Get Flask app URL."""
        return self.get("FLASK_APP_URL", "http://your-flask-api-url")
    
    @property
    def s3_bucket(self) -> str:
        """Get S3 bucket name."""
        return self.get("S3_BUCKET", "your-bucket-name")


# Global config instance
config = Config()

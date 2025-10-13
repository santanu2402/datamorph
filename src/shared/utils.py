"""
Shared utility functions for DataMorph.
"""
import time
import uuid
from datetime import datetime
from typing import Callable, Any, Optional
from botocore.exceptions import ClientError


def generate_run_id() -> str:
    """
    Generate a unique run ID using timestamp and UUID.
    
    Returns:
        Unique run ID string
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}"


def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        
    Returns:
        Result from successful function call
        
    Raises:
        Exception: Last exception if all attempts fail
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return func()
        except (ClientError, Exception) as e:
            last_exception = e
            
            # Don't retry on last attempt
            if attempt == max_attempts - 1:
                break
            
            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            time.sleep(delay)
    
    raise last_exception


def parse_s3_path(s3_path: str) -> tuple[str, str]:
    """
    Parse S3 path into bucket and key.
    
    Args:
        s3_path: S3 path in format s3://bucket/key
        
    Returns:
        Tuple of (bucket, key)
        
    Raises:
        ValueError: If path format is invalid
    """
    if not s3_path.startswith("s3://"):
        raise ValueError(f"Invalid S3 path format: {s3_path}")
    
    path_parts = s3_path[5:].split("/", 1)
    if len(path_parts) != 2:
        raise ValueError(f"Invalid S3 path format: {s3_path}")
    
    return path_parts[0], path_parts[1]


def sanitize_table_name(name: str) -> str:
    """
    Sanitize table name for SQL safety.
    
    Args:
        name: Table name to sanitize
        
    Returns:
        Sanitized table name
    """
    # Remove any characters that aren't alphanumeric or underscore
    sanitized = "".join(c for c in name if c.isalnum() or c == "_")
    
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    
    return sanitized.lower()

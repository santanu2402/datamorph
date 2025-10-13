# DataMorph Agent Documentation: Logger Lambda

## Name
**Logger Lambda (Centralized Logging Service)**

## Services Using
- **AWS DynamoDB**: Persistent log storage
- **AWS Secrets Manager**: Configuration retrieval

## Input
Lambda event with log entry:
```json
{
  "run_id": "20250113_123456_abc123",
  "log_entry": {
    "timestamp": "2025-01-13T12:34:56.789Z",  // optional, auto-generated if missing
    "type": "status|code|info|start|end|result|error|warning",
    "title": "Log Entry Title",
    "description": "Detailed description of the event",
    "metadata": {  // optional
      "key1": "value1",
      "key2": 123,
      "nested": {
        "data": "value"
      }
    }
  }
}
```

## Output
Success or error response:
```json
{
  "statusCode": 200,
  "body": {
    "success": true,
    "message": "Log entry appended successfully",
    "run_id": "20250113_123456_abc123",
    "timestamp": "2025-01-13T12:34:56.789Z"
  }
}
```

## Objectives

### Primary Objectives
1. **Centralized Logging**: Single point for all workflow logging across all agents
2. **Persistent Storage**: Store logs in DynamoDB for long-term retention
3. **Structured Logging**: Enforce consistent log entry format
4. **Append-Only**: Append new log entries to existing run_id records
5. **Timestamp Management**: Auto-generate timestamps if not provided

### Secondary Objectives
1. **Error Handling**: Gracefully handle logging failures without breaking workflows
2. **Retry Logic**: Retry failed DynamoDB operations with exponential backoff
3. **Type Conversion**: Convert Python objects to DynamoDB format
4. **Validation**: Validate log entry structure before storage
5. **Performance**: Fast logging to minimize workflow overhead

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Logger Lambda                              │
│              (Centralized Logging Service)                      │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────┐         │
│  │  1. Receive Log Entry                            │         │
│  │     - run_id (required)                          │         │
│  │     - log_entry (required)                       │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  2. Validate Input                               │         │
│  │     - Check required fields                      │         │
│  │     - Validate log_entry structure               │         │
│  │     - Ensure type, title, description present    │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  3. Add Timestamp (if missing)                   │         │
│  │     - Generate ISO 8601 timestamp                │         │
│  │     - Format: 2025-01-13T12:34:56.789Z           │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  4. Convert to DynamoDB Format                   │         │
│  │     - Python dict → DynamoDB Map (M)             │         │
│  │     - Python str → DynamoDB String (S)           │         │
│  │     - Python int/float → DynamoDB Number (N)     │         │
│  │     - Python list → DynamoDB List (L)            │         │
│  │     - Python bool → DynamoDB Boolean (BOOL)      │         │
│  │     - Python None → DynamoDB Null (NULL)         │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  5. Append to DynamoDB                           │         │
│  │     - Try UPDATE (append to existing logs array) │         │
│  │     - If item doesn't exist, CREATE new item     │         │
│  │     - Update updated_at timestamp                │         │
│  │     - Retry with exponential backoff (3 attempts)│         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  6. Return Success Response                      │         │
│  │     - Confirm log appended                       │         │
│  │     - Return run_id and timestamp                │         │
│  └──────────────────────────────────────────────────┘         │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

## Detailed Working

### Phase 1: Input Validation

```python
def lambda_handler(event, context):
    # Validate run_id
    if "run_id" not in event:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": True,
                "message": "Missing required field: run_id"
            })
        }
    
    # Validate log_entry
    if "log_entry" not in event:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": True,
                "message": "Missing required field: log_entry"
            })
        }
    
    log_entry = event["log_entry"]
    
    # Validate log_entry structure
    required_fields = ["type", "title", "description"]
    for field in required_fields:
        if field not in log_entry:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": True,
                    "message": f"Missing required field in log_entry: {field}"
                })
            }
```

### Phase 2: Timestamp Management

```python
# Add timestamp if not present
if "timestamp" not in log_entry:
    log_entry["timestamp"] = datetime.utcnow().isoformat() + "Z"
```

### Phase 3: DynamoDB Format Conversion

The Logger converts Python objects to DynamoDB's type-annotated format:

```python
def _convert_to_dynamodb_format(obj: Any, is_root: bool = True) -> Dict[str, Any]:
    """
    Convert Python object to DynamoDB format.
    
    Examples:
    - "hello" → {"S": "hello"}
    - 123 → {"N": "123"}
    - True → {"BOOL": True}
    - None → {"NULL": True}
    - {"key": "value"} → {"M": {"key": {"S": "value"}}}
    - [1, 2, 3] → {"L": [{"N": "1"}, {"N": "2"}, {"N": "3"}]}
    """
    if obj is None:
        return {"NULL": True}
    elif isinstance(obj, bool):
        # Must check bool before int (bool is subclass of int)
        return {"BOOL": obj}
    elif isinstance(obj, (int, float)):
        return {"N": str(obj)}
    elif isinstance(obj, str):
        return {"S": obj}
    elif isinstance(obj, dict):
        # Recursively convert dict values
        converted = {k: _convert_to_dynamodb_format(v, is_root=False) for k, v in obj.items()}
        # Only wrap in M if not root level
        return converted if is_root else {"M": converted}
    elif isinstance(obj, list):
        # Recursively convert list items and wrap in L
        return {"L": [_convert_to_dynamodb_format(item, is_root=False) for item in obj]}
    else:
        # Fallback: convert to string
        return {"S": str(obj)}
```

### Phase 4: DynamoDB Append Operation

The Logger uses an atomic append operation to add log entries:

```python
def append_log_to_dynamodb(run_id: str, log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Append a log entry to DynamoDB.
    
    Uses UpdateExpression with list_append to atomically append to logs array.
    If item doesn't exist, creates it with the log entry.
    """
    dynamodb = AWSClients().get_dynamodb_client(config.aws_region)
    table_name = config.dynamodb_table
    partition_key = config.dynamodb_partition_key
    
    try:
        # Try to update existing item
        response = dynamodb.update_item(
            TableName=table_name,
            Key={partition_key: {"S": run_id}},
            UpdateExpression="SET logs = list_append(if_not_exists(logs, :empty_list), :new_log), updated_at = :updated_at",
            ExpressionAttributeValues={
                ":new_log": {"L": [{"M": _convert_to_dynamodb_format(log_entry)}]},
                ":empty_list": {"L": []},
                ":updated_at": {"S": datetime.utcnow().isoformat() + "Z"}
            },
            ReturnValues="UPDATED_NEW"
        )
        return response
    except Exception as e:
        # If item doesn't exist, create it
        if "ConditionalCheckFailedException" in str(type(e)):
            response = dynamodb.put_item(
                TableName=table_name,
                Item={
                    partition_key: {"S": run_id},
                    "logs": {"L": [{"M": _convert_to_dynamodb_format(log_entry)}]},
                    "created_at": {"S": datetime.utcnow().isoformat() + "Z"},
                    "updated_at": {"S": datetime.utcnow().isoformat() + "Z"}
                }
            )
            return response
        raise
```

### Phase 5: Retry Logic

```python
def append_operation():
    return append_log_to_dynamodb(run_id, log_entry)

# Retry with exponential backoff
response = retry_with_backoff(append_operation, max_attempts=3)
```

## DynamoDB Schema

### Table Structure
```
Table Name: dmdb_logs
Partition Key: run_id (String)
```

### Item Structure
```json
{
  "run_id": {"S": "20250113_123456_abc123"},
  "logs": {
    "L": [
      {
        "M": {
          "timestamp": {"S": "2025-01-13T12:34:56.789Z"},
          "type": {"S": "start"},
          "title": {"S": "Starting Orchestrator"},
          "description": {"S": "Starting ETL workflow with run_id: 20250113_123456_abc123"},
          "metadata": {
            "M": {
              "key1": {"S": "value1"},
              "key2": {"N": "123"}
            }
          }
        }
      },
      {
        "M": {
          "timestamp": {"S": "2025-01-13T12:35:10.123Z"},
          "type": {"S": "result"},
          "title": {"S": "Specifications Generated Successfully"},
          "description": {"S": "ETL specifications created and stored in S3"},
          "metadata": {
            "M": {
              "s3_path": {"S": "s3://dmbckt/specs/20250113_123456_abc123_specs.json"},
              "source_tables": {
                "L": [
                  {"S": "customers"},
                  {"S": "orders"}
                ]
              }
            }
          }
        }
      }
    ]
  },
  "created_at": {"S": "2025-01-13T12:34:56.789Z"},
  "updated_at": {"S": "2025-01-13T12:35:10.123Z"}
}
```

## Log Entry Types

### 1. START
Marks the beginning of a component's execution:
```python
{
  "type": "start",
  "title": "Starting Orchestrator",
  "description": "Starting ETL workflow with run_id: 20250113_123456_abc123"
}
```

### 2. STATUS
Progress updates during execution:
```python
{
  "type": "status",
  "title": "Step 1: Generating Specifications",
  "description": "Invoking Specs Generator"
}
```

### 3. RESULT
Successful completion of a task with artifacts:
```python
{
  "type": "result",
  "title": "Specifications Generated Successfully",
  "description": "ETL specifications created and stored in S3",
  "metadata": {
    "s3_path": "s3://dmbckt/specs/20250113_123456_abc123_specs.json",
    "source_tables": ["customers", "orders"]
  }
}
```

### 4. CODE
Code generation or modification events:
```python
{
  "type": "code",
  "title": "Glue Code Generated Successfully",
  "description": "PySpark ETL code created and stored in S3",
  "metadata": {
    "generated_item": "import sys\nfrom awsglue...",
    "path": "s3://dmbckt/glue/codes/20250113_123456_abc123_glue.py",
    "code_size_bytes": 2048
  }
}
```

### 5. INFO
Informational messages:
```python
{
  "type": "info",
  "title": "Glue Job Created",
  "description": "Job datamorph-job-20250113_123456_abc123 created successfully"
}
```

### 6. WARNING
Non-critical issues:
```python
{
  "type": "warning",
  "title": "Retrying Validation (Attempt 2)",
  "description": "Some test failures may be due to bad test queries, regenerating and retrying"
}
```

### 7. ERROR
Errors and failures:
```python
{
  "type": "error",
  "title": "Error: ValidationError",
  "description": "Validator: Validation failed with 3 failed tests",
  "metadata": {
    "error_type": "ValidationError",
    "error_message": "Validation failed with 3 failed tests"
  }
}
```

### 8. SUCCESS
Final success status:
```python
{
  "type": "success",
  "title": "ETL Workflow Completed Successfully",
  "description": "All steps completed. Data loaded to 'customer_order_summary' and validated.",
  "metadata": {
    "workflow_status": "completed",
    "target_table": "customer_order_summary",
    "validation_status": "pass"
  }
}
```

### 9. END
Marks the end of a component's execution:
```python
{
  "type": "end",
  "title": "Completed Orchestrator",
  "description": "Orchestrator execution completed",
  "metadata": {
    "execution_time_seconds": 120
  }
}
```

## Merits

### Centralization Benefits
1. **Single Source of Truth**: All logs in one place
2. **Consistent Format**: Enforced structure across all agents
3. **Easy Querying**: Query logs by run_id
4. **Audit Trail**: Complete workflow history
5. **Debugging Support**: Detailed execution trace

### Technical Advantages
1. **Atomic Appends**: No race conditions with concurrent logging
2. **Type Safety**: Proper DynamoDB type conversion
3. **Retry Logic**: Handles transient failures gracefully
4. **Timestamp Management**: Auto-generates timestamps
5. **Nested Data Support**: Handles complex metadata structures

### Operational Benefits
1. **Fast Logging**: <100ms per log entry
2. **Scalable**: DynamoDB auto-scales with load
3. **Durable**: Logs persisted permanently
4. **Queryable**: Easy to retrieve logs via Flask API
5. **Cost Effective**: Pay-per-request pricing

## Key Design Patterns

### 1. Append-Only Pattern
```python
# Never overwrite, always append
UpdateExpression="SET logs = list_append(if_not_exists(logs, :empty_list), :new_log)"
```

### 2. Create-If-Not-Exists Pattern
```python
try:
    # Try to update
    update_item(...)
except ConditionalCheckFailedException:
    # Create if doesn't exist
    put_item(...)
```

### 3. Type Conversion Pattern
```python
def convert(obj):
    if isinstance(obj, str):
        return {"S": obj}
    elif isinstance(obj, (int, float)):
        return {"N": str(obj)}
    elif isinstance(obj, dict):
        return {"M": {k: convert(v) for k, v in obj.items()}}
    # ... handle all types
```

### 4. Retry Pattern
```python
def retry_with_backoff(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt)
```

## Performance Characteristics

- **Latency**: 50-100ms per log entry
- **Throughput**: 1000+ logs/second (DynamoDB limit)
- **Storage**: Unlimited (DynamoDB auto-scales)
- **Retention**: Permanent (no TTL configured)

## Error Handling

### 1. Missing Required Fields
```python
if "run_id" not in event:
    return {
        "statusCode": 400,
        "body": json.dumps({"error": True, "message": "Missing run_id"})
    }
```

### 2. DynamoDB Errors
```python
try:
    append_log_to_dynamodb(run_id, log_entry)
except ClientError as e:
    return {
        "statusCode": 500,
        "body": json.dumps({
            "error": True,
            "message": f"Failed to append log: {str(e)}"
        })
    }
```

### 3. Retry Exhaustion
```python
try:
    response = retry_with_backoff(append_operation, max_attempts=3)
except Exception as e:
    # Log to CloudWatch and return error
    print(f"Error: Failed after 3 retries: {str(e)}")
    return error_response
```

## Usage Examples

### From Orchestrator
```python
from shared.logger import format_start_log, create_log_entry, LogType

# Start log
log_to_logger(run_id, format_start_log("Orchestrator", "Starting workflow"))

# Status log
log_to_logger(run_id, create_log_entry(
    LogType.STATUS,
    "Step 1: Generating Specifications",
    "Invoking Specs Generator"
))

# Result log
log_to_logger(run_id, create_log_entry(
    LogType.RESULT,
    "Specifications Generated",
    "Specs stored in S3",
    metadata={"s3_path": "s3://..."}
))
```

### From Glue Executor
```python
# Code generation log
log_to_logger(run_id, create_log_entry(
    LogType.CODE,
    "Glue Code Generated",
    "PySpark code created",
    metadata={
        "generated_item": code,
        "path": s3_path,
        "code_size_bytes": len(code)
    }
))
```

### From Validator
```python
# Validation result log
log_to_logger(run_id, create_log_entry(
    LogType.RESULT,
    "Phase 5: Final Analysis Complete",
    f"Validation {status}: {passed}/{total} tests passed",
    metadata={
        "phase": 5,
        "status": status,
        "passed": passed,
        "failed": failed
    }
))
```

## Dependencies

- **boto3**: AWS SDK for DynamoDB
- **datetime**: Timestamp generation
- **Shared modules**: aws_clients, config, utils

## Configuration

```python
# Lambda Configuration
- Memory: 128 MB (minimal)
- Timeout: 30 seconds
- Runtime: Python 3.11

# DynamoDB Configuration
- Table: dmdb_logs
- Partition Key: run_id
- Billing Mode: On-Demand
```

## Future Enhancements

1. **Log Levels**: Add DEBUG, INFO, WARN, ERROR levels
2. **Log Filtering**: Filter logs by type, component, time range
3. **Log Aggregation**: Aggregate logs across multiple runs
4. **Log Analytics**: Built-in analytics and visualization
5. **Log Retention**: Implement TTL for old logs
6. **Log Streaming**: Stream logs to CloudWatch Logs
7. **Log Search**: Full-text search across all logs
8. **Log Compression**: Compress large log entries

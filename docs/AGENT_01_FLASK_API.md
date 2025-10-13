# DataMorph Agent Documentation: Flask API Gateway

## Name
**Flask API Gateway**

## Services Using
- **AWS RDS PostgreSQL**: Database operations (read/write)
- **AWS Lambda**: Orchestrator invocation
- **AWS DynamoDB**: Log retrieval
- **AWS Secrets Manager**: Configuration management

## Input
HTTP REST API requests with JSON payloads:

1. **POST /start** - Start ETL workflow
   ```json
   {
     "prompt": "Natural language ETL description",
     "source_tables": ["table1", "table2"],  // optional
     "target_table": "target_table_name"     // optional
   }
   ```

2. **POST /get/schemas** - Get table schemas
   ```json
   {
     "table_names": ["table1", "table2"]
   }
   ```

3. **POST /get/data** - Get sample data
   ```json
   {
     "table_names": ["table1", "table2"],
     "limit": 10  // optional, default 10
   }
   ```

4. **POST /execute/query** - Execute SQL query
   ```json
   {
     "query": "SELECT * FROM table"
   }
   ```

5. **GET /get/logs/{run_id}** - Retrieve workflow logs

6. **GET /health** - Health check

## Output
JSON responses with appropriate HTTP status codes:

- **Success (200)**: Operation completed successfully
- **Bad Request (400)**: Invalid input parameters
- **Not Found (404)**: Resource not found
- **Internal Error (500)**: Server-side error

Example success response:
```json
{
  "status": "success",
  "run_id": "20250113_123456_abc123",
  "message": "ETL pipeline executed and validated successfully",
  "details": { ... }
}
```

## Objectives

### Primary Objectives
1. **API Gateway**: Provide HTTP interface for external clients to interact with DataMorph
2. **Database Proxy**: Execute database operations on behalf of Lambda functions (which cannot directly access RDS in private VPC)
3. **Workflow Orchestration**: Trigger and coordinate ETL workflows via Orchestrator Lambda
4. **Data Access**: Provide schema introspection and data sampling capabilities
5. **Log Retrieval**: Fetch workflow execution logs from DynamoDB

### Secondary Objectives
1. **Connection Pooling**: Manage database connections efficiently
2. **Error Handling**: Provide meaningful error messages to clients
3. **Logging**: Track all API requests and responses
4. **Health Monitoring**: Expose health check endpoint for monitoring

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Flask API Gateway                       │
│                     (EC2 Instance)                           │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   /start     │  │ /get/schemas │  │  /get/data   │      │
│  │   Endpoint   │  │   Endpoint   │  │   Endpoint   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         ▼                  ▼                  ▼               │
│  ┌──────────────────────────────────────────────────┐       │
│  │         Database Connection Manager              │       │
│  │         (psycopg2 with RealDictCursor)          │       │
│  └──────────────────────────────────────────────────┘       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  AWS Lambda     │  │   RDS PostgreSQL │  │   DynamoDB      │
│  (Orchestrator) │  │   (Database)     │  │   (Logs)        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Detailed Working

### 1. Initialization Phase
- Flask application starts on EC2 instance
- Configures CloudWatch-friendly logging with rotating file handlers
- Loads configuration from AWS Secrets Manager
- Sets up database connection parameters

### 2. Request Processing Flow

#### A. Workflow Initiation (/start)
1. Receives user prompt and optional parameters
2. Creates Lambda client with custom configuration:
   - No retries (prevents duplicate executions)
   - 950-second read timeout (accommodates long-running workflows)
3. Invokes Orchestrator Lambda synchronously
4. Waits for complete workflow execution
5. Returns consolidated results to client

#### B. Schema Retrieval (/get/schemas)
1. Validates input (table names list)
2. Establishes PostgreSQL connection
3. For each table:
   - Queries `information_schema.columns` for column metadata
   - Queries `pg_index` for primary keys
   - Queries `information_schema.table_constraints` for foreign keys
4. Constructs comprehensive schema objects
5. Returns schemas as JSON

#### C. Data Sampling (/get/data)
1. Validates input parameters
2. Connects to database
3. For each table:
   - Executes `SELECT * FROM table ORDER BY RANDOM() LIMIT n`
   - Converts rows to dictionaries using RealDictCursor
4. Returns sample data as JSON

#### D. Query Execution (/execute/query)
1. Receives arbitrary SQL query
2. Logs query for audit trail
3. Executes query with transaction support
4. Handles both SELECT (returns results) and DML (commits changes)
5. Returns results or error details

#### E. Log Retrieval (/get/logs/{run_id})
1. Queries DynamoDB for run_id
2. Parses DynamoDB format (removes type markers)
3. Recursively converts nested structures to clean JSON
4. Returns formatted logs with metadata

### 3. Error Handling Strategy
- **Connection Errors**: Retry with exponential backoff
- **Query Errors**: Rollback transaction, return detailed error
- **Lambda Errors**: Parse response, extract error details
- **Timeout Errors**: Return timeout message with partial results

### 4. Logging Architecture
- **File Logging**: Rotating logs in `/var/log/flask_app.log`
- **Console Logging**: Real-time output for debugging
- **CloudWatch Integration**: Logs forwarded to CloudWatch Logs
- **Structured Logging**: Includes timestamp, level, function, line number

## Merits

### Technical Advantages
1. **VPC Bridge**: Enables Lambda functions to access RDS in private VPC without VPC configuration
2. **Connection Efficiency**: Reuses database connections, reducing overhead
3. **Synchronous Execution**: Provides blocking API for workflow completion
4. **Schema Introspection**: Automatic discovery of database structure
5. **Random Sampling**: Efficient data sampling using PostgreSQL's RANDOM()

### Operational Benefits
1. **Centralized Access**: Single point of entry for all database operations
2. **Audit Trail**: Complete logging of all database queries
3. **Error Isolation**: Database errors don't crash Lambda functions
4. **Health Monitoring**: Built-in health check for monitoring systems
5. **Scalability**: Can handle multiple concurrent requests

### Development Benefits
1. **Simple Interface**: RESTful API with JSON payloads
2. **Type Safety**: Uses RealDictCursor for dictionary-based results
3. **Extensibility**: Easy to add new endpoints
4. **Testing**: Can be tested independently of Lambda functions

## Key Design Patterns

### 1. Database Connection Management
```python
def get_db_connection():
    """Create PostgreSQL database connection."""
    return psycopg2.connect(
        host=config.rds_endpoint,
        port=config.rds_port,
        database=config.rds_dbname,
        user=config.rds_username,
        password=config.rds_password
    )
```
- Creates new connection per request (stateless)
- Uses connection pooling at PostgreSQL level
- Automatically closes connections after use

### 2. Lambda Invocation with Timeout Handling
```python
lambda_config = Config(
    retries={'max_attempts': 0},  # No retries
    read_timeout=950,  # 950 seconds
    connect_timeout=10
)
```
- Prevents duplicate workflow executions
- Accommodates long-running Glue jobs
- Fails fast on connection issues

### 3. DynamoDB Format Parsing
```python
def parse_dynamodb_value(value):
    """Recursively parse DynamoDB value format to clean JSON."""
    if "S" in value: return value["S"]
    elif "N" in value: return float/int(value["N"])
    elif "M" in value: return {k: parse(v) for k, v in value["M"].items()}
    # ... handles all DynamoDB types
```
- Removes DynamoDB type markers (S, N, M, L, etc.)
- Recursively processes nested structures
- Converts to native Python types

## Performance Characteristics

- **Startup Time**: ~2-3 seconds
- **Schema Query**: ~100-200ms per table
- **Data Sampling**: ~50-100ms per table (10 rows)
- **Workflow Invocation**: 60-900 seconds (depends on ETL complexity)
- **Log Retrieval**: ~200-500ms

## Security Considerations

1. **Credentials**: Stored in AWS Secrets Manager, never hardcoded
2. **SQL Injection**: Uses parameterized queries for user input
3. **Access Control**: Runs in private subnet, not publicly accessible
4. **Audit Logging**: All queries logged for compliance
5. **Error Messages**: Sanitized to prevent information disclosure

## Deployment Configuration

- **Platform**: EC2 instance (Ubuntu)
- **Web Server**: Gunicorn with 4 workers
- **Port**: 5000 (internal)
- **Process Manager**: systemd service
- **Logging**: CloudWatch Logs agent
- **Monitoring**: CloudWatch metrics

## Dependencies

- **Flask**: Web framework
- **psycopg2**: PostgreSQL adapter
- **boto3**: AWS SDK
- **gunicorn**: WSGI HTTP server
- **requests**: HTTP client (for testing)

## Future Enhancements

1. **Connection Pooling**: Implement pgbouncer or SQLAlchemy pooling
2. **Caching**: Cache schema metadata to reduce database queries
3. **Rate Limiting**: Prevent abuse with request throttling
4. **Authentication**: Add API key or OAuth authentication
5. **Async Support**: Use async/await for concurrent operations
6. **GraphQL**: Alternative query interface for complex data fetching

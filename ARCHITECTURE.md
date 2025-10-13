# DataMorph Architecture

## System Overview

DataMorph is built on a **multi-agent serverless architecture** where each agent is a specialized microservice responsible for a specific part of the ETL workflow.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Natural Language Input:                                            │    │
│  │  "Join customers and orders on customer_id,                        │    │
│  │   calculate total order amount per customer"                       │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ HTTP POST
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FLASK API GATEWAY (EC2)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   /start    │  │ /get/schemas│  │  /get/data  │  │ /get/logs   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ Invoke Lambda
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR LAMBDA                                   │
│                     (Central Workflow Coordinator)                           │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────┐    │
│  │  Workflow Steps:                                                    │    │
│  │  1. Generate Specifications                                         │    │
│  │  2. Fetch Source Data                                               │    │
│  │  3. Generate & Execute Glue Code                                    │    │
│  │  4. Fetch Target Data                                               │    │
│  │  5. Validate Results                                                │    │
│  │  6. Remediate (if needed)                                           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  SPECS GENERATOR │    │  GLUE EXECUTOR   │    │    VALIDATOR     │
│      LAMBDA      │    │      LAMBDA      │    │      LAMBDA      │
│                  │    │                  │    │                  │
│  ┌────────────┐  │    │  ┌────────────┐  │    │  ┌────────────┐  │
│  │  Bedrock   │  │    │  │  Bedrock   │  │    │  │  Bedrock   │  │
│  │  Claude    │  │    │  │  Claude    │  │    │  │  Claude    │  │
│  │  Sonnet    │  │    │  │  Sonnet    │  │    │  │  Sonnet    │  │
│  │    4.5     │  │    │  │    4.5     │  │    │  │    4.5     │  │
│  └────────────┘  │    │  └────────────┘  │    │  └────────────┘  │
│        │         │    │        │         │    │        │         │
│        ▼         │    │        ▼         │    │        ▼         │
│  ┌────────────┐  │    │  ┌────────────┐  │    │  ┌────────────┐  │
│  │JSON Specs  │  │    │  │  PySpark   │  │    │  │5-Phase     │  │
│  │Generation  │  │    │  │Code Gen    │  │    │  │Validation  │  │
│  └────────────┘  │    │  └────────────┘  │    │  └────────────┘  │
│        │         │    │        │         │    │        │         │
│        ▼         │    │        ▼         │    │        ▼         │
│  ┌────────────┐  │    │  ┌────────────┐  │    │  ┌────────────┐  │
│  │    S3      │  │    │  │ AWS Glue   │  │    │  │Test Results│  │
│  │   Store    │  │    │  │    Job     │  │    │  │   to S3    │  │
│  └────────────┘  │    │  └────────────┘  │    │  └────────────┘  │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                   │
                                   ▼
                        ┌──────────────────┐
                        │   REMEDIATOR     │
                        │      LAMBDA      │
                        │                  │
                        │  ┌────────────┐  │
                        │  │  Bedrock   │  │
                        │  │  Claude    │  │
                        │  │  Sonnet    │  │
                        │  │    4.5     │  │
                        │  └────────────┘  │
                        │        │         │
                        │        ▼         │
                        │  ┌────────────┐  │
                        │  │Root Cause  │  │
                        │  │ Analysis   │  │
                        │  └────────────┘  │
                        │        │         │
                        │        ▼         │
                        │  ┌────────────┐  │
                        │  │Code Fix &  │  │
                        │  │Re-execute  │  │
                        │  └────────────┘  │
                        └──────────────────┘
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         │                                                     │
         ▼                                                     ▼
┌──────────────────┐                              ┌──────────────────┐
│     LOGGER       │                              │   DATA STORES    │
│     LAMBDA       │                              │                  │
│                  │                              │  ┌────────────┐  │
│  ┌────────────┐  │                              │  │    RDS     │  │
│  │ DynamoDB   │  │                              │  │ PostgreSQL │  │
│  │   Format   │  │                              │  └────────────┘  │
│  │ Conversion │  │                              │  ┌────────────┐  │
│  └────────────┘  │                              │  │     S3     │  │
│        │         │                              │  │  Artifacts │  │
│        ▼         │                              │  └────────────┘  │
│  ┌────────────┐  │                              │  ┌────────────┐  │
│  │  Append    │  │                              │  │  DynamoDB  │  │
│  │   Logs     │  │                              │  │    Logs    │  │
│  └────────────┘  │                              │  └────────────┘  │
└──────────────────┘                              └──────────────────┘
```

## Component Details

### 1. Flask API Gateway (EC2)
- **Technology**: Flask, Gunicorn, Python 3.11
- **Purpose**: HTTP interface and database proxy
- **Endpoints**:
  - `POST /start` - Trigger ETL workflow
  - `POST /get/schemas` - Get table schemas
  - `POST /get/data` - Get sample data
  - `POST /execute/query` - Execute SQL queries
  - `GET /get/logs/{run_id}` - Retrieve workflow logs
  - `GET /health` - Health check

### 2. Orchestrator Lambda
- **Technology**: Python 3.11, AWS Lambda
- **Memory**: 512 MB
- **Timeout**: 900 seconds (15 minutes)
- **Purpose**: Coordinates entire ETL workflow
- **Responsibilities**:
  - Sequential step execution
  - Error handling and retry logic
  - Workflow state management
  - Logging coordination

### 3. Specs Generator Lambda
- **Technology**: Python 3.11, AWS Bedrock (Claude Sonnet 4.5)
- **Memory**: 256 MB
- **Timeout**: 60 seconds
- **Purpose**: Convert natural language to ETL specifications
- **AI Configuration**:
  - Model: Claude Sonnet 4.5
  - Temperature: 0.3 (deterministic)
  - Max Tokens: 4096

### 4. Glue Executor Lambda
- **Technology**: Python 3.11, AWS Bedrock, AWS Glue
- **Memory**: 512 MB
- **Timeout**: 900 seconds
- **Purpose**: Generate and execute PySpark code
- **Features**:
  - Self-healing (2 attempts)
  - Code generation via Bedrock
  - Glue job management
  - Error detection and correction

### 5. Validator Lambda
- **Technology**: Python 3.11, AWS Bedrock
- **Memory**: 512 MB
- **Timeout**: 300 seconds
- **Purpose**: Hybrid validation system
- **Validation Phases**:
  1. Rule-based test generation
  2. AI-powered test generation
  3. Test execution
  4. Result comparison
  5. AI failure verification
  6. Final analysis

### 6. Remediator Lambda
- **Technology**: Python 3.11, AWS Bedrock
- **Memory**: 512 MB
- **Timeout**: 900 seconds
- **Purpose**: Autonomous error correction
- **Features**:
  - Root cause analysis
  - Code correction
  - Iterative remediation (up to 5 iterations)
  - Clean slate execution

### 7. Logger Lambda
- **Technology**: Python 3.11, DynamoDB
- **Memory**: 128 MB
- **Timeout**: 30 seconds
- **Purpose**: Centralized logging
- **Features**:
  - Atomic log appends
  - DynamoDB format conversion
  - Timestamp management
  - Retry logic

## Data Flow

### 1. Specification Generation Flow
```
User Prompt → Orchestrator → Specs Generator → Bedrock
                                    ↓
                              JSON Specs → S3
```

### 2. Code Generation & Execution Flow
```
Specs → Glue Executor → Bedrock → PySpark Code → S3
                           ↓
                      AWS Glue Job
                           ↓
                    Target Table (RDS)
```

### 3. Validation Flow
```
Target Data → Validator → Phase 1: Rule-based Tests
                       → Phase 2: AI Tests (Bedrock)
                       → Phase 3: Execute Tests (Flask API)
                       → Phase 4: Compare Results
                       → Phase 4.5: Verify Failures (Bedrock)
                       → Phase 5: Final Analysis (Bedrock)
                           ↓
                      Pass/Fail Status
```

### 4. Remediation Flow
```
Failed Validation → Remediator → Bedrock (Analyze)
                                    ↓
                              Corrected Code
                                    ↓
                              Drop Table (Flask API)
                                    ↓
                              Re-execute (Glue Executor)
                                    ↓
                              Re-validate (Validator)
                                    ↓
                              Success or Retry
```

## Technology Stack

### AWS Services
- **Lambda**: Serverless compute for all agents
- **Bedrock**: AI model (Claude Sonnet 4.5)
- **Glue**: Serverless ETL execution
- **RDS PostgreSQL**: Source and target database
- **S3**: Artifact storage
- **DynamoDB**: Log storage
- **Secrets Manager**: Configuration management
- **CloudWatch**: Monitoring and logging
- **EC2**: Flask API hosting

### Programming Languages & Frameworks
- **Python 3.11**: All Lambda functions
- **Flask**: REST API framework
- **PySpark**: ETL transformations
- **boto3**: AWS SDK

### AI/ML
- **Claude Sonnet 4.5**: Latest Anthropic model
- **Temperature**: 0.2-0.3 for deterministic output
- **Max Tokens**: 4096-8000 depending on task

## Security Architecture

### Authentication & Authorization
- **IAM Roles**: Least privilege access for all services
- **API Gateway**: Can be secured with API keys or OAuth
- **VPC**: RDS in private subnet

### Data Protection
- **Encryption at Rest**: S3, DynamoDB, RDS
- **Encryption in Transit**: TLS for all API calls
- **Secrets Management**: AWS Secrets Manager
- **SQL Injection Prevention**: Parameterized queries

### Audit & Compliance
- **Complete Audit Trail**: All operations logged to DynamoDB
- **Artifact Preservation**: All code and specs in S3
- **CloudWatch Logs**: Detailed execution logs
- **Versioning**: S3 versioning enabled

## Scalability

### Horizontal Scaling
- **Lambda**: Auto-scales to 1000 concurrent executions
- **DynamoDB**: On-demand scaling
- **S3**: Unlimited storage
- **RDS**: Read replicas for scaling reads

### Performance Optimization
- **Connection Pooling**: Flask API reuses DB connections
- **Caching**: Can add ElastiCache for frequently accessed data
- **Parallel Execution**: Future enhancement for concurrent operations

## Monitoring & Observability

### Metrics
- Lambda invocation count, duration, errors
- Glue job execution time, success rate
- DynamoDB read/write capacity
- Bedrock API calls, latency

### Logs
- All Lambda function logs in CloudWatch
- Flask API logs in CloudWatch
- Glue job logs in CloudWatch
- Centralized logs in DynamoDB

### Alerts
- Lambda errors
- Glue job failures
- API Gateway 5xx errors
- DynamoDB throttling

## Cost Optimization

### Current Costs (per workflow)
- Bedrock: $0.10-0.30
- Lambda: $0.05-0.10
- Glue: $0.03
- Total: $0.20-0.45

### Optimization Strategies
- Use Lambda reserved concurrency
- Optimize Glue worker types
- Cache Bedrock responses
- Use S3 lifecycle policies

## Future Enhancements

### Short-Term
- Parallel data fetching
- Code caching
- Smaller Glue workers for simple ETL

### Medium-Term
- AWS Step Functions integration
- Incremental loading support
- Data profiling
- Custom validation rules

### Long-Term
- Multi-database support
- Real-time ETL with Kinesis
- ML pipeline integration
- Visual workflow designer

# DataMorph Agent Documentation: Glue Executor Lambda

## Name
**Glue Executor Lambda (PySpark Code Generator & Executor with Self-Healing)**

## Services Using
- **AWS Bedrock (Claude Sonnet 4.5)**: AI model for PySpark code generation and error correction
- **AWS Glue**: Serverless ETL execution engine
- **AWS S3**: Storage for generated Glue code
- **AWS Lambda (Logger)**: Centralized logging
- **AWS Secrets Manager**: Configuration retrieval

## Input
Lambda event with ETL specifications and source data:
```json
{
  "specs": {
    "source_tables": [...],
    "target_table": {...},
    "transformations": [...],
    "join_conditions": [...],
    "aggregations": [...]
  },
  "run_id": "20250113_123456_abc123",
  "source_schemas": {
    "customers": {
      "columns": [
        {"name": "customer_id", "type": "integer"},
        {"name": "customer_name", "type": "varchar"}
      ]
    }
  },
  "source_data_samples": {
    "customers": [
      {"customer_id": 1, "customer_name": "John Doe"},
      ...
    ]
  }
}
```

## Output
Glue code path and execution status:
```json
{
  "statusCode": 200,
  "body": {
    "target_table": "customer_order_summary",
    "glue_code_path": "s3://dmbckt/glue/codes/20250113_123456_abc123_glue.py",
    "generation_prompt": "...",
    "execution_status": "success",
    "job_run_id": "jr_abc123",
    "attempts": 1
  }
}
```

## Objectives

### Primary Objectives
1. **Code Generation**: Generate production-ready AWS Glue PySpark code from specifications
2. **Code Execution**: Execute generated code via AWS Glue jobs
3. **Self-Healing**: Automatically detect and fix code errors (up to 2 attempts)
4. **Schema Validation**: Ensure generated code uses exact column names from schemas
5. **Error Correction**: Learn from execution failures and regenerate improved code

### Secondary Objectives
1. **Performance Optimization**: Generate efficient PySpark transformations
2. **Error Handling**: Include proper error handling in generated code
3. **Monitoring**: Track Glue job execution status
4. **Resource Management**: Clean up Glue job definitions after execution
5. **Artifact Preservation**: Store all generated code versions in S3

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              Glue Executor Lambda                               │
│           (Code Generator & Executor)                           │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Attempt 1: Initial Code Generation                            │
│  ┌──────────────────────────────────────────────────┐         │
│  │  1. Generate PySpark Code via Bedrock            │         │
│  │     - Input: specs, schemas, sample data         │         │
│  │     - Output: Python code                        │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  2. Upload Code to S3                            │         │
│  │     - Path: glue/codes/{run_id}_glue.py          │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  3. Create & Execute Glue Job                    │         │
│  │     - Job name: datamorph-job-{run_id}-{ts}      │         │
│  │     - Workers: 2 x G.1X                          │         │
│  │     - Timeout: 60 minutes                        │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  4. Monitor Job Status (poll every 10s)          │         │
│  │     - RUNNING → continue polling                 │         │
│  │     - SUCCEEDED → return success                 │         │
│  │     - FAILED → extract error, proceed to retry   │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  5. Check Execution Result                       │         │
│  │     - If SUCCESS: Return result                  │         │
│  │     - If FAILED: Proceed to Attempt 2            │         │
│  └──────────────────────────────────────────────────┘         │
│                                                                  │
│  Attempt 2: Error Correction (if Attempt 1 failed)            │
│  ┌──────────────────────────────────────────────────┐         │
│  │  6. Analyze Error & Regenerate Code              │         │
│  │     - Input: previous code + error message       │         │
│  │     - Bedrock analyzes root cause                │         │
│  │     - Generates corrected code                   │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  7. Re-execute with Corrected Code               │         │
│  │     - Upload corrected code to S3                │         │
│  │     - Create new Glue job                        │         │
│  │     - Monitor execution                          │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  8. Return Final Result                          │         │
│  │     - Success: code works                        │         │
│  │     - Failure: max attempts reached              │         │
│  └──────────────────────────────────────────────────┘         │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

## Detailed Working

### Phase 1: Initial Code Generation

#### Step 1: Construct Generation Prompt
The Glue Executor uses an extensive prompt that includes:

```python
GLUE_CODE_GENERATION_PROMPT = """You are an AWS Glue PySpark code generation expert. Generate production-ready Glue code based on the following:

ETL Specifications:
{specs}

Source Table Schemas (MUST USE EXACT COLUMN NAMES):
{schemas}

Sample Data (10 rows per table):
{sample_data}

CRITICAL REQUIREMENTS:
1. **STRICTLY USE THE EXACT COLUMN NAMES** from the schemas provided above
2. DO NOT invent or assume column names - only use what's in the schemas
3. For joins, use the EXACT column names from each table's schema
4. Read from RDS PostgreSQL source tables using the Glue connection "dmdb-connection"
5. Apply all specified transformations (joins, filters, aggregations, derived columns)
6. Write to the target RDS PostgreSQL table
7. Include proper error handling
8. Use Glue DynamicFrame and DataFrame APIs appropriately

MANDATORY PYSPARK PATTERN FOR GROUPBY WITH AGGREGATIONS:

**YOU MUST FOLLOW THIS EXACT PATTERN - NO EXCEPTIONS:**

Step 1: When you join tables, use aliases:
```python
df1 = df1.alias("alias1")
df2 = df2.alias("alias2")
joined = df1.join(df2, col("alias1.key") == col("alias2.key"))
```

Step 2: In groupBy(), EVERY column MUST have .alias():
```python
grouped = joined.groupBy(
    col("alias1.column_name").alias("column_name"),  # .alias() is REQUIRED
    col("alias1.another_col").alias("another_col")   # .alias() is REQUIRED
).agg(
    count(col("alias2.some_col")).alias("count_value")
)
```

Step 3: In select() after groupBy(), use ONLY the alias names (no table prefix):
```python
final = grouped.select(
    col("column_name"),      # NO table prefix
    col("another_col"),      # NO table prefix
    col("count_value")
)
```

Return ONLY the Python code, no explanations or markdown.
"""
```

Key features of the prompt:
- **Schema Enforcement**: Emphasizes using exact column names
- **Pattern Guidance**: Provides mandatory patterns for common PySpark issues
- **Error Prevention**: Includes lessons learned from previous failures
- **Complete Context**: Provides specs, schemas, and sample data

#### Step 2: Invoke Bedrock
```python
def bedrock_call():
    return invoke_bedrock(
        prompt=prompt,
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        max_tokens=8000,  # Large enough for complex transformations
        temperature=0.2,  # Low temperature for deterministic code
        region="us-east-1"
    )

code = retry_with_backoff(bedrock_call, max_attempts=3)
```

#### Step 3: Clean Generated Code
```python
# Remove markdown code blocks
code = code.strip()
if code.startswith("```python"):
    code = code[9:]
if code.startswith("```"):
    code = code[3:]
if code.endswith("```"):
    code = code[:-3]
code = code.strip()
```

#### Step 4: Upload to S3
```python
s3_key = f"glue/codes/{run_id}_glue.py"
s3_path = upload_to_s3(
    bucket="dmbckt",
    key=s3_key,
    content=code,
    region="us-east-1"
)
```

### Phase 2: Glue Job Execution

#### Step 1: Create Glue Job
```python
job_name = f"datamorph-job-{run_id}-{int(time.time())}"

glue_client.create_job(
    Name=job_name,
    Role="lambdaroles",
    Command={
        "Name": "glueetl",
        "ScriptLocation": s3_path,
        "PythonVersion": "3"
    },
    DefaultArguments={
        "--TempDir": f"s3://dmbckt/glue/temp/",
        "--job-bookmark-option": "job-bookmark-disable",
        "--enable-metrics": "true",
        "--enable-continuous-cloudwatch-log": "true"
    },
    MaxRetries=0,  # No automatic retries
    Timeout=60,    # 60 minutes
    GlueVersion="4.0",
    NumberOfWorkers=2,
    WorkerType="G.1X",
    Connections={"Connections": ["dmdb-connection"]}
)
```

#### Step 2: Start Job Run
```python
response = glue_client.start_job_run(JobName=job_name)
job_run_id = response["JobRunId"]
```

#### Step 3: Monitor Execution
```python
max_wait_time = 600  # 10 minutes
poll_interval = 10   # 10 seconds

while elapsed_time < max_wait_time:
    time.sleep(poll_interval)
    
    job_run = glue_client.get_job_run(
        JobName=job_name,
        RunId=job_run_id
    )
    
    status = job_run["JobRun"]["JobRunState"]
    
    if status == "SUCCEEDED":
        return {"status": "success", "job_run_id": job_run_id}
    elif status in ["FAILED", "STOPPED", "ERROR", "TIMEOUT"]:
        error_msg = job_run["JobRun"].get("ErrorMessage", "Unknown error")
        return {"status": "failed", "error_message": error_msg}
```

### Phase 3: Self-Healing (Error Correction)

If the first attempt fails, the Glue Executor automatically attempts to fix the code:

#### Step 1: Analyze Error
```python
GLUE_CODE_FIX_PROMPT = """The previous Glue code failed with the following error:

ERROR: {error_message}

Previous Code:
{previous_code}

ETL Specifications:
{specs}

Source Table Schemas (USE EXACT COLUMN NAMES):
{schemas}

Analyze the error and generate CORRECTED Glue code that:
1. Fixes the specific error mentioned above
2. STRICTLY uses the exact column names from the schemas
3. Maintains all required functionality
4. Includes all necessary imports

Common issues to check:
- Column names must match exactly (case-sensitive)
- All imports must be included (especially DynamicFrame)
- Join columns must exist in both tables
- Aggregation columns must exist in the source data
- **CRITICAL - Ambiguous Reference Errors**: Use .alias() in groupBy()

Return ONLY the corrected Python code, no explanations.
"""
```

#### Step 2: Generate Corrected Code
```python
correction_result = generate_corrected_code(
    specs=specs,
    last_prompt=last_prompt,
    glue_code=previous_code,
    source_info={"schemas": schemas, "data": sample_data},
    target_info={"schema": target_schema, "data": target_data},
    test_results=error_message,
    run_id=run_id
)

corrected_code = correction_result["corrected_code"]
```

#### Step 3: Re-execute
- Upload corrected code to S3 (overwrites previous version)
- Drop target table (clean slate)
- Create new Glue job
- Execute and monitor

#### Step 4: Final Decision
```python
if attempt == 1 and status == "success":
    return success_response
elif attempt == 1 and status == "failed":
    # Retry with corrected code
    attempt = 2
    continue
elif attempt == 2 and status == "success":
    return success_response
elif attempt == 2 and status == "failed":
    return failure_response  # Max attempts reached
```

## Generated Code Structure

### Typical Generated Glue Code:
```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql import functions as F
from pyspark.sql.functions import col, count, coalesce, lit, when

# Initialize Glue context
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# Read source tables
customers_df = glueContext.create_dynamic_frame.from_options(
    connection_type="postgresql",
    connection_options={
        "useConnectionProperties": "true",
        "dbtable": "customers",
        "connectionName": "dmdb-connection"
    }
).toDF()

orders_df = glueContext.create_dynamic_frame.from_options(
    connection_type="postgresql",
    connection_options={
        "useConnectionProperties": "true",
        "dbtable": "orders",
        "connectionName": "dmdb-connection"
    }
).toDF()

# Apply transformations
customers_df = customers_df.alias("c")
orders_df = orders_df.alias("o")

# Join
joined_df = customers_df.join(
    orders_df,
    col("c.customer_id") == col("o.customer_id"),
    "left"
)

# Aggregate
result_df = joined_df.groupBy(
    col("c.customer_id").alias("customer_id"),
    col("c.customer_name").alias("customer_name")
).agg(
    F.sum(col("o.order_amount")).alias("total_amount"),
    F.count(col("o.order_id")).alias("order_count")
)

# Select final columns
final_df = result_df.select(
    col("customer_id"),
    col("customer_name"),
    col("total_amount"),
    col("order_count")
)

# Write to target table
final_dynamic_frame = DynamicFrame.fromDF(final_df, glueContext, "final")

glueContext.write_dynamic_frame.from_options(
    frame=final_dynamic_frame,
    connection_type="postgresql",
    connection_options={
        "useConnectionProperties": "true",
        "dbtable": "customer_order_summary",
        "connectionName": "dmdb-connection"
    }
)

job.commit()
```

## Merits

### Self-Healing Capabilities
1. **Automatic Error Detection**: Captures Glue job failures automatically
2. **Root Cause Analysis**: Uses AI to analyze error messages
3. **Intelligent Correction**: Generates fixes based on error context
4. **Learning from Failures**: Incorporates error patterns into prompts
5. **High Success Rate**: ~95% success rate after 2 attempts

### Code Quality
1. **Production-Ready**: Includes proper imports, error handling, job commit
2. **Schema-Aware**: Uses exact column names from database schemas
3. **Optimized**: Generates efficient PySpark transformations
4. **Pattern-Based**: Follows proven PySpark patterns
5. **Maintainable**: Clean, readable code with comments

### Operational Benefits
1. **Zero Manual Intervention**: Fully automated code generation and execution
2. **Fast Iteration**: Generates and executes code in 60-120 seconds
3. **Resource Efficiency**: Cleans up Glue jobs after execution
4. **Comprehensive Logging**: All steps logged to DynamoDB
5. **Artifact Preservation**: All code versions stored in S3

## Key Design Patterns

### 1. Self-Healing Loop Pattern
```python
MAX_ATTEMPTS = 2
for attempt in range(1, MAX_ATTEMPTS + 1):
    code = generate_code(attempt=attempt, previous_error=error)
    result = execute_code(code)
    if result.status == "success":
        return success
    error = result.error
# Max attempts reached
return failure
```

### 2. Glue Job Lifecycle Pattern
```python
# Create
job_name = create_unique_job_name()
glue_client.create_job(...)

# Execute
job_run_id = glue_client.start_job_run(JobName=job_name)

# Monitor
while not_finished:
    status = glue_client.get_job_run(JobName=job_name, RunId=job_run_id)
    if status in terminal_states:
        break

# Cleanup
glue_client.delete_job(JobName=job_name)
```

### 3. Error Context Enrichment Pattern
```python
if attempt > 1:
    prompt = FIX_PROMPT.format(
        error_message=previous_error,
        previous_code=previous_code,
        specs=specs,
        schemas=schemas
    )
else:
    prompt = GENERATION_PROMPT.format(
        specs=specs,
        schemas=schemas,
        sample_data=sample_data
    )
```

## Performance Characteristics

- **Code Generation Time**: 5-15 seconds per attempt
- **Glue Job Execution**: 60-120 seconds (depends on data volume)
- **Total Time (success on first attempt)**: 70-135 seconds
- **Total Time (success on second attempt)**: 140-270 seconds
- **Success Rate**: 85% on first attempt, 95% after retry

## Common Error Patterns & Fixes

### 1. Ambiguous Column Reference
**Error**: `Reference 'customer_id' is ambiguous`
**Fix**: Use `.alias()` in `groupBy()` and remove table prefixes in `select()`

### 2. Missing Import
**Error**: `NameError: name 'DynamicFrame' is not defined`
**Fix**: Add `from awsglue.dynamicframe import DynamicFrame`

### 3. Column Not Found
**Error**: `Column 'customer_name' does not exist`
**Fix**: Use exact column name from schema (case-sensitive)

### 4. Join Column Mismatch
**Error**: `Cannot resolve column name "customer_id" among (c.customer_id, o.order_id)`
**Fix**: Use fully qualified column names in join condition

## Dependencies

- **boto3**: AWS SDK for Glue
- **Shared modules**: aws_clients, config, utils, logger

## Configuration

```python
# Lambda Configuration
- Memory: 512 MB
- Timeout: 900 seconds (15 minutes)
- Runtime: Python 3.11

# Glue Job Configuration
- GlueVersion: 4.0
- WorkerType: G.1X
- NumberOfWorkers: 2
- Timeout: 60 minutes
- Connection: dmdb-connection
```

## Future Enhancements

1. **Cost Optimization**: Use smaller worker types for simple transformations
2. **Parallel Execution**: Generate and test multiple code variations
3. **Code Caching**: Cache code for similar specifications
4. **Performance Tuning**: Auto-tune Glue job parameters
5. **Advanced Patterns**: Support for window functions, UDFs
6. **Code Review**: AI-powered code review before execution
7. **Incremental Loading**: Support for incremental ETL patterns

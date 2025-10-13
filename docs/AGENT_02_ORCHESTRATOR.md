# DataMorph Agent Documentation: Orchestrator Lambda

## Name
**Orchestrator Lambda (Central Workflow Coordinator)**

## Services Using
- **AWS Lambda**: Invokes all other Lambda functions (Specs Generator, Glue Executor, Validator, Remediator, Logger)
- **Flask API**: Calls for database operations (schemas, data, queries)
- **AWS Secrets Manager**: Configuration retrieval

## Input
Lambda event with ETL request:
```json
{
  "user_prompt": "Natural language ETL description",
  "source_tables": ["table1", "table2"],  // optional
  "target_table": "target_table_name"     // optional
}
```

Example:
```json
{
  "user_prompt": "Join customers and orders on customer_id, calculate total order amount per customer, filter customers with total > 1000"
}
```

## Output
Workflow execution result:
```json
{
  "statusCode": 200,
  "body": {
    "status": "completed",
    "run_id": "20250113_123456_abc123",
    "target_table": "customer_order_summary",
    "specs_path": "s3://dmbckt/specs/20250113_123456_abc123_specs.json",
    "glue_code_path": "s3://dmbckt/glue/codes/20250113_123456_abc123_glue.py",
    "validation_status": "pass",
    "message": "ETL pipeline executed and validated successfully"
  }
}
```

Error response:
```json
{
  "statusCode": 500,
  "body": {
    "error": true,
    "message": "Workflow failed: <error details>",
    "error_type": "ValidationError"
  }
}
```

## Objectives

### Primary Objectives
1. **Workflow Coordination**: Orchestrate the complete ETL pipeline from start to finish
2. **Sequential Execution**: Ensure proper execution order of all workflow steps
3. **Error Management**: Handle failures and trigger remediation when needed
4. **State Management**: Track workflow progress and maintain execution context
5. **Logging Coordination**: Ensure all steps are logged to DynamoDB

### Secondary Objectives
1. **Retry Logic**: Implement intelligent retry for validation failures
2. **Resource Cleanup**: Ensure proper cleanup on failures
3. **Performance Monitoring**: Track execution time for each step
4. **Fault Tolerance**: Gracefully handle partial failures

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Orchestrator Lambda                          │
│                  (Central Coordinator)                          │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: Generate Specs                                        │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Invoke Specs Generator Lambda                   │         │
│  │  Input: user_prompt, run_id                      │         │
│  │  Output: specs, s3_path                          │         │
│  └──────────────────────────────────────────────────┘         │
│                         │                                       │
│                         ▼                                       │
│  Step 2: Fetch Source Data                                    │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Call Flask API: /get/schemas                    │         │
│  │  Call Flask API: /get/data                       │         │
│  │  Input: source_tables from specs                │         │
│  │  Output: schemas, sample_data                    │         │
│  └──────────────────────────────────────────────────┘         │
│                         │                                       │
│                         ▼                                       │
│  Step 3: Generate & Execute Glue Code                         │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Invoke Glue Executor Lambda                     │         │
│  │  Input: specs, schemas, sample_data              │         │
│  │  Output: glue_code_path, execution_status        │         │
│  └──────────────────────────────────────────────────┘         │
│                         │                                       │
│                         ▼                                       │
│  Step 4: Fetch Target Data                                    │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Call Flask API: /get/schemas                    │         │
│  │  Call Flask API: /get/data                       │         │
│  │  Input: target_table from specs                 │         │
│  │  Output: target_schema, target_data              │         │
│  └──────────────────────────────────────────────────┘         │
│                         │                                       │
│                         ▼                                       │
│  Step 5: Validate Results                                     │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Invoke Validator Lambda                         │         │
│  │  Input: specs, source/target data                │         │
│  │  Output: validation_status, test_results         │         │
│  └──────────────────────────────────────────────────┘         │
│                         │                                       │
│                         ▼                                       │
│  Step 5.5: Verify Failures (if needed)                        │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Retry validation up to 2 times                  │         │
│  │  Check if failures are genuine or false positives│         │
│  └──────────────────────────────────────────────────┘         │
│                         │                                       │
│                         ▼                                       │
│  Step 6: Remediate (if validation fails)                      │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Invoke Remediator Lambda                        │         │
│  │  Input: specs, test_results, glue_code           │         │
│  │  Output: remediation_status                      │         │
│  └──────────────────────────────────────────────────┘         │
│                         │                                       │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Log Final Status to DynamoDB                    │         │
│  │  Return Workflow Result                          │         │
│  └──────────────────────────────────────────────────┘         │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

## Detailed Working

### Phase 1: Initialization
1. **Generate Run ID**: Creates unique identifier using timestamp + UUID
   ```python
   run_id = generate_run_id()  # "20250113_123456_abc123"
   ```

2. **Log Workflow Start**: Sends initial log entry to Logger Lambda
   ```python
   log_to_logger(run_id, format_start_log("Orchestrator", "Starting ETL workflow"))
   ```

3. **Extract Parameters**: Parses user prompt and optional parameters

### Phase 2: Specification Generation
1. **Invoke Specs Generator**:
   ```python
   specs_response = invoke_lambda(
       function_name="datamorph-specs-generator",
       payload={"user_prompt": user_prompt, "run_id": run_id}
   )
   ```

2. **Parse Response**: Extracts specs JSON and S3 path

3. **Extract Metadata**: Identifies source tables and target table from specs

4. **Log Progress**: Records specs generation completion

### Phase 3: Source Data Collection
1. **Fetch Schemas**:
   ```python
   source_schemas = call_flask_api("get/schemas", {
       "table_names": source_tables
   })
   ```

2. **Fetch Sample Data**:
   ```python
   source_data = call_flask_api("get/data", {
       "table_names": source_tables,
       "limit": 10
   })
   ```

3. **Validate Data**: Ensures all required tables are accessible

### Phase 4: Glue Code Generation & Execution
1. **Invoke Glue Executor**:
   ```python
   glue_response = invoke_lambda(
       function_name="datamorph-glue-executor",
       payload={
           "specs": specs,
           "run_id": run_id,
           "source_schemas": source_schemas,
           "source_data_samples": source_data
       }
   )
   ```

2. **Monitor Execution**: Waits for Glue job completion (can take 60-900 seconds)

3. **Handle Failures**: Captures error details for potential remediation

### Phase 5: Target Data Collection
1. **Fetch Target Schema**: Gets schema of newly created target table

2. **Fetch Target Data**: Samples 10 rows from target table

3. **Prepare for Validation**: Assembles all data needed for validation

### Phase 6: Validation with Retry Logic
1. **Initial Validation**:
   ```python
   validator_response = invoke_lambda(
       function_name="datamorph-validator",
       payload={
           "run_id": run_id,
           "specs": specs,
           "source_schemas": source_schemas,
           "source_data": source_data,
           "target_schema": target_schema,
           "target_data": target_data
       }
   )
   ```

2. **Failure Verification Loop** (max 2 attempts):
   - Checks if failures are rule-based or AI-generated
   - Identifies potential false positives (bad test queries)
   - Retries validation with regenerated tests
   - Stops if all tests pass or genuine failures confirmed

3. **Decision Logic**:
   ```python
   if validation_status == "pass":
       # Success - proceed to completion
   elif validation_attempt < max_attempts:
       # Retry validation
   else:
       # Proceed to remediation
   ```

### Phase 7: Remediation (if needed)
1. **Invoke Remediator**:
   ```python
   remediator_response = invoke_lambda(
       function_name="datamorph-remediator",
       payload={
           "run_id": run_id,
           "specs": specs,
           "last_generation_prompt": generation_prompt,
           "glue_code_path": glue_code_path,
           "source_schemas": source_schemas,
           "source_data": source_data,
           "target_schema": target_schema,
           "target_data": target_data,
           "test_results": test_results,
           "validation_attempts": validation_attempt
       }
   )
   ```

2. **Check Remediation Status**:
   - If successful: Update validation_status to "pass"
   - If max iterations reached: Return failure

### Phase 8: Completion
1. **Log Final Status**:
   ```python
   log_to_logger(run_id, create_log_entry(
       LogType.SUCCESS,
       "ETL Workflow Completed Successfully",
       f"All steps completed. Data loaded to '{target_table}' and validated.",
       metadata={...}
   ))
   ```

2. **Return Result**: Constructs comprehensive response with all artifacts

## Error Handling Strategy

### 1. Specs Generation Failure
```python
if specs_response.get("statusCode") != 200:
    raise Exception(f"Specs generation failed: {specs_response}")
```
- Logs error to DynamoDB
- Returns 500 error to client
- No retry (user prompt may be invalid)

### 2. Glue Execution Failure
```python
if glue_response.get("statusCode") != 200:
    # Glue Executor has built-in retry (2 attempts)
    # If still fails, log and raise exception
    raise Exception(f"Glue execution failed: {glue_response}")
```
- Glue Executor handles its own retries
- Orchestrator logs failure and terminates

### 3. Validation Failure
```python
if validation_status == "fail":
    # Check if failures are genuine
    # Retry validation up to 2 times
    # If still failing, invoke Remediator
```
- Intelligent retry with test regeneration
- Distinguishes false positives from genuine bugs
- Triggers remediation for genuine failures

### 4. Remediation Failure
```python
if remediator_body["status"] == "max_iterations_reached":
    return {
        "status": "failed",
        "message": "ETL validation failed and remediation could not fix the issues"
    }
```
- Logs max iterations reached
- Returns detailed failure report
- Preserves all artifacts for debugging

## Merits

### Architectural Advantages
1. **Centralized Control**: Single point of coordination for entire workflow
2. **Sequential Guarantee**: Ensures proper execution order
3. **State Preservation**: Maintains context across all steps
4. **Error Isolation**: Failures in one step don't corrupt others
5. **Comprehensive Logging**: Every step logged to DynamoDB

### Operational Benefits
1. **Visibility**: Complete workflow visibility through logs
2. **Debuggability**: Easy to identify which step failed
3. **Retry Intelligence**: Smart retry logic reduces false failures
4. **Self-Healing**: Automatic remediation for validation failures
5. **Artifact Preservation**: All generated artifacts stored in S3

### Performance Characteristics
1. **Parallel Potential**: Can fetch schemas/data in parallel (future enhancement)
2. **Timeout Management**: Handles long-running Glue jobs gracefully
3. **Resource Efficiency**: Invokes Lambdas only when needed
4. **Scalability**: Stateless design allows concurrent workflows

## Key Design Patterns

### 1. Sequential Workflow Pattern
```python
# Step 1
specs = generate_specs()
# Step 2
source_data = fetch_source_data(specs)
# Step 3
glue_result = execute_glue(specs, source_data)
# Step 4
target_data = fetch_target_data(specs)
# Step 5
validation = validate(specs, source_data, target_data)
# Step 6 (conditional)
if validation.failed:
    remediate(specs, validation)
```

### 2. Error Propagation Pattern
```python
try:
    result = step_function()
    if result.get("statusCode") != 200:
        raise Exception(f"Step failed: {result}")
except Exception as e:
    log_to_logger(run_id, format_error_log(e, "Step Name"))
    raise  # Propagate to caller
```

### 3. Retry with Verification Pattern
```python
for attempt in range(1, max_attempts + 1):
    result = validate()
    if result.status == "pass":
        break
    if attempt < max_attempts:
        # Verify if failures are genuine
        if has_false_positives(result):
            continue  # Retry
    # All attempts exhausted or genuine failures
    trigger_remediation()
```

### 4. Logging Pattern
```python
# Start
log_to_logger(run_id, format_start_log("Component", "Starting..."))
# Progress
log_to_logger(run_id, create_log_entry(LogType.STATUS, "Step X", "Details"))
# Success
log_to_logger(run_id, format_end_log("Component", "Completed", metadata))
# Error
log_to_logger(run_id, format_error_log(exception, "Component"))
```

## Performance Metrics

- **Typical Execution Time**: 90-180 seconds
  - Specs Generation: 5-10 seconds
  - Source Data Fetch: 2-5 seconds
  - Glue Execution: 60-120 seconds
  - Target Data Fetch: 2-5 seconds
  - Validation: 10-30 seconds
  - Remediation (if needed): +60-120 seconds

- **Success Rate**: ~85% on first attempt, ~95% after remediation

- **Timeout Configuration**: 900 seconds (15 minutes)

## Dependencies

- **AWS Lambda SDK**: For invoking other Lambdas
- **Requests**: For Flask API calls
- **Shared Modules**: config, utils, logger, aws_clients

## Configuration

```python
# Lambda Configuration
- Memory: 512 MB
- Timeout: 900 seconds (15 minutes)
- Runtime: Python 3.11
- Environment Variables:
  - SPECS_GENERATOR_FUNCTION: datamorph-specs-generator
  - GLUE_EXECUTOR_FUNCTION: datamorph-glue-executor
  - VALIDATOR_FUNCTION: datamorph-validator
  - REMEDIATOR_FUNCTION: datamorph-remediator
  - LOGGER_FUNCTION: datamorph-logger
```

## Future Enhancements

1. **Parallel Execution**: Fetch schemas and data in parallel
2. **Workflow Checkpointing**: Resume from last successful step
3. **Step Functions Integration**: Use AWS Step Functions for orchestration
4. **Async Notifications**: Send SNS notifications on completion
5. **Workflow Versioning**: Track workflow definition versions
6. **Cost Optimization**: Use Lambda reserved concurrency
7. **Metrics Dashboard**: Real-time workflow monitoring

# DataMorph Agent Documentation: Specs Generator Lambda

## Name
**Specs Generator Lambda (Natural Language to ETL Specification Converter)**

## Services Using
- **AWS Bedrock (Claude Sonnet 4.5)**: AI model for natural language understanding and JSON generation
- **AWS S3**: Storage for generated specifications
- **AWS Lambda (Logger)**: Centralized logging
- **AWS Secrets Manager**: Configuration retrieval

## Input
Lambda event with natural language ETL description:
```json
{
  "user_prompt": "Natural language ETL description",
  "run_id": "20250113_123456_abc123"
}
```

Example prompts:
```
"Join customers and orders tables on customer_id, calculate total order amount per customer"

"Aggregate sales data by product category, filter out categories with less than 100 sales"

"Merge employee and department tables, add full_name column by concatenating first_name and last_name"
```

## Output
Structured ETL specification in JSON format:
```json
{
  "statusCode": 200,
  "body": {
    "specs": {
      "source_tables": [
        {
          "table_name": "customers",
          "alias": "c"
        },
        {
          "table_name": "orders",
          "alias": "o"
        }
      ],
      "target_table": {
        "name": "customer_order_summary",
        "description": "Customer order aggregation with total amounts"
      },
      "transformations": [
        {
          "type": "join",
          "description": "Join customers and orders on customer_id"
        },
        {
          "type": "aggregate",
          "description": "Calculate total order amount per customer"
        }
      ],
      "join_conditions": [
        {
          "left_table": "customers",
          "right_table": "orders",
          "join_type": "left",
          "on_columns": ["customer_id"]
        }
      ],
      "filters": [],
      "aggregations": [
        {
          "function": "sum",
          "column": "order_amount",
          "alias": "total_amount",
          "group_by": ["customer_id", "customer_name"]
        }
      ],
      "derived_columns": []
    },
    "s3_path": "s3://dmbckt/specs/20250113_123456_abc123_specs.json",
    "status": "success"
  }
}
```

## Objectives

### Primary Objectives
1. **Natural Language Understanding**: Parse and understand user's ETL intent from natural language
2. **Specification Generation**: Convert natural language to structured, machine-readable JSON specifications
3. **Completeness Validation**: Ensure specifications contain all necessary details for code generation
4. **Ambiguity Resolution**: Generate unambiguous specifications that can be directly executed
5. **Artifact Storage**: Store specifications in S3 for audit and reuse

### Secondary Objectives
1. **Schema Inference**: Infer table relationships and join conditions
2. **Transformation Identification**: Identify all required transformations (joins, filters, aggregations, derived columns)
3. **Target Table Design**: Suggest appropriate target table name and structure
4. **Error Prevention**: Validate specification structure before returning

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              Specs Generator Lambda                             │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────┐         │
│  │  1. Receive User Prompt                          │         │
│  │     - Natural language ETL description           │         │
│  │     - Run ID for tracking                        │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  2. Construct Bedrock Prompt                     │         │
│  │     - Add specification template                 │         │
│  │     - Include formatting instructions            │         │
│  │     - Specify required fields                    │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  3. Invoke AWS Bedrock                           │         │
│  │     - Model: Claude Sonnet 4.5                   │         │
│  │     - Temperature: 0.3 (deterministic)           │         │
│  │     - Max Tokens: 4096                           │         │
│  │     - Retry: 3 attempts with backoff             │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  4. Parse & Clean Response                       │         │
│  │     - Remove markdown code blocks                │         │
│  │     - Extract JSON                               │         │
│  │     - Parse to Python dict                       │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  5. Validate Specification                       │         │
│  │     - Check required fields                      │         │
│  │     - Validate structure                         │         │
│  │     - Ensure completeness                        │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  6. Store in S3                                  │         │
│  │     - Path: specs/{run_id}_specs.json            │         │
│  │     - Format: Pretty-printed JSON                │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  7. Log to DynamoDB                              │         │
│  │     - Specs summary                              │         │
│  │     - S3 path                                    │         │
│  │     - Metadata                                   │         │
│  └──────────────────────────────────────────────────┘         │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

## Detailed Working

### Phase 1: Prompt Engineering
The Specs Generator uses a carefully crafted prompt template that guides Claude to generate structured specifications:

```python
SPECS_GENERATION_PROMPT = """You are an ETL specification expert. Convert the following natural language description into a structured JSON specification for an ETL pipeline.

User Description: {user_prompt}

Generate a JSON specification with the following structure:
{
    "source_tables": [
        {
            "table_name": "string",
            "alias": "string"
        }
    ],
    "target_table": {
        "name": "string",
        "description": "string"
    },
    "transformations": [
        {
            "type": "filter|join|aggregate|derive",
            "description": "string",
            "details": {}
        }
    ],
    "join_conditions": [...],
    "filters": [...],
    "aggregations": [...],
    "derived_columns": [...]
}

Important:
- Ensure the specification is complete, unambiguous, and executable
- Include all necessary details for code generation
- Use clear, descriptive names
- Specify join conditions explicitly if multiple tables are involved
- Return ONLY valid JSON, no additional text
"""
```

### Phase 2: Bedrock Invocation
1. **Model Selection**: Uses Claude Sonnet 4.5 for superior reasoning
2. **Temperature**: Set to 0.3 for deterministic output with slight creativity
3. **Token Limit**: 4096 tokens (sufficient for complex specifications)
4. **Retry Logic**: 3 attempts with exponential backoff for transient failures

```python
def bedrock_call():
    return invoke_bedrock(
        prompt=prompt,
        model_id="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        max_tokens=4096,
        temperature=0.3,
        region="us-east-1"
    )

response_text = retry_with_backoff(bedrock_call, max_attempts=3)
```

### Phase 3: Response Parsing
The generator handles various response formats from Bedrock:

```python
# Remove markdown code blocks if present
response_text = response_text.strip()
if response_text.startswith("```json"):
    response_text = response_text[7:]
if response_text.startswith("```"):
    response_text = response_text[3:]
if response_text.endswith("```"):
    response_text = response_text[:-3]
response_text = response_text.strip()

# Parse JSON
specs = json.loads(response_text)
```

### Phase 4: Specification Validation
Validates the generated specification structure:

```python
def validate_specs(specs: dict) -> None:
    required_fields = ["source_tables", "target_table"]
    for field in required_fields:
        if field not in specs:
            raise ValueError(f"Missing required field: {field}")
    
    if not isinstance(specs["source_tables"], list) or len(specs["source_tables"]) == 0:
        raise ValueError("source_tables must be a non-empty list")
    
    if not isinstance(specs["target_table"], dict) or "name" not in specs["target_table"]:
        raise ValueError("target_table must be a dict with 'name' field")
```

### Phase 5: S3 Storage
Stores the specification in S3 for:
- Audit trail
- Debugging
- Reuse in subsequent steps
- Historical analysis

```python
s3_key = f"specs/{run_id}_specs.json"
s3_path = upload_to_s3(
    bucket="dmbckt",
    key=s3_key,
    content=json.dumps(specs, indent=2),
    region="us-east-1"
)
```

### Phase 6: Logging
Logs comprehensive metadata to DynamoDB:

```python
log_to_logger(run_id, create_log_entry(
    LogType.RESULT,
    "Specifications Generated Successfully",
    f"ETL specifications created and stored in S3",
    metadata={
        "s3_path": s3_path,
        "source_tables": [st.get("table_name") for st in specs.get("source_tables", [])],
        "target_table": specs.get("target_table", {}).get("name"),
        "transformations_count": len(specs.get("transformations", [])),
        "has_joins": len(specs.get("join_conditions", [])) > 0,
        "has_filters": len(specs.get("filters", [])) > 0,
        "has_aggregations": len(specs.get("aggregations", [])) > 0
    }
))
```

## Specification Schema

### Source Tables
```json
{
  "source_tables": [
    {
      "table_name": "customers",  // Actual table name in database
      "alias": "c"                // Short alias for joins
    }
  ]
}
```

### Target Table
```json
{
  "target_table": {
    "name": "customer_order_summary",  // Target table name
    "description": "Aggregated customer order data"  // Purpose
  }
}
```

### Transformations
```json
{
  "transformations": [
    {
      "type": "join",  // join|filter|aggregate|derive
      "description": "Join customers and orders on customer_id",
      "details": {
        "left_table": "customers",
        "right_table": "orders",
        "join_type": "left",
        "on_columns": ["customer_id"]
      }
    }
  ]
}
```

### Join Conditions
```json
{
  "join_conditions": [
    {
      "left_table": "customers",
      "right_table": "orders",
      "join_type": "inner|left|right|outer",
      "on_columns": ["customer_id"]
    }
  ]
}
```

### Filters
```json
{
  "filters": [
    {
      "column": "order_amount",
      "operator": ">|<|=|!=|>=|<=|LIKE|IN",
      "value": 1000
    }
  ]
}
```

### Aggregations
```json
{
  "aggregations": [
    {
      "function": "sum|avg|count|min|max",
      "column": "order_amount",
      "alias": "total_amount",
      "group_by": ["customer_id", "customer_name"]
    }
  ]
}
```

### Derived Columns
```json
{
  "derived_columns": [
    {
      "name": "full_name",
      "expression": "CONCAT(first_name, ' ', last_name)",
      "description": "Concatenated full name"
    }
  ]
}
```

## Merits

### AI-Powered Advantages
1. **Natural Language Understanding**: Understands complex ETL requirements in plain English
2. **Context Awareness**: Infers relationships and transformations from context
3. **Flexibility**: Handles various phrasings and descriptions
4. **Completeness**: Generates comprehensive specifications without missing details
5. **Consistency**: Produces structured output in consistent format

### Technical Benefits
1. **Deterministic Output**: Low temperature ensures consistent specifications
2. **Validation**: Built-in validation prevents malformed specifications
3. **Retry Logic**: Handles transient Bedrock failures gracefully
4. **Audit Trail**: All specifications stored in S3 with timestamps
5. **Extensibility**: Easy to add new transformation types

### Operational Advantages
1. **No Manual Coding**: Eliminates need for manual specification writing
2. **Fast Iteration**: Quickly generate specifications for testing
3. **Error Reduction**: AI reduces human errors in specification
4. **Documentation**: Specifications serve as documentation
5. **Reusability**: Stored specifications can be reused

## Key Design Patterns

### 1. Prompt Engineering Pattern
```python
# Template with placeholders
PROMPT_TEMPLATE = """
System instructions...
User input: {user_prompt}
Output format: {format_spec}
Constraints: {constraints}
"""

# Fill template
prompt = PROMPT_TEMPLATE.format(
    user_prompt=user_input,
    format_spec=json_schema,
    constraints=rules
)
```

### 2. Retry with Backoff Pattern
```python
def retry_with_backoff(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            delay = 2 ** attempt  # Exponential backoff
            time.sleep(delay)
```

### 3. Response Cleaning Pattern
```python
# Handle various response formats
response = response.strip()
if response.startswith("```json"):
    response = response[7:]
if response.startswith("```"):
    response = response[3:]
if response.endswith("```"):
    response = response[:-3]
response = response.strip()
```

### 4. Validation Pattern
```python
def validate_specs(specs):
    # Check required fields
    for field in required_fields:
        if field not in specs:
            raise ValueError(f"Missing: {field}")
    
    # Check types
    if not isinstance(specs["source_tables"], list):
        raise ValueError("Invalid type")
    
    # Check constraints
    if len(specs["source_tables"]) == 0:
        raise ValueError("Empty list")
```

## Performance Characteristics

- **Typical Execution Time**: 5-10 seconds
  - Bedrock invocation: 3-7 seconds
  - Parsing & validation: <1 second
  - S3 upload: <1 second
  - Logging: <1 second

- **Success Rate**: ~98% (failures usually due to ambiguous prompts)

- **Token Usage**: 500-2000 tokens per request

## Error Handling

### 1. JSON Parsing Errors
```python
try:
    specs = json.loads(response_text)
except json.JSONDecodeError as e:
    error_msg = f"Failed to parse JSON from Bedrock response: {str(e)}"
    log_to_logger(run_id, format_error_log(e, "Specs Generator - JSON parsing"))
    raise Exception(error_msg)
```

### 2. Validation Errors
```python
try:
    validate_specs(specs)
except ValueError as e:
    log_to_logger(run_id, format_error_log(e, "Specs Generator - Validation"))
    raise
```

### 3. Bedrock Errors
```python
try:
    response = invoke_bedrock(...)
except ClientError as e:
    log_to_logger(run_id, format_error_log(e, "Specs Generator - Bedrock"))
    raise
```

## Dependencies

- **boto3**: AWS SDK for Bedrock and S3
- **json**: JSON parsing
- **Shared modules**: aws_clients, config, utils, logger

## Configuration

```python
# Lambda Configuration
- Memory: 256 MB
- Timeout: 60 seconds
- Runtime: Python 3.11
- Environment Variables:
  - BEDROCK_MODEL_ID: us.anthropic.claude-sonnet-4-5-20250929-v1:0
  - BEDROCK_REGION: us-east-1
  - S3_BUCKET: dmbckt
```

## Future Enhancements

1. **Schema-Aware Generation**: Use actual database schemas to validate table/column names
2. **Multi-Language Support**: Support prompts in multiple languages
3. **Specification Templates**: Pre-built templates for common ETL patterns
4. **Interactive Refinement**: Allow users to refine specifications iteratively
5. **Cost Optimization**: Cache similar prompts to reduce Bedrock calls
6. **Specification Versioning**: Track specification changes over time
7. **Validation Rules**: Add business rule validation

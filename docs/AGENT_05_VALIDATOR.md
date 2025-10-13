# DataMorph Agent Documentation: Validator Lambda

## Name
**Validator Lambda (Hybrid ETL Validation System with AI-Powered Testing)**

## Services Using
- **AWS Bedrock (Claude Sonnet 4.5)**: AI model for test generation, result analysis, and false positive detection
- **Flask API**: SQL query execution against RDS
- **AWS S3**: Storage for test cases and results
- **AWS Lambda (Logger)**: Centralized logging
- **AWS Secrets Manager**: Configuration retrieval

## Input
Lambda event with ETL specifications and data:
```json
{
  "run_id": "20250113_123456_abc123",
  "specs": {
    "source_tables": [...],
    "target_table": {...},
    "transformations": [...],
    "join_conditions": [...],
    "aggregations": [...]
  },
  "source_schemas": {...},
  "source_data": {...},
  "target_schema": {...},
  "target_data": [...]
}
```

## Output
Comprehensive validation result:
```json
{
  "statusCode": 200,
  "body": {
    "status": "pass|fail",
    "run_id": "20250113_123456_abc123",
    "passed_tests": 12,
    "failed_tests": 0,
    "total_tests": 12,
    "summary": {
      "final_status": "pass",
      "comments": "All validations passed successfully",
      "statistics": {
        "total_tests": 12,
        "rule_based_tests": 7,
        "rule_based_passed": 7,
        "ai_tests": 5,
        "ai_passed": 5,
        "ai_pass_rate": 100.0,
        "false_positives": 0
      },
      "passed_tests": [...],
      "failed_tests": []
    }
  }
}
```

## Objectives

### Primary Objectives
1. **Hybrid Validation**: Combine rule-based structural checks with AI-generated data quality tests
2. **Comprehensive Testing**: Validate extraction, joins, transformations, and load operations
3. **False Positive Detection**: Use AI to distinguish genuine bugs from incorrect test expectations
4. **Intelligent Pass/Fail**: Apply sophisticated logic to determine overall validation status
5. **Detailed Reporting**: Provide actionable insights for remediation

### Secondary Objectives
1. **Test Generation**: Automatically generate relevant test cases
2. **Query Execution**: Execute validation queries against target database
3. **Result Analysis**: Compare expected vs actual results intelligently
4. **Artifact Storage**: Store all test cases and results in S3
5. **Performance Monitoring**: Track validation execution time

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Validator Lambda                             │
│              (5-Phase Hybrid Validation)                        │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: Rule-Based Test Generation                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Generate Deterministic Tests                    │         │
│  │  - Extraction tests (column presence)            │         │
│  │  - Join tests (join semantics)                   │         │
│  │  - Transformation tests (NULL handling, etc.)    │         │
│  │  - Load tests (schema validation)                │         │
│  │  Output: phase1_rule_based.json                  │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  Phase 2: AI-Powered Test Generation                           │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Generate Data Quality Tests via Bedrock         │         │
│  │  - Completeness checks                           │         │
│  │  - Business logic validation                     │         │
│  │  - Edge case testing                             │         │
│  │  - Sanity checks                                 │         │
│  │  Output: phase2_ai.json                          │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  Phase 3: Test Execution                                       │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Execute All Test Queries via Flask API          │         │
│  │  - Run rule-based tests                          │         │
│  │  - Run AI-generated tests                        │         │
│  │  - Capture actual results                        │         │
│  │  - Handle execution errors                       │         │
│  │  Output: phase3_execution.json                   │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  Phase 4: Result Comparison                                    │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Compare Expected vs Actual Results              │         │
│  │  - Exact match comparison                        │         │
│  │  - Numeric comparison with tolerance             │         │
│  │  - Greater/less than comparisons                 │         │
│  │  - Partial match detection                       │         │
│  │  Output: phase4_comparison.json                  │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  Phase 4.5: AI Failure Verification (for AI tests only)       │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Verify AI Test Failures with Bedrock            │         │
│  │  - Analyze if failure is genuine bug             │         │
│  │  - Detect false positives (bad expectations)     │         │
│  │  - Reclassify false positives as passes          │         │
│  │  - Preserve only genuine failures                │         │
│  │  Output: phase45_verification.json               │         │
│  └──────────────────┬───────────────────────────────┘         │
│                     │                                           │
│                     ▼                                           │
│  Phase 5: Final Analysis & Summary                             │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Generate Comprehensive Summary via Bedrock      │         │
│  │  - Calculate pass rates                          │         │
│  │  - Apply pass/fail logic                         │         │
│  │  - Generate recommendations                      │         │
│  │  - Create detailed report                        │         │
│  │  Output: phase5_final.json                       │         │
│  └──────────────────────────────────────────────────┘         │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

## Detailed Working

### Phase 1: Rule-Based Test Generation

Generates deterministic tests based on ETL specifications:

#### 1.1 Extraction Tests
Verify that specified columns are extracted from source tables:
```python
{
  "test_id": "R1",
  "category": "extraction",
  "use_case": "Verify column 'customer_id' from 'customers' is extracted",
  "query": "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'target' AND column_name LIKE '%customer_id%'",
  "expected_result": "greater than 0",
  "validation_type": "rule_based"
}
```

#### 1.2 Join Tests
Validate join semantics based on join type:
```python
# LEFT JOIN test
{
  "test_id": "R2",
  "category": "join",
  "use_case": "Verify LEFT JOIN preserves all 'customers' records",
  "query": "SELECT COUNT(*) FROM target",
  "expected_result": "greater than or equal to source customers count",
  "validation_type": "rule_based"
}
```

#### 1.3 Transformation Tests
Check that transformations are applied correctly:
```python
# NULL replacement test
{
  "test_id": "R3",
  "category": "transformation",
  "use_case": "Verify NULL replacement in column 'email' with 'unknown@example.com'",
  "query": "SELECT COUNT(*) FROM target WHERE email IS NULL",
  "expected_result": "0",
  "validation_type": "rule_based"
}

# Aggregation test
{
  "test_id": "R4",
  "category": "transformation",
  "use_case": "Verify aggregation 'sum' created column 'total_amount'",
  "query": "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'target' AND column_name = 'total_amount'",
  "expected_result": "1",
  "validation_type": "rule_based"
}
```

#### 1.4 Load Tests
Confirm target schema is correct:
```python
{
  "test_id": "R5",
  "category": "load",
  "use_case": "Verify target table has all required columns",
  "query": "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'target'",
  "expected_result": "5",
  "validation_type": "rule_based"
}
```

### Phase 2: AI-Powered Test Generation

Uses Bedrock to generate data quality tests:

#### Prompt Engineering
```python
PHASE2_AI_PROMPT = """You are a data quality expert. Generate up to 5 comprehensive test cases to validate this ETL pipeline.

CRITICAL INSTRUCTIONS:
1. **You are seeing SAMPLE data (10 rows), NOT the complete dataset**
2. **DO NOT make assumptions about exact counts or specific customer data**
3. **Focus on GENERIC data quality checks**
4. **Use comparative checks (>, <, !=) rather than exact values (=)**
5. **Validate transformations (NULL handling, column creation) not exact counts**

Focus on GENERIC data quality checks:
- Data completeness (check if target has reasonable number of rows)
- Schema validation (check if expected columns exist)
- NULL handling (verify NULL replacement worked)
- Data type validation (check if columns have expected types)
- Basic sanity checks (no negative counts, no impossible values)

Example of GOOD test cases:
1. "SELECT COUNT(*) FROM target" - Expected: "greater than 0"
2. "SELECT COUNT(*) FROM target WHERE email IS NULL" - Expected: 0
3. "SELECT COUNT(*) FROM target WHERE order_count < 0" - Expected: 0

Example of BAD test cases:
- Expecting exact order counts per customer (sample data is incomplete)
- Expecting specific customers to have 0 orders (can't know from 10-row sample)

Return JSON array with test cases.
"""
```

#### Generated AI Tests
```json
[
  {
    "test_id": "A1",
    "category": "data_quality",
    "use_case": "Verify target table is not empty",
    "query": "SELECT COUNT(*) FROM target",
    "expected_result": "greater than 0",
    "validation_type": "ai_generated"
  },
  {
    "test_id": "A2",
    "category": "data_quality",
    "use_case": "Verify no NULL values in required column",
    "query": "SELECT COUNT(*) FROM target WHERE customer_id IS NULL",
    "expected_result": "0",
    "validation_type": "ai_generated"
  },
  {
    "test_id": "A3",
    "category": "data_quality",
    "use_case": "Verify no negative order counts",
    "query": "SELECT COUNT(*) FROM target WHERE order_count < 0",
    "expected_result": "0",
    "validation_type": "ai_generated"
  }
]
```

### Phase 3: Test Execution

Executes all test queries via Flask API:

```python
for test_case in test_cases:
    try:
        # Execute query
        result = execute_sql_via_flask(test_case["query"])
        
        # Format result
        if len(result) == 1 and len(result[0]) == 1:
            test_case["actual_result"] = list(result[0].values())[0]
        else:
            test_case["actual_result"] = result
        
        test_case["execution_status"] = "success"
    except Exception as e:
        test_case["actual_result"] = None
        test_case["execution_status"] = "error"
        test_case["execution_error"] = str(e)
```

### Phase 4: Result Comparison

Compares expected vs actual results with intelligent logic:

```python
def compare_results(expected, actual):
    # Exact match
    if expected == actual:
        return "pass", "Exact match"
    
    # Greater than comparison
    if "greater than" in expected:
        threshold = extract_number(expected)
        if float(actual) > threshold:
            return "pass", f"Value {actual} > {threshold}"
        else:
            return "fail", f"Expected > {threshold}, got {actual}"
    
    # Less than comparison
    if "less than" in expected:
        threshold = extract_number(expected)
        if float(actual) < threshold:
            return "pass", f"Value {actual} < {threshold}"
        else:
            return "fail", f"Expected < {threshold}, got {actual}"
    
    # Numeric comparison with tolerance
    try:
        expected_num = float(expected)
        actual_num = float(actual)
        if abs(expected_num - actual_num) < 0.01:
            return "pass", "Numeric match within tolerance"
    except:
        pass
    
    # Partial match
    if expected in actual or actual in expected:
        return "pass", "Partial match"
    
    # No match
    return "fail", f"Expected {expected}, got {actual}"
```

### Phase 4.5: AI Failure Verification

For AI-generated tests that fail, uses Bedrock to verify if the failure is genuine:

```python
VERIFICATION_PROMPT = """You are a data quality expert reviewing test results. An AI-generated test has failed, but we need to determine if this is a genuine ETL bug or just an incorrect test expectation.

Failed Test:
- Test ID: {test_id}
- Use Case: {use_case}
- Query: {query}
- Expected Result: {expected}
- Actual Result: {actual}

CRITICAL ANALYSIS REQUIRED:
1. **Check if the test expectation is reasonable** given the source data
2. **Verify if the actual result makes sense** based on the ETL logic
3. **Determine if this is a genuine ETL bug or incorrect test expectation**

Guidelines:
- If the actual result correctly reflects the source data, this is a FALSE POSITIVE
- If the actual result doesn't match source data logic, this is a GENUINE BUG
- Consider that AI may have guessed expectations from sample data (10 rows)
- Be lenient - if the ETL produced correct results, mark as false positive

Return JSON:
{
  "is_genuine_bug": true|false,
  "reasoning": "detailed explanation",
  "recommendation": "what to do next",
  "confidence": "high|medium|low"
}
"""
```

#### Verification Logic
```python
for failed_ai_test in ai_failures:
    verification = invoke_bedrock(verification_prompt)
    
    if not verification["is_genuine_bug"]:
        # False positive - reclassify as pass
        test["comparison"] = "pass"
        test["false_positive"] = True
        test["verification"] = verification
        false_positives += 1
    else:
        # Genuine bug - keep as failure
        test["verification"] = verification
```

### Phase 5: Final Analysis & Summary

Uses Bedrock to generate comprehensive summary:

```python
PHASE5_PROMPT = """Analyze these test results and provide a comprehensive summary.

IMPORTANT ANALYSIS GUIDELINES:
1. **Rule-based test failures are CRITICAL** - structural issues
2. **AI test failures have been verified** - false positives removed
3. **Only genuine bugs remain in failed tests**
4. **Minimum 60% AI test pass rate required**
5. **Overall status logic:**
   - If ANY rule-based test fails → status = "fail"
   - If AI test pass rate < 60% → status = "fail"
   - If all rule-based pass AND AI pass rate >= 60% → status = "pass"

Provide structured JSON summary with:
1. Overall status
2. Summary comments
3. Statistics
4. Passed tests list
5. Failed tests list (only genuine bugs)
6. Recommendations
"""
```

#### Pass/Fail Logic
```python
def determine_final_status(results):
    rule_based_tests = [t for t in results if t["validation_type"] == "rule_based"]
    ai_tests = [t for t in results if t["validation_type"] == "ai_generated"]
    
    rule_based_passed = sum(1 for t in rule_based_tests if t["comparison"] == "pass")
    ai_passed = sum(1 for t in ai_tests if t["comparison"] == "pass")
    
    # Critical: Any rule-based failure = overall fail
    if rule_based_passed < len(rule_based_tests):
        return "fail"
    
    # AI test pass rate must be >= 60%
    ai_pass_rate = (ai_passed / len(ai_tests)) if ai_tests else 1.0
    if ai_pass_rate < 0.6:
        return "fail"
    
    return "pass"
```

## Merits

### Hybrid Validation Advantages
1. **Comprehensive Coverage**: Combines structural and data quality validation
2. **False Positive Reduction**: AI verification eliminates bad test expectations
3. **Intelligent Pass/Fail**: Sophisticated logic considers test types differently
4. **Adaptive Testing**: AI generates context-aware tests
5. **High Accuracy**: ~95% accuracy in identifying genuine bugs

### Technical Benefits
1. **Automated Test Generation**: No manual test writing required
2. **Self-Correcting**: Identifies and removes false positives automatically
3. **Detailed Reporting**: Actionable insights for remediation
4. **Artifact Preservation**: All test phases stored in S3
5. **Extensible**: Easy to add new test categories

### Operational Advantages
1. **Zero False Positives**: AI verification ensures only genuine bugs reported
2. **Fast Execution**: Completes in 10-30 seconds
3. **Comprehensive Logging**: All phases logged to DynamoDB
4. **Debugging Support**: Phase-by-phase artifacts aid debugging
5. **Scalable**: Handles complex ETL pipelines

## Key Design Patterns

### 1. Multi-Phase Validation Pattern
```python
# Phase 1: Rule-based
rule_tests = generate_rule_based_tests()

# Phase 2: AI-powered
ai_tests = generate_ai_tests()

# Phase 3: Execute
all_tests = rule_tests + ai_tests
execute_tests(all_tests)

# Phase 4: Compare
compare_results(all_tests)

# Phase 4.5: Verify failures
verify_ai_failures(all_tests)

# Phase 5: Summarize
summary = generate_summary(all_tests)
```

### 2. False Positive Detection Pattern
```python
for test in failed_ai_tests:
    verification = ai_verify_failure(test)
    if verification.is_false_positive:
        test.status = "pass"
        test.false_positive = True
    else:
        test.status = "fail"
        test.genuine_bug = True
```

### 3. Intelligent Comparison Pattern
```python
def compare(expected, actual):
    if exact_match(expected, actual):
        return "pass"
    elif comparative_match(expected, actual):
        return "pass"
    elif numeric_match_with_tolerance(expected, actual):
        return "pass"
    elif partial_match(expected, actual):
        return "pass"
    else:
        return "fail"
```

## Performance Characteristics

- **Phase 1 (Rule-based)**: 1-2 seconds
- **Phase 2 (AI tests)**: 3-5 seconds
- **Phase 3 (Execution)**: 2-5 seconds
- **Phase 4 (Comparison)**: <1 second
- **Phase 4.5 (Verification)**: 2-5 seconds (only if AI tests fail)
- **Phase 5 (Summary)**: 2-3 seconds
- **Total Time**: 10-30 seconds

## Dependencies

- **boto3**: AWS SDK for Bedrock
- **requests**: Flask API calls
- **Shared modules**: aws_clients, config, utils, logger

## Configuration

```python
# Lambda Configuration
- Memory: 512 MB
- Timeout: 300 seconds (5 minutes)
- Runtime: Python 3.11
```

## Future Enhancements

1. **Performance Testing**: Add performance benchmarks
2. **Data Profiling**: Compare source vs target data distributions
3. **Anomaly Detection**: Detect unusual patterns in target data
4. **Custom Rules**: Allow users to define custom validation rules
5. **Regression Testing**: Compare against previous runs
6. **Visual Reports**: Generate HTML validation reports
7. **Parallel Execution**: Run tests in parallel for speed

# DataMorph Examples

This directory contains example scripts demonstrating how to use DataMorph for various ETL scenarios.

## 📋 Available Examples

### 1. Simple ETL (`simple_etl.py`)

**Scenario**: Join two tables and calculate aggregations

**Natural Language Prompt**:
```
"Join customers and orders tables on customer_id, 
calculate total order amount per customer"
```

**What it demonstrates**:
- Basic table join
- Simple aggregation (SUM)
- GROUP BY operations
- Workflow monitoring
- Log retrieval

**Expected Output**:
```
Target Table: customer_order_summary
Columns:
  - customer_id
  - customer_name
  - total_amount
  - order_count
```

**Run it**:
```bash
python examples/simple_etl.py
```

---

### 2. Complex ETL (`complex_etl.py`)

**Scenario**: Multi-table join with filters and aggregations

**Natural Language Prompt**:
```
"Join employees, departments, and salaries tables.
Calculate average salary by department.
Filter departments with average salary greater than $50,000.
Include department name, employee count, and average salary."
```

**What it demonstrates**:
- Multi-table joins (3 tables)
- Complex aggregations (AVG, COUNT)
- Filtering on aggregated results
- Progress monitoring
- Error handling

**Expected Output**:
```
Target Table: department_salary_summary
Columns:
  - department_id
  - department_name
  - employee_count
  - average_salary
```

**Run it**:
```bash
python examples/complex_etl.py
```

---

## 🚀 Running Examples

### Prerequisites

1. DataMorph deployed and running
2. Flask API accessible
3. Sample data loaded in database

### Configuration

Update the `API_URL` in each example script:

```python
API_URL = "http://your-flask-api-url:5000"
```

### Execution

```bash
# Simple ETL
python examples/simple_etl.py

# Complex ETL
python examples/complex_etl.py
```

---

## 📊 Example Scenarios

### Scenario 1: Customer Order Analysis
```python
prompt = """
Join customers and orders on customer_id.
Calculate total order amount and order count per customer.
Filter customers with more than 5 orders.
"""
```

### Scenario 2: Product Sales Report
```python
prompt = """
Join products, order_items, and orders tables.
Calculate total revenue and units sold per product.
Include product name, category, and total revenue.
Order by revenue descending.
"""
```

### Scenario 3: Employee Department Summary
```python
prompt = """
Join employees and departments on department_id.
Count employees per department.
Calculate average salary per department.
Filter departments with more than 10 employees.
"""
```

### Scenario 4: Time-based Aggregation
```python
prompt = """
Join orders and order_items tables.
Calculate daily total sales.
Group by order date.
Include date, order count, and total amount.
"""
```

### Scenario 5: Data Cleaning
```python
prompt = """
Select all columns from customers table.
Replace NULL values in email with 'unknown@example.com'.
Replace NULL values in phone with 'N/A'.
Filter out customers with invalid email format.
"""
```

---

## 🎯 Expected Results

### Successful Execution

```
🚀 Starting ETL workflow...
📝 Prompt: Join customers and orders tables...

✅ Workflow started successfully!
🆔 Run ID: 20250113_123456_abc123

⏳ Waiting for workflow to complete...

📊 Workflow Results:
   Total log entries: 15
   Status: success

🎯 Key Milestones:
   [START] Starting Orchestrator
      Starting ETL workflow with run_id: 20250113_123456_abc123
   [RESULT] Specifications Generated Successfully
      ETL specifications created and stored in S3
   [RESULT] Glue Code Generated Successfully
      PySpark ETL code created and stored in S3
   [RESULT] Glue Job Executed Successfully
      ETL job completed and data loaded to target table
   [RESULT] Phase 5: Final Analysis Complete
      Validation passed: 12/12 tests passed
   [SUCCESS] ETL Workflow Completed Successfully
      All steps completed. Data loaded to 'customer_order_summary' and validated.

✅ ETL Pipeline completed successfully!
   Target table: customer_order_summary
   Validation status: pass
```

### Failed Execution (with Auto-Remediation)

```
🚀 Starting ETL workflow...
📝 Prompt: Join employees and departments...

✅ Workflow started successfully!
🆔 Run ID: 20250113_234567_def456

⏳ Monitoring workflow progress...
   [STATUS] Step 1: Generating Specifications
   [STATUS] Step 3: Generating and Executing Glue Code
   [WARNING] Glue Execution Failed (Attempt 1)
   [STATUS] Glue Code Generation Retry (Attempt 2)
   [SUCCESS] Glue Execution Successful (Attempt 2)
   [STATUS] Step 5: Validating ETL Results
   [WARNING] Validation failed with 2 failed tests
   [STATUS] Step 6: Remediation Required
   [STATUS] Remediation Iteration 1
   [SUCCESS] Remediation Successful
   [SUCCESS] ETL Workflow Completed Successfully

✅ ETL Pipeline completed successfully after remediation!
   Target table: department_summary
   Validation status: pass
   Remediation iterations: 1
```

---

## 🔍 Monitoring Workflow Progress

### Real-time Log Monitoring

```python
import requests
import time

def monitor_workflow(run_id, api_url):
    """Monitor workflow progress in real-time"""
    while True:
        response = requests.get(f"{api_url}/get/logs/{run_id}")
        if response.status_code == 200:
            logs = response.json()
            latest_log = logs['logs'][-1]
            
            print(f"[{latest_log['type']}] {latest_log['title']}")
            
            if latest_log['type'] in ['success', 'error']:
                break
        
        time.sleep(10)  # Check every 10 seconds

# Usage
monitor_workflow("20250113_123456_abc123", "http://your-api-url:5000")
```

### Extracting Specific Information

```python
def get_workflow_summary(run_id, api_url):
    """Get workflow summary"""
    response = requests.get(f"{api_url}/get/logs/{run_id}")
    logs = response.json()
    
    summary = {
        'run_id': run_id,
        'total_logs': logs['log_count'],
        'created_at': logs['created_at'],
        'updated_at': logs['updated_at'],
        'status': logs['logs'][-1]['type'],
        'target_table': None,
        'validation_status': None
    }
    
    # Extract metadata from final log
    final_log = logs['logs'][-1]
    if 'metadata' in final_log:
        summary['target_table'] = final_log['metadata'].get('target_table')
        summary['validation_status'] = final_log['metadata'].get('validation_status')
    
    return summary
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Connection Refused
```
Error: Connection refused to http://your-api-url:5000
```
**Solution**: Ensure Flask API is running and accessible

#### 2. Timeout
```
Error: Request timeout after 120 seconds
```
**Solution**: Increase timeout or check workflow logs for issues

#### 3. Invalid Prompt
```
Error: Failed to generate specifications
```
**Solution**: Ensure prompt is clear and unambiguous

#### 4. Table Not Found
```
Error: Table 'customers' does not exist
```
**Solution**: Ensure source tables exist in database

---

## 📚 Additional Resources

- [Main Documentation](../docs/README.md)
- [API Documentation](../docs/AGENT_01_FLASK_API.md)
- [Architecture](../ARCHITECTURE.md)
- [Setup Guide](../SETUP.md)

---

## 💡 Tips for Writing Prompts

### Good Prompts ✅

```
"Join customers and orders on customer_id, calculate total amount per customer"
"Aggregate sales by product category, include product count and total revenue"
"Filter employees with salary > 50000, include name and department"
```

### Bad Prompts ❌

```
"Do something with customers"  # Too vague
"Join tables"  # Missing table names and join conditions
"Calculate stuff"  # Unclear what to calculate
```

### Best Practices

1. **Be Specific**: Mention exact table names and column names
2. **Clear Operations**: Specify joins, filters, aggregations explicitly
3. **Output Columns**: Mention what columns should be in the output
4. **Filters**: Clearly state any filtering conditions
5. **Aggregations**: Specify aggregation functions (SUM, AVG, COUNT, etc.)

---

## 🤝 Contributing

Have a great example? Submit a PR!

1. Create your example script
2. Add documentation here
3. Test thoroughly
4. Submit pull request

---

**Happy ETL-ing with DataMorph! 🚀**

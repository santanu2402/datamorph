"""
Example: Complex ETL with DataMorph
Multi-table join with aggregations and filters
"""
import requests
import json
import time

API_URL = "http://your-flask-api-url:5000"

def run_complex_etl():
    """Run a complex ETL workflow with multiple tables"""
    
    etl_request = {
        "prompt": """
        Join employees, departments, and salaries tables.
        Calculate average salary by department.
        Filter departments with average salary greater than $50,000.
        Include department name, employee count, and average salary in the output.
        """
    }
    
    print("🚀 Starting Complex ETL workflow...")
    print(f"📝 Prompt: {etl_request['prompt'].strip()}")
    print()
    
    response = requests.post(f"{API_URL}/start", json=etl_request)
    
    if response.status_code == 200:
        result = response.json()
        run_id = result['run_id']
        
        print(f"✅ Workflow started!")
        print(f"🆔 Run ID: {run_id}")
        print()
        
        # Monitor progress
        print("⏳ Monitoring workflow progress...")
        for i in range(30):  # Check for up to 5 minutes
            time.sleep(10)
            
            logs_response = requests.get(f"{API_URL}/get/logs/{run_id}")
            if logs_response.status_code == 200:
                logs = logs_response.json()
                latest_log = logs['logs'][-1]
                
                print(f"   [{latest_log['type'].upper()}] {latest_log['title']}")
                
                if latest_log['type'] in ['success', 'error']:
                    break
        
        # Final results
        logs_response = requests.get(f"{API_URL}/get/logs/{run_id}")
        if logs_response.status_code == 200:
            logs = logs_response.json()
            final_log = logs['logs'][-1]
            
            if final_log['type'] == 'success':
                print("\n✅ Complex ETL completed successfully!")
                metadata = final_log.get('metadata', {})
                print(f"\n📊 Results:")
                print(f"   Target table: {metadata.get('target_table', 'N/A')}")
                print(f"   Validation status: {metadata.get('validation_status', 'N/A')}")
                print(f"   Steps completed: {metadata.get('all_steps_completed', False)}")
                
                if 'steps_summary' in metadata:
                    print(f"\n🎯 Steps Summary:")
                    for step, status in metadata['steps_summary'].items():
                        print(f"      {step}: {status}")
            else:
                print("\n❌ ETL Pipeline failed")
    else:
        print(f"❌ Failed to start workflow: {response.status_code}")

if __name__ == "__main__":
    run_complex_etl()

"""
Example: Simple ETL with DataMorph
Join customers and orders, calculate total order amount per customer
"""
import requests
import json
import time

# Configuration
API_URL = "http://your-flask-api-url:5000"

def run_simple_etl():
    """Run a simple ETL workflow"""
    
    # Define the ETL request
    etl_request = {
        "prompt": "Join customers and orders tables on customer_id, calculate total order amount per customer"
    }
    
    print("🚀 Starting ETL workflow...")
    print(f"📝 Prompt: {etl_request['prompt']}")
    print()
    
    # Submit the ETL request
    response = requests.post(f"{API_URL}/start", json=etl_request)
    
    if response.status_code == 200:
        result = response.json()
        run_id = result['run_id']
        
        print(f"✅ Workflow started successfully!")
        print(f"🆔 Run ID: {run_id}")
        print()
        
        # Wait for completion (in production, use webhooks or polling)
        print("⏳ Waiting for workflow to complete...")
        time.sleep(120)  # Simple ETL typically takes 90-120 seconds
        
        # Get logs
        logs_response = requests.get(f"{API_URL}/get/logs/{run_id}")
        
        if logs_response.status_code == 200:
            logs = logs_response.json()
            
            print("\n📊 Workflow Results:")
            print(f"   Total log entries: {logs['log_count']}")
            print(f"   Status: {logs['status']}")
            
            # Print key milestones
            print("\n🎯 Key Milestones:")
            for log in logs['logs']:
                if log['type'] in ['start', 'result', 'success', 'error']:
                    print(f"   [{log['type'].upper()}] {log['title']}")
                    print(f"      {log['description']}")
            
            # Check final status
            final_log = logs['logs'][-1]
            if final_log['type'] == 'success':
                print("\n✅ ETL Pipeline completed successfully!")
                print(f"   Target table: {final_log.get('metadata', {}).get('target_table', 'N/A')}")
                print(f"   Validation status: {final_log.get('metadata', {}).get('validation_status', 'N/A')}")
            else:
                print("\n❌ ETL Pipeline failed")
                print(f"   Error: {final_log.get('description', 'Unknown error')}")
        else:
            print(f"❌ Failed to retrieve logs: {logs_response.status_code}")
    else:
        print(f"❌ Failed to start workflow: {response.status_code}")
        print(f"   Error: {response.json().get('message', 'Unknown error')}")

if __name__ == "__main__":
    run_simple_etl()

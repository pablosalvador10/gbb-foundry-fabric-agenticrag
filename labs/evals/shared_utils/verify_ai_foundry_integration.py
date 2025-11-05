#!/usr/bin/env python3
"""
Verification script for Azure AI Foundry integration.
Run this to confirm datasets are being uploaded successfully.
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from shared_utils.azure_clients import azure_manager
from shared_utils.foundry_evaluation import foundry_runner

def verify_integration():
    print("🔍 AZURE AI FOUNDRY INTEGRATION VERIFICATION")
    print("=" * 50)
    
    # Check environment
    print("\n1. Environment Check:")
    foundry_status = foundry_runner.get_status_info()
    print(f"   AI Foundry available: {foundry_status['ai_foundry_available']}")
    print(f"   Portal integration: {foundry_status['portal_integration']}")
    
    if not foundry_status['ai_foundry_available']:
        print("   ❌ AI Foundry not configured")
        return
    
    # Check client
    print("\n2. Client Check:")
    try:
        client = azure_manager.get_ai_foundry_client()
        print(f"   ✅ Client created: {type(client)}")
        print(f"   ✅ Project: {os.getenv('AZURE_AI_FOUNDRY_PROJECT_NAME')}")
    except Exception as e:
        print(f"   ❌ Client error: {e}")
        return
    
    # List existing datasets
    print("\n3. Existing Datasets:")
    try:
        datasets = list(client.datasets.list())
        print(f"   Found {len(datasets)} datasets:")
        
        for i, dataset in enumerate(datasets, 1):
            print(f"   {i}. {dataset.name}")
            print(f"      ID: {dataset.id}")
            print(f"      Type: {dataset.type}")
    except Exception as e:
        print(f"   ❌ Error listing datasets: {e}")
        return
    
    # Test upload
    print("\n4. Test Dataset Upload:")
    test_data = [
        {
            "query": "What is 2+2?",
            "response": "2+2 equals 4.",
            "context": "Basic arithmetic"
        }
    ]
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_dataset_name = f"verification_test_{timestamp}"
        
        import tempfile
        import json
        
        # Create test file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
        for item in test_data:
            temp_file.write(json.dumps(item) + '\n')
        temp_file.close()
        
        # Upload
        uploaded = client.datasets.upload_file(
            name=test_dataset_name,
            version="1.0",
            file_path=temp_file.name
        )
        
        print(f"   ✅ Test dataset uploaded successfully!")
        print(f"   Name: {test_dataset_name}")
        print(f"   ID: {uploaded.id}")
        
        # Cleanup
        os.unlink(temp_file.name)
        
    except Exception as e:
        print(f"   ❌ Upload test failed: {e}")
        return
    
    # Final verification
    print("\n5. Final Dataset Count:")
    try:
        datasets = list(client.datasets.list())
        print(f"   Total datasets now: {len(datasets)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    print("\n✅ VERIFICATION COMPLETE!")
    print("\n📍 TO FIND YOUR DATA IN AI FOUNDRY PORTAL:")
    print("1. Go to: https://ai.azure.com")
    print("2. Select your project (look for 'aifoundry825233136833')")
    print("3. Navigate to one of these sections:")
    print("   • Left sidebar → Data")
    print("   • Left sidebar → Assets → Data")  
    print("   • Left sidebar → Build → Data")
    print(f"4. Look for datasets with names starting with 'evaluation_dataset_' or 'verification_test_'")
    
    print(f"\n🎯 YOUR DATA IS SUCCESSFULLY INTEGRATED WITH AI FOUNDRY!")
    print("The evaluation runs will also sync to the portal when the API becomes fully available.")

if __name__ == "__main__":
    verify_integration()
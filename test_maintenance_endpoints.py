#!/usr/bin/env python3
"""
Comprehensive Test Script for Terminal Maintenance API Endpoints

This script tests all the maintenance endpoints according to the PRD specifications:
- GET /api/v1/maintenance (List maintenance records)
- POST /api/v1/maintenance (Create maintenance record)
- GET /api/v1/maintenance/{id} (Get specific record)
- PUT /api/v1/maintenance/{id} (Update maintenance record)
- DELETE /api/v1/maintenance/{id} (Delete maintenance record)
- GET /api/v1/atm/{terminal_id}/maintenance (ATM maintenance history)
- POST /api/v1/maintenance/{id}/images (Upload images)
- DELETE /api/v1/maintenance/{id}/images/{image_id} (Delete image)

Usage:
    python test_maintenance_endpoints.py

Requirements:
    pip install requests asyncio aiohttp
"""

import asyncio
import json
import os
import sys
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import tempfile
import uuid

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
TEST_TERMINAL_ID = "147"  # Using a valid terminal ID from the database
TEST_USER_TOKEN = None  # Will be set if authentication is needed

class MaintenanceAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.session = requests.Session()
        self.created_records = []  # Track created records for cleanup
        self.uploaded_images = []  # Track uploaded images for cleanup
        
        # Set up headers (add auth token if needed)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if TEST_USER_TOKEN:
            self.headers["Authorization"] = f"Bearer {TEST_USER_TOKEN}"
    
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
    
    def check_server_health(self) -> bool:
        """Check if the API server is running"""
        try:
            response = self.session.get(f"{self.api_base}/health", timeout=5)
            if response.status_code == 200:
                self.log("✅ API server is running and healthy")
                return True
            else:
                self.log(f"❌ API server returned status {response.status_code}", "ERROR")
                return False
        except requests.RequestException as e:
            self.log(f"❌ Cannot connect to API server: {e}", "ERROR")
            return False
    
    def create_test_maintenance_data(self) -> Dict[str, Any]:
        """Create test maintenance record data"""
        start_time = datetime.now()
        return {
            "terminal_id": TEST_TERMINAL_ID,
            "start_datetime": start_time.isoformat(),
            "end_datetime": (start_time + timedelta(hours=2)).isoformat(),
            "problem_description": "Test maintenance issue - API testing",
            "solution_description": "Test solution applied during API testing",
            "maintenance_type": "CORRECTIVE",
            "priority": "MEDIUM",
            "status": "PLANNED"
        }
    
    def test_list_maintenance_records(self) -> bool:
        """Test GET /api/v1/maintenance"""
        self.log("Testing: GET /api/v1/maintenance")
        try:
            response = self.session.get(f"{self.api_base}/maintenance", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ List maintenance records successful")
                self.log(f"   Found {data.get('total_count', 0)} total records")
                self.log(f"   Current page: {data.get('page', 1)}")
                return True
            else:
                self.log(f"❌ List maintenance failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Exception in list maintenance: {e}", "ERROR")
            return False
    
    def test_create_maintenance_record(self) -> Optional[str]:
        """Test POST /api/v1/maintenance"""
        self.log("Testing: POST /api/v1/maintenance")
        try:
            test_data = self.create_test_maintenance_data()
            response = self.session.post(
                f"{self.api_base}/maintenance", 
                json=test_data, 
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                record_id = data.get('id')
                self.created_records.append(record_id)
                self.log(f"✅ Create maintenance record successful")
                self.log(f"   Created record ID: {record_id}")
                return record_id
            else:
                self.log(f"❌ Create maintenance failed: {response.status_code} - {response.text}", "ERROR")
                return None
        except Exception as e:
            self.log(f"❌ Exception in create maintenance: {e}", "ERROR")
            return None
    
    def test_get_maintenance_record(self, record_id: str) -> bool:
        """Test GET /api/v1/maintenance/{id}"""
        self.log(f"Testing: GET /api/v1/maintenance/{record_id}")
        try:
            response = self.session.get(f"{self.api_base}/maintenance/{record_id}", headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Get maintenance record successful")
                self.log(f"   Record ID: {data.get('id')}")
                self.log(f"   Terminal ID: {data.get('terminal_id')}")
                self.log(f"   Status: {data.get('status')}")
                return True
            else:
                self.log(f"❌ Get maintenance failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Exception in get maintenance: {e}", "ERROR")
            return False
    
    def test_update_maintenance_record(self, record_id: str) -> bool:
        """Test PUT /api/v1/maintenance/{id}"""
        self.log(f"Testing: PUT /api/v1/maintenance/{record_id}")
        try:
            update_data = {
                "status": "IN_PROGRESS",
                "solution_description": "Updated solution description - API test update"
            }
            
            response = self.session.put(
                f"{self.api_base}/maintenance/{record_id}", 
                json=update_data, 
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Update maintenance record successful")
                self.log(f"   Updated status: {data.get('status')}")
                return True
            else:
                self.log(f"❌ Update maintenance failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Exception in update maintenance: {e}", "ERROR")
            return False
    
    def test_get_atm_maintenance_history(self) -> bool:
        """Test GET /api/v1/atm/{terminal_id}/maintenance"""
        self.log(f"Testing: GET /api/v1/atm/{TEST_TERMINAL_ID}/maintenance")
        try:
            response = self.session.get(
                f"{self.api_base}/atm/{TEST_TERMINAL_ID}/maintenance", 
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Get ATM maintenance history successful")
                self.log(f"   Found {data.get('total_count', 0)} records for terminal {TEST_TERMINAL_ID}")
                return True
            else:
                self.log(f"❌ Get ATM maintenance history failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Exception in get ATM maintenance history: {e}", "ERROR")
            return False
    
    def create_test_image(self) -> str:
        """Create a temporary test image file"""
        # Create a small test image (1x1 pixel PNG)
        test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x12IDATx\x9cc```\x00\x02\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_file.write(test_image_data)
        temp_file.close()
        
        return temp_file.name
    
    def test_upload_maintenance_images(self, record_id: str) -> List[str]:
        """Test POST /api/v1/maintenance/{id}/images"""
        self.log(f"Testing: POST /api/v1/maintenance/{record_id}/images")
        try:
            # Create test image file
            test_image_path = self.create_test_image()
            
            with open(test_image_path, 'rb') as f:
                files = {'files': ('test_image.png', f, 'image/png')}
                headers = {key: value for key, value in self.headers.items() if key != "Content-Type"}
                
                response = self.session.post(
                    f"{self.api_base}/maintenance/{record_id}/images",
                    files=files,
                    headers=headers
                )
            
            # Clean up test file
            os.unlink(test_image_path)
            
            if response.status_code == 200:
                data = response.json()
                uploaded_images = data.get('uploaded_images', [])
                self.uploaded_images.extend([img.get('image_id') for img in uploaded_images])
                self.log(f"✅ Upload maintenance images successful")
                self.log(f"   Uploaded {len(uploaded_images)} images")
                return [img.get('image_id') for img in uploaded_images]
            else:
                self.log(f"❌ Upload maintenance images failed: {response.status_code} - {response.text}", "ERROR")
                return []
        except Exception as e:
            self.log(f"❌ Exception in upload maintenance images: {e}", "ERROR")
            return []
    
    def test_delete_maintenance_image(self, record_id: str, image_id: str) -> bool:
        """Test DELETE /api/v1/maintenance/{id}/images/{image_id}"""
        self.log(f"Testing: DELETE /api/v1/maintenance/{record_id}/images/{image_id}")
        try:
            response = self.session.delete(
                f"{self.api_base}/maintenance/{record_id}/images/{image_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                self.log(f"✅ Delete maintenance image successful")
                return True
            else:
                self.log(f"❌ Delete maintenance image failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Exception in delete maintenance image: {e}", "ERROR")
            return False
    
    def test_delete_maintenance_record(self, record_id: str) -> bool:
        """Test DELETE /api/v1/maintenance/{id}"""
        self.log(f"Testing: DELETE /api/v1/maintenance/{record_id}")
        try:
            response = self.session.delete(f"{self.api_base}/maintenance/{record_id}", headers=self.headers)
            
            if response.status_code == 200:
                self.log(f"✅ Delete maintenance record successful")
                return True
            else:
                self.log(f"❌ Delete maintenance failed: {response.status_code} - {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Exception in delete maintenance: {e}", "ERROR")
            return False
    
    def cleanup(self):
        """Clean up any created test data"""
        self.log("Cleaning up test data...")
        
        # Clean up created records
        for record_id in self.created_records:
            try:
                self.test_delete_maintenance_record(record_id)
            except Exception as e:
                self.log(f"Failed to cleanup record {record_id}: {e}", "WARN")
    
    def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run all maintenance endpoint tests"""
        results = {}
        
        self.log("🚀 Starting Comprehensive Maintenance API Tests")
        self.log("=" * 60)
        
        # Check server health first
        if not self.check_server_health():
            self.log("❌ Cannot proceed with tests - server is not healthy", "ERROR")
            return {"server_health": False}
        
        results["server_health"] = True
        
        # Test 1: List maintenance records
        results["list_maintenance"] = self.test_list_maintenance_records()
        
        # Test 2: Create maintenance record
        record_id = self.test_create_maintenance_record()
        results["create_maintenance"] = record_id is not None
        
        if record_id:
            # Test 3: Get specific maintenance record
            results["get_maintenance"] = self.test_get_maintenance_record(record_id)
            
            # Test 4: Update maintenance record
            results["update_maintenance"] = self.test_update_maintenance_record(record_id)
            
            # Test 5: Upload images
            uploaded_image_ids = self.test_upload_maintenance_images(record_id)
            results["upload_images"] = len(uploaded_image_ids) > 0
            
            # Test 6: Delete image (if we uploaded any)
            if uploaded_image_ids:
                results["delete_image"] = self.test_delete_maintenance_image(record_id, uploaded_image_ids[0])
            else:
                results["delete_image"] = False
                self.log("⏭️  Skipping delete image test - no images uploaded", "WARN")
            
            # Test 7: Get ATM maintenance history
            results["get_atm_history"] = self.test_get_atm_maintenance_history()
            
            # Test 8: Delete maintenance record (cleanup)
            results["delete_maintenance"] = self.test_delete_maintenance_record(record_id)
        else:
            # Skip tests that require a record ID
            for test in ["get_maintenance", "update_maintenance", "upload_images", "delete_image", "delete_maintenance"]:
                results[test] = False
                self.log(f"⏭️  Skipping {test} - no record created", "WARN")
            
            results["get_atm_history"] = self.test_get_atm_maintenance_history()
        
        return results
    
    def print_test_summary(self, results: Dict[str, bool]):
        """Print a summary of test results"""
        self.log("=" * 60)
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            self.log(f"{test_name:<20}: {status}")
        
        self.log("-" * 60)
        self.log(f"Total Tests: {total_tests}")
        self.log(f"Passed: {passed_tests}")
        self.log(f"Failed: {total_tests - passed_tests}")
        self.log(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            self.log("🎉 All tests passed! Maintenance API is working correctly.")
        else:
            self.log("⚠️  Some tests failed. Check the logs above for details.")

def main():
    """Main function to run the tests"""
    print(f"""
🔧 Terminal Maintenance API Endpoint Tester
==========================================

Testing all endpoints according to PRD specifications:
- List maintenance records
- Create maintenance record  
- Get specific record
- Update maintenance record
- Delete maintenance record
- Get ATM maintenance history
- Upload images
- Delete image

Server: {BASE_URL}
Terminal ID: {TEST_TERMINAL_ID}

Starting tests...
""")
    
    # Create tester instance
    tester = MaintenanceAPITester(BASE_URL)
    
    try:
        # Run comprehensive tests
        results = tester.run_comprehensive_test()
        
        # Print summary
        tester.print_test_summary(results)
        
        # Exit with appropriate code
        all_passed = all(results.values())
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        tester.log("Tests interrupted by user", "WARN")
        sys.exit(1)
    except Exception as e:
        tester.log(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)
    finally:
        # Always try to cleanup
        try:
            tester.cleanup()
        except Exception as e:
            print(f"Warning: Cleanup failed: {e}")

if __name__ == "__main__":
    main()

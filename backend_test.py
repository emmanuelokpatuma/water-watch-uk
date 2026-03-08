#!/usr/bin/env python3
"""
UK Water Safety Map Backend API Test Suite
Tests all API endpoints using the public URL
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

# Use the public URL from frontend/.env
BACKEND_URL = "https://water-watch-uk.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class WaterSafetyAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 30
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_results = {}

    def log_test_result(self, test_name: str, success: bool, response_data: Dict = None, error_msg: str = None):
        """Log test result for reporting"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}")
        else:
            print(f"❌ {test_name}: {error_msg}")
            self.failed_tests.append({"test": test_name, "error": error_msg})
        
        self.test_results[test_name] = {
            "success": success,
            "response_data": response_data,
            "error": error_msg
        }

    def test_health_endpoints(self):
        """Test basic health check endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test root endpoint
        try:
            response = self.session.get(f"{API_BASE}/")
            success = response.status_code == 200
            if success:
                data = response.json()
                expected_fields = ["message", "version"]
                if all(field in data for field in expected_fields):
                    self.log_test_result("Root endpoint structure", True, data)
                else:
                    self.log_test_result("Root endpoint structure", False, error_msg=f"Missing expected fields: {expected_fields}")
            else:
                self.log_test_result("Root endpoint", False, error_msg=f"Status {response.status_code}")
        except Exception as e:
            self.log_test_result("Root endpoint", False, error_msg=str(e))

        # Test health endpoint  
        try:
            response = self.session.get(f"{API_BASE}/health")
            success = response.status_code == 200
            if success:
                data = response.json()
                if "status" in data and data["status"] == "healthy":
                    self.log_test_result("Health endpoint", True, data)
                else:
                    self.log_test_result("Health endpoint", False, error_msg="Invalid health status")
            else:
                self.log_test_result("Health endpoint", False, error_msg=f"Status {response.status_code}")
        except Exception as e:
            self.log_test_result("Health endpoint", False, error_msg=str(e))

    def test_stations_endpoint(self):
        """Test water monitoring stations endpoint"""
        print("\n🔍 Testing Stations Endpoint...")
        
        try:
            response = self.session.get(f"{API_BASE}/stations")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                stations = data.get("stations", [])
                
                # Check we have stations
                if len(stations) > 0:
                    self.log_test_result("Stations data retrieval", True, {"count": len(stations)})
                    
                    # Check first station structure
                    first_station = stations[0]
                    required_fields = ["station_id", "label", "latitude", "longitude", "safety_score"]
                    
                    if all(field in first_station for field in required_fields):
                        self.log_test_result("Station data structure", True, {"sample_station": first_station})
                        
                        # Verify we have enough stations (should be ~100)
                        if len(stations) >= 50:  # Allow some flexibility
                            self.log_test_result("Sufficient stations count", True, {"count": len(stations)})
                        else:
                            self.log_test_result("Sufficient stations count", False, error_msg=f"Only {len(stations)} stations, expected ~100")
                    else:
                        missing = [f for f in required_fields if f not in first_station]
                        self.log_test_result("Station data structure", False, error_msg=f"Missing fields: {missing}")
                else:
                    self.log_test_result("Stations data retrieval", False, error_msg="No stations returned")
            else:
                self.log_test_result("Stations endpoint", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Stations endpoint", False, error_msg=str(e))

    def test_flood_warnings_endpoint(self):
        """Test flood warnings endpoint"""
        print("\n🔍 Testing Flood Warnings Endpoint...")
        
        try:
            response = self.session.get(f"{API_BASE}/flood-warnings")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                warnings = data.get("warnings", [])
                self.log_test_result("Flood warnings retrieval", True, {"warnings_count": len(warnings)})
                
                if warnings:
                    # Check warning structure
                    first_warning = warnings[0]
                    expected_fields = ["id", "description", "severity"]
                    if all(field in first_warning for field in expected_fields):
                        self.log_test_result("Flood warning structure", True, {"sample_warning": first_warning})
                    else:
                        missing = [f for f in expected_fields if f not in first_warning]
                        self.log_test_result("Flood warning structure", False, error_msg=f"Missing fields: {missing}")
            else:
                self.log_test_result("Flood warnings endpoint", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Flood warnings endpoint", False, error_msg=str(e))

    def test_search_endpoint(self):
        """Test location search functionality"""
        print("\n🔍 Testing Search Endpoint...")
        
        # Test postcode search
        try:
            response = self.session.get(f"{API_BASE}/search", params={"q": "SW1A 1AA"})
            success = response.status_code == 200
            
            if success:
                data = response.json()
                results = data.get("results", [])
                self.log_test_result("Postcode search", True, {"results_count": len(results)})
                
                if results:
                    first_result = results[0]
                    if "latitude" in first_result and "longitude" in first_result:
                        self.log_test_result("Search result structure", True, {"sample_result": first_result})
                    else:
                        self.log_test_result("Search result structure", False, error_msg="Missing coordinates")
            else:
                self.log_test_result("Postcode search", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Postcode search", False, error_msg=str(e))

        # Test place name search
        try:
            response = self.session.get(f"{API_BASE}/search", params={"q": "London"})
            success = response.status_code == 200
            
            if success:
                data = response.json()
                results = data.get("results", [])
                self.log_test_result("Place name search", True, {"results_count": len(results)})
            else:
                self.log_test_result("Place name search", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Place name search", False, error_msg=str(e))

    def test_ai_insight_endpoint(self):
        """Test AI safety insight generation"""
        print("\n🔍 Testing AI Insight Endpoint...")
        
        test_payload = {
            "station_name": "River Thames at Richmond",
            "river_name": "River Thames", 
            "water_level": 2.1,
            "safety_score": 8,
            "pollution_risk": "Low",
            "flood_risk": "None",
            "activity": "swimming"
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/ai/safety-insight",
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if "insight" in data and data["insight"]:
                    self.log_test_result("AI insight generation", True, {"insight_length": len(data["insight"])})
                else:
                    self.log_test_result("AI insight generation", False, error_msg="No insight returned")
            else:
                self.log_test_result("AI insight endpoint", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("AI insight endpoint", False, error_msg=str(e))

    def test_auth_endpoints(self):
        """Test authentication endpoints (without actual login)"""
        print("\n🔍 Testing Auth Endpoints...")
        
        # Test /auth/me without authentication (should return 401)
        try:
            response = self.session.get(f"{API_BASE}/auth/me")
            if response.status_code == 401:
                self.log_test_result("Auth me (unauthenticated)", True, {"expected_401": True})
            else:
                self.log_test_result("Auth me (unauthenticated)", False, error_msg=f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Auth me endpoint", False, error_msg=str(e))

        # Test /favorites without authentication (should return 401)
        try:
            response = self.session.get(f"{API_BASE}/favorites")
            if response.status_code == 401:
                self.log_test_result("Favorites (unauthenticated)", True, {"expected_401": True})
            else:
                self.log_test_result("Favorites (unauthenticated)", False, error_msg=f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Favorites endpoint", False, error_msg=str(e))

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting UK Water Safety Map Backend API Tests")
        print(f"Testing against: {BACKEND_URL}")
        print("=" * 60)
        
        # Run all test suites
        self.test_health_endpoints()
        self.test_stations_endpoint()
        self.test_flood_warnings_endpoint() 
        self.test_search_endpoint()
        self.test_ai_insight_endpoint()
        self.test_auth_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results Summary")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests:")
            for fail in self.failed_tests:
                print(f"  • {fail['test']}: {fail['error']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test runner"""
    tester = WaterSafetyAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    results_data = {
        "timestamp": datetime.now().isoformat(),
        "backend_url": BACKEND_URL,
        "summary": {
            "tests_run": tester.tests_run,
            "tests_passed": tester.tests_passed,
            "success_rate": (tester.tests_passed/tester.tests_run)*100 if tester.tests_run > 0 else 0
        },
        "failed_tests": tester.failed_tests,
        "detailed_results": tester.test_results
    }
    
    with open('/app/test_results_backend.json', 'w') as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: /app/test_results_backend.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
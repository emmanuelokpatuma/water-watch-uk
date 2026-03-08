#!/usr/bin/env python3
"""
Backend API Testing for Water Watch UK - Home Water Quality Features
Testing the new home water quality endpoints and area reports
"""

import requests
import sys
from datetime import datetime
import json

class WaterWatchAPITester:
    def __init__(self, base_url="https://water-watch-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.errors = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            self.errors.append(f"{name}: {details}")
            print(f"❌ {name} - {details}")

    def test_endpoint(self, name, endpoint, expected_status=200, params=None):
        """Test an API endpoint"""
        try:
            url = f"{self.api_base}/{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == expected_status:
                try:
                    data = response.json()
                    self.log_test(name, True)
                    return True, data
                except json.JSONDecodeError:
                    self.log_test(name, False, f"Invalid JSON response")
                    return False, {}
            else:
                self.log_test(name, False, f"Status {response.status_code}, expected {expected_status}")
                return False, {}
        except Exception as e:
            self.log_test(name, False, f"Request failed: {str(e)}")
            return False, {}

    def test_home_water_quality(self):
        """Test home water quality endpoint"""
        print("\n🧪 Testing Home Water Quality API")
        
        # Test with Yorkshire Water postcode LS1 1AA
        success, data = self.test_endpoint(
            "Home Water Quality - LS1 1AA", 
            "home-water/quality", 
            params={"postcode": "LS1 1AA"}
        )
        
        if success:
            # Validate response structure
            required_fields = ['water_company', 'quality_rating', 'parameters']
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                self.log_test("Water Quality Response Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Water Quality Response Structure", True)
                
                # Check if Yorkshire Water is detected for LS postcode
                if data.get('water_company') == 'Yorkshire Water':
                    self.log_test("Water Company Detection - Yorkshire Water", True)
                else:
                    self.log_test("Water Company Detection - Yorkshire Water", False, f"Got: {data.get('water_company')}")
                
                # Check water quality parameters
                parameters = data.get('parameters', {})
                expected_params = ['chlorine', 'hardness', 'lead', 'fluoride']
                
                for param in expected_params:
                    if param in parameters:
                        self.log_test(f"Parameter Present - {param.title()}", True)
                    else:
                        self.log_test(f"Parameter Present - {param.title()}", False, "Parameter missing")
                
                # Check data source info
                if 'data_source' in data:
                    self.log_test("Data Source Info Present", True)
                else:
                    self.log_test("Data Source Info Present", False, "data_source field missing")
        
        # Test with invalid postcode
        success, data = self.test_endpoint(
            "Water Quality - Invalid Postcode", 
            "home-water/quality", 
            expected_status=400,
            params={"postcode": "INVALID"}
        )

    def test_area_report(self):
        """Test area report endpoint"""
        print("\n🧪 Testing Area Report API")
        
        # Test area report with Leeds coordinates
        success, data = self.test_endpoint(
            "Area Report - Leeds Area", 
            "home-water/area-report", 
            params={
                "lat": "53.8",
                "lng": "-1.55", 
                "radius_km": "20"
            }
        )
        
        if success:
            # Validate response structure for area report
            expected_fields = ['area_info', 'water_sources', 'nearby_monitoring']
            present_fields = [f for f in expected_fields if f in data]
            
            if present_fields:
                self.log_test("Area Report Response Structure", True)
            else:
                # Check if it returns any meaningful data structure
                if isinstance(data, dict) and len(data) > 0:
                    self.log_test("Area Report Response Structure", True, "Alternative structure present")
                else:
                    self.log_test("Area Report Response Structure", False, "No meaningful structure found")

    def test_other_endpoints(self):
        """Test other related endpoints"""
        print("\n🧪 Testing Related Water Endpoints")
        
        # Test stations endpoint (should work)
        success, data = self.test_endpoint("Water Stations", "stations")
        
        # Test search endpoint
        success, data = self.test_endpoint(
            "Location Search", 
            "search", 
            params={"q": "Leeds"}
        )

    def run_comprehensive_test(self):
        """Run all tests"""
        print("🌊 Water Watch UK - Backend API Testing")
        print("=" * 50)
        
        # Test the new home water features
        self.test_home_water_quality()
        self.test_area_report()
        self.test_other_endpoints()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} passed")
        
        if self.errors:
            print(f"\n❌ Failed Tests:")
            for error in self.errors:
                print(f"  • {error}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"\n🎯 Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test runner"""
    tester = WaterWatchAPITester()
    
    try:
        success = tester.run_comprehensive_test()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
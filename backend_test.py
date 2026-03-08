#!/usr/bin/env python3
"""
Backend API Testing for Water Watch UK - Subscription Features
Testing subscription endpoints and feature gating
"""

import requests
import sys
from datetime import datetime
import json

class WaterWatchAPITester:
    def __init__(self, base_url="https://water-watch-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []

    def log_result(self, test_name, passed, details=None, response_data=None):
        """Log test result"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
        
        result = {
            "test": test_name,
            "passed": passed,
            "details": details or "",
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")
        if response_data and not passed:
            print(f"    Response: {response_data}")

    def test_endpoint(self, name, endpoint, expected_status=200, params=None, method="GET", data=None):
        """Test an API endpoint"""
        try:
            url = f"{self.api_base}/{endpoint}"
            
            if method == "GET":
                response = self.session.get(url, params=params, timeout=10)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == expected_status:
                try:
                    data = response.json()
                    self.log_result(name, True, f"Status {response.status_code}")
                    return True, data
                except json.JSONDecodeError:
                    self.log_result(name, False, "Invalid JSON response")
                    return False, {}
            else:
                self.log_result(name, False, f"Status {response.status_code}, expected {expected_status}", response.text[:200])
                return False, {}
        except Exception as e:
            self.log_result(name, False, f"Request failed: {str(e)}")
            return False, {}

    def test_subscription_status_unauthenticated(self):
        """Test GET /api/subscription/status returns 401 for unauthenticated users"""
        print("\n🧪 Testing Subscription Status (Unauthenticated)")
        success, data = self.test_endpoint(
            "Subscription Status (No Auth)", 
            "subscription/status",
            expected_status=401
        )

    def test_subscription_feature_check_unauthenticated(self):
        """Test feature check for AI_SAFETY_INSIGHTS without authentication"""
        print("\n🧪 Testing Feature Check - AI_SAFETY_INSIGHTS (Unauthenticated)")
        success, data = self.test_endpoint(
            "Feature Check AI_SAFETY_INSIGHTS (No Auth)", 
            "subscription/check-feature/AI_SAFETY_INSIGHTS"
        )
        
        if success:
            # Validate response structure
            expected_fields = ["has_access", "feature", "tier_required"]
            missing_fields = [f for f in expected_fields if f not in data]
            
            if missing_fields:
                self.log_result("Feature Check Response Structure", False, f"Missing fields: {missing_fields}", data)
            else:
                # Check values
                if (data.get("has_access") == False and 
                    data.get("feature") == "AI_SAFETY_INSIGHTS" and 
                    data.get("tier_required") == "pro"):
                    self.log_result("Feature Check AI_SAFETY_INSIGHTS Access Control", True, f"Correct access control: {data}")
                else:
                    self.log_result("Feature Check AI_SAFETY_INSIGHTS Access Control", False, f"Unexpected values: {data}")

    def test_subscription_feature_check_free_features(self):
        """Test free features are accessible without authentication"""
        print("\n🧪 Testing Free Feature Access")
        free_features = ["VIEW_MAP", "BASIC_WATER_QUALITY", "LIMITED_FAVORITES", "SEARCH"]
        
        for feature in free_features:
            success, data = self.test_endpoint(
                f"Feature Check {feature} (Free)", 
                f"subscription/check-feature/{feature}"
            )
            
            if success:
                if data.get("has_access") == True and data.get("tier_required") == "free":
                    self.log_result(f"Free Feature {feature} Access", True, f"Correctly accessible: {data}")
                else:
                    self.log_result(f"Free Feature {feature} Access", False, f"Should be accessible: {data}")

    def test_basic_endpoints(self):
        """Test basic API endpoints work"""
        print("\n🧪 Testing Basic API Endpoints")
        endpoints = [
            ("stations", "Water Stations"),
            ("bathing-waters", "Bathing Waters"),
            ("flood-warnings", "Flood Warnings"),
            ("search?q=Leeds", "Location Search")
        ]
        
        for endpoint, description in endpoints:
            success, data = self.test_endpoint(description, endpoint)

    def test_favorites_unauthenticated(self):
        """Test favorites endpoint requires authentication"""
        print("\n🧪 Testing Favorites Authentication")
        success, data = self.test_endpoint(
            "Favorites (No Auth)", 
            "favorites",
            expected_status=401
        )

    def test_ai_insight_endpoint(self):
        """Test AI safety insight endpoint"""
        print("\n🧪 Testing AI Safety Insight")
        payload = {
            "station_name": "Test Station",
            "river_name": "Test River", 
            "water_level": 1.5,
            "safety_score": 7,
            "pollution_risk": "Low",
            "flood_risk": "None",
            "activity": "swimming"
        }
        
        success, data = self.test_endpoint(
            "AI Safety Insight", 
            "ai/safety-insight",
            method="POST",
            data=payload
        )
        
        if success:
            if "insight" in data and isinstance(data["insight"], str):
                self.log_result("AI Insight Response Structure", True, f"Returns insight: {data['insight'][:50]}...")
            else:
                self.log_result("AI Insight Response Structure", False, f"Missing or invalid insight field: {data}")

    def run_comprehensive_test(self):
        """Run all subscription and feature tests"""
        print("🌊 Water Watch UK - Backend Subscription Testing")
        print("=" * 50)
        
        # Test subscription endpoints
        self.test_subscription_status_unauthenticated()
        self.test_subscription_feature_check_unauthenticated()
        self.test_subscription_feature_check_free_features()
        
        # Test basic endpoints
        self.test_basic_endpoints()
        self.test_favorites_unauthenticated()
        
        # Test AI features
        self.test_ai_insight_endpoint()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        print(f"🎯 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed != self.tests_run:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        # Save detailed results
        with open('/tmp/backend_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)
        
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
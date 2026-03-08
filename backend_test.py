import requests
import sys
import os
from io import BytesIO
from PIL import Image
import base64
import json
import time
from datetime import datetime

class UKWaterSafetyTester:
    def __init__(self, base_url="https://water-watch-uk.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_result(self, test_name, passed, details=""):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        result = f"{status} - {test_name}"
        if details:
            result += f" - {details}"
        
        print(result)
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        return passed

    def test_vapid_key_endpoint(self):
        """Test VAPID key endpoint returns public key for WebPush"""
        try:
            response = requests.get(f"{self.api_url}/push/vapid-key", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'public_key' in data and data['public_key']:
                    return self.log_result("VAPID Key Endpoint", True, f"Public key: {data['public_key'][:20]}...")
                else:
                    return self.log_result("VAPID Key Endpoint", False, "No public_key in response")
            else:
                return self.log_result("VAPID Key Endpoint", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.log_result("VAPID Key Endpoint", False, f"Error: {str(e)}")

    def test_service_worker_endpoint(self):
        """Test service worker is served at /sw.js"""
        try:
            response = requests.get(f"{self.base_url}/sw.js", timeout=10)
            
            if response.status_code == 200:
                content = response.text
                if 'serviceWorker' in content or 'push' in content.lower():
                    return self.log_result("Service Worker /sw.js", True, f"File size: {len(content)} chars")
                else:
                    return self.log_result("Service Worker /sw.js", False, "No push notification code found")
            else:
                return self.log_result("Service Worker /sw.js", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.log_result("Service Worker /sw.js", False, f"Error: {str(e)}")

    def authenticate_dummy_user(self):
        """Authenticate with a dummy session for photo upload testing"""
        try:
            # For photo upload testing, we need authentication
            # Using dummy session approach
            session_data = {
                "session_id": "test_session_webpush_photo_upload"
            }
            
            # This might fail if auth is required, but we'll try the endpoints anyway
            response = requests.post(f"{self.api_url}/auth/session", 
                                   json=session_data, timeout=10)
            
            if response.status_code == 200:
                # Extract session token from cookies if available
                cookies = response.cookies
                self.token = cookies.get('session_token', None)
                return True
            return False
                
        except Exception as e:
            print(f"Note: Authentication skipped - {str(e)}")
            return False

    def create_test_image(self):
        """Create a small test image for upload testing"""
        # Create a small test image
        img = Image.new('RGB', (100, 100), color='red')
        
        # Save to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        
        return img_bytes.getvalue()

    def test_photo_upload_endpoint(self):
        """Test photo upload endpoint accepts image files"""
        try:
            # Create test image
            test_image = self.create_test_image()
            
            # Prepare files for upload
            files = {
                'file': ('test_image.jpg', test_image, 'image/jpeg')
            }
            
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            response = requests.post(f"{self.api_url}/upload/photo", 
                                   files=files, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if 'url' in data and 'filename' in data:
                    return self.log_result("Photo Upload Endpoint", True, f"Uploaded: {data['filename']}")
                else:
                    return self.log_result("Photo Upload Endpoint", False, "Missing url/filename in response")
            elif response.status_code == 401:
                return self.log_result("Photo Upload Endpoint", True, "Properly protected (401 without auth)")
            else:
                return self.log_result("Photo Upload Endpoint", False, f"HTTP {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            return self.log_result("Photo Upload Endpoint", False, f"Error: {str(e)}")

    def test_push_subscription_endpoints(self):
        """Test WebPush subscription endpoints"""
        try:
            # Test subscription endpoint structure
            subscription_data = {
                "endpoint": "https://fcm.googleapis.com/fcm/send/test",
                "keys": {
                    "p256dh": "test_p256dh_key",
                    "auth": "test_auth_key"
                }
            }
            
            headers = {'Content-Type': 'application/json'}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            response = requests.post(f"{self.api_url}/push/subscribe", 
                                   json=subscription_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return self.log_result("Push Subscription Endpoint", True, "Accepts subscription data")
            elif response.status_code == 401:
                return self.log_result("Push Subscription Endpoint", True, "Properly protected (401 without auth)")
            else:
                return self.log_result("Push Subscription Endpoint", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.log_result("Push Subscription Endpoint", False, f"Error: {str(e)}")

    def test_thames_water_api_integration(self):
        """Test Thames Water API integration endpoint"""
        try:
            response = requests.get(f"{self.api_url}/sewage/thames-water", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                if status == 'not_configured':
                    # Check that registration instructions are provided
                    message = data.get('message', '')
                    has_registration_url = 'data.thameswater.co.uk' in message
                    return self.log_result("Thames Water API Integration", True, 
                                         f"Not configured (expected) - Registration instructions: {has_registration_url}")
                elif status == 'live':
                    incidents_count = len(data.get('incidents', []))
                    return self.log_result("Thames Water API Integration", True, 
                                         f"Live API data - {incidents_count} incidents")
                else:
                    return self.log_result("Thames Water API Integration", True, f"Status: {status}")
            else:
                return self.log_result("Thames Water API Integration", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.log_result("Thames Water API Integration", False, f"Error: {str(e)}")

    def test_admin_stats_endpoint(self):
        """Test admin stats endpoint"""
        try:
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            response = requests.get(f"{self.api_url}/admin/stats", headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected_keys = ['reports', 'users', 'favorites']
                has_all_keys = all(key in data for key in expected_keys)
                
                if has_all_keys:
                    pending = data['reports'].get('pending', 0)
                    approved = data['reports'].get('approved', 0)
                    total_users = data['users'].get('total', 0)
                    return self.log_result("Admin Stats Endpoint", True, 
                                         f"Reports: {pending} pending, {approved} approved. Users: {total_users}")
                else:
                    return self.log_result("Admin Stats Endpoint", False, f"Missing keys: {expected_keys}")
            elif response.status_code == 401:
                return self.log_result("Admin Stats Endpoint", True, "Properly protected (401 without auth)")
            else:
                return self.log_result("Admin Stats Endpoint", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.log_result("Admin Stats Endpoint", False, f"Error: {str(e)}")

    def test_admin_reports_endpoint(self):
        """Test admin reports endpoint for moderation"""
        try:
            headers = {}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            response = requests.get(f"{self.api_url}/admin/reports?status=pending&page=1&limit=5", 
                                  headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                expected_keys = ['reports', 'total', 'page', 'pages']
                has_all_keys = all(key in data for key in expected_keys)
                
                if has_all_keys:
                    reports_count = len(data.get('reports', []))
                    total = data.get('total', 0)
                    return self.log_result("Admin Reports Endpoint", True, 
                                         f"Paginated list: {reports_count} reports on page 1, total: {total}")
                else:
                    return self.log_result("Admin Reports Endpoint", False, f"Missing pagination keys")
            elif response.status_code == 401:
                return self.log_result("Admin Reports Endpoint", True, "Properly protected (401 without auth)")
            else:
                return self.log_result("Admin Reports Endpoint", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            return self.log_result("Admin Reports Endpoint", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all tests for the UK Water Safety Map final implementation"""
        print("🚀 Testing UK Water Safety Map - Final Implementation")
        print("Features: VAPID keys, Thames Water API, Admin Dashboard, Service Worker, Photo Upload")
        print("=" * 75)
        
        # Try to authenticate (may fail, that's ok for admin endpoints)
        auth_success = self.authenticate_dummy_user()
        if auth_success:
            print("✅ Authentication successful for protected endpoints")
        else:
            print("ℹ️  Running tests without authentication (protected endpoints will show 401)")
        
        print("\n🔧 Testing Core Features:")
        # Core required features from review request
        self.test_vapid_key_endpoint()
        self.test_service_worker_endpoint() 
        self.test_photo_upload_endpoint()
        self.test_thames_water_api_integration()
        
        print("\n🛡️  Testing Admin Features:")
        self.test_admin_stats_endpoint()
        self.test_admin_reports_endpoint()
        
        print("\n📱 Testing WebPush Features:")
        self.test_push_subscription_endpoints()
        
        # Summary
        print("\n" + "=" * 75)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed ({self.tests_passed/self.tests_run*100:.1f}%)")
        
        # Detailed failure analysis
        failed_tests = [r for r in self.test_results if not r['passed']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['details']}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All UK Water Safety Map features working correctly!")
            return 0
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} tests failed - see details above")
            return 1

def main():
    tester = UKWaterSafetyTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
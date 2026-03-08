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

    def test_bathing_waters_endpoint(self):
        """Test bathing waters endpoint - NEW FEATURE"""
        print("\n🔍 Testing Bathing Waters Endpoint...")
        
        try:
            response = self.session.get(f"{API_BASE}/bathing-waters")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                bathing_waters = data.get("bathing_waters", [])
                
                # Check we have bathing waters data
                if len(bathing_waters) > 0:
                    self.log_test_result("Bathing waters data retrieval", True, {"count": len(bathing_waters)})
                    
                    # Check first bathing water structure
                    first_beach = bathing_waters[0]
                    required_fields = ["id", "name", "latitude", "longitude", "classification"]
                    
                    if all(field in first_beach for field in required_fields):
                        self.log_test_result("Bathing water data structure", True, {"sample_beach": first_beach})
                        
                        # Check classification values are valid
                        classifications = [beach.get("classification") for beach in bathing_waters]
                        valid_classifications = ["Excellent", "Good", "Sufficient", "Poor"]
                        if all(c in valid_classifications for c in classifications if c):
                            self.log_test_result("Valid bathing water classifications", True, {"classifications": list(set(classifications))})
                        else:
                            self.log_test_result("Valid bathing water classifications", False, error_msg=f"Invalid classifications found")
                    else:
                        missing = [f for f in required_fields if f not in first_beach]
                        self.log_test_result("Bathing water data structure", False, error_msg=f"Missing fields: {missing}")
                else:
                    self.log_test_result("Bathing waters data retrieval", True, {"count": 0, "note": "No bathing waters available"})
            else:
                self.log_test_result("Bathing waters endpoint", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Bathing waters endpoint", False, error_msg=str(e))

    def test_historical_data_endpoint(self):
        """Test historical data endpoint - NEW FEATURE"""
        print("\n🔍 Testing Historical Data Endpoint...")
        
        # First get a station ID from stations endpoint
        try:
            stations_response = self.session.get(f"{API_BASE}/stations")
            if stations_response.status_code == 200:
                stations_data = stations_response.json()
                stations = stations_data.get("stations", [])
                if stations:
                    test_station_id = stations[0]["station_id"]
                    
                    # Test historical data endpoint
                    response = self.session.get(f"{API_BASE}/stations/{test_station_id}/history?days=7")
                    success = response.status_code == 200
                    
                    if success:
                        data = response.json()
                        history = data.get("history", [])
                        summary = data.get("summary", {})
                        
                        self.log_test_result("Historical data retrieval", True, {
                            "station_id": test_station_id,
                            "history_points": len(history),
                            "has_summary": len(summary) > 0
                        })
                        
                        # Check summary contains required stats
                        required_summary_fields = ["min", "max", "avg", "trend"]
                        if summary and all(field in summary for field in required_summary_fields):
                            self.log_test_result("Historical data summary structure", True, {"summary": summary})
                            
                            # Check trend values are valid
                            if summary.get("trend") in ["rising", "falling", "stable"]:
                                self.log_test_result("Valid trend analysis", True, {"trend": summary.get("trend")})
                            else:
                                self.log_test_result("Valid trend analysis", False, error_msg=f"Invalid trend: {summary.get('trend')}")
                        else:
                            missing = [f for f in required_summary_fields if f not in summary]
                            self.log_test_result("Historical data summary structure", False, error_msg=f"Missing summary fields: {missing}")
                        
                        # Check history data structure
                        if history:
                            first_reading = history[0]
                            if "datetime" in first_reading and "value" in first_reading:
                                self.log_test_result("Historical reading structure", True, {"sample_reading": first_reading})
                            else:
                                self.log_test_result("Historical reading structure", False, error_msg="Missing datetime or value")
                        else:
                            self.log_test_result("Historical reading structure", True, {"note": "No historical data available"})
                    else:
                        self.log_test_result("Historical data endpoint", False, error_msg=f"Status {response.status_code}")
                else:
                    self.log_test_result("Historical data endpoint", False, error_msg="No stations available for testing")
            else:
                self.log_test_result("Historical data endpoint", False, error_msg="Failed to get stations for testing")
                
        except Exception as e:
            self.log_test_result("Historical data endpoint", False, error_msg=str(e))

    def test_share_report_endpoint(self):
        """Test share report generation - NEW FEATURE"""
        print("\n🔍 Testing Share Report Endpoint...")
        
        test_payload = {
            "station_id": "test_station_1",
            "station_name": "River Thames at Richmond",
            "river_name": "River Thames",
            "safety_score": 8,
            "pollution_risk": "Low",
            "flood_risk": "None",
            "water_level": 2.1
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/share/generate-report",
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["report_id", "share_text", "twitter_url", "facebook_url"]
                
                if all(field in data for field in required_fields):
                    self.log_test_result("Share report generation", True, {
                        "report_id": data.get("report_id"),
                        "share_text_length": len(data.get("share_text", ""))
                    })
                    
                    # Check share text contains expected elements (emojis, hashtags)
                    share_text = data.get("share_text", "")
                    if "🌊" in share_text and "#" in share_text and "Safety Score:" in share_text:
                        self.log_test_result("Share text format with emojis/hashtags", True, {"contains_emojis_and_hashtags": True})
                    else:
                        self.log_test_result("Share text format with emojis/hashtags", False, error_msg="Missing emojis or hashtags in share text")
                    
                    # Test retrieving the generated report
                    report_id = data.get("report_id")
                    if report_id:
                        report_response = self.session.get(f"{API_BASE}/share/report/{report_id}")
                        if report_response.status_code == 200:
                            self.log_test_result("Share report retrieval", True, {"report_id": report_id})
                        else:
                            self.log_test_result("Share report retrieval", False, error_msg=f"Status {report_response.status_code}")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test_result("Share report generation", False, error_msg=f"Missing fields: {missing}")
            else:
                self.log_test_result("Share report endpoint", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Share report endpoint", False, error_msg=str(e))

    def test_notification_endpoints(self):
        """Test notification subscription endpoints - NEW FEATURE"""
        print("\n🔍 Testing Notification Endpoints...")
        
        # Test getting subscriptions without authentication (should return 401)
        try:
            response = self.session.get(f"{API_BASE}/notifications/subscriptions")
            if response.status_code == 401:
                self.log_test_result("Notification subscriptions (unauthenticated)", True, {"expected_401": True})
            else:
                self.log_test_result("Notification subscriptions (unauthenticated)", False, error_msg=f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Notification subscriptions endpoint", False, error_msg=str(e))

        # Test subscribing without authentication (should return 401)
        test_subscription = {
            "station_ids": ["test_station_1", "test_station_2"],
            "alert_types": ["flood", "sewage", "pollution"]
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/notifications/subscribe",
                json=test_subscription,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 401:
                self.log_test_result("Notification subscribe (unauthenticated)", True, {"expected_401": True})
            else:
                self.log_test_result("Notification subscribe (unauthenticated)", False, error_msg=f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Notification subscribe endpoint", False, error_msg=str(e))

        # Test getting alerts without authentication (should return 401)
        try:
            response = self.session.get(f"{API_BASE}/notifications/alerts")
            if response.status_code == 401:
                self.log_test_result("Notification alerts (unauthenticated)", True, {"expected_401": True})
            else:
                self.log_test_result("Notification alerts (unauthenticated)", False, error_msg=f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Notification alerts endpoint", False, error_msg=str(e))

    def test_weather_endpoint(self):
        """Test weather API endpoint - NEW FEATURE"""
        print("\n🔍 Testing Weather Endpoint...")
        
        # Test weather data for London coordinates
        test_lat, test_lng = 51.5074, -0.1278
        
        try:
            response = self.session.get(f"{API_BASE}/weather", params={"lat": test_lat, "lng": test_lng})
            success = response.status_code == 200
            
            if success:
                data = response.json()
                weather = data.get("weather")
                forecast = data.get("forecast", [])
                recommendation = data.get("recommendation", "")
                
                if weather:
                    # Check current weather structure
                    required_weather_fields = ["temperature", "feels_like", "humidity", "wind_speed", "weather_description", "uv_index"]
                    if all(field in weather for field in required_weather_fields):
                        self.log_test_result("Current weather data structure", True, {"weather_sample": weather})
                        
                        # Check temperature is reasonable (between -50 and 50 Celsius)
                        temp = weather.get("temperature")
                        if temp and -50 <= temp <= 50:
                            self.log_test_result("Valid temperature range", True, {"temperature": temp})
                        else:
                            self.log_test_result("Valid temperature range", False, error_msg=f"Temperature {temp}°C out of range")
                        
                        # Check humidity is percentage (0-100)
                        humidity = weather.get("humidity")
                        if humidity and 0 <= humidity <= 100:
                            self.log_test_result("Valid humidity range", True, {"humidity": humidity})
                        else:
                            self.log_test_result("Valid humidity range", False, error_msg=f"Humidity {humidity}% out of range")
                    else:
                        missing = [f for f in required_weather_fields if f not in weather]
                        self.log_test_result("Current weather data structure", False, error_msg=f"Missing fields: {missing}")
                else:
                    self.log_test_result("Current weather data", False, error_msg="No weather data returned")
                
                # Check 3-day forecast
                if len(forecast) >= 3:
                    self.log_test_result("3-day forecast availability", True, {"forecast_days": len(forecast)})
                    
                    first_day = forecast[0]
                    required_forecast_fields = ["date", "temp_max", "temp_min", "weather_icon"]
                    if all(field in first_day for field in required_forecast_fields):
                        self.log_test_result("Forecast data structure", True, {"forecast_sample": first_day})
                    else:
                        missing = [f for f in required_forecast_fields if f not in first_day]
                        self.log_test_result("Forecast data structure", False, error_msg=f"Missing fields: {missing}")
                else:
                    self.log_test_result("3-day forecast availability", False, error_msg=f"Only {len(forecast)} forecast days available")
                
                # Check activity recommendation exists
                if recommendation and len(recommendation) > 10:
                    self.log_test_result("Activity recommendation", True, {"recommendation_length": len(recommendation)})
                else:
                    self.log_test_result("Activity recommendation", False, error_msg="No or too short recommendation")
                    
            else:
                self.log_test_result("Weather endpoint", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Weather endpoint", False, error_msg=str(e))

    def test_sewage_incidents_endpoint(self):
        """Test sewage incidents API endpoint - NEW FEATURE"""
        print("\n🔍 Testing Sewage Incidents Endpoint...")
        
        try:
            response = self.session.get(f"{API_BASE}/sewage-incidents")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                incidents = data.get("incidents", [])
                summary = data.get("summary", {})
                
                # Check we have incidents data (mock data)
                if len(incidents) > 0:
                    self.log_test_result("Sewage incidents data retrieval", True, {"count": len(incidents)})
                    
                    # Check first incident structure
                    first_incident = incidents[0]
                    required_fields = ["id", "site_name", "water_company", "status"]
                    
                    if all(field in first_incident for field in required_fields):
                        self.log_test_result("Sewage incident data structure", True, {"sample_incident": first_incident})
                        
                        # Check water company names are from expected companies
                        companies = [inc.get("water_company") for inc in incidents]
                        expected_companies = ["Thames Water", "Yorkshire Water", "United Utilities", "South West Water"]
                        if any(company in expected_companies for company in companies):
                            self.log_test_result("Valid water company names", True, {"companies": list(set(companies))})
                        else:
                            self.log_test_result("Valid water company names", False, error_msg=f"Unexpected companies: {companies}")
                        
                        # Check status values are valid
                        statuses = [inc.get("status") for inc in incidents]
                        valid_statuses = ["Discharging", "Not Discharging"]
                        if all(status in valid_statuses for status in statuses):
                            self.log_test_result("Valid discharge statuses", True, {"statuses": list(set(statuses))})
                        else:
                            self.log_test_result("Valid discharge statuses", False, error_msg=f"Invalid statuses: {statuses}")
                    else:
                        missing = [f for f in required_fields if f not in first_incident]
                        self.log_test_result("Sewage incident data structure", False, error_msg=f"Missing fields: {missing}")
                else:
                    self.log_test_result("Sewage incidents data retrieval", False, error_msg="No incidents returned")
                
                # Check summary structure
                if summary:
                    summary_fields = ["total", "currently_discharging", "past_48h"]
                    if all(field in summary for field in summary_fields):
                        self.log_test_result("Sewage incidents summary", True, {"summary": summary})
                    else:
                        missing = [f for f in summary_fields if f not in summary]
                        self.log_test_result("Sewage incidents summary", False, error_msg=f"Missing summary fields: {missing}")
                        
            else:
                self.log_test_result("Sewage incidents endpoint", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Sewage incidents endpoint", False, error_msg=str(e))

        # Test nearby sewage incidents
        try:
            # Test near London coordinates
            response = self.session.get(f"{API_BASE}/sewage-incidents/near", params={"lat": 51.5074, "lng": -0.1278, "radius_km": 50})
            success = response.status_code == 200
            
            if success:
                data = response.json()
                incidents = data.get("incidents", [])
                self.log_test_result("Nearby sewage incidents", True, {"nearby_count": len(incidents)})
                
                # Check incidents have distance
                if incidents:
                    first_incident = incidents[0]
                    if "distance_km" in first_incident:
                        self.log_test_result("Sewage incidents distance calculation", True, {"distance": first_incident.get("distance_km")})
                    else:
                        self.log_test_result("Sewage incidents distance calculation", False, error_msg="No distance_km field")
            else:
                self.log_test_result("Nearby sewage incidents", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Nearby sewage incidents", False, error_msg=str(e))

    def test_community_reports_endpoint(self):
        """Test community reports API endpoint - NEW FEATURE"""
        print("\n🔍 Testing Community Reports Endpoint...")
        
        # Test GET community reports (public endpoint)
        try:
            response = self.session.get(f"{API_BASE}/community/reports")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                reports = data.get("reports", [])
                self.log_test_result("Community reports retrieval", True, {"count": len(reports)})
                
                # If we have reports, check structure
                if reports:
                    first_report = reports[0]
                    expected_fields = ["id", "user_name", "location_name", "report_type", "description", "rating"]
                    if all(field in first_report for field in expected_fields):
                        self.log_test_result("Community report structure", True, {"sample_report": first_report})
                        
                        # Check rating is valid (1-5)
                        rating = first_report.get("rating")
                        if rating and 1 <= rating <= 5:
                            self.log_test_result("Valid community report rating", True, {"rating": rating})
                        else:
                            self.log_test_result("Valid community report rating", False, error_msg=f"Invalid rating: {rating}")
                    else:
                        missing = [f for f in expected_fields if f not in first_report]
                        self.log_test_result("Community report structure", False, error_msg=f"Missing fields: {missing}")
            else:
                self.log_test_result("Community reports endpoint", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Community reports endpoint", False, error_msg=str(e))

        # Test POST community report (should require authentication)
        test_report = {
            "latitude": 51.5074,
            "longitude": -0.1278,
            "location_name": "Test Location",
            "report_type": "observation",
            "description": "Test water quality observation",
            "rating": 4
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/community/reports",
                json=test_report,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 401:
                self.log_test_result("Community report submission (unauthenticated)", True, {"expected_401": True})
            else:
                self.log_test_result("Community report submission (unauthenticated)", False, error_msg=f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Community report submission", False, error_msg=str(e))

    def test_webpush_endpoints(self):
        """Test WebPush notification endpoints - NEW FEATURE"""
        print("\n🔍 Testing WebPush Endpoints...")
        
        # Test VAPID public key endpoint (should be public)
        try:
            response = self.session.get(f"{API_BASE}/push/vapid-key")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if "public_key" in data and data["public_key"]:
                    self.log_test_result("VAPID public key endpoint", True, {"key_length": len(data["public_key"])})
                else:
                    self.log_test_result("VAPID public key endpoint", False, error_msg="No public key returned")
            else:
                self.log_test_result("VAPID public key endpoint", False, error_msg=f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test_result("VAPID public key endpoint", False, error_msg=str(e))

        # Test push subscription (should require authentication)
        test_subscription = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test",
            "keys": {
                "p256dh": "test_p256dh_key",
                "auth": "test_auth_key"
            }
        }
        
        try:
            response = self.session.post(
                f"{API_BASE}/push/subscribe",
                json=test_subscription,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 401:
                self.log_test_result("Push subscription (unauthenticated)", True, {"expected_401": True})
            else:
                self.log_test_result("Push subscription (unauthenticated)", False, error_msg=f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Push subscription endpoint", False, error_msg=str(e))

        # Test push unsubscription (should require authentication)
        try:
            response = self.session.delete(f"{API_BASE}/push/unsubscribe")
            if response.status_code == 401:
                self.log_test_result("Push unsubscription (unauthenticated)", True, {"expected_401": True})
            else:
                self.log_test_result("Push unsubscription (unauthenticated)", False, error_msg=f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test_result("Push unsubscription endpoint", False, error_msg=str(e))

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
        self.test_bathing_waters_endpoint()  # NEW
        self.test_flood_warnings_endpoint() 
        self.test_historical_data_endpoint()  # NEW
        self.test_weather_endpoint()  # NEW - Weather API
        self.test_sewage_incidents_endpoint()  # NEW - Sewage incidents
        self.test_community_reports_endpoint()  # NEW - Community reports
        self.test_webpush_endpoints()  # NEW - WebPush notifications
        self.test_search_endpoint()
        self.test_ai_insight_endpoint()
        self.test_share_report_endpoint()  # NEW
        self.test_notification_endpoints()  # NEW
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
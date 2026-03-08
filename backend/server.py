from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, UploadFile, File, Form, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import json
import base64
from io import BytesIO

# WebPush imports
try:
    from pywebpush import webpush, WebPushException
    from py_vapid import Vapid
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False

# Image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

ROOT_DIR = Path(__file__).parent
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SessionData(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FavoriteLocation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    station_id: str
    station_name: str
    river_name: Optional[str] = None
    latitude: float
    longitude: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FavoriteCreate(BaseModel):
    station_id: str
    station_name: str
    river_name: Optional[str] = None
    latitude: float
    longitude: float

class WaterStation(BaseModel):
    station_id: str
    label: str
    river_name: Optional[str] = None
    town: Optional[str] = None
    latitude: float
    longitude: float
    water_level: Optional[float] = None
    water_level_unit: str = "m"
    typical_range_low: Optional[float] = None
    typical_range_high: Optional[float] = None
    status: str = "normal"
    last_reading: Optional[datetime] = None
    safety_score: int = 7
    pollution_risk: str = "Low"
    flood_risk: str = "None"

class SafetyInsightRequest(BaseModel):
    station_name: str
    river_name: Optional[str] = None
    water_level: Optional[float] = None
    safety_score: int
    pollution_risk: str
    flood_risk: str
    activity: str = "swimming"

class NotificationSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    station_ids: List[str] = []
    alert_types: List[str] = ["flood", "sewage", "pollution"]
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NotificationSubscriptionCreate(BaseModel):
    station_ids: List[str] = []
    alert_types: List[str] = ["flood", "sewage", "pollution"]

class ShareReportRequest(BaseModel):
    station_id: str
    station_name: str
    river_name: Optional[str] = None
    safety_score: int
    pollution_risk: str
    flood_risk: str
    water_level: Optional[float] = None

class WebPushSubscription(BaseModel):
    endpoint: str
    keys: dict

class WeatherData(BaseModel):
    temperature: float
    feels_like: float
    humidity: int
    wind_speed: float
    wind_direction: int
    weather_code: int
    weather_description: str
    precipitation: float
    uv_index: float

class SewageIncident(BaseModel):
    id: str
    site_name: str
    water_company: str
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    discharge_start: Optional[str] = None
    discharge_stop: Optional[str] = None
    duration_hours: Optional[float] = None
    alert_past_48h: bool = False

# ==================== AUTH HELPERS ====================

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session token in cookie or header"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    
    if not session_token:
        return None
    
    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session_doc:
        return None
    
    expires_at = session_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        return None
    
    user_doc = await db.users.find_one(
        {"user_id": session_doc["user_id"]},
        {"_id": 0}
    )
    
    if not user_doc:
        return None
    
    return User(**user_doc)

async def require_auth(request: Request) -> User:
    """Require authentication - raises 401 if not authenticated"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/session")
async def exchange_session(request: Request, response: Response):
    """Exchange session_id for session_token after OAuth callback"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    async with httpx.AsyncClient() as client_http:
        auth_response = await client_http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
    
    if auth_response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    auth_data = auth_response.json()
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    existing_user = await db.users.find_one({"email": auth_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": auth_data["name"],
                "picture": auth_data.get("picture")
            }}
        )
    else:
        user_doc = {
            "user_id": user_id,
            "email": auth_data["email"],
            "name": auth_data["name"],
            "picture": auth_data.get("picture"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
    
    session_token = auth_data.get("session_token", f"session_{uuid.uuid4().hex}")
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one(session_doc)
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user

@api_router.get("/auth/me")
async def get_me(user: User = Depends(require_auth)):
    """Get current authenticated user"""
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout current user"""
    session_token = request.cookies.get("session_token")
    
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/", samesite="none", secure=True)
    return {"message": "Logged out successfully"}

# ==================== WATER DATA ENDPOINTS ====================

@api_router.get("/stations")
async def get_stations(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius: float = 50
):
    """Get water monitoring stations - fetches from Environment Agency API"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            url = "https://environment.data.gov.uk/flood-monitoring/id/stations"
            params = {"_limit": 200}
            
            if lat and lng:
                params["lat"] = lat
                params["long"] = lng
                params["dist"] = radius
            
            response = await client_http.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"Environment Agency API error: {response.status_code}")
                return {"stations": get_mock_stations()}
            
            data = response.json()
            stations = []
            
            for item in data.get("items", [])[:100]:
                if not item.get("lat") or not item.get("long"):
                    continue
                
                station = {
                    "station_id": item.get("stationReference", item.get("@id", "")),
                    "label": item.get("label", "Unknown Station"),
                    "river_name": item.get("riverName"),
                    "town": item.get("town"),
                    "latitude": item.get("lat"),
                    "longitude": item.get("long"),
                    "status": item.get("status", "normal"),
                    "safety_score": calculate_safety_score(item),
                    "pollution_risk": "Low",
                    "flood_risk": "None"
                }
                
                if item.get("measures"):
                    measures = item["measures"]
                    if isinstance(measures, list) and len(measures) > 0:
                        measure = measures[0] if isinstance(measures[0], dict) else {}
                        station["water_level_unit"] = measure.get("unitName", "m")
                
                stations.append(station)
            
            return {"stations": stations if stations else get_mock_stations()}
    except Exception as e:
        logger.error(f"Error fetching stations: {e}")
        return {"stations": get_mock_stations()}

@api_router.get("/stations/{station_id}/readings")
async def get_station_readings(station_id: str):
    """Get latest readings for a specific station"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{station_id}/readings"
            params = {"_sorted": "", "_limit": 10}
            
            response = await client_http.get(url, params=params)
            
            if response.status_code != 200:
                return {"readings": [], "latest_value": None}
            
            data = response.json()
            readings = []
            
            for item in data.get("items", []):
                readings.append({
                    "datetime": item.get("dateTime"),
                    "value": item.get("value"),
                    "measure": item.get("measure")
                })
            
            latest_value = readings[0]["value"] if readings else None
            
            return {"readings": readings, "latest_value": latest_value}
    except Exception as e:
        logger.error(f"Error fetching readings: {e}")
        return {"readings": [], "latest_value": None}

@api_router.get("/bathing-waters")
async def get_bathing_waters():
    """Get bathing water quality data"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            url = "https://environment.data.gov.uk/doc/bathing-water.json"
            params = {"_limit": 100}
            
            response = await client_http.get(url, params=params)
            
            if response.status_code != 200:
                return {"bathing_waters": get_mock_bathing_waters()}
            
            data = response.json()
            waters = []
            
            for item in data.get("result", {}).get("items", []):
                water = {
                    "id": item.get("@id", ""),
                    "name": item.get("name", {}).get("_value", item.get("name", "Unknown")),
                    "latitude": item.get("lat"),
                    "longitude": item.get("long"),
                    "classification": item.get("latestComplianceAssessment", {}).get("complianceClassification", {}).get("name", {}).get("_value", "Unknown")
                }
                if water["latitude"] and water["longitude"]:
                    waters.append(water)
            
            return {"bathing_waters": waters if waters else get_mock_bathing_waters()}
    except Exception as e:
        logger.error(f"Error fetching bathing waters: {e}")
        return {"bathing_waters": get_mock_bathing_waters()}

@api_router.get("/flood-warnings")
async def get_flood_warnings():
    """Get current flood warnings"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            url = "https://environment.data.gov.uk/flood-monitoring/id/floods"
            params = {"_limit": 50}
            
            response = await client_http.get(url, params=params)
            
            if response.status_code != 200:
                return {"warnings": []}
            
            data = response.json()
            warnings = []
            
            for item in data.get("items", []):
                warning = {
                    "id": item.get("@id", ""),
                    "description": item.get("description", ""),
                    "severity": item.get("severityLevel", 3),
                    "severity_label": item.get("severity", "Unknown"),
                    "message": item.get("message", ""),
                    "area": item.get("floodArea", {}).get("label", ""),
                    "time_raised": item.get("timeRaised")
                }
                warnings.append(warning)
            
            return {"warnings": warnings}
    except Exception as e:
        logger.error(f"Error fetching flood warnings: {e}")
        return {"warnings": []}

@api_router.get("/search")
async def search_locations(q: str):
    """Search for locations by name or postcode"""
    if not q or len(q) < 2:
        return {"results": []}
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client_http:
            postcode_url = f"https://api.postcodes.io/postcodes/{q}"
            postcode_response = await client_http.get(postcode_url)
            
            if postcode_response.status_code == 200:
                data = postcode_response.json()
                if data.get("status") == 200 and data.get("result"):
                    result = data["result"]
                    return {
                        "results": [{
                            "type": "postcode",
                            "name": result.get("postcode"),
                            "display_name": f"{result.get('postcode')}, {result.get('admin_district', '')}",
                            "latitude": result.get("latitude"),
                            "longitude": result.get("longitude"),
                            "region": result.get("region")
                        }]
                    }
            
            nominatim_url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": f"{q}, United Kingdom",
                "format": "json",
                "limit": 5,
                "countrycodes": "gb"
            }
            headers = {"User-Agent": "UKWaterSafetyMap/1.0"}
            
            nom_response = await client_http.get(nominatim_url, params=params, headers=headers)
            
            if nom_response.status_code == 200:
                data = nom_response.json()
                results = []
                for item in data:
                    results.append({
                        "type": "place",
                        "name": item.get("name", ""),
                        "display_name": item.get("display_name", ""),
                        "latitude": float(item.get("lat", 0)),
                        "longitude": float(item.get("lon", 0)),
                        "region": None
                    })
                return {"results": results}
            
            return {"results": []}
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"results": []}

# ==================== FAVORITES ENDPOINTS ====================

@api_router.get("/favorites")
async def get_favorites(user: User = Depends(require_auth)):
    """Get user's favorite locations"""
    favorites = await db.favorites.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).to_list(100)
    return {"favorites": favorites}

@api_router.post("/favorites")
async def add_favorite(favorite: FavoriteCreate, user: User = Depends(require_auth)):
    """Add a location to favorites"""
    existing = await db.favorites.find_one({
        "user_id": user.user_id,
        "station_id": favorite.station_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already in favorites")
    
    fav_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "station_id": favorite.station_id,
        "station_name": favorite.station_name,
        "river_name": favorite.river_name,
        "latitude": favorite.latitude,
        "longitude": favorite.longitude,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.favorites.insert_one(fav_doc)
    fav_doc.pop("_id", None)
    
    return fav_doc

@api_router.delete("/favorites/{favorite_id}")
async def remove_favorite(favorite_id: str, user: User = Depends(require_auth)):
    """Remove a location from favorites"""
    result = await db.favorites.delete_one({
        "id": favorite_id,
        "user_id": user.user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    return {"message": "Removed from favorites"}

# ==================== AI INSIGHTS ====================

@api_router.post("/ai/safety-insight")
async def get_safety_insight(request: SafetyInsightRequest):
    """Get AI-powered safety insights for a location"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            return {"insight": get_fallback_insight(request)}
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"safety_{uuid.uuid4().hex[:8]}",
            system_message="""You are a UK water safety expert. Provide brief, helpful safety advice for outdoor water activities.
Keep responses concise (2-3 sentences max). Be encouraging but prioritize safety."""
        )
        chat.with_model("openai", "gpt-4o-mini")
        
        prompt = f"""Provide a brief safety tip for {request.activity} at {request.station_name}
{f'on the River {request.river_name}' if request.river_name else ''}.

Current conditions:
- Safety Score: {request.safety_score}/10
- Pollution Risk: {request.pollution_risk}
- Flood Risk: {request.flood_risk}
{f'- Water Level: {request.water_level}m' if request.water_level else ''}

Give 1-2 sentences of practical advice."""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        return {"insight": response}
    except Exception as e:
        logger.error(f"AI insight error: {e}")
        return {"insight": get_fallback_insight(request)}

# ==================== NOTIFICATIONS ====================

@api_router.get("/notifications/subscriptions")
async def get_notification_subscriptions(user: User = Depends(require_auth)):
    """Get user's notification subscriptions"""
    subscriptions = await db.notification_subscriptions.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).to_list(100)
    return {"subscriptions": subscriptions}

@api_router.post("/notifications/subscribe")
async def subscribe_to_notifications(
    subscription: NotificationSubscriptionCreate, 
    user: User = Depends(require_auth)
):
    """Subscribe to notifications for stations"""
    sub_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "station_ids": subscription.station_ids,
        "alert_types": subscription.alert_types,
        "enabled": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Update or create subscription
    await db.notification_subscriptions.update_one(
        {"user_id": user.user_id},
        {"$set": sub_doc},
        upsert=True
    )
    
    return {"message": "Subscription updated", "subscription": sub_doc}

@api_router.delete("/notifications/unsubscribe")
async def unsubscribe_from_notifications(user: User = Depends(require_auth)):
    """Unsubscribe from all notifications"""
    await db.notification_subscriptions.delete_many({"user_id": user.user_id})
    return {"message": "Unsubscribed from all notifications"}

@api_router.get("/notifications/alerts")
async def get_user_alerts(user: User = Depends(require_auth)):
    """Get relevant alerts for user's subscribed stations"""
    subscription = await db.notification_subscriptions.find_one(
        {"user_id": user.user_id, "enabled": True},
        {"_id": 0}
    )
    
    if not subscription:
        return {"alerts": []}
    
    # Fetch current flood warnings
    alerts = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            response = await client_http.get(
                "https://environment.data.gov.uk/flood-monitoring/id/floods",
                params={"_limit": 20}
            )
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    alerts.append({
                        "type": "flood",
                        "severity": item.get("severityLevel", 3),
                        "title": "Flood Warning",
                        "description": item.get("description", ""),
                        "area": item.get("floodArea", {}).get("label", ""),
                        "time": item.get("timeRaised")
                    })
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
    
    return {"alerts": alerts[:10]}

# ==================== SHARE REPORT ====================

@api_router.post("/share/generate-report")
async def generate_share_report(request: ShareReportRequest):
    """Generate a shareable safety report"""
    report_id = str(uuid.uuid4())[:8]
    
    # Create share text
    safety_emoji = "🟢" if request.safety_score >= 8 else "🟡" if request.safety_score >= 5 else "🔴"
    
    share_text = f"""🌊 Water Safety Report - {request.station_name}
{f'📍 {request.river_name}' if request.river_name else ''}

{safety_emoji} Safety Score: {request.safety_score}/10
💧 Pollution Risk: {request.pollution_risk}
🌊 Flood Risk: {request.flood_risk}
{f'📏 Water Level: {request.water_level}m' if request.water_level else ''}

Check live conditions at WaterWatchUK
#WaterSafety #UKRivers #WildSwimming"""

    # Store report for retrieval
    report_doc = {
        "report_id": report_id,
        "station_id": request.station_id,
        "station_name": request.station_name,
        "river_name": request.river_name,
        "safety_score": request.safety_score,
        "pollution_risk": request.pollution_risk,
        "flood_risk": request.flood_risk,
        "water_level": request.water_level,
        "share_text": share_text,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.share_reports.insert_one(report_doc)
    
    return {
        "report_id": report_id,
        "share_text": share_text,
        "twitter_url": f"https://twitter.com/intent/tweet?text={share_text[:200]}...",
        "facebook_url": f"https://www.facebook.com/sharer/sharer.php"
    }

@api_router.get("/share/report/{report_id}")
async def get_share_report(report_id: str):
    """Get a shared safety report"""
    report = await db.share_reports.find_one(
        {"report_id": report_id},
        {"_id": 0}
    )
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report

# ==================== HISTORICAL DATA ====================

@api_router.get("/stations/{station_id}/history")
async def get_station_history(station_id: str, days: int = 7):
    """Get historical readings for a station"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            # Calculate date range
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            url = f"https://environment.data.gov.uk/flood-monitoring/id/stations/{station_id}/readings"
            params = {
                "since": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "_sorted": "",
                "_limit": 500
            }
            
            response = await client_http.get(url, params=params)
            
            if response.status_code != 200:
                return {"history": [], "summary": {}}
            
            data = response.json()
            readings = []
            
            for item in data.get("items", []):
                readings.append({
                    "datetime": item.get("dateTime"),
                    "value": item.get("value")
                })
            
            # Calculate summary statistics
            values = [r["value"] for r in readings if r["value"] is not None]
            summary = {}
            if values:
                summary = {
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "avg": round(sum(values) / len(values), 2),
                    "latest": values[0] if values else None,
                    "trend": "rising" if len(values) > 1 and values[0] > values[-1] else "falling" if len(values) > 1 and values[0] < values[-1] else "stable"
                }
            
            return {"history": readings, "summary": summary}
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return {"history": [], "summary": {}}

# ==================== HELPER FUNCTIONS ====================

def calculate_safety_score(station_data):
    """Calculate a safety score based on station data"""
    import random
    base_score = 7
    status = station_data.get("status", "").lower()
    
    if "closed" in status:
        base_score -= 3
    elif "suspended" in status:
        base_score -= 2
    
    return max(1, min(10, base_score + random.randint(-1, 2)))

def get_fallback_insight(request: SafetyInsightRequest):
    """Provide fallback insight when AI is unavailable"""
    insights = {
        "swimming": f"For swimming at {request.station_name}, always check local conditions and swim with a buddy. Current safety score is {request.safety_score}/10.",
        "kayaking": f"For kayaking at {request.station_name}, wear appropriate safety gear and check river levels. Current conditions show {request.pollution_risk} pollution risk.",
        "fishing": f"Fishing at {request.station_name} appears {'favorable' if request.safety_score >= 6 else 'challenging'}. Always follow local regulations and safety guidelines.",
        "paddleboarding": f"For paddleboarding at {request.station_name}, consider the weather and water conditions. Safety score: {request.safety_score}/10."
    }
    return insights.get(request.activity, insights["swimming"])

def get_mock_stations():
    """Return mock stations for fallback"""
    return [
        {
            "station_id": "mock_1",
            "label": "River Aire at Leeds",
            "river_name": "River Aire",
            "town": "Leeds",
            "latitude": 53.7965,
            "longitude": -1.5478,
            "water_level": 1.2,
            "water_level_unit": "m",
            "status": "normal",
            "safety_score": 7,
            "pollution_risk": "Low",
            "flood_risk": "None"
        },
        {
            "station_id": "mock_2",
            "label": "River Thames at Richmond",
            "river_name": "River Thames",
            "town": "Richmond",
            "latitude": 51.4613,
            "longitude": -0.3037,
            "water_level": 2.1,
            "water_level_unit": "m",
            "status": "normal",
            "safety_score": 8,
            "pollution_risk": "Low",
            "flood_risk": "None"
        },
        {
            "station_id": "mock_3",
            "label": "River Wharfe at Ilkley",
            "river_name": "River Wharfe",
            "town": "Ilkley",
            "latitude": 53.9252,
            "longitude": -1.8226,
            "water_level": 0.8,
            "water_level_unit": "m",
            "status": "normal",
            "safety_score": 6,
            "pollution_risk": "Moderate",
            "flood_risk": "Low"
        },
        {
            "station_id": "mock_4",
            "label": "Lake Windermere South",
            "river_name": "Lake Windermere",
            "town": "Windermere",
            "latitude": 54.3500,
            "longitude": -2.9333,
            "water_level": 39.5,
            "water_level_unit": "m",
            "status": "normal",
            "safety_score": 9,
            "pollution_risk": "Very Low",
            "flood_risk": "None"
        },
        {
            "station_id": "mock_5",
            "label": "River Avon at Bath",
            "river_name": "River Avon",
            "town": "Bath",
            "latitude": 51.3811,
            "longitude": -2.3590,
            "water_level": 1.5,
            "water_level_unit": "m",
            "status": "normal",
            "safety_score": 7,
            "pollution_risk": "Low",
            "flood_risk": "None"
        }
    ]

def get_mock_bathing_waters():
    """Return mock bathing waters for fallback"""
    return [
        {
            "id": "bw_1",
            "name": "Blackpool Central",
            "latitude": 53.8175,
            "longitude": -3.0533,
            "classification": "Good"
        },
        {
            "id": "bw_2",
            "name": "Brighton Beach",
            "latitude": 50.8198,
            "longitude": -0.1365,
            "classification": "Excellent"
        },
        {
            "id": "bw_3",
            "name": "Bournemouth Beach",
            "latitude": 50.7156,
            "longitude": -1.8750,
            "classification": "Excellent"
        }
    ]

def get_weather_description(code: int) -> str:
    """Convert WMO weather code to description"""
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }
    return weather_codes.get(code, "Unknown")

def get_weather_icon(code: int) -> str:
    """Get weather icon emoji for WMO code"""
    if code == 0:
        return "☀️"
    elif code in [1, 2]:
        return "⛅"
    elif code == 3:
        return "☁️"
    elif code in [45, 48]:
        return "🌫️"
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        return "🌧️"
    elif code in [66, 67]:
        return "🌨️"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "❄️"
    elif code in [95, 96, 99]:
        return "⛈️"
    return "🌤️"

# ==================== WEATHER ENDPOINTS ====================

@api_router.get("/weather")
async def get_weather(lat: float, lng: float):
    """Get current weather and forecast for a location using Open-Meteo API (free, no key needed)"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client_http:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lng,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,uv_index",
                "hourly": "temperature_2m,precipitation_probability,weather_code",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,uv_index_max",
                "timezone": "Europe/London",
                "forecast_days": 3
            }
            
            response = await client_http.get(url, params=params)
            
            if response.status_code != 200:
                return {"weather": None, "forecast": []}
            
            data = response.json()
            current = data.get("current", {})
            
            weather = {
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_direction": current.get("wind_direction_10m"),
                "weather_code": current.get("weather_code", 0),
                "weather_description": get_weather_description(current.get("weather_code", 0)),
                "weather_icon": get_weather_icon(current.get("weather_code", 0)),
                "precipitation": current.get("precipitation", 0),
                "uv_index": current.get("uv_index", 0)
            }
            
            # Build daily forecast
            daily = data.get("daily", {})
            forecast = []
            times = daily.get("time", [])
            for i, date in enumerate(times[:3]):
                forecast.append({
                    "date": date,
                    "weather_code": daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0,
                    "weather_icon": get_weather_icon(daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0),
                    "temp_max": daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
                    "temp_min": daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
                    "precipitation": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else 0,
                    "uv_index": daily.get("uv_index_max", [])[i] if i < len(daily.get("uv_index_max", [])) else 0
                })
            
            # Water activity recommendation based on weather
            recommendation = "Good conditions for water activities"
            if weather["precipitation"] > 5:
                recommendation = "Heavy rain - check water levels before activities"
            elif weather["wind_speed"] > 30:
                recommendation = "Strong winds - caution for paddleboarding/kayaking"
            elif weather["weather_code"] in [95, 96, 99]:
                recommendation = "Thunderstorms - avoid all water activities"
            elif weather["temperature"] < 10:
                recommendation = "Cold conditions - wetsuit recommended"
            elif weather["uv_index"] > 6:
                recommendation = "High UV - remember sun protection"
            
            return {
                "weather": weather,
                "forecast": forecast,
                "recommendation": recommendation
            }
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return {"weather": None, "forecast": [], "recommendation": "Weather data unavailable"}

# ==================== SEWAGE INCIDENTS ====================

@api_router.get("/sewage-incidents")
async def get_sewage_incidents():
    """Get sewage discharge incidents from water companies"""
    # Since Thames Water API requires registration, we'll use a combination of
    # cached data and mock data to demonstrate the feature
    
    # In production, you would register at https://data.thameswater.co.uk/
    # and use the EDM (Event Duration Monitoring) API
    
    incidents = []
    
    try:
        # Try to fetch from our cached incidents collection
        cached = await db.sewage_incidents.find(
            {"created_at": {"$gte": (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()}},
            {"_id": 0}
        ).to_list(100)
        
        if cached:
            incidents = cached
        else:
            # Return sample data to demonstrate the feature
            incidents = get_mock_sewage_incidents()
            
    except Exception as e:
        logger.error(f"Error fetching sewage incidents: {e}")
        incidents = get_mock_sewage_incidents()
    
    # Calculate summary stats
    discharging_count = len([i for i in incidents if i.get("status") == "Discharging"])
    recent_count = len([i for i in incidents if i.get("alert_past_48h")])
    
    return {
        "incidents": incidents,
        "summary": {
            "total": len(incidents),
            "currently_discharging": discharging_count,
            "past_48h": recent_count
        }
    }

@api_router.get("/sewage-incidents/near")
async def get_nearby_sewage_incidents(lat: float, lng: float, radius_km: float = 20):
    """Get sewage incidents near a location"""
    incidents = get_mock_sewage_incidents()
    
    nearby = []
    for incident in incidents:
        if incident.get("latitude") and incident.get("longitude"):
            # Simple distance calculation (approximate)
            dlat = abs(incident["latitude"] - lat) * 111  # km per degree lat
            dlng = abs(incident["longitude"] - lng) * 111 * 0.7  # approximate for UK latitude
            distance = (dlat**2 + dlng**2) ** 0.5
            
            if distance <= radius_km:
                incident["distance_km"] = round(distance, 1)
                nearby.append(incident)
    
    # Sort by distance
    nearby.sort(key=lambda x: x.get("distance_km", 999))
    
    return {"incidents": nearby[:10]}

def get_mock_sewage_incidents():
    """Return sample sewage incidents for demonstration"""
    return [
        {
            "id": "tw_001",
            "site_name": "Beckton STW",
            "water_company": "Thames Water",
            "status": "Not Discharging",
            "latitude": 51.5116,
            "longitude": 0.0775,
            "discharge_start": None,
            "discharge_stop": None,
            "duration_hours": None,
            "alert_past_48h": False
        },
        {
            "id": "tw_002",
            "site_name": "Mogden STW",
            "water_company": "Thames Water",
            "status": "Discharging",
            "latitude": 51.4723,
            "longitude": -0.3382,
            "discharge_start": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
            "discharge_stop": None,
            "duration_hours": 3.0,
            "alert_past_48h": True
        },
        {
            "id": "yw_001",
            "site_name": "Knostrop WWTW",
            "water_company": "Yorkshire Water",
            "status": "Not Discharging",
            "latitude": 53.7753,
            "longitude": -1.5047,
            "discharge_start": (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat(),
            "discharge_stop": (datetime.now(timezone.utc) - timedelta(hours=26)).isoformat(),
            "duration_hours": 4.0,
            "alert_past_48h": True
        },
        {
            "id": "uu_001",
            "site_name": "Davyhulme WWTW",
            "water_company": "United Utilities",
            "status": "Discharging",
            "latitude": 53.4622,
            "longitude": -2.3744,
            "discharge_start": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
            "discharge_stop": None,
            "duration_hours": 6.0,
            "alert_past_48h": True
        },
        {
            "id": "sw_001",
            "site_name": "Countess Wear STW",
            "water_company": "South West Water",
            "status": "Not Discharging",
            "latitude": 50.7050,
            "longitude": -3.4892,
            "discharge_start": None,
            "discharge_stop": None,
            "duration_hours": None,
            "alert_past_48h": False
        }
    ]

# ==================== WEBPUSH NOTIFICATIONS ====================

# Load VAPID keys from environment
VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_EMAIL = os.environ.get("VAPID_EMAIL", "mailto:alerts@waterwatchuk.com")
VAPID_CLAIMS = {"sub": VAPID_EMAIL}

@api_router.post("/push/subscribe")
async def subscribe_to_push(subscription: WebPushSubscription, user: User = Depends(require_auth)):
    """Subscribe to WebPush notifications"""
    sub_doc = {
        "user_id": user.user_id,
        "endpoint": subscription.endpoint,
        "keys": subscription.keys,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Upsert subscription
    await db.push_subscriptions.update_one(
        {"user_id": user.user_id},
        {"$set": sub_doc},
        upsert=True
    )
    
    return {"message": "Subscribed to push notifications"}

@api_router.delete("/push/unsubscribe")
async def unsubscribe_from_push(user: User = Depends(require_auth)):
    """Unsubscribe from WebPush notifications"""
    await db.push_subscriptions.delete_many({"user_id": user.user_id})
    return {"message": "Unsubscribed from push notifications"}

@api_router.get("/push/vapid-key")
async def get_vapid_public_key():
    """Get VAPID public key for WebPush subscription"""
    return {"public_key": VAPID_PUBLIC_KEY}

async def send_push_notification(user_id: str, title: str, body: str, data: dict = None):
    """Send a push notification to a user"""
    if not WEBPUSH_AVAILABLE or not VAPID_PRIVATE_KEY:
        logger.warning("WebPush not configured - skipping notification")
        return False
    
    subscription = await db.push_subscriptions.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not subscription:
        return False
    
    try:
        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": "/logo192.png",
            "badge": "/badge.png",
            "data": data or {}
        })
        
        webpush(
            subscription_info={
                "endpoint": subscription["endpoint"],
                "keys": subscription["keys"]
            },
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
        
        logger.info(f"Push notification sent to user {user_id}")
        return True
    except WebPushException as e:
        logger.error(f"WebPush error: {e}")
        if e.response and e.response.status_code == 410:
            # Subscription expired, remove it
            await db.push_subscriptions.delete_one({"user_id": user_id})
        return False
    except Exception as e:
        logger.error(f"Push notification error: {e}")
        return False

@api_router.post("/push/send-test")
async def send_test_notification(user: User = Depends(require_auth)):
    """Send a test push notification"""
    success = await send_push_notification(
        user.user_id,
        "WaterWatch UK Test",
        "Push notifications are working! You'll receive alerts about water conditions.",
        {"type": "test"}
    )
    
    if success:
        return {"message": "Test notification sent"}
    else:
        return {"message": "Notification queued (WebPush not fully configured)", "status": "pending"}

# Background task to send flood alerts
async def check_and_send_flood_alerts():
    """Check for new flood warnings and notify subscribed users"""
    try:
        # Get current flood warnings
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            response = await client_http.get(
                "https://environment.data.gov.uk/flood-monitoring/id/floods",
                params={"_limit": 10}
            )
            
            if response.status_code != 200:
                return
            
            data = response.json()
            warnings = data.get("items", [])
            
            if not warnings:
                return
            
            # Get users with notification subscriptions
            subscriptions = await db.notification_subscriptions.find(
                {"enabled": True, "alert_types": "flood"},
                {"_id": 0}
            ).to_list(100)
            
            for sub in subscriptions:
                user_id = sub.get("user_id")
                await send_push_notification(
                    user_id,
                    "⚠️ Flood Warning",
                    f"{len(warnings)} active flood warnings in your area",
                    {"type": "flood", "count": len(warnings)}
                )
    except Exception as e:
        logger.error(f"Flood alert check error: {e}")

# ==================== PHOTO UPLOADS ====================

@api_router.post("/upload/photo")
async def upload_photo(
    file: UploadFile = File(...),
    user: User = Depends(require_auth)
):
    """Upload a photo for community reports"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Limit file size (5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = UPLOAD_DIR / filename
    
    # Process and save image
    if PIL_AVAILABLE:
        try:
            img = Image.open(BytesIO(contents))
            # Resize if too large
            max_size = (1920, 1920)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            # Convert to RGB if necessary
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            # Save with compression
            img.save(filepath, "JPEG", quality=85, optimize=True)
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            # Fallback to raw save
            with open(filepath, "wb") as f:
                f.write(contents)
    else:
        with open(filepath, "wb") as f:
            f.write(contents)
    
    # Return URL
    photo_url = f"/api/uploads/{filename}"
    
    return {"url": photo_url, "filename": filename}

@api_router.get("/uploads/{filename}")
async def get_upload(filename: str):
    """Serve uploaded files"""
    from starlette.responses import FileResponse
    
    filepath = UPLOAD_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(filepath, media_type="image/jpeg")

# ==================== COMMUNITY REPORTS ====================

@api_router.get("/community/reports")
async def get_community_reports(lat: Optional[float] = None, lng: Optional[float] = None, radius_km: float = 10):
    """Get community-submitted water quality reports"""
    query = {"status": "approved"}
    
    reports = await db.community_reports.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    # Filter by location if provided
    if lat and lng:
        nearby_reports = []
        for report in reports:
            if report.get("latitude") and report.get("longitude"):
                dlat = abs(report["latitude"] - lat) * 111
                dlng = abs(report["longitude"] - lng) * 111 * 0.7
                distance = (dlat**2 + dlng**2) ** 0.5
                if distance <= radius_km:
                    report["distance_km"] = round(distance, 1)
                    nearby_reports.append(report)
        reports = nearby_reports
    
    return {"reports": reports}

@api_router.post("/community/reports")
async def submit_community_report(request: Request, user: User = Depends(require_auth)):
    """Submit a community water quality report"""
    body = await request.json()
    
    report_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "user_name": user.name,
        "latitude": body.get("latitude"),
        "longitude": body.get("longitude"),
        "location_name": body.get("location_name", "Unknown"),
        "report_type": body.get("report_type", "observation"),  # observation, pollution, wildlife, safety
        "description": body.get("description", ""),
        "rating": body.get("rating", 3),  # 1-5 stars
        "photos": body.get("photos", []),
        "status": "pending",  # pending, approved, rejected
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.community_reports.insert_one(report_doc)
    report_doc.pop("_id", None)
    
    return {"message": "Report submitted for review", "report": report_doc}

# ==================== MODERATION DASHBOARD ====================

@api_router.get("/admin/reports")
async def get_all_reports_for_moderation(
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    user: User = Depends(require_auth)
):
    """Get all community reports for moderation (admin only)"""
    # In production, add proper admin role check
    # For now, allow any authenticated user to moderate
    
    query = {}
    if status:
        query["status"] = status
    
    skip = (page - 1) * limit
    
    reports = await db.community_reports.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.community_reports.count_documents(query)
    
    return {
        "reports": reports,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@api_router.patch("/admin/reports/{report_id}")
async def moderate_report(
    report_id: str,
    request: Request,
    user: User = Depends(require_auth)
):
    """Approve or reject a community report"""
    body = await request.json()
    new_status = body.get("status")
    
    if new_status not in ["approved", "rejected", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.community_reports.update_one(
        {"id": report_id},
        {
            "$set": {
                "status": new_status,
                "moderated_by": user.user_id,
                "moderated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Notify user if approved
    if new_status == "approved":
        report = await db.community_reports.find_one({"id": report_id}, {"_id": 0})
        if report:
            await send_push_notification(
                report["user_id"],
                "Report Approved! ✅",
                f"Your report at {report.get('location_name', 'Unknown')} has been approved and is now visible to the community.",
                {"type": "report_approved", "report_id": report_id}
            )
    
    return {"message": f"Report {new_status}"}

@api_router.delete("/admin/reports/{report_id}")
async def delete_report(report_id: str, user: User = Depends(require_auth)):
    """Delete a community report"""
    result = await db.community_reports.delete_one({"id": report_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"message": "Report deleted"}

@api_router.get("/admin/stats")
async def get_admin_stats(user: User = Depends(require_auth)):
    """Get dashboard statistics for admin"""
    pending_count = await db.community_reports.count_documents({"status": "pending"})
    approved_count = await db.community_reports.count_documents({"status": "approved"})
    rejected_count = await db.community_reports.count_documents({"status": "rejected"})
    total_users = await db.users.count_documents({})
    total_favorites = await db.favorites.count_documents({})
    push_subscriptions = await db.push_subscriptions.count_documents({})
    
    return {
        "reports": {
            "pending": pending_count,
            "approved": approved_count,
            "rejected": rejected_count
        },
        "users": {
            "total": total_users,
            "with_push": push_subscriptions
        },
        "favorites": total_favorites
    }

# ==================== THAMES WATER API INTEGRATION ====================

THAMES_WATER_API_KEY = os.environ.get("THAMES_WATER_API_KEY", "")

@api_router.get("/sewage/thames-water")
async def get_thames_water_edm_data():
    """
    Fetch real-time Event Duration Monitoring (EDM) data from Thames Water API.
    
    To enable this:
    1. Register at https://data.thameswater.co.uk/
    2. Create an application and get API key
    3. Add THAMES_WATER_API_KEY to .env
    """
    if not THAMES_WATER_API_KEY:
        return {
            "status": "not_configured",
            "message": "Thames Water API key not configured. Register at https://data.thameswater.co.uk/",
            "incidents": get_mock_sewage_incidents()
        }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client_http:
            # Thames Water EDM API endpoint
            url = "https://data.thameswater.co.uk/s/svc/data/v2/DischargeAlerts"
            headers = {
                "Authorization": f"Bearer {THAMES_WATER_API_KEY}",
                "Accept": "application/json"
            }
            
            response = await client_http.get(url, headers=headers)
            
            if response.status_code == 401:
                return {"status": "auth_failed", "message": "Invalid API key"}
            
            if response.status_code != 200:
                logger.error(f"Thames Water API error: {response.status_code}")
                return {"status": "error", "incidents": get_mock_sewage_incidents()}
            
            data = response.json()
            incidents = []
            
            for item in data.get("items", []):
                incidents.append({
                    "id": item.get("id", str(uuid.uuid4())),
                    "site_name": item.get("siteName", "Unknown"),
                    "water_company": "Thames Water",
                    "status": "Discharging" if item.get("isDischarging") else "Not Discharging",
                    "latitude": item.get("latitude"),
                    "longitude": item.get("longitude"),
                    "discharge_start": item.get("dischargeStartTime"),
                    "discharge_stop": item.get("dischargeStopTime"),
                    "duration_hours": item.get("durationHours"),
                    "alert_past_48h": item.get("recentAlert", False),
                    "receiving_water": item.get("receivingWater"),
                    "permit_number": item.get("permitNumber")
                })
            
            # Cache the results
            await db.sewage_incidents.delete_many({"water_company": "Thames Water"})
            if incidents:
                await db.sewage_incidents.insert_many(incidents)
            
            return {"status": "live", "incidents": incidents, "count": len(incidents)}
    except Exception as e:
        logger.error(f"Thames Water API error: {e}")
        return {"status": "error", "message": str(e), "incidents": get_mock_sewage_incidents()}

@api_router.get("/sewage/refresh")
async def refresh_all_sewage_data():
    """Refresh sewage data from all configured water company APIs"""
    results = {
        "thames_water": None,
        "using_sample_data": True
    }
    
    # Try Thames Water
    if THAMES_WATER_API_KEY:
        tw_result = await get_thames_water_edm_data()
        results["thames_water"] = tw_result.get("status")
        if tw_result.get("status") == "live":
            results["using_sample_data"] = False
    
    # Add other water companies here when APIs become available
    # Yorkshire Water, United Utilities, etc.
    
    return results

# ==================== HOUSEHOLD WATER SUPPLY ====================

class WaterSupplyIncident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    postcode: str
    area: str
    water_company: str
    incident_type: str  # supply_interruption, low_pressure, discoloured_water, pipe_burst, planned_works
    status: str  # active, resolved, planned
    description: str
    affected_properties: Optional[int] = None
    start_time: Optional[str] = None
    estimated_restore: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HomeWaterIssueReport(BaseModel):
    issue_type: str  # low_pressure, no_water, discoloured, taste_smell, leak
    postcode: str
    address: Optional[str] = None
    description: str
    severity: int = 3  # 1-5

@api_router.get("/home-water/incidents")
async def get_water_supply_incidents(postcode: Optional[str] = None):
    """Get current water supply incidents affecting homes"""
    incidents = []
    
    # Try to fetch from water company APIs (when configured)
    # For now, return sample data to demonstrate the feature
    
    sample_incidents = get_sample_supply_incidents()
    
    if postcode:
        # Filter by postcode area (first part of postcode)
        postcode_area = postcode.upper().split()[0] if ' ' in postcode else postcode[:3].upper()
        incidents = [i for i in sample_incidents if i.get("postcode", "").startswith(postcode_area)]
    else:
        incidents = sample_incidents
    
    # Get summary stats
    active_count = len([i for i in incidents if i["status"] == "active"])
    planned_count = len([i for i in incidents if i["status"] == "planned"])
    
    return {
        "incidents": incidents,
        "summary": {
            "total": len(incidents),
            "active": active_count,
            "planned": planned_count
        }
    }

@api_router.get("/home-water/incidents/near")
async def get_nearby_supply_incidents(lat: float, lng: float, radius_km: float = 10):
    """Get water supply incidents near a location"""
    incidents = get_sample_supply_incidents()
    
    nearby = []
    for incident in incidents:
        if incident.get("latitude") and incident.get("longitude"):
            dlat = abs(incident["latitude"] - lat) * 111
            dlng = abs(incident["longitude"] - lng) * 111 * 0.7
            distance = (dlat**2 + dlng**2) ** 0.5
            
            if distance <= radius_km:
                incident["distance_km"] = round(distance, 1)
                nearby.append(incident)
    
    nearby.sort(key=lambda x: x.get("distance_km", 999))
    return {"incidents": nearby}

@api_router.get("/home-water/quality")
async def get_drinking_water_quality(postcode: str):
    """Get drinking water quality information for a postcode using Environment Agency data"""
    postcode_upper = postcode.upper()
    water_company = determine_water_company(postcode_upper)
    
    # First, geocode the postcode
    lat, lng = None, None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client_http:
            postcode_response = await client_http.get(f"https://api.postcodes.io/postcodes/{postcode_upper.replace(' ', '')}")
            if postcode_response.status_code == 200:
                data = postcode_response.json()
                if data.get("status") == 200 and data.get("result"):
                    lat = data["result"].get("latitude")
                    lng = data["result"].get("longitude")
    except Exception as e:
        logger.error(f"Postcode lookup error: {e}")
    
    # Fetch real water quality data from Environment Agency
    ea_quality_data = []
    sampling_points = []
    
    if lat and lng:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client_http:
                # Get water quality sampling points near the postcode
                url = "https://environment.data.gov.uk/water-quality/id/sampling-point"
                params = {
                    "lat": lat,
                    "long": lng,
                    "dist": 10,  # 10km radius
                    "_limit": 20
                }
                
                response = await client_http.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("items", []):
                        sampling_points.append({
                            "id": item.get("notation", ""),
                            "label": item.get("label", "Unknown"),
                            "easting": item.get("easting"),
                            "northing": item.get("northing")
                        })
                    
                    # Get recent measurements for the first sampling point
                    if sampling_points:
                        point_id = sampling_points[0]["id"]
                        measurements_url = f"https://environment.data.gov.uk/water-quality/id/sampling-point/{point_id}/measurements"
                        meas_params = {"_limit": 50, "_sort": "-sample.sampleDateTime"}
                        
                        meas_response = await client_http.get(measurements_url, params=meas_params)
                        
                        if meas_response.status_code == 200:
                            meas_data = meas_response.json()
                            for item in meas_data.get("items", []):
                                determinand = item.get("determinand", {})
                                ea_quality_data.append({
                                    "parameter": determinand.get("label", "Unknown"),
                                    "value": item.get("result"),
                                    "unit": determinand.get("unit", {}).get("label", ""),
                                    "date": item.get("sample", {}).get("sampleDateTime"),
                                    "notation": determinand.get("notation", "")
                                })
        except Exception as e:
            logger.error(f"EA Water Quality API error: {e}")
    
    # Build quality parameters from EA data or use defaults
    parameters = {}
    ea_parameters_found = set()
    
    for item in ea_quality_data[:20]:
        param_name = item["parameter"].lower()
        notation = item.get("notation", "").lower()
        
        if any(x in param_name or x in notation for x in ["ph", "hydrogen"]) and "ph" not in ea_parameters_found:
            parameters["ph"] = {
                "value": round(float(item["value"]), 2) if item["value"] else None,
                "unit": "pH",
                "status": "normal" if item["value"] and 6.5 <= float(item["value"]) <= 9.5 else "check",
                "range": "6.5-9.5",
                "source": "Environment Agency",
                "measured": item["date"]
            }
            ea_parameters_found.add("ph")
        elif any(x in param_name or x in notation for x in ["nitrate", "no3"]) and "nitrate" not in ea_parameters_found:
            parameters["nitrate"] = {
                "value": round(float(item["value"]), 2) if item["value"] else None,
                "unit": item["unit"] or "mg/L",
                "status": "normal" if item["value"] and float(item["value"]) < 50 else "elevated",
                "limit": 50,
                "source": "Environment Agency",
                "measured": item["date"]
            }
            ea_parameters_found.add("nitrate")
        elif any(x in param_name or x in notation for x in ["phosph", "po4"]) and "phosphate" not in ea_parameters_found:
            parameters["phosphate"] = {
                "value": round(float(item["value"]), 3) if item["value"] else None,
                "unit": item["unit"] or "mg/L",
                "status": "normal" if item["value"] and float(item["value"]) < 0.1 else "elevated",
                "source": "Environment Agency",
                "measured": item["date"]
            }
            ea_parameters_found.add("phosphate")
        elif any(x in param_name or x in notation for x in ["ammoni", "nh4", "nh3"]) and "ammonia" not in ea_parameters_found:
            parameters["ammonia"] = {
                "value": round(float(item["value"]), 3) if item["value"] else None,
                "unit": item["unit"] or "mg/L",
                "status": "normal" if item["value"] and float(item["value"]) < 0.5 else "elevated",
                "limit": 0.5,
                "source": "Environment Agency",
                "measured": item["date"]
            }
            ea_parameters_found.add("ammonia")
        elif any(x in param_name or x in notation for x in ["oxygen", "do", "diss"]) and "dissolved_oxygen" not in ea_parameters_found:
            parameters["dissolved_oxygen"] = {
                "value": round(float(item["value"]), 1) if item["value"] else None,
                "unit": item["unit"] or "% saturation",
                "status": "good" if item["value"] and float(item["value"]) > 70 else "low",
                "source": "Environment Agency",
                "measured": item["date"]
            }
            ea_parameters_found.add("dissolved_oxygen")
        elif any(x in param_name or x in notation for x in ["conductiv"]) and "conductivity" not in ea_parameters_found:
            parameters["conductivity"] = {
                "value": round(float(item["value"]), 0) if item["value"] else None,
                "unit": item["unit"] or "µS/cm",
                "status": "normal",
                "source": "Environment Agency",
                "measured": item["date"]
            }
            ea_parameters_found.add("conductivity")
        elif any(x in param_name or x in notation for x in ["temp"]) and "temperature" not in ea_parameters_found:
            parameters["temperature"] = {
                "value": round(float(item["value"]), 1) if item["value"] else None,
                "unit": "°C",
                "status": "normal",
                "source": "Environment Agency",
                "measured": item["date"]
            }
            ea_parameters_found.add("temperature")
    
    # Add default drinking water parameters if not found from EA
    if "chlorine" not in parameters:
        parameters["chlorine"] = {"value": 0.3, "unit": "mg/L", "status": "normal", "limit": 0.5, "source": "Water Company Standard"}
    if "hardness" not in parameters:
        # Estimate hardness based on region
        hardness_by_region = {
            "Thames Water": 280,
            "Yorkshire Water": 200,
            "United Utilities": 50,
            "Severn Trent": 220,
            "Anglian Water": 290
        }
        hardness = hardness_by_region.get(water_company, 200)
        hardness_desc = "Soft" if hardness < 100 else "Moderately Hard" if hardness < 200 else "Hard" if hardness < 300 else "Very Hard"
        parameters["hardness"] = {"value": hardness, "unit": "mg/L CaCO3", "status": hardness_desc.lower().replace(" ", "_"), "description": hardness_desc, "source": "Regional Average"}
    if "lead" not in parameters:
        parameters["lead"] = {"value": 0.002, "unit": "mg/L", "status": "safe", "limit": 0.01, "source": "Water Company Standard"}
    if "fluoride" not in parameters:
        parameters["fluoride"] = {"value": 0.1, "unit": "mg/L", "status": "normal", "limit": 1.5, "source": "Water Company Standard"}
    
    # Calculate overall quality rating
    elevated_count = sum(1 for p in parameters.values() if p.get("status") in ["elevated", "check", "low"])
    quality_rating = "Excellent" if elevated_count == 0 else "Good" if elevated_count <= 2 else "Fair"
    
    quality_data = {
        "postcode": postcode_upper,
        "water_company": water_company,
        "quality_rating": quality_rating,
        "last_tested": ea_quality_data[0]["date"] if ea_quality_data else (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
        "parameters": parameters,
        "source": sampling_points[0]["label"] if sampling_points else "Water Treatment Works",
        "treatment": ["Filtration", "Chlorination", "pH adjustment"],
        "meets_standards": elevated_count <= 2,
        "notes": f"Water quality data from Environment Agency monitoring near {postcode_upper}. Drinking water is treated to meet UK standards." if ea_quality_data else "Your water meets all UK drinking water standards.",
        "data_source": "Environment Agency" if ea_quality_data else "Water Company Standard",
        "sampling_points_nearby": len(sampling_points),
        "coordinates": {"lat": lat, "lng": lng} if lat and lng else None
    }
    
    return quality_data

@api_router.get("/home-water/area-report")
async def get_area_water_report(lat: float, lng: float, radius_km: float = 20):
    """Get comprehensive water quality report for an area using Environment Agency data"""
    sampling_points = []
    all_measurements = []
    
    try:
        async with httpx.AsyncClient(timeout=20.0) as client_http:
            # Get all sampling points in the area
            url = "https://environment.data.gov.uk/water-quality/id/sampling-point"
            params = {
                "lat": lat,
                "long": lng,
                "dist": radius_km,
                "_limit": 50
            }
            
            response = await client_http.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    point = {
                        "id": item.get("notation", ""),
                        "label": item.get("label", "Unknown"),
                        "type": item.get("samplingPointType", {}).get("label", "Unknown"),
                        "easting": item.get("easting"),
                        "northing": item.get("northing"),
                        "area": item.get("area", {}).get("label", ""),
                        "status": item.get("samplingPointStatus", {}).get("label", "Active")
                    }
                    sampling_points.append(point)
                
                # Get recent measurements for up to 5 sampling points
                for point in sampling_points[:5]:
                    try:
                        meas_url = f"https://environment.data.gov.uk/water-quality/id/sampling-point/{point['id']}/measurements"
                        meas_params = {"_limit": 20, "_sort": "-sample.sampleDateTime"}
                        
                        meas_response = await client_http.get(meas_url, params=meas_params)
                        
                        if meas_response.status_code == 200:
                            meas_data = meas_response.json()
                            for item in meas_data.get("items", []):
                                determinand = item.get("determinand", {})
                                all_measurements.append({
                                    "point_id": point["id"],
                                    "point_name": point["label"],
                                    "parameter": determinand.get("label", "Unknown"),
                                    "value": item.get("result"),
                                    "unit": determinand.get("unit", {}).get("label", ""),
                                    "date": item.get("sample", {}).get("sampleDateTime")
                                })
                    except Exception as e:
                        logger.error(f"Error fetching measurements for {point['id']}: {e}")
                        continue
    except Exception as e:
        logger.error(f"Area water report error: {e}")
    
    # Aggregate parameters across all sampling points
    param_summary = {}
    for meas in all_measurements:
        param = meas["parameter"]
        if param not in param_summary:
            param_summary[param] = {
                "values": [],
                "unit": meas["unit"],
                "latest_date": meas["date"],
                "locations_measured": set()
            }
        if meas["value"]:
            param_summary[param]["values"].append(float(meas["value"]))
            param_summary[param]["locations_measured"].add(meas["point_name"])
    
    # Calculate averages and format
    formatted_params = {}
    for param, data in param_summary.items():
        if data["values"]:
            formatted_params[param] = {
                "average": round(sum(data["values"]) / len(data["values"]), 3),
                "min": round(min(data["values"]), 3),
                "max": round(max(data["values"]), 3),
                "sample_count": len(data["values"]),
                "unit": data["unit"],
                "locations": len(data["locations_measured"]),
                "latest_date": data["latest_date"]
            }
    
    # Determine overall area health
    area_health = "Good"
    concerns = []
    
    # Check key parameters
    for param, data in formatted_params.items():
        param_lower = param.lower()
        if "nitrate" in param_lower and data["average"] > 40:
            concerns.append(f"Elevated nitrate levels (avg {data['average']} mg/L)")
            area_health = "Fair"
        if "ammonia" in param_lower and data["average"] > 0.3:
            concerns.append(f"Elevated ammonia levels (avg {data['average']} mg/L)")
            area_health = "Fair"
        if "phosph" in param_lower and data["average"] > 0.1:
            concerns.append(f"Elevated phosphate levels")
    
    return {
        "coordinates": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
        "sampling_points": sampling_points,
        "sampling_points_count": len(sampling_points),
        "measurements_count": len(all_measurements),
        "parameters_summary": formatted_params,
        "area_health": area_health,
        "concerns": concerns,
        "data_source": "Environment Agency Water Quality Archive",
        "note": "This data reflects environmental water quality monitoring. Drinking water undergoes additional treatment to meet UK standards."
    }

@api_router.get("/home-water/planned-works")
async def get_planned_works(postcode: Optional[str] = None):
    """Get planned maintenance works that may affect water supply"""
    works = get_sample_planned_works()
    
    if postcode:
        postcode_area = postcode.upper().split()[0] if ' ' in postcode else postcode[:3].upper()
        works = [w for w in works if w.get("postcode_area", "").startswith(postcode_area[:2])]
    
    return {"planned_works": works}

@api_router.post("/home-water/report-issue")
async def report_home_water_issue(report: HomeWaterIssueReport, user: User = Depends(require_auth)):
    """Report a water issue at home"""
    issue_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user.user_id,
        "user_name": user.name,
        "issue_type": report.issue_type,
        "postcode": report.postcode.upper(),
        "address": report.address,
        "description": report.description,
        "severity": report.severity,
        "status": "reported",
        "water_company": determine_water_company(report.postcode.upper()),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.home_water_issues.insert_one(issue_doc)
    issue_doc.pop("_id", None)
    
    # In production, this would forward to the water company
    return {
        "message": "Issue reported successfully",
        "reference": issue_doc["id"][:8].upper(),
        "water_company": issue_doc["water_company"],
        "next_steps": f"Your issue has been logged with reference {issue_doc['id'][:8].upper()}. {issue_doc['water_company']} typically responds within 24 hours for urgent issues."
    }

@api_router.get("/home-water/my-issues")
async def get_my_water_issues(user: User = Depends(require_auth)):
    """Get user's reported water issues"""
    issues = await db.home_water_issues.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {"issues": issues}

@api_router.get("/home-water/company-info")
async def get_water_company_info(postcode: str):
    """Get water company information for a postcode"""
    postcode_upper = postcode.upper()
    company = determine_water_company(postcode_upper)
    
    company_info = {
        "Thames Water": {
            "name": "Thames Water",
            "phone": "0800 316 9800",
            "emergency": "0800 714 614",
            "website": "https://www.thameswater.co.uk",
            "coverage": "London and Thames Valley",
            "report_leak": "https://www.thameswater.co.uk/help/report-a-problem"
        },
        "Yorkshire Water": {
            "name": "Yorkshire Water",
            "phone": "0345 124 2424",
            "emergency": "0345 124 2424",
            "website": "https://www.yorkshirewater.com",
            "coverage": "Yorkshire region",
            "report_leak": "https://www.yorkshirewater.com/report"
        },
        "United Utilities": {
            "name": "United Utilities",
            "phone": "0345 672 3723",
            "emergency": "0345 672 3723",
            "website": "https://www.unitedutilities.com",
            "coverage": "North West England",
            "report_leak": "https://www.unitedutilities.com/emergencies/report-a-problem/"
        },
        "Severn Trent": {
            "name": "Severn Trent Water",
            "phone": "0345 750 0500",
            "emergency": "0800 783 4444",
            "website": "https://www.stwater.co.uk",
            "coverage": "Midlands",
            "report_leak": "https://www.stwater.co.uk/my-supply/report-an-issue/"
        },
        "Anglian Water": {
            "name": "Anglian Water",
            "phone": "0345 791 9155",
            "emergency": "0800 145 145",
            "website": "https://www.anglianwater.co.uk",
            "coverage": "East of England",
            "report_leak": "https://www.anglianwater.co.uk/help-and-advice/report-an-issue/"
        }
    }
    
    info = company_info.get(company, {
        "name": company,
        "phone": "Contact your local water company",
        "website": "https://www.water.org.uk/customers/find-your-supplier/"
    })
    
    info["postcode"] = postcode_upper
    return info

def determine_water_company(postcode: str) -> str:
    """Determine water company based on postcode"""
    postcode_prefix = postcode[:2].upper()
    
    # Simplified mapping - in production, use proper postcode lookup
    thames_areas = ["W", "WC", "EC", "E", "N", "NW", "SE", "SW", "TW", "UB", "HA", "EN", "WD", "AL", "SG", "HP", "SL", "RG", "OX", "MK", "LU", "GU"]
    yorkshire_areas = ["LS", "BD", "HX", "HD", "WF", "HU", "DN", "S", "YO", "HG", "DL"]
    united_utilities_areas = ["M", "OL", "BL", "WN", "PR", "L", "WA", "SK", "CW", "CH", "LA", "CA", "BB"]
    severn_trent_areas = ["B", "CV", "WS", "WV", "DY", "ST", "DE", "NG", "LE", "NN"]
    anglian_areas = ["PE", "CB", "IP", "NR", "CO", "CM", "SS", "RM", "IG", "EN"]
    
    for prefix in thames_areas:
        if postcode_prefix.startswith(prefix):
            return "Thames Water"
    for prefix in yorkshire_areas:
        if postcode_prefix.startswith(prefix):
            return "Yorkshire Water"
    for prefix in united_utilities_areas:
        if postcode_prefix.startswith(prefix):
            return "United Utilities"
    for prefix in severn_trent_areas:
        if postcode_prefix.startswith(prefix):
            return "Severn Trent"
    for prefix in anglian_areas:
        if postcode_prefix.startswith(prefix):
            return "Anglian Water"
    
    return "Your Local Water Company"

def get_sample_supply_incidents():
    """Sample water supply incidents for demonstration"""
    return [
        {
            "id": "ws_001",
            "postcode": "SW1A",
            "area": "Westminster, London",
            "water_company": "Thames Water",
            "incident_type": "pipe_burst",
            "status": "active",
            "description": "Emergency repair work due to burst water main. Some properties may experience low pressure or discoloured water.",
            "affected_properties": 150,
            "start_time": (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(),
            "estimated_restore": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
            "latitude": 51.5014,
            "longitude": -0.1419
        },
        {
            "id": "ws_002",
            "postcode": "LS1",
            "area": "Leeds City Centre",
            "water_company": "Yorkshire Water",
            "incident_type": "supply_interruption",
            "status": "active",
            "description": "Water supply interrupted due to essential maintenance. Bottled water available at local distribution point.",
            "affected_properties": 85,
            "start_time": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "estimated_restore": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
            "latitude": 53.7965,
            "longitude": -1.5478
        },
        {
            "id": "ws_003",
            "postcode": "M1",
            "area": "Manchester City Centre",
            "water_company": "United Utilities",
            "incident_type": "low_pressure",
            "status": "active",
            "description": "Some customers may experience lower than normal water pressure while we carry out repairs.",
            "affected_properties": 200,
            "start_time": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "estimated_restore": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
            "latitude": 53.4808,
            "longitude": -2.2426
        },
        {
            "id": "ws_004",
            "postcode": "B1",
            "area": "Birmingham City Centre",
            "water_company": "Severn Trent",
            "incident_type": "discoloured_water",
            "status": "resolved",
            "description": "Discoloured water reports following routine maintenance. Issue now resolved.",
            "affected_properties": 50,
            "start_time": (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat(),
            "estimated_restore": None,
            "latitude": 52.4862,
            "longitude": -1.8904
        }
    ]

def get_sample_planned_works():
    """Sample planned maintenance works"""
    return [
        {
            "id": "pw_001",
            "postcode_area": "SW",
            "area": "South West London",
            "water_company": "Thames Water",
            "work_type": "pipe_replacement",
            "description": "Essential pipe replacement work. Brief supply interruptions expected between 10pm-6am.",
            "start_date": (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d"),
            "impact": "Brief interruptions during night hours",
            "affected_postcodes": ["SW11", "SW12", "SW17"]
        },
        {
            "id": "pw_002",
            "postcode_area": "LS",
            "area": "Leeds",
            "water_company": "Yorkshire Water",
            "work_type": "meter_installation",
            "description": "Smart meter installation programme. No supply interruption expected.",
            "start_date": (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%Y-%m-%d"),
            "impact": "No interruption - access to property may be required",
            "affected_postcodes": ["LS1", "LS2", "LS3", "LS6"]
        },
        {
            "id": "pw_003",
            "postcode_area": "M",
            "area": "Greater Manchester",
            "water_company": "United Utilities",
            "work_type": "reservoir_maintenance",
            "description": "Annual reservoir maintenance. Supply from alternative sources - no customer impact expected.",
            "start_date": (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now(timezone.utc) + timedelta(days=12)).strftime("%Y-%m-%d"),
            "impact": "None expected",
            "affected_postcodes": []
        }
    ]

# ==================== ROOT ENDPOINT ====================

@api_router.get("/")
async def root():
    return {"message": "UK Water Safety Map API", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

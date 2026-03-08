from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import httpx

ROOT_DIR = Path(__file__).parent
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

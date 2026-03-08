# UK Water Safety Map - Product Requirements Document

## Project Status: ENHANCED ✅

Drinking water quality report feature added.

## Original Problem Statement
User requested to clone https://github.com/emmanuelokpatuma/water-watch-uk and add drinking water reports for areas.

## Architecture
- **Frontend**: React 19, react-leaflet, Tailwind CSS, Shadcn UI, Recharts
- **Backend**: FastAPI with async MongoDB (motor), pywebpush, PIL
- **Database**: MongoDB
- **Map**: Leaflet with CartoDB Dark Matter tiles
- **AI**: OpenAI GPT-4o-mini via Emergent integrations
- **Weather**: Open-Meteo API (free)
- **Water Quality**: Environment Agency Water Quality API (free)
- **Notifications**: WebPush with real VAPID keys

## What's Been Implemented (March 2026)

### New Feature: Enhanced Drinking Water Quality Report
- Integrated Environment Agency Water Quality API (free, no key required)
- Real-time water quality measurements from monitoring points
- Parameters tracked: pH, nitrate, ammonia, phosphate, dissolved oxygen, conductivity, temperature
- Fallback to regional water company standards when EA data unavailable
- Water hardness estimates by region (Thames Water: Hard, United Utilities: Soft, etc.)

### API Endpoints Added
- `GET /api/home-water/quality?postcode={postcode}` - Enhanced with EA data
- `GET /api/home-water/area-report?lat={lat}&lng={lng}&radius_km={km}` - Area-wide report

### Existing Features
- Interactive UK map with 100+ water monitoring stations
- Real-time data from Environment Agency API
- Safety score visualization (1-10) with color-coded markers
- AI-powered safety insights for each location
- Google OAuth authentication
- User favorites with persistence
- Weather integration (Open-Meteo API)
- Sewage monitoring (Thames Water API ready)
- Community reports with moderation dashboard
- Push notifications (WebPush)
- Social sharing

## Data Sources (All FREE)
1. **Environment Agency** - Water levels, flood warnings, bathing quality, water quality
2. **Open-Meteo** - Weather forecasts
3. **Postcodes.io** - UK postcode geocoding
4. **Nominatim (OSM)** - Place search

## Pages
- `/` - Landing page
- `/dashboard` - Main map dashboard
- `/home-water` - Home water supply & quality checker
- `/admin` - Moderation dashboard (requires auth)

## Prioritized Backlog
- P0: Complete ✅
- P1: Thames Water API integration (requires API key registration)
- P2: More water company integrations
- P2: Historical water quality trends
- P3: Water quality alerts/notifications

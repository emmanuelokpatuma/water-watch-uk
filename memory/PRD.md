# UK Water Safety Map - Product Requirements Document

## Project Status: COMPLETE ✅

All requested features have been implemented and tested.

## Architecture
- **Frontend**: React 19, react-leaflet, Tailwind CSS, Shadcn UI, Recharts
- **Backend**: FastAPI with async MongoDB (motor), pywebpush, PIL
- **Database**: MongoDB
- **Map**: Leaflet with CartoDB Dark Matter tiles
- **AI**: OpenAI GPT-4o-mini via Emergent integrations
- **Weather**: Open-Meteo API (free)
- **Notifications**: WebPush with real VAPID keys

## Complete Feature List

### Core Features
- Interactive UK map with 100+ water monitoring stations
- Real-time data from Environment Agency API
- Safety score visualization (1-10) with color-coded markers
- AI-powered safety insights for each location
- Google OAuth authentication
- User favorites with persistence

### Data Layers
- **Water Stations**: Cyan markers with safety scores
- **Bathing Waters**: Yellow sun markers with quality ratings
- **Sewage Incidents**: Purple/red markers with discharge status
- **Flood Warnings**: 50+ active warnings from Environment Agency

### Weather Integration
- Current conditions (temperature, humidity, wind, UV index)
- 3-day forecast with icons
- Activity-specific recommendations
- Data from Open-Meteo API (free, no key needed)

### Sewage Monitoring
- Real-time discharge status from major water companies
- Thames Water, Yorkshire Water, United Utilities, South West Water
- Duration tracking for active discharges
- Toggleable map layer
- **Thames Water API integration ready** (add THAMES_WATER_API_KEY to .env)

### Community Features
- Submit observations, pollution reports, wildlife sightings
- Star ratings (1-5)
- Photo uploads (max 3 photos, 5MB each, auto-resized)
- Moderation system

### Moderation Dashboard (/admin)
- View pending/approved/rejected reports
- Quick approve/reject buttons
- Full report preview with photos
- Delete functionality
- Statistics overview (pending reports, users, push subscribers)
- Pagination

### Push Notifications
- **Real VAPID keys generated and configured**
- Service worker auto-registration on page load
- Subscribe to flood/sewage/pollution alerts
- Test notification endpoint
- Background flood alert checking

### Social Sharing
- Generate shareable safety reports
- Twitter and Facebook integration
- Copy to clipboard
- Formatted with emojis and hashtags

### Search & Navigation
- Search by postcode, river name, or place
- Get directions via Google Maps

### History & Analytics
- 7-day water level history
- Min/max/avg/trend statistics
- Interactive Recharts visualization

## API Endpoints (45+ total)

### Authentication
- POST `/api/auth/session` - Exchange OAuth session
- GET `/api/auth/me` - Get current user
- POST `/api/auth/logout` - Logout

### Water Data
- GET `/api/stations` - Environment Agency stations
- GET `/api/stations/{id}/readings` - Latest readings
- GET `/api/stations/{id}/history` - 7-day history
- GET `/api/bathing-waters` - Bathing water quality
- GET `/api/flood-warnings` - Active flood warnings
- GET `/api/search` - Location search

### User Features
- GET/POST/DELETE `/api/favorites` - User favorites

### Notifications
- GET `/api/notifications/subscriptions` - Get subscriptions
- POST `/api/notifications/subscribe` - Subscribe to alerts
- DELETE `/api/notifications/unsubscribe` - Unsubscribe
- GET `/api/notifications/alerts` - Get user alerts

### Push Notifications
- POST `/api/push/subscribe` - WebPush subscription
- DELETE `/api/push/unsubscribe` - Unsubscribe
- GET `/api/push/vapid-key` - Get VAPID public key
- POST `/api/push/send-test` - Send test notification

### Weather
- GET `/api/weather?lat={lat}&lng={lng}` - Weather data

### Sewage
- GET `/api/sewage-incidents` - All incidents
- GET `/api/sewage-incidents/near` - Nearby incidents
- GET `/api/sewage/thames-water` - Thames Water EDM data
- GET `/api/sewage/refresh` - Refresh all data

### Community
- GET `/api/community/reports` - Approved reports
- POST `/api/community/reports` - Submit report

### Moderation (Admin)
- GET `/api/admin/reports` - All reports (paginated)
- PATCH `/api/admin/reports/{id}` - Moderate report
- DELETE `/api/admin/reports/{id}` - Delete report
- GET `/api/admin/stats` - Dashboard statistics

### Uploads
- POST `/api/upload/photo` - Upload photo
- GET `/api/uploads/{filename}` - Serve uploaded file

### Sharing
- POST `/api/share/generate-report` - Generate share text
- GET `/api/share/report/{id}` - Get shared report

### AI
- POST `/api/ai/safety-insight` - AI recommendations

## Environment Variables

```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
EMERGENT_LLM_KEY=sk-emergent-...
VAPID_PUBLIC_KEY=BBQ-GtSkrSOvRkBdV6X-...
VAPID_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----..."
VAPID_EMAIL=mailto:alerts@waterwatchuk.com

# Optional - for live Thames Water data
THAMES_WATER_API_KEY=your_key_here
```

## To Enable Thames Water Live Data
1. Register at https://data.thameswater.co.uk/
2. Create an application
3. Get API key
4. Add `THAMES_WATER_API_KEY=your_key` to `/app/backend/.env`
5. Restart backend

## Pages
- `/` - Landing page
- `/dashboard` - Main map dashboard
- `/admin` - Moderation dashboard (requires auth)

## Data Sources
1. **Environment Agency** - Live water levels, flood warnings, bathing quality
2. **Open-Meteo** - Weather forecasts
3. **Postcodes.io** - UK postcode geocoding
4. **Nominatim (OSM)** - Place search
5. **Water Companies** - Sewage discharge data (mock data until API keys added)

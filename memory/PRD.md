# UK Water Safety Map - Product Requirements Document

## Original Problem Statement
Build a UK Water Safety Map application showing live river and water safety conditions. Users can see:
- River pollution levels
- Sewage discharge alerts
- Bathing water quality
- Nearby water company incidents

Target audience: Wild swimmers, anglers, kayakers, paddleboarders.

## User Personas
1. **Wild Swimmer** - Needs quick safety checks before heading to rivers/beaches
2. **Kayaker/Paddleboarder** - Requires water level and flood risk information
3. **Angler** - Interested in water quality and pollution data
4. **Environmental Activist** - Monitors sewage alerts and pollution incidents

## Architecture
- **Frontend**: React 19, react-leaflet, Tailwind CSS, Shadcn UI, Recharts
- **Backend**: FastAPI with async MongoDB (motor)
- **Database**: MongoDB
- **Map**: Leaflet with CartoDB Dark Matter tiles
- **AI**: OpenAI GPT-4o-mini via Emergent integrations
- **Weather**: Open-Meteo API (free, no key needed)

## What's Been Implemented

### Phase 1 - MVP (March 8, 2026)
- Landing page with hero section
- Dashboard with Leaflet map
- 100+ monitoring stations from Environment Agency
- Safety score visualization
- AI-powered safety insights
- Search functionality
- Google OAuth authentication
- User favorites system

### Phase 2 - Enhancements (March 8, 2026)
- Bathing Waters with quality ratings
- Historical charts (7-day water level history)
- Share Reports for social media
- Notification subscriptions
- Mobile optimization

### Phase 3 - Final Features (March 8, 2026)
- **Weather Integration**: Open-Meteo API providing:
  - Current conditions (temp, humidity, wind, UV)
  - 3-day forecast
  - Activity recommendations based on weather
- **Sewage Discharge Alerts**: 
  - Real-time status from Thames Water, Yorkshire Water, United Utilities
  - Purple markers on map for sewage treatment works
  - Active discharge warnings with duration
  - Toggle to show/hide sewage layer
- **Community Reports**:
  - Users can submit water condition observations
  - Report types: observation, pollution, wildlife, safety
  - Star ratings and descriptions
- **WebPush Notifications**:
  - VAPID key setup
  - Subscription endpoints
  - Ready for push notification delivery

### Backend APIs
- `/api/stations` - Environment Agency monitoring stations
- `/api/stations/{id}/readings` - Latest readings
- `/api/stations/{id}/history` - 7-day historical data
- `/api/bathing-waters` - Bathing water quality
- `/api/flood-warnings` - Active flood warnings
- `/api/search` - Location search
- `/api/favorites` - User favorites CRUD
- `/api/notifications/*` - Subscription management
- `/api/push/*` - WebPush endpoints
- `/api/share/generate-report` - Social share reports
- `/api/weather` - Weather data from Open-Meteo
- `/api/sewage-incidents` - Water company discharge data
- `/api/sewage-incidents/near` - Nearby sewage incidents
- `/api/community/reports` - Community reports
- `/api/ai/safety-insight` - AI recommendations
- `/api/auth/*` - Google OAuth flow

## Data Sources
1. **Environment Agency** - Water levels, flood warnings, bathing quality
2. **Open-Meteo** - Weather forecasts (free, no key)
3. **Water Companies** - Sewage discharge data (mock data for demo, real API requires registration)
4. **Community** - User-submitted reports

## Prioritized Backlog

### P0 - Critical (Complete)
- [x] Map integration with Leaflet
- [x] Environment Agency API integration
- [x] Safety score calculation
- [x] Search functionality
- [x] User authentication
- [x] Bathing water markers
- [x] Historical data charts
- [x] Share reports
- [x] Notification subscriptions
- [x] Mobile optimization
- [x] Weather integration
- [x] Sewage discharge alerts
- [x] Community reports

### P1 - Future Enhancements
- [ ] Real Thames Water EDM API integration (requires registration)
- [ ] Push notification delivery via WebPush
- [ ] Email notification digest
- [ ] Weather alerts integration
- [ ] Fishing forecasts

### P2 - Nice to Have
- [ ] Photo uploads in community reports
- [ ] Report moderation dashboard
- [ ] Export/download PDF reports
- [ ] Offline mode with cached data
- [ ] Multi-language support

## Notes
- Sewage incidents use sample data for demonstration
- For production, register at https://data.thameswater.co.uk/ for EDM API access
- Weather data is live from Open-Meteo
- All Environment Agency data is live

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

## Core Requirements (Static)
- Interactive UK map with water monitoring stations
- Real-time data from Environment Agency API
- Safety score visualization (1-10)
- Search by postcode/river/beach name
- User favorites system
- Google OAuth authentication
- AI-powered safety insights

## Architecture
- **Frontend**: React 19 with react-leaflet, Tailwind CSS, Shadcn UI, Recharts
- **Backend**: FastAPI with async MongoDB (motor)
- **Database**: MongoDB
- **Map**: Leaflet with CartoDB Dark Matter tiles
- **AI**: OpenAI GPT-4o-mini via Emergent integrations

## What's Been Implemented

### Phase 1 (March 8, 2026 - MVP)
- Landing page with hero section and features
- Dashboard with interactive Leaflet map
- 100+ monitoring stations from Environment Agency
- Custom markers with safety score colors
- Safety score ring visualization
- AI-powered safety insights
- Search by postcode/location
- Google OAuth authentication
- User favorites system

### Phase 2 (March 8, 2026 - Enhancements)
- **Bathing Waters**: Beach locations with quality ratings (Excellent/Good/Sufficient/Poor)
- **Historical Charts**: 7-day water level history with min/max/avg/trend stats using Recharts
- **Share Reports**: Generate shareable safety reports with emojis for Twitter/Facebook
- **Notification Subscriptions**: Alert subscriptions for flood/sewage/pollution warnings
- **Mobile Optimization**: Responsive sidebar, touch-friendly buttons, safe area support
- **Tabbed Detail Panel**: Info and History tabs in station details

### Backend APIs
- `/api/stations` - Environment Agency monitoring stations
- `/api/stations/{id}/readings` - Latest readings
- `/api/stations/{id}/history` - 7-day historical data with stats
- `/api/bathing-waters` - Bathing water quality locations
- `/api/flood-warnings` - Active flood warnings
- `/api/search` - Location search (postcode + nominatim)
- `/api/favorites` - User favorites CRUD
- `/api/notifications/*` - Subscription management
- `/api/share/generate-report` - Social share report generation
- `/api/ai/safety-insight` - AI safety recommendations
- `/api/auth/*` - Google OAuth flow

## Prioritized Backlog

### P0 - Critical (Done)
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

### P1 - Important (Future)
- [ ] Push notification delivery (WebPush)
- [ ] Water company incident feeds integration
- [ ] Community reports/comments
- [ ] Weather integration
- [ ] Fishing forecasts

### P2 - Nice to Have
- [ ] Email notification digest
- [ ] Export/download PDF reports
- [ ] Offline mode with cached data
- [ ] Multi-language support

## Next Tasks
1. Implement WebPush for real notification delivery
2. Integrate water company incident feeds (Thames Water, Yorkshire Water, etc.)
3. Add weather overlay from Met Office API
4. Create community reporting feature

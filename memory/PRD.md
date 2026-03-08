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
- **Frontend**: React 19 with react-leaflet, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI with async MongoDB (motor)
- **Database**: MongoDB
- **Map**: Leaflet with CartoDB Dark Matter tiles
- **AI**: OpenAI GPT-4o-mini via Emergent integrations

## What's Been Implemented (March 8, 2026)

### Landing Page
- Hero section with animated stats
- Features grid with glassmorphism cards
- AI features showcase
- Community section
- Navigation with auth buttons

### Dashboard
- Full-screen interactive Leaflet map
- Custom markers with safety score colors
- Glassmorphism sidebar with:
  - Search input (postcode/river)
  - Active flood warnings
  - User favorites (when logged in)
  - Station list with safety badges
- Station detail panel with:
  - Safety score ring visualization
  - Pollution/flood risk indicators
  - AI-powered safety insights
  - Favorite toggle
  - Google Maps directions

### Backend APIs
- `/api/stations` - Environment Agency monitoring stations
- `/api/stations/{id}/readings` - Latest readings
- `/api/bathing-waters` - Bathing water quality
- `/api/flood-warnings` - Active flood warnings
- `/api/search` - Location search (postcode + nominatim)
- `/api/favorites` - User favorites CRUD
- `/api/ai/safety-insight` - AI safety recommendations
- `/api/auth/*` - Google OAuth flow

### Authentication
- Emergent-managed Google OAuth
- Session token with 7-day expiry
- httpOnly secure cookies

## Prioritized Backlog

### P0 - Critical (Done)
- [x] Map integration with Leaflet
- [x] Environment Agency API integration
- [x] Safety score calculation
- [x] Search functionality
- [x] User authentication

### P1 - Important (Next Phase)
- [ ] Push notifications for alerts
- [ ] Historical data charts
- [ ] Bathing water markers on map
- [ ] User profile settings page
- [ ] Mobile-responsive optimization

### P2 - Nice to Have
- [ ] Community reports/comments
- [ ] Weather integration
- [ ] Fishing forecasts
- [ ] Water company incident feeds
- [ ] Export/share functionality

## Next Tasks
1. Add bathing water locations as separate markers
2. Implement historical readings chart in detail panel
3. Add push notification subscription
4. Create user profile/settings page
5. Improve mobile layout for outdoor use

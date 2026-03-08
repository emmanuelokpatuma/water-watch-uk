# WaterWatch UK - Product Requirements Document

## Project Status: MOBILE APP READY ✅

Subscription system and Capacitor mobile app framework implemented.

## Original Problem Statement
1. Clone https://github.com/emmanuelokpatuma/water-watch-uk
2. Add drinking water reports for areas (DONE)
3. Convert to mobile app for iOS/Android with £3/month subscription

## Architecture
- **Frontend**: React 19, react-leaflet, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI with async MongoDB (motor)
- **Mobile**: Capacitor (wraps React app for iOS/Android)
- **Payments**: Stripe (web) + RevenueCat (mobile app stores)
- **Database**: MongoDB

## Subscription Tiers

### FREE Tier
- View map & 100+ monitoring stations
- Basic water quality info
- Search locations
- Save up to 3 favorites

### PRO Tier (£3/month or £30/year)
- AI-powered safety insights (GPT-4o-mini)
- Full water quality reports
- Unlimited favorites
- Push notifications
- Sewage discharge alerts
- 7-day historical data
- Area water reports
- Ad-free experience

## What's Been Implemented

### March 2026 - Session 1
- Enhanced drinking water quality with Environment Agency API
- Added area-wide water report endpoint

### March 2026 - Session 2 (Current)
- **Subscription System**:
  - SubscriptionContext for frontend feature gating
  - SubscriptionPaywall component with pricing UI
  - Backend subscription endpoints (create-checkout, webhook, cancel, restore, portal)
  - Stripe integration for web payments
  - Feature access control on API endpoints

- **Mobile App Setup**:
  - Capacitor configuration for iOS/Android
  - RevenueCat integration for in-app purchases
  - Build scripts and publishing guide

- **Feature Gating**:
  - AI insights locked for free users with "PRO" badge
  - Favorites limited to 3 for free users
  - Upgrade button in user dropdown menu

## Files Added
- `/app/frontend/src/context/SubscriptionContext.js` - Frontend state management
- `/app/frontend/src/components/SubscriptionPaywall.js` - Paywall UI
- `/app/frontend/capacitor.config.json` - Capacitor config
- `/app/MOBILE_APP_GUIDE.md` - Complete publishing guide

## API Endpoints Added
- `GET /api/subscription/status` - Get user subscription status
- `POST /api/subscription/create-checkout` - Create Stripe checkout session
- `POST /api/subscription/webhook` - Handle Stripe webhooks
- `POST /api/subscription/cancel` - Cancel subscription
- `POST /api/subscription/restore` - Restore purchases
- `GET /api/subscription/portal` - Get Stripe customer portal URL
- `GET /api/subscription/check-feature/{feature}` - Check feature access

## Required Setup for Production

### Stripe (Web Payments)
1. Create Stripe account at https://stripe.com
2. Create product "WaterWatch Pro" with:
   - Monthly price: £3.00/month
   - Yearly price: £30.00/year
3. Configure webhook endpoint
4. Add keys to backend/.env:
   ```
   STRIPE_SECRET_KEY=sk_live_xxx
   STRIPE_WEBHOOK_SECRET=whsec_xxx
   STRIPE_PRICE_MONTHLY=price_xxx
   STRIPE_PRICE_YEARLY=price_xxx
   ```

### RevenueCat (Mobile App Payments)
1. Create RevenueCat account at https://revenuecat.com
2. Configure App Store Connect and Google Play Console
3. Create products in both stores
4. Import products to RevenueCat
5. Add API keys to capacitor.config.json

### App Store Publishing
- Apple Developer Account ($99/year)
- Google Play Developer Account ($25 one-time)
- See `/app/MOBILE_APP_GUIDE.md` for complete instructions

## Prioritized Backlog
- P0: ✅ Subscription system
- P0: ✅ Mobile app framework
- P1: Test with real Stripe keys
- P1: Build iOS/Android apps with Capacitor
- P2: Add analytics for subscription conversion
- P3: A/B test pricing

## Revenue Projections
At £3/month with 30% Apple/15% Google cut:
- 1,000 subscribers = £2,550/month after fees (web+mobile avg)
- Break-even: ~50 subscribers covers hosting + developer accounts

## Next Steps
1. Get Stripe API keys and test checkout flow
2. Build iOS app with `npx cap sync ios && npx cap open ios`
3. Build Android app with `npx cap sync android && npx cap open android`
4. Submit to app stores for review

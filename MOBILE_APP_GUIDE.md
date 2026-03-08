# WaterWatch UK - Mobile App Publishing Guide

## Overview
This guide covers converting WaterWatch UK to native iOS/Android apps with subscription payments.

## Tech Stack
- **Framework**: Capacitor (wraps React web app in native container)
- **Subscriptions**: RevenueCat (for app stores) + Stripe (for web)
- **Pricing**: £3/month or £30/year (2 months free)

---

## Step 1: Developer Accounts

### Apple App Store
1. Create Apple Developer Account at https://developer.apple.com/
2. Pay $99/year enrollment fee
3. Complete enrollment (can take 24-48 hours)

### Google Play Store
1. Create Google Play Developer Account at https://play.google.com/console/
2. Pay $25 one-time registration fee
3. Complete identity verification

---

## Step 2: RevenueCat Setup

### Create RevenueCat Account
1. Sign up at https://www.revenuecat.com/ (free tier available)
2. Create a new project called "WaterWatch UK"

### Configure App Stores in RevenueCat
1. **iOS**: Add App Store Connect credentials
   - App Bundle ID: `com.waterwatchuk.app`
   - Shared Secret from App Store Connect
   - In-App Purchase Key (download from App Store Connect)

2. **Android**: Add Google Play credentials
   - Package Name: `com.waterwatchuk.app`
   - Service Account JSON from Google Cloud Console

### Create Products

#### In App Store Connect:
1. Go to your app > Features > In-App Purchases
2. Create Auto-Renewable Subscription:
   - Product ID: `com.waterwatchuk.pro_monthly`
   - Price: £3.00/month
   - Create another: `com.waterwatchuk.pro_yearly` at £30.00/year

#### In Google Play Console:
1. Go to your app > Monetize > Subscriptions
2. Create subscription: `pro_monthly` with base plan at £3.00/month
3. Create subscription: `pro_yearly` with base plan at £30.00/year

### Import Products to RevenueCat
1. In RevenueCat dashboard > Products > Import Products
2. Select your iOS and Android products
3. Create Entitlement: `pro_tier`
4. Attach all subscription products to `pro_tier` entitlement

### Create Offering
1. Create offering named `default`
2. Add packages:
   - `$rc_monthly` → monthly subscription
   - `$rc_annual` → yearly subscription

### Get API Keys
1. Go to Project Settings > API Keys
2. Copy:
   - iOS Public API Key
   - Android Public API Key
   - REST API Secret Key (for backend)

---

## Step 3: Stripe Setup (for Web Payments)

### Create Stripe Products
1. Go to Stripe Dashboard > Products
2. Create product "WaterWatch Pro"
3. Add prices:
   - Monthly: £3.00/month recurring
   - Yearly: £30.00/year recurring
4. Copy Price IDs

### Configure Webhook
1. Go to Developers > Webhooks
2. Add endpoint: `https://your-domain.com/api/subscription/webhook`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_failed`
4. Copy Webhook Signing Secret

### Environment Variables
Add to `/app/backend/.env`:
```
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_MONTHLY=price_xxx
STRIPE_PRICE_YEARLY=price_xxx
```

---

## Step 4: Build Native Apps

### Build for iOS
```bash
cd /app/frontend

# Build React app
yarn build

# Sync to iOS
npx cap sync ios

# Open in Xcode
npx cap open ios
```

In Xcode:
1. Set Bundle Identifier: `com.waterwatchuk.app`
2. Configure signing with your Apple Developer account
3. Add In-App Purchase capability
4. Archive and upload to App Store Connect

### Build for Android
```bash
cd /app/frontend

# Build React app
yarn build

# Sync to Android
npx cap sync android

# Open in Android Studio
npx cap open android
```

In Android Studio:
1. Set Application ID: `com.waterwatchuk.app`
2. Configure signing for release
3. Build signed APK or AAB
4. Upload to Google Play Console

---

## Step 5: App Store Submissions

### iOS App Store
1. Complete App Store Connect listing:
   - App Name: WaterWatch UK
   - Description, keywords, screenshots
   - Privacy Policy URL (required)
2. Submit for review (typically 24-48 hours)

### Google Play Store
1. Complete Play Console listing:
   - Store listing details
   - Content rating questionnaire
   - Privacy Policy URL
2. Submit for review (typically 24-48 hours)

---

## Feature Tiers

### FREE Features
- View map & monitoring stations
- Basic water quality info
- Search locations
- Save 3 favorites

### PRO Features (£3/month)
- AI-powered safety insights
- Full water quality reports
- Unlimited favorites
- Push notifications
- Sewage discharge alerts
- 7-day historical data
- Area water reports
- Ad-free experience

---

## Revenue Split

| Platform | Your Cut | Platform Fee |
|----------|----------|--------------|
| iOS (Year 1) | 70% | 30% |
| iOS (Year 2+) | 85% | 15% |
| Android (Year 1) | 85% | 15% |
| Web (Stripe) | 97.1% | 2.9% + 30p |

---

## Testing Before Launch

### Sandbox Testing
1. Create sandbox test accounts in App Store Connect
2. Create license testers in Google Play Console
3. Test complete purchase flows

### RevenueCat Testing
1. Use Test Store during development
2. Verify webhooks are firing
3. Test entitlement activation

---

## Checklist Before Launch

- [ ] Apple Developer Account active
- [ ] Google Play Developer Account active
- [ ] RevenueCat project configured
- [ ] Products created in both stores
- [ ] Products imported to RevenueCat
- [ ] Entitlements configured
- [ ] Stripe products and webhook set up
- [ ] Privacy Policy URL added
- [ ] Terms of Service URL added
- [ ] App icons and screenshots ready
- [ ] Sandbox testing complete
- [ ] Backend webhook endpoints tested

---

## Support & Resources

- RevenueCat Docs: https://docs.revenuecat.com/
- Capacitor Docs: https://capacitorjs.com/docs
- Stripe Docs: https://stripe.com/docs
- App Store Guidelines: https://developer.apple.com/app-store/review/guidelines/
- Google Play Policies: https://play.google.com/console/about/

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Feature definitions for free vs paid tiers
export const FEATURES = {
  // FREE features
  VIEW_MAP: { tier: 'free', name: 'View Map & Stations' },
  BASIC_WATER_QUALITY: { tier: 'free', name: 'Basic Water Quality' },
  LIMITED_FAVORITES: { tier: 'free', name: 'Save 3 Favorites', limit: 3 },
  SEARCH: { tier: 'free', name: 'Location Search' },
  
  // PAID features (£3/month)
  AI_SAFETY_INSIGHTS: { tier: 'paid', name: 'AI Safety Insights' },
  FULL_WATER_REPORTS: { tier: 'paid', name: 'Full Water Quality Reports' },
  UNLIMITED_FAVORITES: { tier: 'paid', name: 'Unlimited Favorites' },
  PUSH_NOTIFICATIONS: { tier: 'paid', name: 'Push Notifications' },
  SEWAGE_ALERTS: { tier: 'paid', name: 'Sewage Discharge Alerts' },
  HISTORICAL_DATA: { tier: 'paid', name: '7-Day Historical Data' },
  AD_FREE: { tier: 'paid', name: 'Ad-Free Experience' },
  AREA_REPORTS: { tier: 'paid', name: 'Area Water Reports' },
};

const SubscriptionContext = createContext();

export function SubscriptionProvider({ children }) {
  const { user } = useAuth();
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isProUser, setIsProUser] = useState(false);

  // Check subscription status from backend
  const checkSubscription = useCallback(async () => {
    if (!user) {
      setSubscription(null);
      setIsProUser(false);
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/subscription/status`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setSubscription(data);
        setIsProUser(data.is_active && data.tier === 'pro');
      } else {
        setSubscription(null);
        setIsProUser(false);
      }
    } catch (error) {
      console.error('Failed to check subscription:', error);
      setSubscription(null);
      setIsProUser(false);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    checkSubscription();
  }, [checkSubscription]);

  // Check if user has access to a specific feature
  const hasAccess = useCallback((featureKey) => {
    const feature = FEATURES[featureKey];
    if (!feature) return false;
    
    // Free features are always accessible
    if (feature.tier === 'free') return true;
    
    // Paid features require pro subscription
    return isProUser;
  }, [isProUser]);

  // Check favorites limit
  const canAddFavorite = useCallback((currentCount) => {
    if (isProUser) return true;
    return currentCount < FEATURES.LIMITED_FAVORITES.limit;
  }, [isProUser]);

  // Get subscription info
  const getSubscriptionInfo = useCallback(() => {
    if (!subscription) {
      return {
        tier: 'free',
        is_active: false,
        features: Object.entries(FEATURES)
          .filter(([_, f]) => f.tier === 'free')
          .map(([key, f]) => ({ key, ...f }))
      };
    }
    
    return subscription;
  }, [subscription]);

  const value = {
    subscription,
    loading,
    isProUser,
    hasAccess,
    canAddFavorite,
    getSubscriptionInfo,
    refreshSubscription: checkSubscription,
    FEATURES
  };

  return (
    <SubscriptionContext.Provider value={value}>
      {children}
    </SubscriptionContext.Provider>
  );
}

export function useSubscription() {
  const context = useContext(SubscriptionContext);
  if (!context) {
    throw new Error('useSubscription must be used within a SubscriptionProvider');
  }
  return context;
}

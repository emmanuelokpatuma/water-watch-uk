import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useSubscription, FEATURES } from '../context/SubscriptionContext';
import { 
  X, 
  Check, 
  Crown, 
  Sparkles, 
  Shield, 
  Bell, 
  Heart,
  Zap,
  Lock,
  CreditCard
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Feature icons mapping
const featureIcons = {
  AI_SAFETY_INSIGHTS: Sparkles,
  FULL_WATER_REPORTS: Shield,
  UNLIMITED_FAVORITES: Heart,
  PUSH_NOTIFICATIONS: Bell,
  SEWAGE_ALERTS: Zap,
  HISTORICAL_DATA: Shield,
  AD_FREE: Check,
  AREA_REPORTS: Shield,
};

export default function SubscriptionPaywall({ isOpen, onClose, featureRequested }) {
  const { user, initiateGoogleLogin } = useAuth();
  const { isProUser, refreshSubscription } = useSubscription();
  const [loading, setLoading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState('monthly');

  const plans = [
    {
      id: 'monthly',
      name: 'Monthly',
      price: '£3',
      period: '/month',
      description: 'Billed monthly, cancel anytime',
      popular: true,
    },
    {
      id: 'yearly',
      name: 'Yearly',
      price: '£30',
      period: '/year',
      description: 'Save £6 (2 months free!)',
      savings: '17%',
    },
  ];

  const paidFeatures = Object.entries(FEATURES)
    .filter(([_, f]) => f.tier === 'paid')
    .map(([key, f]) => ({ key, ...f }));

  const handleSubscribe = async () => {
    if (!user) {
      toast.error('Please sign in first');
      initiateGoogleLogin();
      return;
    }

    setLoading(true);
    try {
      // Create checkout session
      const response = await fetch(`${BACKEND_URL}/api/subscription/create-checkout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          plan_id: selectedPlan,
          success_url: `${window.location.origin}/dashboard?subscription=success`,
          cancel_url: `${window.location.origin}/dashboard?subscription=cancelled`,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // For web, redirect to Stripe checkout
        if (data.checkout_url) {
          window.location.href = data.checkout_url;
        } else {
          // For native app, this would trigger RevenueCat
          toast.success('Redirecting to payment...');
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to start checkout');
      }
    } catch (error) {
      console.error('Checkout error:', error);
      toast.error('Failed to start checkout. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRestorePurchases = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/api/subscription/restore`, {
        method: 'POST',
        credentials: 'include',
      });

      if (response.ok) {
        await refreshSubscription();
        toast.success('Purchases restored successfully!');
        onClose();
      } else {
        toast.error('No purchases found to restore');
      }
    } catch (error) {
      toast.error('Failed to restore purchases');
    } finally {
      setLoading(false);
    }
  };

  if (isProUser) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="bg-slate-900 border-slate-700 text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-emerald-400">
              <Crown className="w-6 h-6" />
              You're a Pro Member!
            </DialogTitle>
          </DialogHeader>
          <div className="text-center py-6">
            <Check className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
            <p className="text-slate-300">You have access to all premium features.</p>
          </div>
          <Button onClick={onClose} className="w-full bg-cyan-500 hover:bg-cyan-400 text-black">
            Continue
          </Button>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-slate-900 border-slate-700 text-white max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            <Crown className="w-7 h-7 text-yellow-400" />
            Upgrade to Pro
          </DialogTitle>
          <DialogDescription className="text-slate-400">
            Unlock all features and get the most out of WaterWatch UK
          </DialogDescription>
        </DialogHeader>

        {/* Feature that triggered the paywall */}
        {featureRequested && (
          <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30 mb-4">
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-cyan-400" />
              <span className="text-cyan-400 text-sm">
                <strong>{FEATURES[featureRequested]?.name}</strong> is a Pro feature
              </span>
            </div>
          </div>
        )}

        {/* Plan Selection */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {plans.map((plan) => (
            <button
              key={plan.id}
              onClick={() => setSelectedPlan(plan.id)}
              className={`relative p-4 rounded-xl border-2 transition-all ${
                selectedPlan === plan.id
                  ? 'border-cyan-500 bg-cyan-500/10'
                  : 'border-slate-700 hover:border-slate-600'
              }`}
            >
              {plan.popular && (
                <Badge className="absolute -top-2 -right-2 bg-cyan-500 text-black text-xs">
                  Popular
                </Badge>
              )}
              {plan.savings && (
                <Badge className="absolute -top-2 -right-2 bg-emerald-500 text-black text-xs">
                  Save {plan.savings}
                </Badge>
              )}
              <div className="text-lg font-bold text-white">{plan.name}</div>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-2xl font-bold text-cyan-400">{plan.price}</span>
                <span className="text-slate-500 text-sm">{plan.period}</span>
              </div>
              <div className="text-xs text-slate-500 mt-1">{plan.description}</div>
            </button>
          ))}
        </div>

        {/* Features List */}
        <div className="space-y-2 mb-6">
          <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
            Pro Features Include:
          </h4>
          <div className="grid gap-2">
            {paidFeatures.map((feature) => {
              const Icon = featureIcons[feature.key] || Check;
              return (
                <div key={feature.key} className="flex items-center gap-3 p-2 rounded-lg bg-slate-800/50">
                  <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center">
                    <Icon className="w-4 h-4 text-cyan-400" />
                  </div>
                  <span className="text-slate-200">{feature.name}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Subscribe Button */}
        <Button
          onClick={handleSubscribe}
          disabled={loading}
          className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-white font-semibold py-6 text-lg"
          data-testid="subscribe-btn"
        >
          {loading ? (
            'Processing...'
          ) : (
            <>
              <CreditCard className="w-5 h-5 mr-2" />
              Subscribe for {plans.find(p => p.id === selectedPlan)?.price}{plans.find(p => p.id === selectedPlan)?.period}
            </>
          )}
        </Button>

        {/* Restore Purchases */}
        <button
          onClick={handleRestorePurchases}
          className="w-full text-center text-sm text-slate-500 hover:text-slate-400 mt-3"
          disabled={loading}
        >
          Restore previous purchases
        </button>

        {/* Terms */}
        <p className="text-xs text-slate-600 text-center mt-4">
          By subscribing, you agree to our Terms of Service. Subscription auto-renews. Cancel anytime.
        </p>
      </DialogContent>
    </Dialog>
  );
}

// Hook to show paywall when accessing premium features
export function usePaywall() {
  const [paywallOpen, setPaywallOpen] = useState(false);
  const [requestedFeature, setRequestedFeature] = useState(null);
  const { hasAccess } = useSubscription();

  const requireFeature = (featureKey, callback) => {
    if (hasAccess(featureKey)) {
      callback();
      return true;
    } else {
      setRequestedFeature(featureKey);
      setPaywallOpen(true);
      return false;
    }
  };

  const PaywallDialog = () => (
    <SubscriptionPaywall
      isOpen={paywallOpen}
      onClose={() => {
        setPaywallOpen(false);
        setRequestedFeature(null);
      }}
      featureRequested={requestedFeature}
    />
  );

  return { requireFeature, PaywallDialog, openPaywall: () => setPaywallOpen(true) };
}

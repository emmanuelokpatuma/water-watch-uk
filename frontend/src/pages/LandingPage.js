import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Droplets, 
  Map, 
  ShieldCheck, 
  AlertTriangle, 
  Waves, 
  ChevronRight,
  Users,
  Sparkles,
  MapPin,
  Activity
} from 'lucide-react';
import { Button } from '../components/ui/button';

export default function LandingPage() {
  const { user, login } = useAuth();
  const [statsVisible, setStatsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setStatsVisible(true), 500);
    return () => clearTimeout(timer);
  }, []);

  const features = [
    {
      icon: <Map className="w-6 h-6" />,
      title: "Live River Map",
      description: "Interactive map showing all UK water monitoring stations with real-time data."
    },
    {
      icon: <ShieldCheck className="w-6 h-6" />,
      title: "Safety Scores",
      description: "AI-powered safety ratings for swimming, kayaking, and water activities."
    },
    {
      icon: <AlertTriangle className="w-6 h-6" />,
      title: "Instant Alerts",
      description: "Real-time sewage discharge and pollution warnings for your favorite spots."
    },
    {
      icon: <Waves className="w-6 h-6" />,
      title: "Water Quality",
      description: "Detailed water quality data from the Environment Agency."
    }
  ];

  const stats = [
    { value: "2,000+", label: "Monitoring Stations" },
    { value: "Live", label: "Data Updates" },
    { value: "100%", label: "Free to Use" }
  ];

  return (
    <div className="min-h-screen bg-slate-950 hero-gradient overflow-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass-card border-0 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2" data-testid="logo-link">
              <Droplets className="w-8 h-8 text-cyan-400" />
              <span className="font-bold text-xl text-white tracking-tight" style={{ fontFamily: 'Manrope' }}>
                WaterWatch<span className="text-cyan-400">UK</span>
              </span>
            </Link>
            
            <div className="flex items-center gap-4">
              {user ? (
                <Link to="/dashboard">
                  <Button 
                    className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold btn-primary-glow"
                    data-testid="go-to-dashboard-btn"
                  >
                    Open Dashboard
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </Link>
              ) : (
                <>
                  <Link to="/dashboard">
                    <Button 
                      variant="ghost" 
                      className="text-slate-300 hover:text-white hover:bg-slate-800"
                      data-testid="explore-map-btn"
                    >
                      Explore Map
                    </Button>
                  </Link>
                  <Button 
                    onClick={login}
                    className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold btn-primary-glow"
                    data-testid="sign-in-btn"
                  >
                    Sign In
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <div className="space-y-8 animate-slide-up">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20">
                <Activity className="w-4 h-4 text-cyan-400" />
                <span className="text-cyan-400 text-sm font-medium">Live UK Water Data</span>
              </div>
              
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white leading-tight" style={{ fontFamily: 'Manrope' }}>
                Know Before<br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-emerald-400">
                  You Go
                </span>
              </h1>
              
              <p className="text-lg text-slate-400 max-w-lg">
                Real-time river safety conditions, pollution alerts, and water quality data 
                for swimmers, kayakers, and water sports enthusiasts across the UK.
              </p>
              
              <div className="flex flex-wrap gap-4">
                <Link to="/dashboard">
                  <Button 
                    size="lg"
                    className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-lg px-8 btn-primary-glow"
                    data-testid="cta-explore-map"
                  >
                    <MapPin className="w-5 h-5 mr-2" />
                    Explore the Map
                  </Button>
                </Link>
                <Button 
                  size="lg"
                  variant="outline"
                  className="border-slate-700 text-white hover:bg-slate-800 text-lg px-8"
                  data-testid="cta-learn-more"
                  onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                >
                  Learn More
                </Button>
              </div>

              {/* Stats */}
              <div className={`grid grid-cols-3 gap-6 pt-8 transition-all duration-700 ${statsVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
                {stats.map((stat, index) => (
                  <div key={index} className="text-center">
                    <div className="text-2xl sm:text-3xl font-bold text-white" style={{ fontFamily: 'JetBrains Mono' }}>
                      {stat.value}
                    </div>
                    <div className="text-slate-500 text-sm">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right - Map Preview */}
            <div className="relative animate-slide-in-right delay-200">
              <div className="relative rounded-2xl overflow-hidden border border-slate-800 shadow-2xl">
                <div className="aspect-[4/3] bg-slate-900 relative">
                  <img 
                    src="https://images.unsplash.com/photo-1765907893701-a81511073256"
                    alt="Water activities"
                    className="w-full h-full object-cover opacity-60"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/50 to-transparent" />
                  
                  {/* Floating Cards */}
                  <div className="absolute top-6 left-6 glass-card p-4 animate-slide-in-left delay-400">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                        <ShieldCheck className="w-5 h-5 text-emerald-400" />
                      </div>
                      <div>
                        <div className="text-white font-semibold">River Aire</div>
                        <div className="text-emerald-400 text-sm">Safe for swimming</div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="absolute bottom-6 right-6 glass-card p-4 animate-slide-in-right delay-500">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center">
                        <Waves className="w-5 h-5 text-cyan-400" />
                      </div>
                      <div>
                        <div className="text-white font-semibold font-mono">1.2m</div>
                        <div className="text-slate-400 text-sm">Water Level</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Glow Effect */}
              <div className="absolute -inset-4 bg-cyan-500/20 rounded-3xl blur-3xl -z-10 opacity-50" />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4" style={{ fontFamily: 'Manrope' }}>
              Everything You Need
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Comprehensive water safety data powered by the Environment Agency 
              and enhanced with AI insights.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="glass-card glass-card-hover p-6 space-y-4 transition-all duration-300"
                style={{ animationDelay: `${index * 100}ms` }}
                data-testid={`feature-card-${index}`}
              >
                <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-white" style={{ fontFamily: 'Manrope' }}>
                  {feature.title}
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="glass-card p-8 sm:p-12 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-1/2 h-full opacity-30">
              <img 
                src="https://images.unsplash.com/photo-1686656485534-d8518c3d911a"
                alt="Clean water"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-slate-900 to-transparent" />
            </div>
            
            <div className="relative z-10 max-w-xl">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 mb-6">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <span className="text-purple-400 text-sm font-medium">AI-Powered</span>
              </div>
              
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4" style={{ fontFamily: 'Manrope' }}>
                Smart Safety Insights
              </h2>
              <p className="text-slate-400 mb-8">
                Get personalized safety recommendations based on current conditions, 
                your activity type, and local environmental data.
              </p>
              
              <div className="space-y-4">
                {[
                  "Activity-specific safety advice",
                  "Weather-aware recommendations", 
                  "Historical pattern analysis"
                ].map((item, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="w-6 h-6 rounded-full bg-cyan-500/20 flex items-center justify-center">
                      <ShieldCheck className="w-4 h-4 text-cyan-400" />
                    </div>
                    <span className="text-slate-300">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Community Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
            <Users className="w-4 h-4 text-emerald-400" />
            <span className="text-emerald-400 text-sm font-medium">Community</span>
          </div>
          
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4" style={{ fontFamily: 'Manrope' }}>
            Built for UK Water Enthusiasts
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto mb-12">
            Whether you're a wild swimmer, angler, kayaker, or paddleboarder - 
            get the safety data you need before heading out.
          </p>

          <Link to="/dashboard">
            <Button 
              size="lg"
              className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-lg px-12 btn-primary-glow"
              data-testid="cta-start-exploring"
            >
              Start Exploring
              <ChevronRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Droplets className="w-6 h-6 text-cyan-400" />
            <span className="font-semibold text-white" style={{ fontFamily: 'Manrope' }}>
              WaterWatch<span className="text-cyan-400">UK</span>
            </span>
          </div>
          <div className="text-slate-500 text-sm">
            Data provided by Environment Agency under Open Government Licence
          </div>
        </div>
      </footer>
    </div>
  );
}

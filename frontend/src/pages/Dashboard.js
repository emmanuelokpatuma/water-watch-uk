import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, Circle } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useAuth } from '../context/AuthContext';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { 
  Search, 
  Droplets, 
  ShieldCheck, 
  AlertTriangle, 
  Waves,
  Heart,
  HeartOff,
  X,
  Menu,
  LogOut,
  User,
  Sparkles,
  MapPin,
  Activity,
  RefreshCw,
  Navigation,
  Share2,
  Bell,
  BellOff,
  TrendingUp,
  TrendingDown,
  Minus,
  Twitter,
  Facebook,
  Copy,
  Check,
  Umbrella,
  Cloud,
  Wind,
  Thermometer,
  AlertOctagon,
  MessageSquare,
  Star,
  Send,
  Eye,
  Sun,
  CloudRain,
  Users
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Switch } from '../components/ui/switch';
import { Textarea } from '../components/ui/textarea';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import { usePushNotifications } from '../hooks/usePushNotifications';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Fix Leaflet default marker icon issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icon creator
const createCustomIcon = (safetyScore, hasAlert = false, type = 'station') => {
  let borderColor = '#06b6d4';
  let glowColor = 'rgba(6, 182, 212, 0.4)';
  let iconSvg = '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>';
  
  if (type === 'beach') {
    borderColor = '#fbbf24';
    glowColor = 'rgba(251, 191, 36, 0.4)';
    iconSvg = '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>';
  } else if (type === 'sewage') {
    borderColor = hasAlert ? '#ef4444' : '#a855f7';
    glowColor = hasAlert ? 'rgba(239, 68, 68, 0.6)' : 'rgba(168, 85, 247, 0.4)';
    iconSvg = '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/>';
  } else if (hasAlert) {
    borderColor = '#ef4444';
    glowColor = 'rgba(239, 68, 68, 0.5)';
  } else if (safetyScore >= 8) {
    borderColor = '#10b981';
    glowColor = 'rgba(16, 185, 129, 0.4)';
  } else if (safetyScore >= 5) {
    borderColor = '#eab308';
    glowColor = 'rgba(234, 179, 8, 0.4)';
  } else if (safetyScore < 5) {
    borderColor = '#f97316';
    glowColor = 'rgba(249, 115, 22, 0.4)';
  }

  return L.divIcon({
    className: 'custom-div-icon',
    html: `
      <div style="
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 2px solid ${borderColor};
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 15px ${glowColor}, 0 4px 10px rgba(0,0,0,0.4);
        ${hasAlert ? 'animation: pulse-alert 2s infinite;' : ''}
      ">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="${borderColor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          ${iconSvg}
        </svg>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
  });
};

// Map center controller component
function MapController({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, 12, { duration: 1.5 });
    }
  }, [center, map]);
  return null;
}

// Safety Score Ring Component
function SafetyRing({ score, size = 80 }) {
  const circumference = 2 * Math.PI * 35;
  const progress = (score / 10) * circumference;
  const offset = circumference - progress;
  
  let color = '#06b6d4';
  if (score >= 8) color = '#10b981';
  else if (score >= 5) color = '#eab308';
  else if (score < 5) color = '#f97316';

  return (
    <div className="safety-ring relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 80 80">
        <circle
          className="safety-ring-bg"
          cx="40"
          cy="40"
          r="35"
          fill="none"
          strokeWidth="6"
        />
        <circle
          className="safety-ring-progress"
          cx="40"
          cy="40"
          r="35"
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ filter: `drop-shadow(0 0 8px ${color}80)` }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-bold text-white font-mono">{score}</span>
      </div>
    </div>
  );
}

// Historical Chart Component
function HistoryChart({ data, summary }) {
  if (!data || data.length === 0) {
    return (
      <div className="h-32 flex items-center justify-center text-slate-500 text-sm">
        No historical data available
      </div>
    );
  }

  const chartData = data.slice(0, 50).reverse().map((item, index) => ({
    name: index,
    value: item.value,
    time: new Date(item.datetime).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  }));

  return (
    <div className="space-y-2">
      <ResponsiveContainer width="100%" height={120}>
        <LineChart data={chartData}>
          <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} width={30} />
          <Tooltip 
            contentStyle={{ 
              background: 'rgba(15, 23, 42, 0.95)', 
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: '#f8fafc'
            }}
            formatter={(value) => [`${value}m`, 'Level']}
          />
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke="#06b6d4" 
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: '#06b6d4' }}
          />
        </LineChart>
      </ResponsiveContainer>
      
      {summary && Object.keys(summary).length > 0 && (
        <div className="grid grid-cols-4 gap-2 text-xs">
          <div className="text-center p-2 rounded bg-slate-800/50">
            <div className="text-slate-500">Min</div>
            <div className="text-white font-mono">{summary.min}m</div>
          </div>
          <div className="text-center p-2 rounded bg-slate-800/50">
            <div className="text-slate-500">Max</div>
            <div className="text-white font-mono">{summary.max}m</div>
          </div>
          <div className="text-center p-2 rounded bg-slate-800/50">
            <div className="text-slate-500">Avg</div>
            <div className="text-white font-mono">{summary.avg}m</div>
          </div>
          <div className="text-center p-2 rounded bg-slate-800/50">
            <div className="text-slate-500">Trend</div>
            <div className="flex items-center justify-center">
              {summary.trend === 'rising' ? (
                <TrendingUp className="w-4 h-4 text-orange-400" />
              ) : summary.trend === 'falling' ? (
                <TrendingDown className="w-4 h-4 text-emerald-400" />
              ) : (
                <Minus className="w-4 h-4 text-slate-400" />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const { user, login, logout } = useAuth();
  const { isSupported: pushSupported, isSubscribed: pushSubscribed, subscribe: subscribePush, unsubscribe: unsubscribePush, sendTestNotification } = usePushNotifications();
  const [stations, setStations] = useState([]);
  const [bathingWaters, setBathingWaters] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mapCenter, setMapCenter] = useState(null);
  const [aiInsight, setAiInsight] = useState('');
  const [loadingInsight, setLoadingInsight] = useState(false);
  const [floodWarnings, setFloodWarnings] = useState([]);
  const [historyData, setHistoryData] = useState({ history: [], summary: {} });
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [shareData, setShareData] = useState(null);
  const [copied, setCopied] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [activeTab, setActiveTab] = useState('info');
  const [weatherData, setWeatherData] = useState(null);
  const [loadingWeather, setLoadingWeather] = useState(false);
  const [sewageIncidents, setSewageIncidents] = useState([]);
  const [showSewageLayer, setShowSewageLayer] = useState(true);
  const [communityReports, setCommunityReports] = useState([]);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [newReport, setNewReport] = useState({ description: '', rating: 3, report_type: 'observation', photos: [] });
  const [sidebarTab, setSidebarTab] = useState('stations');
  const searchTimeoutRef = useRef(null);

  // Default center: UK
  const defaultCenter = [54.0, -2.5];
  const defaultZoom = 6;

  // Check window width for mobile
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Auto-close sidebar on mobile when station selected
  useEffect(() => {
    if (isMobile && selectedStation) {
      setSidebarOpen(false);
    }
  }, [selectedStation, isMobile]);

  // Fetch stations
  const fetchStations = useCallback(async (retryCount = 0) => {
    try {
      const response = await fetch(`${API}/stations`);
      if (response.ok) {
        const data = await response.json();
        setStations(data.stations || []);
      } else if (retryCount < 2) {
        setTimeout(() => fetchStations(retryCount + 1), 1000);
        return;
      }
    } catch (error) {
      console.error('Error fetching stations:', error);
      if (retryCount < 2) {
        setTimeout(() => fetchStations(retryCount + 1), 1000);
        return;
      }
      toast.error('Failed to load stations');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch bathing waters
  const fetchBathingWaters = useCallback(async () => {
    try {
      const response = await fetch(`${API}/bathing-waters`);
      if (response.ok) {
        const data = await response.json();
        setBathingWaters(data.bathing_waters || []);
      }
    } catch (error) {
      console.error('Error fetching bathing waters:', error);
    }
  }, []);

  // Fetch favorites (if authenticated)
  const fetchFavorites = useCallback(async () => {
    if (!user) return;
    try {
      const response = await fetch(`${API}/favorites`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setFavorites(data.favorites || []);
      }
    } catch (error) {
      console.error('Error fetching favorites:', error);
    }
  }, [user]);

  // Fetch flood warnings
  const fetchFloodWarnings = useCallback(async () => {
    try {
      const response = await fetch(`${API}/flood-warnings`);
      if (response.ok) {
        const data = await response.json();
        setFloodWarnings(data.warnings || []);
      }
    } catch (error) {
      console.error('Error fetching flood warnings:', error);
    }
  }, []);

  // Fetch historical data for station
  const fetchHistory = useCallback(async (stationId) => {
    setLoadingHistory(true);
    try {
      const response = await fetch(`${API}/stations/${stationId}/history?days=7`);
      if (response.ok) {
        const data = await response.json();
        setHistoryData(data);
      }
    } catch (error) {
      console.error('Error fetching history:', error);
      setHistoryData({ history: [], summary: {} });
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  // Check notification subscription
  const checkNotificationStatus = useCallback(async () => {
    if (!user) return;
    try {
      const response = await fetch(`${API}/notifications/subscriptions`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setNotificationsEnabled(data.subscriptions?.length > 0 && data.subscriptions[0]?.enabled);
      }
    } catch (error) {
      console.error('Error checking notifications:', error);
    }
  }, [user]);

  // Fetch sewage incidents
  const fetchSewageIncidents = useCallback(async () => {
    try {
      const response = await fetch(`${API}/sewage-incidents`);
      if (response.ok) {
        const data = await response.json();
        setSewageIncidents(data.incidents || []);
      }
    } catch (error) {
      console.error('Error fetching sewage incidents:', error);
    }
  }, []);

  // Fetch weather for location
  const fetchWeather = useCallback(async (lat, lng) => {
    setLoadingWeather(true);
    try {
      const response = await fetch(`${API}/weather?lat=${lat}&lng=${lng}`);
      if (response.ok) {
        const data = await response.json();
        setWeatherData(data);
      }
    } catch (error) {
      console.error('Error fetching weather:', error);
      setWeatherData(null);
    } finally {
      setLoadingWeather(false);
    }
  }, []);

  // Fetch community reports
  const fetchCommunityReports = useCallback(async () => {
    try {
      const response = await fetch(`${API}/community/reports`);
      if (response.ok) {
        const data = await response.json();
        setCommunityReports(data.reports || []);
      }
    } catch (error) {
      console.error('Error fetching community reports:', error);
    }
  }, []);

  // Submit community report
  const submitCommunityReport = async () => {
    if (!user) {
      toast.error('Please sign in to submit a report');
      return;
    }
    if (!selectedStation) {
      toast.error('Please select a location first');
      return;
    }
    try {
      const response = await fetch(`${API}/community/reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          latitude: selectedStation.latitude,
          longitude: selectedStation.longitude,
          location_name: selectedStation.label,
          ...newReport
        })
      });
      if (response.ok) {
        toast.success('Report submitted for review!');
        setReportDialogOpen(false);
        setNewReport({ description: '', rating: 3, report_type: 'observation' });
        fetchCommunityReports();
      }
    } catch (error) {
      toast.error('Failed to submit report');
    }
  };

  useEffect(() => {
    fetchStations();
    fetchBathingWaters();
    fetchFloodWarnings();
    fetchSewageIncidents();
    fetchCommunityReports();
  }, [fetchStations, fetchBathingWaters, fetchFloodWarnings, fetchSewageIncidents, fetchCommunityReports]);

  useEffect(() => {
    fetchFavorites();
    checkNotificationStatus();
  }, [fetchFavorites, checkNotificationStatus]);

  // Search handler with debounce
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const response = await fetch(`${API}/search?q=${encodeURIComponent(searchQuery)}`);
        if (response.ok) {
          const data = await response.json();
          setSearchResults(data.results || []);
        }
      } catch (error) {
        console.error('Search error:', error);
      } finally {
        setSearching(false);
      }
    }, 400);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery]);

  // Toggle favorite
  const toggleFavorite = async (station) => {
    if (!user) {
      toast.error('Please sign in to save favorites');
      return;
    }

    const isFavorited = favorites.some(f => f.station_id === station.station_id);

    if (isFavorited) {
      const fav = favorites.find(f => f.station_id === station.station_id);
      try {
        const response = await fetch(`${API}/favorites/${fav.id}`, {
          method: 'DELETE',
          credentials: 'include'
        });
        if (response.ok) {
          setFavorites(favorites.filter(f => f.id !== fav.id));
          toast.success('Removed from favorites');
        }
      } catch (error) {
        toast.error('Failed to remove favorite');
      }
    } else {
      try {
        const response = await fetch(`${API}/favorites`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            station_id: station.station_id,
            station_name: station.label,
            river_name: station.river_name,
            latitude: station.latitude,
            longitude: station.longitude
          })
        });
        if (response.ok) {
          const newFav = await response.json();
          setFavorites([...favorites, newFav]);
          toast.success('Added to favorites');
        }
      } catch (error) {
        toast.error('Failed to add favorite');
      }
    }
  };

  // Toggle notifications
  const toggleNotifications = async () => {
    if (!user) {
      toast.error('Please sign in to enable notifications');
      return;
    }

    try {
      if (notificationsEnabled) {
        // Unsubscribe from push
        if (pushSubscribed) {
          await unsubscribePush();
        }
        await fetch(`${API}/notifications/unsubscribe`, {
          method: 'DELETE',
          credentials: 'include'
        });
        setNotificationsEnabled(false);
        toast.success('Notifications disabled');
      } else {
        // Subscribe to push notifications
        if (pushSupported && !pushSubscribed) {
          try {
            await subscribePush();
            toast.success('Push notifications enabled!');
          } catch (err) {
            console.log('Push subscription failed, continuing with email notifications');
          }
        }
        
        const stationIds = favorites.map(f => f.station_id);
        await fetch(`${API}/notifications/subscribe`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            station_ids: stationIds,
            alert_types: ['flood', 'sewage', 'pollution']
          })
        });
        setNotificationsEnabled(true);
        toast.success('Notifications enabled for your favorites');
      }
    } catch (error) {
      toast.error('Failed to update notification settings');
    }
  };

  // Get AI insight
  const getAiInsight = async (station, activity = 'swimming') => {
    setLoadingInsight(true);
    setAiInsight('');
    try {
      const response = await fetch(`${API}/ai/safety-insight`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          station_name: station.label,
          river_name: station.river_name,
          water_level: station.water_level,
          safety_score: station.safety_score,
          pollution_risk: station.pollution_risk,
          flood_risk: station.flood_risk,
          activity
        })
      });
      if (response.ok) {
        const data = await response.json();
        setAiInsight(data.insight);
      }
    } catch (error) {
      console.error('AI insight error:', error);
      setAiInsight('Unable to generate safety insight at this time.');
    } finally {
      setLoadingInsight(false);
    }
  };

  // Generate share report
  const generateShareReport = async (station) => {
    try {
      const response = await fetch(`${API}/share/generate-report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          station_id: station.station_id,
          station_name: station.label,
          river_name: station.river_name,
          safety_score: station.safety_score,
          pollution_risk: station.pollution_risk,
          flood_risk: station.flood_risk,
          water_level: station.water_level
        })
      });
      if (response.ok) {
        const data = await response.json();
        setShareData(data);
        setShareDialogOpen(true);
      }
    } catch (error) {
      toast.error('Failed to generate share report');
    }
  };

  // Copy share text
  const copyShareText = () => {
    if (shareData?.share_text) {
      navigator.clipboard.writeText(shareData.share_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success('Copied to clipboard!');
    }
  };

  // Handle search result click
  const handleSearchResultClick = (result) => {
    setMapCenter([result.latitude, result.longitude]);
    setSearchQuery('');
    setSearchResults([]);
    toast.success(`Navigated to ${result.name || result.display_name}`);
  };

  // Handle station click
  const handleStationClick = (station) => {
    setSelectedStation(station);
    setMapCenter([station.latitude, station.longitude]);
    setActiveTab('info');
    getAiInsight(station);
    fetchHistory(station.station_id);
    fetchWeather(station.latitude, station.longitude);
  };

  // Check if station is favorited
  const isFavorited = (stationId) => {
    return favorites.some(f => f.station_id === stationId);
  };

  // Memoized markers
  const markers = useMemo(() => {
    const stationMarkers = stations.map((station) => (
      <Marker
        key={station.station_id}
        position={[station.latitude, station.longitude]}
        icon={createCustomIcon(station.safety_score, station.flood_risk !== 'None', 'station')}
        eventHandlers={{
          click: () => handleStationClick(station)
        }}
      >
        <Popup>
          <div className="min-w-[200px]">
            <h3 className="font-semibold text-base mb-1">{station.label}</h3>
            {station.river_name && (
              <p className="text-slate-400 text-sm">{station.river_name}</p>
            )}
            <div className="mt-2 flex items-center gap-2">
              <span className="text-cyan-400 font-mono text-sm">
                Score: {station.safety_score}/10
              </span>
            </div>
          </div>
        </Popup>
      </Marker>
    ));

    const beachMarkers = bathingWaters.map((beach) => (
      <Marker
        key={beach.id}
        position={[beach.latitude, beach.longitude]}
        icon={createCustomIcon(beach.classification === 'Excellent' ? 9 : beach.classification === 'Good' ? 7 : 5, false, 'beach')}
      >
        <Popup>
          <div className="min-w-[180px]">
            <h3 className="font-semibold text-base mb-1">{beach.name}</h3>
            <Badge variant="outline" className={`${
              beach.classification === 'Excellent' ? 'border-emerald-500 text-emerald-400' :
              beach.classification === 'Good' ? 'border-cyan-500 text-cyan-400' :
              'border-yellow-500 text-yellow-400'
            }`}>
              {beach.classification}
            </Badge>
          </div>
        </Popup>
      </Marker>
    ));

    const sewageMarkers = showSewageLayer ? sewageIncidents.filter(i => i.latitude && i.longitude).map((incident) => (
      <Marker
        key={incident.id}
        position={[incident.latitude, incident.longitude]}
        icon={createCustomIcon(0, incident.status === 'Discharging', 'sewage')}
      >
        <Popup>
          <div className="min-w-[200px]">
            <h3 className="font-semibold text-base mb-1">{incident.site_name}</h3>
            <p className="text-slate-400 text-sm">{incident.water_company}</p>
            <Badge 
              variant="outline" 
              className={`mt-2 ${
                incident.status === 'Discharging' 
                  ? 'border-red-500 text-red-400 animate-pulse' 
                  : 'border-emerald-500 text-emerald-400'
              }`}
            >
              {incident.status}
            </Badge>
            {incident.duration_hours && (
              <p className="text-slate-500 text-xs mt-1">Duration: {incident.duration_hours}h</p>
            )}
          </div>
        </Popup>
      </Marker>
    )) : [];

    return [...stationMarkers, ...beachMarkers, ...sewageMarkers];
  }, [stations, bathingWaters, sewageIncidents, showSewageLayer]);

  return (
    <div className="h-screen w-screen bg-slate-950 overflow-hidden flex flex-col md:flex-row" data-testid="dashboard">
      {/* Mobile Header */}
      {isMobile && (
        <div className="flex items-center justify-between p-3 glass-card rounded-none border-0 border-b border-white/5 z-30">
          <div className="flex items-center gap-2">
            <Droplets className="w-5 h-5 text-cyan-400" />
            <span className="font-bold text-sm text-white" style={{ fontFamily: 'Manrope' }}>
              WaterWatch<span className="text-cyan-400">UK</span>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="text-slate-400 hover:text-white h-8 w-8"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              data-testid="mobile-menu-btn"
            >
              <Menu className="w-5 h-5" />
            </Button>
          </div>
        </div>
      )}

      {/* Sidebar */}
      <div 
        className={`${sidebarOpen ? (isMobile ? 'absolute inset-0 z-40' : 'w-80') : 'w-0'} transition-all duration-300 h-full z-20 flex-shrink-0 ${isMobile ? 'bg-slate-950/95 backdrop-blur-xl' : ''}`}
      >
        <div className={`h-full glass-card rounded-none border-r border-white/5 flex flex-col ${sidebarOpen ? 'opacity-100' : 'opacity-0'} transition-opacity duration-200`}>
          {/* Sidebar Header */}
          <div className="p-4 border-b border-white/5">
            <div className="flex items-center justify-between mb-4">
              {!isMobile && (
                <div className="flex items-center gap-2">
                  <Droplets className="w-6 h-6 text-cyan-400" />
                  <span className="font-bold text-lg text-white" style={{ fontFamily: 'Manrope' }}>
                    WaterWatch<span className="text-cyan-400">UK</span>
                  </span>
                </div>
              )}
              <Button
                variant="ghost"
                size="icon"
                className={`text-slate-400 hover:text-white ${isMobile ? 'ml-auto' : ''}`}
                onClick={() => setSidebarOpen(false)}
                data-testid="close-sidebar-btn"
              >
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <Input
                type="text"
                placeholder="Search postcode or river..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-slate-900/50 border-slate-700 text-white placeholder:text-slate-500 focus:border-cyan-500"
                data-testid="search-input"
              />
              {searching && (
                <RefreshCw className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-400 animate-spin" />
              )}
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="absolute left-0 right-0 mt-2 mx-4 glass-card rounded-lg overflow-hidden z-50" data-testid="search-results">
                {searchResults.map((result, index) => (
                  <button
                    key={index}
                    onClick={() => handleSearchResultClick(result)}
                    className="w-full p-3 text-left hover:bg-slate-800 border-b border-white/5 last:border-0 transition-colors"
                    data-testid={`search-result-${index}`}
                  >
                    <div className="flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-cyan-400" />
                      <span className="text-white text-sm">{result.name}</span>
                    </div>
                    {result.display_name && result.display_name !== result.name && (
                      <p className="text-slate-500 text-xs mt-1 truncate">{result.display_name}</p>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Sidebar Content */}
          <ScrollArea className="flex-1 p-4">
            {/* Notification Toggle (if logged in) */}
            {user && (
              <div className="mb-4 p-3 rounded-lg bg-slate-800/50 border border-slate-700 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {notificationsEnabled ? (
                    <Bell className="w-4 h-4 text-cyan-400" />
                  ) : (
                    <BellOff className="w-4 h-4 text-slate-500" />
                  )}
                  <span className="text-sm text-slate-300">Alert Notifications</span>
                </div>
                <Switch
                  checked={notificationsEnabled}
                  onCheckedChange={toggleNotifications}
                  data-testid="notification-toggle"
                />
              </div>
            )}

            {/* Flood Warnings */}
            {floodWarnings.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-orange-400" />
                  Active Warnings ({floodWarnings.length})
                </h3>
                <div className="space-y-2">
                  {floodWarnings.slice(0, 3).map((warning, index) => (
                    <div 
                      key={index}
                      className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/20"
                      data-testid={`flood-warning-${index}`}
                    >
                      <div className="text-orange-400 text-sm font-medium">{warning.area || 'Flood Warning'}</div>
                      <div className="text-slate-400 text-xs mt-1 line-clamp-2">{warning.description}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sewage Incidents */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                  <AlertOctagon className="w-4 h-4 text-purple-400" />
                  Sewage Alerts ({sewageIncidents.filter(i => i.status === 'Discharging').length})
                </h3>
                <Switch
                  checked={showSewageLayer}
                  onCheckedChange={setShowSewageLayer}
                  data-testid="sewage-layer-toggle"
                />
              </div>
              {sewageIncidents.filter(i => i.status === 'Discharging').length > 0 ? (
                <div className="space-y-2">
                  {sewageIncidents.filter(i => i.status === 'Discharging').map((incident) => (
                    <button
                      key={incident.id}
                      onClick={() => incident.latitude && setMapCenter([incident.latitude, incident.longitude])}
                      className="w-full p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-left transition-colors hover:bg-red-500/20"
                      data-testid={`sewage-${incident.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-red-400 text-sm font-medium">{incident.site_name}</div>
                          <div className="text-slate-500 text-xs">{incident.water_company}</div>
                        </div>
                        <Badge variant="outline" className="border-red-500 text-red-400 animate-pulse">
                          Active
                        </Badge>
                      </div>
                      {incident.duration_hours && (
                        <div className="text-slate-500 text-xs mt-1">Duration: {incident.duration_hours}h</div>
                      )}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center">
                  <div className="text-emerald-400 text-sm">No active discharges</div>
                </div>
              )}
            </div>

            {/* Bathing Waters */}
            {bathingWaters.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Umbrella className="w-4 h-4 text-yellow-400" />
                  Bathing Waters ({bathingWaters.length})
                </h3>
                <div className="space-y-2">
                  {bathingWaters.slice(0, 5).map((beach) => (
                    <button
                      key={beach.id}
                      onClick={() => setMapCenter([beach.latitude, beach.longitude])}
                      className="w-full p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700 text-left transition-colors"
                      data-testid={`beach-${beach.id}`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="text-white text-sm font-medium truncate">{beach.name}</div>
                        <Badge 
                          variant="outline" 
                          className={`ml-2 ${
                            beach.classification === 'Excellent' ? 'border-emerald-500 text-emerald-400' :
                            beach.classification === 'Good' ? 'border-cyan-500 text-cyan-400' :
                            'border-yellow-500 text-yellow-400'
                          }`}
                        >
                          {beach.classification}
                        </Badge>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Favorites */}
            {user && favorites.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <Heart className="w-4 h-4 text-red-400" />
                  Favorites
                </h3>
                <div className="space-y-2">
                  {favorites.map((fav) => (
                    <button
                      key={fav.id}
                      onClick={() => {
                        const station = stations.find(s => s.station_id === fav.station_id);
                        if (station) {
                          handleStationClick(station);
                        } else {
                          setMapCenter([fav.latitude, fav.longitude]);
                        }
                      }}
                      className="w-full p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700 text-left transition-colors"
                      data-testid={`favorite-${fav.id}`}
                    >
                      <div className="text-white text-sm font-medium">{fav.station_name}</div>
                      {fav.river_name && (
                        <div className="text-slate-500 text-xs">{fav.river_name}</div>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Nearby Stations */}
            <div>
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                Monitoring Stations ({stations.length})
              </h3>
              <div className="space-y-2">
                {stations.slice(0, 10).map((station) => (
                  <button
                    key={station.station_id}
                    onClick={() => handleStationClick(station)}
                    className="w-full p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 border border-slate-700 text-left transition-colors"
                    data-testid={`station-item-${station.station_id}`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="text-white text-sm font-medium truncate">{station.label}</div>
                        {station.river_name && (
                          <div className="text-slate-500 text-xs truncate">{station.river_name}</div>
                        )}
                      </div>
                      <Badge 
                        variant="outline" 
                        className={`ml-2 ${
                          station.safety_score >= 8 ? 'border-emerald-500 text-emerald-400' :
                          station.safety_score >= 5 ? 'border-yellow-500 text-yellow-400' :
                          'border-orange-500 text-orange-400'
                        }`}
                      >
                        {station.safety_score}/10
                      </Badge>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </ScrollArea>

          {/* User Section */}
          <div className="p-4 border-t border-white/5">
            {user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800 transition-colors" data-testid="user-menu-trigger">
                    {user.picture ? (
                      <img src={user.picture} alt="" className="w-8 h-8 rounded-full" />
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center">
                        <User className="w-4 h-4 text-cyan-400" />
                      </div>
                    )}
                    <div className="flex-1 text-left">
                      <div className="text-white text-sm font-medium">{user.name}</div>
                      <div className="text-slate-500 text-xs truncate">{user.email}</div>
                    </div>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56 bg-slate-900 border-slate-700">
                  <DropdownMenuItem className="text-slate-300 focus:bg-slate-800 focus:text-white">
                    <User className="w-4 h-4 mr-2" />
                    Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    onClick={() => window.location.href = '/admin'}
                    className="text-slate-300 focus:bg-slate-800 focus:text-white"
                    data-testid="admin-link"
                  >
                    <ShieldCheck className="w-4 h-4 mr-2" />
                    Moderation Dashboard
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-slate-700" />
                  <DropdownMenuItem 
                    onClick={logout}
                    className="text-red-400 focus:bg-slate-800 focus:text-red-400"
                    data-testid="logout-btn"
                  >
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button 
                onClick={login}
                className="w-full bg-cyan-500 hover:bg-cyan-400 text-black font-bold"
                data-testid="sidebar-signin-btn"
              >
                Sign In
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Map Container */}
      <div className="flex-1 relative">
        {/* Toggle Sidebar Button */}
        {!sidebarOpen && !isMobile && (
          <Button
            variant="ghost"
            size="icon"
            className="absolute top-4 left-4 z-20 glass-card border-0"
            onClick={() => setSidebarOpen(true)}
            data-testid="open-sidebar-btn"
          >
            <Menu className="w-5 h-5 text-white" />
          </Button>
        )}

        {/* Loading State */}
        {loading && (
          <div className="absolute inset-0 z-30 bg-slate-950 flex items-center justify-center">
            <div className="text-center">
              <div className="spinner mx-auto mb-4"></div>
              <p className="text-slate-400">Loading water stations...</p>
            </div>
          </div>
        )}

        {/* Map */}
        <MapContainer
          center={defaultCenter}
          zoom={defaultZoom}
          style={{ height: '100%', width: '100%' }}
          zoomControl={true}
          attributionControl={true}
          data-testid="map-container"
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          />
          <MapController center={mapCenter} />
          {markers}
        </MapContainer>

        {/* Station Detail Panel */}
        {selectedStation && (
          <div 
            className={`absolute ${isMobile ? 'bottom-0 left-0 right-0 rounded-t-2xl max-h-[70vh]' : 'top-4 right-4 w-96'} glass-card rounded-xl overflow-hidden z-20 animate-slide-in-right`}
            data-testid="station-detail-panel"
          >
            <div className="p-4 border-b border-white/5">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h2 className="text-lg font-semibold text-white" style={{ fontFamily: 'Manrope' }}>
                    {selectedStation.label}
                  </h2>
                  {selectedStation.river_name && (
                    <p className="text-slate-400 text-sm">{selectedStation.river_name}</p>
                  )}
                  {selectedStation.town && (
                    <p className="text-slate-500 text-xs">{selectedStation.town}</p>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => generateShareReport(selectedStation)}
                    className="text-slate-400 hover:text-cyan-400"
                    data-testid="share-btn"
                  >
                    <Share2 className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setSelectedStation(null)}
                    className="text-slate-400 hover:text-white"
                    data-testid="close-detail-btn"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="w-full bg-slate-900/50 p-1 rounded-none border-b border-white/5">
                <TabsTrigger value="info" className="flex-1 data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400">
                  Info
                </TabsTrigger>
                <TabsTrigger value="weather" className="flex-1 data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400">
                  Weather
                </TabsTrigger>
                <TabsTrigger value="history" className="flex-1 data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400">
                  History
                </TabsTrigger>
              </TabsList>

              <TabsContent value="info" className="p-4 space-y-4 mt-0">
                {/* Safety Score */}
                <div className="flex items-center gap-4">
                  <SafetyRing score={selectedStation.safety_score} />
                  <div>
                    <div className="text-slate-400 text-sm">Safety Score</div>
                    <div className="text-white font-semibold">
                      {selectedStation.safety_score >= 8 ? 'Excellent' :
                       selectedStation.safety_score >= 5 ? 'Moderate' : 'Caution'}
                    </div>
                  </div>
                </div>

                {/* Status Grid */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700">
                    <div className="text-slate-500 text-xs mb-1">Pollution Risk</div>
                    <div className={`font-medium text-sm ${
                      selectedStation.pollution_risk === 'Low' ? 'text-emerald-400' :
                      selectedStation.pollution_risk === 'Moderate' ? 'text-yellow-400' :
                      'text-red-400'
                    }`}>
                      {selectedStation.pollution_risk}
                    </div>
                  </div>
                  <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700">
                    <div className="text-slate-500 text-xs mb-1">Flood Risk</div>
                    <div className={`font-medium text-sm ${
                      selectedStation.flood_risk === 'None' ? 'text-emerald-400' :
                      selectedStation.flood_risk === 'Low' ? 'text-yellow-400' :
                      'text-red-400'
                    }`}>
                      {selectedStation.flood_risk}
                    </div>
                  </div>
                </div>

                {/* AI Insight */}
                <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-4 h-4 text-purple-400" />
                    <span className="text-purple-400 text-sm font-medium">AI Safety Insight</span>
                  </div>
                  {loadingInsight ? (
                    <div className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 text-slate-400 animate-spin" />
                      <span className="text-slate-400 text-sm">Generating insight...</span>
                    </div>
                  ) : (
                    <p className="text-slate-300 text-sm">{aiInsight}</p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className={`flex-1 border-slate-700 ${
                      isFavorited(selectedStation.station_id) 
                        ? 'text-red-400 hover:text-red-300' 
                        : 'text-slate-300 hover:text-white'
                    }`}
                    onClick={() => toggleFavorite(selectedStation)}
                    data-testid="toggle-favorite-btn"
                  >
                    {isFavorited(selectedStation.station_id) ? (
                      <>
                        <HeartOff className="w-4 h-4 mr-2" />
                        Remove
                      </>
                    ) : (
                      <>
                        <Heart className="w-4 h-4 mr-2" />
                        Save
                      </>
                    )}
                  </Button>
                  <Button
                    className="flex-1 bg-cyan-500 hover:bg-cyan-400 text-black"
                    onClick={() => {
                      window.open(
                        `https://www.google.com/maps/dir/?api=1&destination=${selectedStation.latitude},${selectedStation.longitude}`,
                        '_blank'
                      );
                    }}
                    data-testid="get-directions-btn"
                  >
                    <Navigation className="w-4 h-4 mr-2" />
                    Directions
                  </Button>
                </div>

                {/* Community Report Button */}
                {user && (
                  <Button
                    variant="outline"
                    className="w-full border-slate-700 text-slate-300 hover:text-white mt-2"
                    onClick={() => setReportDialogOpen(true)}
                    data-testid="submit-report-btn"
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Submit Community Report
                  </Button>
                )}
              </TabsContent>

              <TabsContent value="weather" className="p-4 mt-0 space-y-4">
                {loadingWeather ? (
                  <div className="h-32 flex items-center justify-center">
                    <RefreshCw className="w-5 h-5 text-cyan-400 animate-spin" />
                  </div>
                ) : weatherData?.weather ? (
                  <>
                    {/* Current Weather */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="text-4xl">{weatherData.weather.weather_icon}</span>
                        <div>
                          <div className="text-2xl font-bold text-white font-mono">
                            {Math.round(weatherData.weather.temperature)}°C
                          </div>
                          <div className="text-slate-400 text-sm">
                            {weatherData.weather.weather_description}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-slate-400 text-xs">Feels like</div>
                        <div className="text-white font-mono">
                          {Math.round(weatherData.weather.feels_like)}°C
                        </div>
                      </div>
                    </div>

                    {/* Weather Stats */}
                    <div className="grid grid-cols-3 gap-2">
                      <div className="p-2 rounded-lg bg-slate-800/50 text-center">
                        <Wind className="w-4 h-4 text-cyan-400 mx-auto mb-1" />
                        <div className="text-white text-sm font-mono">{Math.round(weatherData.weather.wind_speed)}</div>
                        <div className="text-slate-500 text-xs">km/h</div>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-800/50 text-center">
                        <Droplets className="w-4 h-4 text-cyan-400 mx-auto mb-1" />
                        <div className="text-white text-sm font-mono">{weatherData.weather.humidity}%</div>
                        <div className="text-slate-500 text-xs">Humidity</div>
                      </div>
                      <div className="p-2 rounded-lg bg-slate-800/50 text-center">
                        <Sun className="w-4 h-4 text-yellow-400 mx-auto mb-1" />
                        <div className="text-white text-sm font-mono">{weatherData.weather.uv_index}</div>
                        <div className="text-slate-500 text-xs">UV Index</div>
                      </div>
                    </div>

                    {/* Activity Recommendation */}
                    <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                      <div className="flex items-center gap-2 mb-1">
                        <Activity className="w-4 h-4 text-cyan-400" />
                        <span className="text-cyan-400 text-sm font-medium">Activity Tip</span>
                      </div>
                      <p className="text-slate-300 text-sm">{weatherData.recommendation}</p>
                    </div>

                    {/* 3-Day Forecast */}
                    {weatherData.forecast?.length > 0 && (
                      <div>
                        <h4 className="text-sm font-semibold text-slate-400 mb-2">3-Day Forecast</h4>
                        <div className="grid grid-cols-3 gap-2">
                          {weatherData.forecast.map((day, index) => (
                            <div key={index} className="p-2 rounded-lg bg-slate-800/50 text-center">
                              <div className="text-slate-500 text-xs">
                                {index === 0 ? 'Today' : new Date(day.date).toLocaleDateString('en-GB', { weekday: 'short' })}
                              </div>
                              <div className="text-xl my-1">{day.weather_icon}</div>
                              <div className="text-white text-xs font-mono">
                                {Math.round(day.temp_max)}° / {Math.round(day.temp_min)}°
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center text-slate-500 py-8">
                    <Cloud className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>Weather data unavailable</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="history" className="p-4 mt-0">
                <h4 className="text-sm font-semibold text-slate-400 mb-3">7-Day Water Level History</h4>
                {loadingHistory ? (
                  <div className="h-32 flex items-center justify-center">
                    <RefreshCw className="w-5 h-5 text-cyan-400 animate-spin" />
                  </div>
                ) : (
                  <HistoryChart data={historyData.history} summary={historyData.summary} />
                )}
              </TabsContent>
            </Tabs>
          </div>
        )}
      </div>

      {/* Community Report Dialog */}
      <Dialog open={reportDialogOpen} onOpenChange={setReportDialogOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-cyan-400" />
              Submit Community Report
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Share your observations about water conditions at {selectedStation?.label}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 mb-2 block">Report Type</label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { value: 'observation', label: 'General', icon: Eye },
                  { value: 'pollution', label: 'Pollution', icon: AlertTriangle },
                  { value: 'wildlife', label: 'Wildlife', icon: Activity },
                  { value: 'safety', label: 'Safety', icon: ShieldCheck }
                ].map(({ value, label, icon: Icon }) => (
                  <button
                    key={value}
                    onClick={() => setNewReport({ ...newReport, report_type: value })}
                    className={`p-2 rounded-lg border flex items-center gap-2 transition-colors ${
                      newReport.report_type === value 
                        ? 'border-cyan-500 bg-cyan-500/10 text-cyan-400' 
                        : 'border-slate-700 text-slate-400 hover:border-slate-600'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm">{label}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-2 block">Rating</label>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setNewReport({ ...newReport, rating: star })}
                    className="p-1"
                  >
                    <Star className={`w-6 h-6 ${
                      star <= newReport.rating ? 'text-yellow-400 fill-yellow-400' : 'text-slate-600'
                    }`} />
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-2 block">Description</label>
              <Textarea
                value={newReport.description}
                onChange={(e) => setNewReport({ ...newReport, description: e.target.value })}
                placeholder="Describe current water conditions..."
                className="bg-slate-800 border-slate-700 text-white"
                rows={3}
              />
            </div>

            {/* Photo Upload */}
            <div>
              <label className="text-sm text-slate-400 mb-2 block">Add Photos (optional)</label>
              <div className="flex flex-wrap gap-2">
                {newReport.photos?.map((photo, index) => (
                  <div key={index} className="relative w-16 h-16">
                    <img src={photo} alt="" className="w-full h-full object-cover rounded-lg" />
                    <button
                      onClick={() => setNewReport({
                        ...newReport,
                        photos: newReport.photos.filter((_, i) => i !== index)
                      })}
                      className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center"
                    >
                      <X className="w-3 h-3 text-white" />
                    </button>
                  </div>
                ))}
                {(!newReport.photos || newReport.photos.length < 3) && (
                  <label className="w-16 h-16 border-2 border-dashed border-slate-600 rounded-lg flex items-center justify-center cursor-pointer hover:border-cyan-500 transition-colors">
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={async (e) => {
                        const file = e.target.files?.[0];
                        if (!file) return;
                        
                        const formData = new FormData();
                        formData.append('file', file);
                        
                        try {
                          const response = await fetch(`${API}/upload/photo`, {
                            method: 'POST',
                            credentials: 'include',
                            body: formData
                          });
                          
                          if (response.ok) {
                            const data = await response.json();
                            setNewReport({
                              ...newReport,
                              photos: [...(newReport.photos || []), `${BACKEND_URL}${data.url}`]
                            });
                            toast.success('Photo uploaded');
                          } else {
                            toast.error('Failed to upload photo');
                          }
                        } catch (error) {
                          toast.error('Upload failed');
                        }
                      }}
                    />
                    <span className="text-2xl text-slate-500">+</span>
                  </label>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-1">Max 3 photos, 5MB each</p>
            </div>

            <Button
              onClick={submitCommunityReport}
              className="w-full bg-cyan-500 hover:bg-cyan-400 text-black"
              disabled={!newReport.description}
            >
              <Send className="w-4 h-4 mr-2" />
              Submit Report
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Share Dialog */}
      <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Share2 className="w-5 h-5 text-cyan-400" />
              Share Safety Report
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Share this water safety report with friends and community
            </DialogDescription>
          </DialogHeader>
          
          {shareData && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                <pre className="text-sm text-slate-300 whitespace-pre-wrap font-mono">
                  {shareData.share_text}
                </pre>
              </div>
              
              <div className="flex gap-2">
                <Button
                  onClick={copyShareText}
                  className="flex-1 bg-slate-800 hover:bg-slate-700 text-white"
                  data-testid="copy-share-btn"
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4 mr-2 text-emerald-400" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4 mr-2" />
                      Copy
                    </>
                  )}
                </Button>
                <Button
                  onClick={() => window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareData.share_text.substring(0, 280))}`, '_blank')}
                  className="bg-[#1DA1F2] hover:bg-[#1a8cd8] text-white"
                  data-testid="share-twitter-btn"
                >
                  <Twitter className="w-4 h-4" />
                </Button>
                <Button
                  onClick={() => window.open(`https://www.facebook.com/sharer/sharer.php?quote=${encodeURIComponent(shareData.share_text.substring(0, 280))}`, '_blank')}
                  className="bg-[#4267B2] hover:bg-[#375695] text-white"
                  data-testid="share-facebook-btn"
                >
                  <Facebook className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

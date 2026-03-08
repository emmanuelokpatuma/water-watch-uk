import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Droplets,
  ArrowLeft,
  Search,
  MapPin,
  AlertTriangle,
  CheckCircle,
  Clock,
  Phone,
  Globe,
  Wrench,
  Droplet,
  ThermometerSun,
  Send,
  RefreshCw,
  Home,
  AlertOctagon,
  Calendar,
  Users,
  ExternalLink,
  Info,
  Shield,
  Waves
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function HomeWater() {
  const { user } = useAuth();
  const [postcode, setPostcode] = useState('');
  const [searchedPostcode, setSearchedPostcode] = useState('');
  const [loading, setLoading] = useState(false);
  const [incidents, setIncidents] = useState([]);
  const [incidentSummary, setIncidentSummary] = useState(null);
  const [waterQuality, setWaterQuality] = useState(null);
  const [plannedWorks, setPlannedWorks] = useState([]);
  const [companyInfo, setCompanyInfo] = useState(null);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [myIssues, setMyIssues] = useState([]);
  const [newIssue, setNewIssue] = useState({
    issue_type: '',
    description: '',
    severity: 3,
    address: ''
  });
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch data for postcode
  const searchPostcode = async () => {
    if (!postcode || postcode.length < 3) {
      toast.error('Please enter a valid postcode');
      return;
    }

    setLoading(true);
    setSearchedPostcode(postcode.toUpperCase());

    try {
      // Fetch all data in parallel
      const [incidentsRes, qualityRes, worksRes, companyRes] = await Promise.all([
        fetch(`${API}/home-water/incidents?postcode=${encodeURIComponent(postcode)}`),
        fetch(`${API}/home-water/quality?postcode=${encodeURIComponent(postcode)}`),
        fetch(`${API}/home-water/planned-works?postcode=${encodeURIComponent(postcode)}`),
        fetch(`${API}/home-water/company-info?postcode=${encodeURIComponent(postcode)}`)
      ]);

      if (incidentsRes.ok) {
        const data = await incidentsRes.json();
        setIncidents(data.incidents || []);
        setIncidentSummary(data.summary);
      }

      if (qualityRes.ok) {
        const data = await qualityRes.json();
        setWaterQuality(data);
      }

      if (worksRes.ok) {
        const data = await worksRes.json();
        setPlannedWorks(data.planned_works || []);
      }

      if (companyRes.ok) {
        const data = await companyRes.json();
        setCompanyInfo(data);
      }

      toast.success(`Found water information for ${postcode.toUpperCase()}`);
    } catch (error) {
      console.error('Error fetching water data:', error);
      toast.error('Failed to fetch water data');
    } finally {
      setLoading(false);
    }
  };

  // Fetch user's reported issues
  const fetchMyIssues = useCallback(async () => {
    if (!user) return;
    try {
      const response = await fetch(`${API}/home-water/my-issues`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setMyIssues(data.issues || []);
      }
    } catch (error) {
      console.error('Error fetching my issues:', error);
    }
  }, [user]);

  useEffect(() => {
    fetchMyIssues();
  }, [fetchMyIssues]);

  // Submit issue report
  const submitIssue = async () => {
    if (!user) {
      toast.error('Please sign in to report an issue');
      return;
    }

    if (!newIssue.issue_type || !newIssue.description || !searchedPostcode) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      const response = await fetch(`${API}/home-water/report-issue`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          ...newIssue,
          postcode: searchedPostcode
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Issue reported! Reference: ${data.reference}`);
        setReportDialogOpen(false);
        setNewIssue({ issue_type: '', description: '', severity: 3, address: '' });
        fetchMyIssues();
      } else {
        toast.error('Failed to report issue');
      }
    } catch (error) {
      toast.error('Failed to report issue');
    }
  };

  // Get incident type icon and color
  const getIncidentStyle = (type) => {
    switch (type) {
      case 'pipe_burst':
        return { icon: <AlertOctagon className="w-5 h-5" />, color: 'text-red-400', bg: 'bg-red-500/10' };
      case 'supply_interruption':
        return { icon: <Droplet className="w-5 h-5" />, color: 'text-orange-400', bg: 'bg-orange-500/10' };
      case 'low_pressure':
        return { icon: <Waves className="w-5 h-5" />, color: 'text-yellow-400', bg: 'bg-yellow-500/10' };
      case 'discoloured_water':
        return { icon: <Droplets className="w-5 h-5" />, color: 'text-amber-400', bg: 'bg-amber-500/10' };
      case 'planned_works':
        return { icon: <Wrench className="w-5 h-5" />, color: 'text-cyan-400', bg: 'bg-cyan-500/10' };
      default:
        return { icon: <AlertTriangle className="w-5 h-5" />, color: 'text-slate-400', bg: 'bg-slate-500/10' };
    }
  };

  // Get status badge
  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return <Badge variant="outline" className="border-red-500 text-red-400">Active</Badge>;
      case 'resolved':
        return <Badge variant="outline" className="border-emerald-500 text-emerald-400">Resolved</Badge>;
      case 'planned':
        return <Badge variant="outline" className="border-cyan-500 text-cyan-400">Planned</Badge>;
      default:
        return <Badge variant="outline" className="border-slate-500 text-slate-400">{status}</Badge>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950" data-testid="home-water">
      {/* Header */}
      <header className="glass-card border-0 border-b border-white/5 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link to="/dashboard" className="text-slate-400 hover:text-white">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div className="flex items-center gap-2">
                <Home className="w-6 h-6 text-cyan-400" />
                <span className="font-bold text-lg text-white" style={{ fontFamily: 'Manrope' }}>
                  Home Water Supply
                </span>
              </div>
            </div>
            <Link to="/dashboard">
              <Button variant="ghost" className="text-slate-400 hover:text-white">
                <Droplets className="w-4 h-4 mr-2" />
                Back to Map
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section */}
        <div className="glass-card p-6 mb-8">
          <h2 className="text-xl font-semibold text-white mb-4" style={{ fontFamily: 'Manrope' }}>
            Check Your Water Supply
          </h2>
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
              <Input
                type="text"
                placeholder="Enter your postcode (e.g., SW1A 1AA)"
                value={postcode}
                onChange={(e) => setPostcode(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchPostcode()}
                className="pl-10 bg-slate-900/50 border-slate-700 text-white placeholder:text-slate-500 h-12 text-lg"
                data-testid="postcode-input"
              />
            </div>
            <Button
              onClick={searchPostcode}
              disabled={loading}
              className="bg-cyan-500 hover:bg-cyan-400 text-black h-12 px-8"
              data-testid="search-btn"
            >
              {loading ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Search className="w-5 h-5 mr-2" />
                  Check
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Results */}
        {searchedPostcode && (
          <div className="space-y-6">
            {/* Water Company Info Card */}
            {companyInfo && (
              <div className="glass-card p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">{companyInfo.name}</h3>
                    <p className="text-slate-400 mb-4">{companyInfo.coverage || 'Your local water supplier'}</p>
                    <div className="flex flex-wrap gap-4">
                      <a
                        href={`tel:${companyInfo.phone}`}
                        className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300"
                      >
                        <Phone className="w-4 h-4" />
                        {companyInfo.phone}
                      </a>
                      {companyInfo.emergency && (
                        <a
                          href={`tel:${companyInfo.emergency}`}
                          className="flex items-center gap-2 text-red-400 hover:text-red-300"
                        >
                          <AlertTriangle className="w-4 h-4" />
                          Emergency: {companyInfo.emergency}
                        </a>
                      )}
                      {companyInfo.website && (
                        <a
                          href={companyInfo.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 text-slate-400 hover:text-white"
                        >
                          <Globe className="w-4 h-4" />
                          Website
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>
                  <Button
                    onClick={() => setReportDialogOpen(true)}
                    className="bg-orange-500 hover:bg-orange-400 text-white"
                    data-testid="report-issue-btn"
                  >
                    <AlertTriangle className="w-4 h-4 mr-2" />
                    Report Issue
                  </Button>
                </div>
              </div>
            )}

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="glass-card">
              <TabsList className="w-full bg-slate-900/50 p-1 rounded-t-lg border-b border-white/5">
                <TabsTrigger value="overview" className="flex-1 data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400">
                  <Home className="w-4 h-4 mr-2" />
                  Overview
                </TabsTrigger>
                <TabsTrigger value="quality" className="flex-1 data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400">
                  <Shield className="w-4 h-4 mr-2" />
                  Water Quality
                </TabsTrigger>
                <TabsTrigger value="incidents" className="flex-1 data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400">
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  Incidents
                </TabsTrigger>
                <TabsTrigger value="works" className="flex-1 data-[state=active]:bg-cyan-500/20 data-[state=active]:text-cyan-400">
                  <Wrench className="w-4 h-4 mr-2" />
                  Planned Works
                </TabsTrigger>
              </TabsList>

              {/* Overview Tab */}
              <TabsContent value="overview" className="p-6 mt-0">
                <div className="grid md:grid-cols-3 gap-6">
                  {/* Current Status */}
                  <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                    <div className="flex items-center gap-3 mb-3">
                      {incidentSummary?.active > 0 ? (
                        <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
                          <AlertTriangle className="w-5 h-5 text-red-400" />
                        </div>
                      ) : (
                        <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
                          <CheckCircle className="w-5 h-5 text-emerald-400" />
                        </div>
                      )}
                      <div>
                        <div className="text-lg font-semibold text-white">
                          {incidentSummary?.active > 0 ? `${incidentSummary.active} Active Issue${incidentSummary.active > 1 ? 's' : ''}` : 'All Clear'}
                        </div>
                        <div className="text-slate-400 text-sm">Current Status</div>
                      </div>
                    </div>
                  </div>

                  {/* Water Quality */}
                  <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-full bg-cyan-500/20 flex items-center justify-center">
                        <Droplets className="w-5 h-5 text-cyan-400" />
                      </div>
                      <div>
                        <div className="text-lg font-semibold text-white">
                          {waterQuality?.quality_rating || 'Good'}
                        </div>
                        <div className="text-slate-400 text-sm">Water Quality</div>
                      </div>
                    </div>
                  </div>

                  {/* Planned Works */}
                  <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center">
                        <Wrench className="w-5 h-5 text-yellow-400" />
                      </div>
                      <div>
                        <div className="text-lg font-semibold text-white">
                          {plannedWorks.length} Planned
                        </div>
                        <div className="text-slate-400 text-sm">Upcoming Works</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Active Incidents Summary */}
                {incidents.filter(i => i.status === 'active').length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
                      Active Issues in Your Area
                    </h4>
                    <div className="space-y-3">
                      {incidents.filter(i => i.status === 'active').map((incident) => {
                        const style = getIncidentStyle(incident.incident_type);
                        return (
                          <div
                            key={incident.id}
                            className={`p-4 rounded-lg ${style.bg} border border-white/5`}
                          >
                            <div className="flex items-start gap-3">
                              <div className={style.color}>{style.icon}</div>
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className={`font-medium ${style.color}`}>
                                    {incident.incident_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                                  </span>
                                  {getStatusBadge(incident.status)}
                                </div>
                                <p className="text-slate-300 text-sm">{incident.description}</p>
                                {incident.estimated_restore && (
                                  <p className="text-slate-500 text-xs mt-2">
                                    <Clock className="w-3 h-3 inline mr-1" />
                                    Estimated restore: {new Date(incident.estimated_restore).toLocaleString()}
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </TabsContent>

              {/* Water Quality Tab */}
              <TabsContent value="quality" className="p-6 mt-0">
                {waterQuality ? (
                  <div className="space-y-6">
                    <div className="flex items-center gap-4">
                      <div className={`w-16 h-16 rounded-full flex items-center justify-center ${
                        waterQuality.quality_rating === 'Excellent' ? 'bg-emerald-500/20' :
                        waterQuality.quality_rating === 'Good' ? 'bg-cyan-500/20' : 'bg-yellow-500/20'
                      }`}>
                        <Shield className={`w-8 h-8 ${
                          waterQuality.quality_rating === 'Excellent' ? 'text-emerald-400' :
                          waterQuality.quality_rating === 'Good' ? 'text-cyan-400' : 'text-yellow-400'
                        }`} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="text-xl font-semibold text-white">{waterQuality.quality_rating}</h3>
                          {waterQuality.data_source === 'Environment Agency' && (
                            <Badge variant="outline" className="border-cyan-500 text-cyan-400">
                              Live Data
                            </Badge>
                          )}
                        </div>
                        <p className="text-slate-400">{waterQuality.notes}</p>
                        {waterQuality.sampling_points_nearby > 0 && (
                          <p className="text-slate-500 text-sm mt-1">
                            Based on {waterQuality.sampling_points_nearby} monitoring points nearby
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Data Source Info */}
                    <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                      <div className="flex items-start gap-2">
                        <Info className="w-4 h-4 text-cyan-400 mt-0.5" />
                        <div className="text-sm">
                          <span className="text-cyan-400 font-medium">Data Source: </span>
                          <span className="text-slate-300">{waterQuality.data_source}</span>
                          {waterQuality.last_tested && (
                            <span className="text-slate-500"> • Last tested: {new Date(waterQuality.last_tested).toLocaleDateString()}</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
                        Water Parameters
                      </h4>
                      <div className="grid md:grid-cols-2 gap-4">
                        {Object.entries(waterQuality.parameters || {}).map(([key, param]) => (
                          <div
                            key={key}
                            className="p-4 rounded-lg bg-slate-800/50 border border-slate-700"
                          >
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-white font-medium capitalize">{key.replace(/_/g, ' ')}</span>
                              <Badge
                                variant="outline"
                                className={
                                  param.status === 'safe' || param.status === 'normal' || param.status === 'good'
                                    ? 'border-emerald-500 text-emerald-400'
                                    : param.status === 'elevated' || param.status === 'check' || param.status === 'low'
                                    ? 'border-orange-500 text-orange-400'
                                    : 'border-yellow-500 text-yellow-400'
                                }
                              >
                                {param.status?.replace(/_/g, ' ')}
                              </Badge>
                            </div>
                            <div className="text-2xl font-mono text-cyan-400">
                              {param.value !== null ? param.value : 'N/A'} <span className="text-sm text-slate-500">{param.unit}</span>
                            </div>
                            {param.limit && (
                              <div className="text-xs text-slate-500 mt-1">
                                Limit: {param.limit} {param.unit}
                              </div>
                            )}
                            {param.range && (
                              <div className="text-xs text-slate-500 mt-1">
                                Safe range: {param.range}
                              </div>
                            )}
                            {param.description && (
                              <div className="text-xs text-slate-400 mt-1">{param.description}</div>
                            )}
                            {param.source && (
                              <div className="text-xs text-slate-600 mt-1">Source: {param.source}</div>
                            )}
                            {param.measured && (
                              <div className="text-xs text-slate-600 mt-1">
                                Measured: {new Date(param.measured).toLocaleDateString()}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700">
                      <h4 className="text-sm font-semibold text-slate-400 mb-2">Water Source & Treatment</h4>
                      <p className="text-white mb-2">Source: {waterQuality.source}</p>
                      <p className="text-slate-400 mb-2">Provider: {waterQuality.water_company}</p>
                      <div className="flex flex-wrap gap-2">
                        {waterQuality.treatment?.map((t, i) => (
                          <Badge key={i} variant="outline" className="border-slate-600 text-slate-300">
                            {t}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Meets Standards Badge */}
                    <div className={`p-4 rounded-lg border ${
                      waterQuality.meets_standards 
                        ? 'bg-emerald-500/10 border-emerald-500/30' 
                        : 'bg-orange-500/10 border-orange-500/30'
                    }`}>
                      <div className="flex items-center gap-3">
                        {waterQuality.meets_standards ? (
                          <CheckCircle className="w-6 h-6 text-emerald-400" />
                        ) : (
                          <AlertTriangle className="w-6 h-6 text-orange-400" />
                        )}
                        <div>
                          <p className={`font-medium ${waterQuality.meets_standards ? 'text-emerald-400' : 'text-orange-400'}`}>
                            {waterQuality.meets_standards 
                              ? 'Meets UK Drinking Water Standards' 
                              : 'Some Parameters Need Attention'}
                          </p>
                          <p className="text-slate-400 text-sm">
                            Based on Drinking Water Inspectorate guidelines
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-slate-500 py-8">
                    <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p>Water quality data not available</p>
                  </div>
                )}
              </TabsContent>

              {/* Incidents Tab */}
              <TabsContent value="incidents" className="p-6 mt-0">
                {incidents.length > 0 ? (
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-4">
                      {incidents.map((incident) => {
                        const style = getIncidentStyle(incident.incident_type);
                        return (
                          <div
                            key={incident.id}
                            className="p-4 rounded-lg bg-slate-800/50 border border-slate-700"
                          >
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg ${style.bg}`}>
                                  <span className={style.color}>{style.icon}</span>
                                </div>
                                <div>
                                  <div className="text-white font-medium">
                                    {incident.incident_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                                  </div>
                                  <div className="text-slate-500 text-sm">{incident.area}</div>
                                </div>
                              </div>
                              {getStatusBadge(incident.status)}
                            </div>
                            <p className="text-slate-300 text-sm mb-3">{incident.description}</p>
                            <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                              <span className="flex items-center gap-1">
                                <Users className="w-3 h-3" />
                                {incident.affected_properties} properties
                              </span>
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                Started: {new Date(incident.start_time).toLocaleString()}
                              </span>
                              {incident.estimated_restore && (
                                <span className="flex items-center gap-1">
                                  <Calendar className="w-3 h-3" />
                                  Est. restore: {new Date(incident.estimated_restore).toLocaleString()}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="text-center text-slate-500 py-8">
                    <CheckCircle className="w-8 h-8 mx-auto mb-2 text-emerald-400" />
                    <p className="text-emerald-400">No incidents in your area</p>
                  </div>
                )}
              </TabsContent>

              {/* Planned Works Tab */}
              <TabsContent value="works" className="p-6 mt-0">
                {plannedWorks.length > 0 ? (
                  <div className="space-y-4">
                    {plannedWorks.map((work) => (
                      <div
                        key={work.id}
                        className="p-4 rounded-lg bg-slate-800/50 border border-slate-700"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="p-2 rounded-lg bg-cyan-500/10">
                              <Wrench className="w-5 h-5 text-cyan-400" />
                            </div>
                            <div>
                              <div className="text-white font-medium">
                                {work.work_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                              </div>
                              <div className="text-slate-500 text-sm">{work.area}</div>
                            </div>
                          </div>
                          <Badge variant="outline" className="border-cyan-500 text-cyan-400">
                            Scheduled
                          </Badge>
                        </div>
                        <p className="text-slate-300 text-sm mb-3">{work.description}</p>
                        <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {work.start_date} to {work.end_date}
                          </span>
                          <span className="flex items-center gap-1">
                            <Info className="w-3 h-3" />
                            Impact: {work.impact}
                          </span>
                        </div>
                        {work.affected_postcodes?.length > 0 && (
                          <div className="flex flex-wrap gap-2 mt-3">
                            {work.affected_postcodes.map((pc, i) => (
                              <Badge key={i} variant="outline" className="border-slate-600 text-slate-400">
                                {pc}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center text-slate-500 py-8">
                    <CheckCircle className="w-8 h-8 mx-auto mb-2 text-emerald-400" />
                    <p className="text-emerald-400">No planned works in your area</p>
                  </div>
                )}
              </TabsContent>
            </Tabs>

            {/* My Reported Issues */}
            {user && myIssues.length > 0 && (
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">My Reported Issues</h3>
                <div className="space-y-3">
                  {myIssues.slice(0, 3).map((issue) => (
                    <div
                      key={issue.id}
                      className="p-3 rounded-lg bg-slate-800/50 border border-slate-700 flex items-center justify-between"
                    >
                      <div>
                        <div className="text-white text-sm">
                          {issue.issue_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                        </div>
                        <div className="text-slate-500 text-xs">
                          {issue.postcode} • {new Date(issue.created_at).toLocaleDateString()}
                        </div>
                      </div>
                      <Badge variant="outline" className="border-yellow-500 text-yellow-400">
                        {issue.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!searchedPostcode && (
          <div className="text-center py-16">
            <Home className="w-16 h-16 text-slate-700 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">Check Your Home Water Supply</h3>
            <p className="text-slate-400 max-w-md mx-auto">
              Enter your postcode above to check for supply issues, water quality,
              and planned maintenance in your area.
            </p>
          </div>
        )}
      </div>

      {/* Report Issue Dialog */}
      <Dialog open={reportDialogOpen} onOpenChange={setReportDialogOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-orange-400" />
              Report Water Issue
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Report a problem with your water supply at {searchedPostcode}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 mb-2 block">Issue Type *</label>
              <Select
                value={newIssue.issue_type}
                onValueChange={(v) => setNewIssue({ ...newIssue, issue_type: v })}
              >
                <SelectTrigger className="bg-slate-800 border-slate-700 text-white">
                  <SelectValue placeholder="Select issue type" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-700">
                  <SelectItem value="no_water">No Water Supply</SelectItem>
                  <SelectItem value="low_pressure">Low Pressure</SelectItem>
                  <SelectItem value="discoloured">Discoloured Water</SelectItem>
                  <SelectItem value="taste_smell">Taste or Smell Issue</SelectItem>
                  <SelectItem value="leak">External Leak</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-2 block">Address (optional)</label>
              <Input
                value={newIssue.address}
                onChange={(e) => setNewIssue({ ...newIssue, address: e.target.value })}
                placeholder="Your street address"
                className="bg-slate-800 border-slate-700 text-white"
              />
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-2 block">Severity</label>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((level) => (
                  <button
                    key={level}
                    onClick={() => setNewIssue({ ...newIssue, severity: level })}
                    className={`flex-1 p-2 rounded border transition-colors ${
                      newIssue.severity === level
                        ? 'border-orange-500 bg-orange-500/10 text-orange-400'
                        : 'border-slate-700 text-slate-500 hover:border-slate-600'
                    }`}
                  >
                    {level}
                  </button>
                ))}
              </div>
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>Minor</span>
                <span>Severe</span>
              </div>
            </div>

            <div>
              <label className="text-sm text-slate-400 mb-2 block">Description *</label>
              <Textarea
                value={newIssue.description}
                onChange={(e) => setNewIssue({ ...newIssue, description: e.target.value })}
                placeholder="Describe the issue you're experiencing..."
                className="bg-slate-800 border-slate-700 text-white"
                rows={3}
              />
            </div>

            <Button
              onClick={submitIssue}
              className="w-full bg-orange-500 hover:bg-orange-400 text-white"
              disabled={!newIssue.issue_type || !newIssue.description}
            >
              <Send className="w-4 h-4 mr-2" />
              Submit Report
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

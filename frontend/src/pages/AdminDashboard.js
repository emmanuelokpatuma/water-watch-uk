import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Droplets,
  ArrowLeft,
  CheckCircle,
  XCircle,
  Clock,
  Trash2,
  Eye,
  MapPin,
  Star,
  User,
  Calendar,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Users,
  Bell,
  Heart,
  AlertTriangle,
  Image
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
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

export default function AdminDashboard() {
  const { user, loading: authLoading } = useAuth();
  const [reports, setReports] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedReport, setSelectedReport] = useState(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);

  // Fetch reports
  const fetchReports = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API}/admin/reports?status=${statusFilter}&page=${page}&limit=10`,
        { credentials: 'include' }
      );
      if (response.ok) {
        const data = await response.json();
        setReports(data.reports || []);
        setTotalPages(data.pages || 1);
      }
    } catch (error) {
      console.error('Error fetching reports:', error);
      toast.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, page]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API}/admin/stats`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, []);

  useEffect(() => {
    if (user) {
      fetchReports();
      fetchStats();
    }
  }, [user, fetchReports, fetchStats]);

  // Moderate report
  const moderateReport = async (reportId, newStatus) => {
    try {
      const response = await fetch(`${API}/admin/reports/${reportId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        toast.success(`Report ${newStatus}`);
        fetchReports();
        fetchStats();
        setPreviewDialogOpen(false);
      } else {
        toast.error('Failed to update report');
      }
    } catch (error) {
      toast.error('Failed to update report');
    }
  };

  // Delete report
  const deleteReport = async (reportId) => {
    if (!confirm('Are you sure you want to delete this report?')) return;

    try {
      const response = await fetch(`${API}/admin/reports/${reportId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        toast.success('Report deleted');
        fetchReports();
        fetchStats();
      } else {
        toast.error('Failed to delete report');
      }
    } catch (error) {
      toast.error('Failed to delete report');
    }
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'border-emerald-500 text-emerald-400';
      case 'rejected': return 'border-red-500 text-red-400';
      default: return 'border-yellow-500 text-yellow-400';
    }
  };

  // Get report type icon
  const getReportTypeIcon = (type) => {
    switch (type) {
      case 'pollution': return <AlertTriangle className="w-4 h-4 text-red-400" />;
      case 'wildlife': return <Eye className="w-4 h-4 text-emerald-400" />;
      case 'safety': return <AlertTriangle className="w-4 h-4 text-orange-400" />;
      default: return <Eye className="w-4 h-4 text-cyan-400" />;
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">Access Denied</h1>
          <p className="text-slate-400 mb-4">Please sign in to access the admin dashboard</p>
          <Link to="/dashboard">
            <Button className="bg-cyan-500 hover:bg-cyan-400 text-black">
              Go to Dashboard
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950" data-testid="admin-dashboard">
      {/* Header */}
      <header className="glass-card border-0 border-b border-white/5 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link to="/dashboard" className="text-slate-400 hover:text-white">
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div className="flex items-center gap-2">
                <Droplets className="w-6 h-6 text-cyan-400" />
                <span className="font-bold text-lg text-white" style={{ fontFamily: 'Manrope' }}>
                  Admin Dashboard
                </span>
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => { fetchReports(); fetchStats(); }}
              className="text-slate-400 hover:text-white"
            >
              <RefreshCw className="w-5 h-5" />
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="glass-card p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-yellow-500/20 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-yellow-400" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">{stats.reports.pending}</div>
                  <div className="text-slate-500 text-sm">Pending</div>
                </div>
              </div>
            </div>
            <div className="glass-card p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">{stats.reports.approved}</div>
                  <div className="text-slate-500 text-sm">Approved</div>
                </div>
              </div>
            </div>
            <div className="glass-card p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                  <Users className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">{stats.users.total}</div>
                  <div className="text-slate-500 text-sm">Users</div>
                </div>
              </div>
            </div>
            <div className="glass-card p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <Bell className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">{stats.users.with_push}</div>
                  <div className="text-slate-500 text-sm">Push Subscribers</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Reports Section */}
        <div className="glass-card">
          <div className="p-4 border-b border-white/5">
            <h2 className="text-lg font-semibold text-white" style={{ fontFamily: 'Manrope' }}>
              Community Reports
            </h2>
          </div>

          {/* Status Tabs */}
          <Tabs value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }} className="w-full">
            <TabsList className="w-full bg-slate-900/50 p-1 rounded-none border-b border-white/5">
              <TabsTrigger 
                value="pending" 
                className="flex-1 data-[state=active]:bg-yellow-500/20 data-[state=active]:text-yellow-400"
              >
                <Clock className="w-4 h-4 mr-2" />
                Pending
              </TabsTrigger>
              <TabsTrigger 
                value="approved" 
                className="flex-1 data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Approved
              </TabsTrigger>
              <TabsTrigger 
                value="rejected" 
                className="flex-1 data-[state=active]:bg-red-500/20 data-[state=active]:text-red-400"
              >
                <XCircle className="w-4 h-4 mr-2" />
                Rejected
              </TabsTrigger>
            </TabsList>

            <TabsContent value={statusFilter} className="mt-0">
              {loading ? (
                <div className="p-8 text-center">
                  <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin mx-auto" />
                </div>
              ) : reports.length === 0 ? (
                <div className="p-8 text-center text-slate-500">
                  No {statusFilter} reports
                </div>
              ) : (
                <ScrollArea className="h-[500px]">
                  <div className="divide-y divide-white/5">
                    {reports.map((report) => (
                      <div
                        key={report.id}
                        className="p-4 hover:bg-slate-800/50 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              {getReportTypeIcon(report.report_type)}
                              <span className="text-white font-medium capitalize">
                                {report.report_type}
                              </span>
                              <Badge variant="outline" className={getStatusColor(report.status)}>
                                {report.status}
                              </Badge>
                            </div>
                            
                            <div className="flex items-center gap-2 text-sm text-slate-400 mb-2">
                              <MapPin className="w-4 h-4" />
                              <span>{report.location_name}</span>
                            </div>

                            <p className="text-slate-300 text-sm line-clamp-2 mb-2">
                              {report.description}
                            </p>

                            <div className="flex items-center gap-4 text-xs text-slate-500">
                              <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                {report.user_name}
                              </span>
                              <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {new Date(report.created_at).toLocaleDateString()}
                              </span>
                              <span className="flex items-center gap-1">
                                {[...Array(5)].map((_, i) => (
                                  <Star
                                    key={i}
                                    className={`w-3 h-3 ${
                                      i < report.rating ? 'text-yellow-400 fill-yellow-400' : 'text-slate-600'
                                    }`}
                                  />
                                ))}
                              </span>
                              {report.photos?.length > 0 && (
                                <span className="flex items-center gap-1">
                                  <Image className="w-3 h-3" />
                                  {report.photos.length} photo(s)
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => { setSelectedReport(report); setPreviewDialogOpen(true); }}
                              className="text-slate-400 hover:text-white"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            {report.status === 'pending' && (
                              <>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => moderateReport(report.id, 'approved')}
                                  className="text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                                >
                                  <CheckCircle className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => moderateReport(report.id, 'rejected')}
                                  className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                                >
                                  <XCircle className="w-4 h-4" />
                                </Button>
                              </>
                            )}
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => deleteReport(report.id)}
                              className="text-slate-400 hover:text-red-400 hover:bg-red-500/10"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              )}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="p-4 border-t border-white/5 flex items-center justify-between">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="border-slate-700"
                  >
                    <ChevronLeft className="w-4 h-4 mr-1" />
                    Previous
                  </Button>
                  <span className="text-slate-400 text-sm">
                    Page {page} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="border-slate-700"
                  >
                    Next
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Report Preview Dialog */}
      <Dialog open={previewDialogOpen} onOpenChange={setPreviewDialogOpen}>
        <DialogContent className="bg-slate-900 border-slate-700 text-white max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedReport && getReportTypeIcon(selectedReport.report_type)}
              Report Details
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              Review and moderate this community report
            </DialogDescription>
          </DialogHeader>

          {selectedReport && (
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-500 mb-1">Location</div>
                <div className="flex items-center gap-2 text-white">
                  <MapPin className="w-4 h-4 text-cyan-400" />
                  {selectedReport.location_name}
                </div>
              </div>

              <div>
                <div className="text-sm text-slate-500 mb-1">Description</div>
                <p className="text-slate-300">{selectedReport.description}</p>
              </div>

              <div className="flex items-center gap-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">Rating</div>
                  <div className="flex gap-1">
                    {[...Array(5)].map((_, i) => (
                      <Star
                        key={i}
                        className={`w-5 h-5 ${
                          i < selectedReport.rating ? 'text-yellow-400 fill-yellow-400' : 'text-slate-600'
                        }`}
                      />
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">Submitted by</div>
                  <div className="text-white">{selectedReport.user_name}</div>
                </div>
              </div>

              {selectedReport.photos?.length > 0 && (
                <div>
                  <div className="text-sm text-slate-500 mb-2">Photos</div>
                  <div className="flex gap-2 flex-wrap">
                    {selectedReport.photos.map((photo, index) => (
                      <img
                        key={index}
                        src={photo}
                        alt={`Report photo ${index + 1}`}
                        className="w-24 h-24 object-cover rounded-lg border border-slate-700"
                      />
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-4">
                {selectedReport.status === 'pending' ? (
                  <>
                    <Button
                      onClick={() => moderateReport(selectedReport.id, 'approved')}
                      className="flex-1 bg-emerald-500 hover:bg-emerald-400 text-white"
                    >
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Approve
                    </Button>
                    <Button
                      onClick={() => moderateReport(selectedReport.id, 'rejected')}
                      className="flex-1 bg-red-500 hover:bg-red-400 text-white"
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      Reject
                    </Button>
                  </>
                ) : (
                  <Button
                    onClick={() => moderateReport(selectedReport.id, 'pending')}
                    variant="outline"
                    className="flex-1 border-slate-700"
                  >
                    <Clock className="w-4 h-4 mr-2" />
                    Move to Pending
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

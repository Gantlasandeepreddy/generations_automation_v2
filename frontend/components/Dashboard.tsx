'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { AutomationRun, getAutomationHistory, getDownloadUrl, getRunLogs, deleteRun } from '../lib/api';

interface LogEntry {
  timestamp: string;
  message: string;
}

type SortKey = 'run_id' | 'type' | 'status' | 'user_email' | 'start_time' | 'clients_processed' | 'file_size';
type SortDirection = 'asc' | 'desc';

export default function Dashboard() {
  const { data: session } = useSession();
  const [runs, setRuns] = useState<AutomationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [deleteConfirmRunId, setDeleteConfirmRunId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [sortKey, setSortKey] = useState<SortKey>('start_time');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [filters, setFilters] = useState({
    type: '',
    status: '',
    user_email: '',
  });

  useEffect(() => {
    if (session?.accessToken) {
      loadHistory();
    }
  }, [session]);

  const loadHistory = async () => {
    if (!session?.accessToken) return;

    try {
      setLoading(true);
      const history = await getAutomationHistory(session.accessToken);
      setRuns(history);
      setError('');
    } catch (err) {
      setError('Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  const viewLogs = async (runId: string) => {
    if (!session?.accessToken) return;

    try {
      setSelectedRunId(runId);
      setLogsLoading(true);
      const logsData = await getRunLogs(session.accessToken, runId);
      setLogs(logsData.logs);
    } catch (err) {
      console.error('Failed to load logs:', err);
      setLogs([]);
    } finally {
      setLogsLoading(false);
    }
  };

  const closeLogs = () => {
    setSelectedRunId(null);
    setLogs([]);
  };

  const downloadFile = async (runId: string) => {
    if (!session?.accessToken) return;

    try {
      const response = await fetch(getDownloadUrl(runId), {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to download file');
      }

      // Get the blob and create download link
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `automation_${runId}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download file:', err);
      alert('Failed to download file. Please try again.');
    }
  };

  const handleDeleteRun = (runId: string) => {
    setDeleteConfirmRunId(runId);
  };

  const confirmDelete = async () => {
    if (!session?.accessToken || !deleteConfirmRunId) return;

    setDeleting(true);

    try {
      await deleteRun(session.accessToken, deleteConfirmRunId);

      // Reload the history to reflect changes
      await loadHistory();

      // Close modal
      setDeleteConfirmRunId(null);
    } catch (err) {
      console.error('Failed to delete run:', err);
      alert(`Failed to delete run: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setDeleting(false);
    }
  };

  const cancelDelete = () => {
    setDeleteConfirmRunId(null);
  };

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleString();
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return 'N/A';
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection('asc');
    }
  };

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const getFilteredAndSortedRuns = () => {
    let filtered = [...runs];

    // Apply filters
    if (filters.type) {
      filtered = filtered.filter(r => r.type === filters.type);
    }
    if (filters.status) {
      filtered = filtered.filter(r => r.status === filters.status);
    }
    if (filters.user_email) {
      filtered = filtered.filter(r => r.user_email === filters.user_email);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aVal: any = a[sortKey as keyof AutomationRun];
      let bVal: any = b[sortKey as keyof AutomationRun];

      if (sortKey === 'clients_processed') {
        aVal = a.clients_processed || 0;
        bVal = b.clients_processed || 0;
      } else if (sortKey === 'file_size') {
        aVal = a.file_size || 0;
        bVal = b.file_size || 0;
      } else if (sortKey === 'start_time') {
        aVal = new Date(a.start_time).getTime();
        bVal = new Date(b.start_time).getTime();
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  };

  const filteredAndSortedRuns = getFilteredAndSortedRuns();

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-brand-gray">Loading automation history...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
        <button
          onClick={loadHistory}
          className="mt-4 px-4 py-2 bg-primary text-white rounded hover:bg-opacity-90"
        >
          Retry
        </button>
      </div>
    );
  }

  // Calculate metrics (use all runs, not filtered)
  const totalRuns = runs.length;
  const successfulRuns = runs.filter(r => r.status === 'completed').length;
  const failedRuns = runs.filter(r => r.status === 'failed').length;

  return (
    <div className="space-y-6">
      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Total Runs Card */}
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-brand-gray text-sm font-medium mb-1">Total Runs</p>
              <h3 className="text-3xl font-bold text-navy">{totalRuns}</h3>
            </div>
            <div className="w-14 h-14 bg-primary rounded-2xl flex items-center justify-center shadow-md">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <span className="text-brand-gray">All automation executions</span>
          </div>
        </div>

        {/* Successful Runs Card */}
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-brand-gray text-sm font-medium mb-1">Successful Runs</p>
              <h3 className="text-3xl font-bold text-navy">{successfulRuns}</h3>
            </div>
            <div className="w-14 h-14 bg-accent rounded-2xl flex items-center justify-center shadow-md">
              <svg className="w-7 h-7 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <span className="text-brand-gray">Completed successfully</span>
          </div>
        </div>

        {/* Failed Runs Card */}
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-brand-gray text-sm font-medium mb-1">Failed Runs</p>
              <h3 className="text-3xl font-bold text-navy">{failedRuns}</h3>
            </div>
            <div className="w-14 h-14 bg-navy rounded-2xl flex items-center justify-center shadow-md">
              <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div className="mt-4 flex items-center text-sm">
            <span className="text-brand-gray">Automation failures</span>
          </div>
        </div>
      </div>

      {/* History Section */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-navy">Automation History</h2>
          <button
            onClick={loadHistory}
            className="px-5 py-2.5 bg-primary text-white rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-200 font-medium flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>

        {runs.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-20 h-20 bg-accent rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <p className="text-brand-gray text-lg font-medium">No automation runs yet</p>
            <p className="text-brand-gray text-sm mt-2">Use the Manual Run tab to start your first automation</p>
          </div>
        ) : (
          <>
            {/* Filters Row */}
            <div className="mb-4 flex flex-wrap gap-3">
              <div className="flex-1 min-w-[200px]">
                <label className="block text-xs font-medium text-brand-gray mb-1">Type</label>
                <select
                  value={filters.type}
                  onChange={(e) => handleFilterChange('type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"
                >
                  <option value="">All Types</option>
                  <option value="manual">Manual</option>
                  <option value="scheduled_weekly">Scheduled Weekly</option>
                  <option value="scheduled_monthly">Scheduled Monthly</option>
                </select>
              </div>
              <div className="flex-1 min-w-[200px]">
                <label className="block text-xs font-medium text-brand-gray mb-1">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"
                >
                  <option value="">All Statuses</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                  <option value="running">Running</option>
                </select>
              </div>
              <div className="flex-1 min-w-[200px]">
                <label className="block text-xs font-medium text-brand-gray mb-1">User</label>
                <select
                  value={filters.user_email}
                  onChange={(e) => handleFilterChange('user_email', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary outline-none text-sm"
                >
                  <option value="">All Users</option>
                  {Array.from(new Set(runs.map(r => r.user_email).filter(Boolean))).map(email => (
                    <option key={email} value={email}>{email}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-hidden">
              <table className="w-full table-fixed">
                <colgroup>
                  <col style={{ width: '18%' }} />
                  <col style={{ width: '10%' }} />
                  <col style={{ width: '9%' }} />
                  <col style={{ width: '9%' }} />
                  <col style={{ width: '13%' }} />
                  <col style={{ width: '8%' }} />
                  <col style={{ width: '10%' }} />
                  <col style={{ width: '23%' }} />
                </colgroup>
                <thead className="bg-navy">
                  <tr>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-white rounded-tl-xl">
                      <button onClick={() => handleSort('run_id')} className="flex items-center gap-1 hover:text-accent transition-colors">
                        <span>Run ID</span>
                        {sortKey === 'run_id' && (
                          <span className="text-xs">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </button>
                    </th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-white">
                      <button onClick={() => handleSort('type')} className="flex items-center gap-1 hover:text-accent transition-colors">
                        <span>Type</span>
                        {sortKey === 'type' && (
                          <span className="text-xs">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </button>
                    </th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-white">
                      <button onClick={() => handleSort('status')} className="flex items-center gap-1 hover:text-accent transition-colors">
                        <span>Status</span>
                        {sortKey === 'status' && (
                          <span className="text-xs">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </button>
                    </th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-white">User</th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-white">
                      <button onClick={() => handleSort('start_time')} className="flex items-center gap-1 hover:text-accent transition-colors">
                        <span>Date</span>
                        {sortKey === 'start_time' && (
                          <span className="text-xs">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </button>
                    </th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-white">
                      <button onClick={() => handleSort('clients_processed')} className="flex items-center gap-1 hover:text-accent transition-colors">
                        <span>Clients</span>
                        {sortKey === 'clients_processed' && (
                          <span className="text-xs">{sortDirection === 'asc' ? '↑' : '↓'}</span>
                        )}
                      </button>
                    </th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-white">Size</th>
                    <th className="px-3 py-3 text-left text-xs font-semibold text-white rounded-tr-xl">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredAndSortedRuns.map((run) => (
                    <tr key={run.run_id} className="hover:bg-accent/30 transition-colors">
                      <td className="px-3 py-3 text-xs font-medium text-navy truncate" title={run.run_id}>{run.run_id}</td>
                      <td className="px-3 py-3 text-xs text-brand-gray capitalize">{run.type.replace('_', ' ')}</td>
                      <td className="px-3 py-3 text-xs">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${getStatusBadgeColor(run.status)}`}>
                          {run.status}
                        </span>
                      </td>
                      <td className="px-3 py-3 text-xs text-brand-gray truncate" title={run.user_email || 'System'}>
                        {run.user_email?.split('@')[0] || 'System'}
                      </td>
                      <td className="px-3 py-3 text-xs text-brand-gray">
                        {new Date(run.start_time).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })}
                        <br />
                        {new Date(run.start_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="px-3 py-3 text-xs text-brand-gray text-center">
                        {run.clients_processed}/{run.max_clients}
                      </td>
                      <td className="px-3 py-3 text-xs text-brand-gray">
                        {formatFileSize(run.file_size)}
                      </td>
                      <td className="px-3 py-3 text-xs">
                        <div className="flex gap-1.5 flex-wrap">
                          <button
                            onClick={() => viewLogs(run.run_id)}
                            className="px-2.5 py-1.5 text-xs border border-navy text-navy rounded hover:bg-navy hover:text-white transition-all font-medium whitespace-nowrap"
                          >
                            Logs
                          </button>
                          {run.status === 'completed' && run.file_path && (
                            <button
                              onClick={() => downloadFile(run.run_id)}
                              className="px-2.5 py-1.5 text-xs bg-primary text-white rounded hover:shadow-lg transition-all font-medium whitespace-nowrap"
                            >
                              Download
                            </button>
                          )}
                          {session?.user?.role === 'admin' && (
                            <button
                              onClick={() => handleDeleteRun(run.run_id)}
                              className="px-2.5 py-1.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 hover:shadow-lg transition-all font-medium whitespace-nowrap"
                              title="Delete run, logs, and files (admin only)"
                            >
                              Delete
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>

      {/* Logs Modal */}
      {selectedRunId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[80vh] flex flex-col border border-gray-100">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200 bg-navy rounded-t-2xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white">
                  Logs for {selectedRunId}
                </h3>
              </div>
              <button
                onClick={closeLogs}
                className="w-8 h-8 bg-white/20 hover:bg-white/30 rounded-lg flex items-center justify-center transition-all"
              >
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 bg-background">
              {logsLoading ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
                  <div className="text-brand-gray">Loading logs...</div>
                </div>
              ) : logs.length === 0 ? (
                <div className="text-center py-16">
                  <div className="w-16 h-16 bg-accent rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p className="text-brand-gray text-lg font-medium">No logs available</p>
                  <p className="text-brand-gray text-sm mt-2">This run has no recorded logs</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {logs.map((log, index) => (
                    <div
                      key={index}
                      className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="flex items-center gap-2 text-xs text-brand-gray mb-2">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {formatDate(log.timestamp)}
                      </div>
                      <div className="text-brand-gray whitespace-pre-wrap font-mono text-sm bg-gray-50 p-3 rounded-lg">
                        {log.message}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-200 flex justify-end bg-white rounded-b-2xl">
              <button
                onClick={closeLogs}
                className="px-6 py-2.5 bg-navy text-white rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-200 font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmRunId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full border border-gray-100">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-200 bg-red-600 rounded-t-2xl">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white">
                  Confirm Deletion
                </h3>
              </div>
              <button
                onClick={cancelDelete}
                disabled={deleting}
                className="w-8 h-8 bg-white/20 hover:bg-white/30 rounded-lg flex items-center justify-center transition-all disabled:opacity-50"
              >
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 bg-background">
              <div className="mb-4">
                <p className="text-brand-gray text-sm mb-3">
                  Are you sure you want to delete this automation run?
                </p>
                <div className="bg-white p-4 rounded-xl border border-gray-200 mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="font-semibold text-navy text-sm">Run ID:</span>
                  </div>
                  <p className="font-mono text-xs text-brand-gray ml-6">{deleteConfirmRunId}</p>
                </div>
                <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
                  <p className="text-red-800 text-sm font-semibold mb-2">This will permanently delete:</p>
                  <ul className="text-red-700 text-xs space-y-1.5 ml-4">
                    <li className="flex items-start gap-2">
                      <span className="text-red-500 mt-0.5">•</span>
                      <span>Run record from database</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-500 mt-0.5">•</span>
                      <span>All associated logs</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-red-500 mt-0.5">•</span>
                      <span>Downloaded Excel file (if exists)</span>
                    </li>
                  </ul>
                  <p className="text-red-800 text-xs font-bold mt-3">⚠️ This action cannot be undone!</p>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t border-gray-200 flex justify-end gap-3 bg-white rounded-b-2xl">
              <button
                onClick={cancelDelete}
                disabled={deleting}
                className="px-6 py-2.5 bg-gray-200 text-navy rounded-xl hover:bg-gray-300 hover:shadow-lg transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={confirmDelete}
                disabled={deleting}
                className="px-6 py-2.5 bg-red-600 text-white rounded-xl hover:bg-red-700 hover:shadow-lg transition-all duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {deleting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Deleting...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                    Delete Permanently
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

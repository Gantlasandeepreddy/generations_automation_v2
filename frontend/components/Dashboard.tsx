'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { AutomationRun, getAutomationHistory, getDownloadUrl, getRunLogs } from '../lib/api';

interface LogEntry {
  timestamp: string;
  message: string;
}

export default function Dashboard() {
  const { data: session } = useSession();
  const [runs, setRuns] = useState<AutomationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [logsLoading, setLogsLoading] = useState(false);

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

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-navy">Automation History</h2>
        <button
          onClick={loadHistory}
          className="px-4 py-2 border border-primary text-primary rounded hover:bg-primary hover:text-white transition"
        >
          Refresh
        </button>
      </div>

      {runs.length === 0 ? (
        <div className="text-center py-12 text-brand-gray">
          <p>No automation runs yet.</p>
          <p className="text-sm mt-2">Use the Manual Run tab to start your first automation.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white shadow-md rounded-lg">
            <thead className="bg-navy text-white">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold">Run ID</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Type</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Status</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">User</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Date Range</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Start Time</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Clients</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">File Size</th>
                <th className="px-6 py-3 text-left text-sm font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {runs.map((run) => (
                <tr key={run.run_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm text-brand-gray">{run.run_id}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className="capitalize">{run.type.replace('_', ' ')}</span>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusBadgeColor(run.status)}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-brand-gray">
                    {run.user_email || 'System'}
                  </td>
                  <td className="px-6 py-4 text-sm text-brand-gray">
                    {run.date_range.start_date} to {run.date_range.end_date}
                  </td>
                  <td className="px-6 py-4 text-sm text-brand-gray">
                    {formatDate(run.start_time)}
                  </td>
                  <td className="px-6 py-4 text-sm text-brand-gray">
                    {run.clients_processed}/{run.max_clients}
                  </td>
                  <td className="px-6 py-4 text-sm text-brand-gray">
                    {formatFileSize(run.file_size)}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <div className="flex gap-2">
                      <button
                        onClick={() => viewLogs(run.run_id)}
                        className="px-3 py-1 border border-navy text-navy rounded hover:bg-navy hover:text-white transition"
                      >
                        View Logs
                      </button>
                      {run.status === 'completed' && run.file_path ? (
                        <button
                          onClick={() => downloadFile(run.run_id)}
                          className="px-3 py-1 bg-primary text-white rounded hover:bg-opacity-90"
                        >
                          Download
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Logs Modal */}
      {selectedRunId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[80vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b">
              <h3 className="text-xl font-bold text-navy">
                Logs for {selectedRunId}
              </h3>
              <button
                onClick={closeLogs}
                className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
              >
                &times;
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6">
              {logsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-brand-gray">Loading logs...</div>
                </div>
              ) : logs.length === 0 ? (
                <div className="text-center py-12 text-brand-gray">
                  No logs available for this run.
                </div>
              ) : (
                <div className="space-y-2">
                  {logs.map((log, index) => (
                    <div
                      key={index}
                      className="bg-gray-50 p-3 rounded border border-gray-200 font-mono text-sm"
                    >
                      <div className="text-xs text-gray-500 mb-1">
                        {formatDate(log.timestamp)}
                      </div>
                      <div className="text-brand-gray whitespace-pre-wrap">
                        {log.message}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t flex justify-end">
              <button
                onClick={closeLogs}
                className="px-4 py-2 bg-navy text-white rounded hover:bg-opacity-90"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

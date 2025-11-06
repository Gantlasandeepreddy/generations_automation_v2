'use client';

import { useEffect, useState } from 'react';
import { AutomationRun, getAutomationHistory, getDownloadUrl } from '../lib/api';

export default function Dashboard() {
  const [runs, setRuns] = useState<AutomationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const history = await getAutomationHistory();
      setRuns(history);
      setError('');
    } catch (err) {
      setError('Failed to load history');
    } finally {
      setLoading(false);
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
                    {run.status === 'completed' && run.file_path ? (
                      <a
                        href={getDownloadUrl(run.run_id)}
                        download
                        className="px-3 py-1 bg-primary text-white rounded hover:bg-opacity-90 inline-block"
                      >
                        Download
                      </a>
                    ) : (
                      <span className="text-gray-400">N/A</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

'use client';

import { useState } from 'react';
import { runManualAutomation, getDownloadUrl } from '../lib/api';

export default function ManualRun() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [maxClients, setMaxClients] = useState(10);
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [completed, setCompleted] = useState(false);
  const [downloadRunId, setDownloadRunId] = useState('');
  const [error, setError] = useState('');

  const handleRun = async () => {
    if (!startDate || !endDate) {
      setError('Please select both start and end dates');
      return;
    }

    setRunning(true);
    setCompleted(false);
    setLogs([]);
    setError('');
    setDownloadRunId('');

    try {
      await runManualAutomation(
        startDate,
        endDate,
        maxClients,
        (log) => {
          setLogs((prev) => [...prev, log]);
        },
        (status, filePath, runId) => {
          setRunning(false);
          if (status === 'completed') {
            setCompleted(true);
            setDownloadRunId(runId);
            setLogs((prev) => [...prev, 'Automation completed successfully!']);
          } else {
            setError('Automation failed. Check logs for details.');
          }
        }
      );
    } catch (err) {
      setRunning(false);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    }
  };

  const handleReset = () => {
    setStartDate('');
    setEndDate('');
    setMaxClients(10);
    setRunning(false);
    setLogs([]);
    setCompleted(false);
    setDownloadRunId('');
    setError('');
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-navy mb-6">Manual Automation Run</h2>

      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <label className="block text-sm font-medium text-brand-gray mb-2">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              disabled={running}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-brand-gray mb-2">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              disabled={running}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-brand-gray mb-2">
            Maximum Clients to Process
          </label>
          <input
            type="number"
            min="0"
            value={maxClients}
            onChange={(e) => setMaxClients(parseInt(e.target.value))}
            disabled={running}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
          />
          <p className="text-sm text-gray-500 mt-2">
            Set to <strong>0</strong> to process <strong>ALL</strong> clients in the date range.
            Recommended: 10-20 clients for session stability. Large batches may take longer.
          </p>
        </div>

        {error && (
          <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="flex gap-4">
          <button
            onClick={handleRun}
            disabled={running}
            className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {running ? 'Running...' : 'Run Automation'}
          </button>

          {(completed || error) && (
            <button
              onClick={handleReset}
              className="px-6 py-3 border border-primary text-primary rounded-lg hover:bg-primary hover:text-white transition font-medium"
            >
              Reset
            </button>
          )}

          {completed && downloadRunId && (
            <a
              href={getDownloadUrl(downloadRunId)}
              download
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
            >
              Download Excel
            </a>
          )}
        </div>
      </div>

      {logs.length > 0 && (
        <div className="bg-white shadow-md rounded-lg p-6">
          <h3 className="text-lg font-semibold text-navy mb-4">Real-time Logs</h3>
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-96 overflow-y-auto">
            {logs.map((log, index) => (
              <div key={index} className="mb-1">
                {log}
              </div>
            ))}
            {running && (
              <div className="mt-2 text-yellow-400 animate-pulse">
                Processing...
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

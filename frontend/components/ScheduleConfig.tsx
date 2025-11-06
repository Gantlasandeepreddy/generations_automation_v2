'use client';

import { useEffect, useState } from 'react';
import { getSchedule, updateSchedule, ScheduleConfig as ConfigType } from '../lib/api';

const DAYS_OF_WEEK = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' },
];

const DAYS_OF_MONTH = Array.from({ length: 28 }, (_, i) => i + 1);

export default function ScheduleConfig() {
  const [config, setConfig] = useState<ConfigType>({
    weekly_enabled: false,
    weekly_day: 0,
    weekly_hour: 9,
    weekly_minute: 0,
    monthly_enabled: false,
    monthly_day: 1,
    monthly_hour: 9,
    monthly_minute: 0,
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    loadSchedule();
  }, []);

  const loadSchedule = async () => {
    try {
      setLoading(true);
      const schedule = await getSchedule();
      setConfig(schedule);
      setError('');
    } catch (err) {
      setError('Failed to load schedule configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage('');
      setError('');
      await updateSchedule(config);
      setMessage('Schedule updated successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setError('Failed to update schedule');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-brand-gray">Loading schedule configuration...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-navy mb-6">Schedule Configuration</h2>

      {message && (
        <div className="mb-6 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          {message}
        </div>
      )}

      {error && (
        <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="flex items-center mb-4">
          <input
            type="checkbox"
            id="weekly-enabled"
            checked={config.weekly_enabled}
            onChange={(e) => setConfig({ ...config, weekly_enabled: e.target.checked })}
            className="w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary"
          />
          <label htmlFor="weekly-enabled" className="ml-3 text-lg font-semibold text-navy">
            Weekly Automation
          </label>
        </div>

        {config.weekly_enabled && (
          <div className="ml-8 grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-brand-gray mb-2">
                Day of Week
              </label>
              <select
                value={config.weekly_day}
                onChange={(e) => setConfig({ ...config, weekly_day: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                {DAYS_OF_WEEK.map((day) => (
                  <option key={day.value} value={day.value}>
                    {day.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-brand-gray mb-2">
                Hour (24h format)
              </label>
              <input
                type="number"
                min="0"
                max="23"
                value={config.weekly_hour}
                onChange={(e) => setConfig({ ...config, weekly_hour: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-brand-gray mb-2">
                Minute
              </label>
              <input
                type="number"
                min="0"
                max="59"
                value={config.weekly_minute}
                onChange={(e) => setConfig({ ...config, weekly_minute: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>
        )}

        <div className="ml-8 bg-blue-50 border border-blue-200 p-4 rounded-lg">
          <p className="text-sm text-brand-gray font-medium mb-1">
            ⏰ Schedule: Every {DAYS_OF_WEEK.find(d => d.value === config.weekly_day)?.label || 'Monday'} at{' '}
            {String(config.weekly_hour).padStart(2, '0')}:{String(config.weekly_minute).padStart(2, '0')}
          </p>
          <p className="text-sm text-brand-gray mb-1">
            📅 Date Range: Last 7 days from run time
          </p>
          <p className="text-sm text-brand-gray">
            👥 Clients: <strong>ALL clients</strong> in the date range (no limit)
          </p>
        </div>
      </div>

      <div className="bg-white shadow-md rounded-lg p-6 mb-6">
        <div className="flex items-center mb-4">
          <input
            type="checkbox"
            id="monthly-enabled"
            checked={config.monthly_enabled}
            onChange={(e) => setConfig({ ...config, monthly_enabled: e.target.checked })}
            className="w-5 h-5 text-primary border-gray-300 rounded focus:ring-primary"
          />
          <label htmlFor="monthly-enabled" className="ml-3 text-lg font-semibold text-navy">
            Monthly Automation
          </label>
        </div>

        {config.monthly_enabled && (
          <div className="ml-8 grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-brand-gray mb-2">
                Day of Month
              </label>
              <select
                value={config.monthly_day}
                onChange={(e) => setConfig({ ...config, monthly_day: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                {DAYS_OF_MONTH.map((day) => (
                  <option key={day} value={day}>
                    {day}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-brand-gray mb-2">
                Hour (24h format)
              </label>
              <input
                type="number"
                min="0"
                max="23"
                value={config.monthly_hour}
                onChange={(e) => setConfig({ ...config, monthly_hour: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-brand-gray mb-2">
                Minute
              </label>
              <input
                type="number"
                min="0"
                max="59"
                value={config.monthly_minute}
                onChange={(e) => setConfig({ ...config, monthly_minute: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>
        )}

        <div className="ml-8 bg-blue-50 border border-blue-200 p-4 rounded-lg">
          <p className="text-sm text-brand-gray font-medium mb-1">
            ⏰ Schedule: {config.monthly_day}
            {config.monthly_day === 1 ? 'st' : config.monthly_day === 2 ? 'nd' : config.monthly_day === 3 ? 'rd' : 'th'} of
            each month at {String(config.monthly_hour).padStart(2, '0')}:
            {String(config.monthly_minute).padStart(2, '0')}
          </p>
          <p className="text-sm text-brand-gray mb-1">
            📅 Date Range: Last 30 days from run time
          </p>
          <p className="text-sm text-brand-gray">
            👥 Clients: <strong>ALL clients</strong> in the date range (no limit)
          </p>
        </div>
      </div>

      <div className="flex gap-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {saving ? 'Saving...' : 'Save Schedule'}
        </button>

        <button
          onClick={loadSchedule}
          disabled={saving}
          className="px-6 py-3 border border-primary text-primary rounded-lg hover:bg-primary hover:text-white transition font-medium"
        >
          Reset
        </button>
      </div>
    </div>
  );
}

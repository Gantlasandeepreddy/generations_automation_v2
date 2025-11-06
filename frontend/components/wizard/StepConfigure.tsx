'use client'

import { useState } from 'react'

interface StepConfigureProps {
  token: string
  credentials: any
  onSuccess: (dateRange: any) => void
  onBack: () => void
}

export default function StepConfigure({ token, credentials, onSuccess, onBack }: StepConfigureProps) {
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [clientLimit, setClientLimit] = useState('10')
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validate dates
    const start = new Date(startDate)
    const end = new Date(endDate)
    const today = new Date()

    if (end > today) {
      setError('End date cannot be in the future')
      return
    }

    if (start > end) {
      setError('Start date must be before end date')
      return
    }

    const twoYearsAgo = new Date()
    twoYearsAgo.setFullYear(today.getFullYear() - 2)

    if (start < twoYearsAgo) {
      setError('Start date cannot be more than 2 years in the past')
      return
    }

    // Convert to MM/DD/YYYY format
    const formatDate = (date: Date) => {
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const year = date.getFullYear()
      return `${month}/${day}/${year}`
    }

    onSuccess({
      start_date: formatDate(start),
      end_date: formatDate(end),
      client_limit: clientLimit === 'all' ? 999 : parseInt(clientLimit),
    })
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-6">Configure Date Range</h2>

      <div className="mb-6 p-4 bg-accent rounded-lg">
        <p className="text-sm text-gray-600">
          <strong>Logged in as:</strong> {credentials.email}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray mb-2">
            Start Date
          </label>
          <input
            type="date"
            className="input-field"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            required
            max={new Date().toISOString().split('T')[0]}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray mb-2">
            End Date
          </label>
          <input
            type="date"
            className="input-field"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            required
            max={new Date().toISOString().split('T')[0]}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray mb-2">
            Client Limit
          </label>
          <select
            className="input-field"
            value={clientLimit}
            onChange={(e) => setClientLimit(e.target.value)}
          >
            <option value="5">5 clients (Quick test)</option>
            <option value="10">10 clients (Standard batch)</option>
            <option value="all">All clients (Full report)</option>
          </select>
          <p className="mt-1 text-xs text-gray-600">
            For testing, start with 5 or 10 clients. Use "All clients" for production runs.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-300 text-red-800 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <div className="flex space-x-4">
          <button
            type="button"
            onClick={onBack}
            className="btn-secondary flex-1"
          >
            Back
          </button>
          <button
            type="submit"
            className="btn-primary flex-1"
          >
            Continue
          </button>
        </div>
      </form>

      <p className="mt-4 text-sm text-gray-600">
        Select the date range for client notes export
      </p>
    </div>
  )
}

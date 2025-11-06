'use client'

import { useState, useEffect } from 'react'
import { submitJob, getJobStatus } from '@/lib/api'

interface StepProcessProps {
  token: string
  credentials: any
  dateRange: any
  onJobSubmitted: (jobId: string) => void
  onComplete: () => void
  onBack: () => void
}

export default function StepProcess({
  token,
  credentials,
  dateRange,
  onJobSubmitted,
  onComplete,
  onBack,
}: StepProcessProps) {
  const [jobId, setJobId] = useState('')
  const [status, setStatus] = useState('idle')
  const [logs, setLogs] = useState('')
  const [progress, setProgress] = useState({ processed: 0, total: 0, failed: 0 })
  const [error, setError] = useState('')
  const [started, setStarted] = useState(false)

  useEffect(() => {
    if (!started) {
      handleStartJob()
      setStarted(true)
    }
  }, [])

  useEffect(() => {
    if (jobId && status !== 'completed' && status !== 'failed') {
      const interval = setInterval(async () => {
        try {
          const response = await getJobStatus(jobId)
          setStatus(response.status)
          setLogs(response.logs)
          setProgress({
            processed: response.processed_clients,
            total: response.total_clients,
            failed: response.failed_clients,
          })

          if (response.status === 'completed') {
            clearInterval(interval)
            setTimeout(() => onComplete(), 1000)
          } else if (response.status === 'failed') {
            clearInterval(interval)
            setError(response.error_message || 'Job failed')
          }
        } catch (err: any) {
          console.error('Error polling job status:', err)
        }
      }, 3000) // Poll every 3 seconds

      return () => clearInterval(interval)
    }
  }, [jobId, status])

  const handleStartJob = async () => {
    try {
      const response = await submitJob(
        {
          ...credentials,
          ...dateRange,
        },
        token
      )

      setJobId(response.job_id)
      setStatus('queued')
      onJobSubmitted(response.job_id)
    } catch (err: any) {
      setError(err.message || 'Failed to submit job')
      setStatus('failed')
    }
  }

  const getStatusColor = () => {
    switch (status) {
      case 'queued':
        return 'text-blue-600'
      case 'processing':
        return 'text-primary'
      case 'completed':
        return 'text-green-600'
      case 'failed':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-6">Processing Automation</h2>

      <div className="space-y-4">
        <div className="p-4 bg-accent rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600">Status:</span>
            <span className={`text-sm font-bold ${getStatusColor()}`}>
              {status.toUpperCase()}
            </span>
          </div>
          <div className="mt-2 text-sm text-gray-600">
            Job ID: {jobId || 'Submitting...'}
          </div>
        </div>

        {(status === 'processing' || status === 'completed') && (
          <div className="p-4 bg-white border border-gray-200 rounded-lg">
            <div className="flex justify-between text-sm mb-2">
              <span>Progress</span>
              <span className="font-medium">
                {progress.total > 0
                  ? `${progress.processed} / ${progress.total} clients`
                  : 'Initializing...'}
                {progress.failed > 0 && ` (${progress.failed} failed)`}
              </span>
            </div>
            {progress.total > 0 && (
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className="bg-primary h-3 rounded-full transition-all duration-500"
                  style={{
                    width: `${(progress.processed / progress.total) * 100}%`,
                  }}
                />
              </div>
            )}
          </div>
        )}

        <div className="p-4 bg-gray-50 rounded-lg max-h-64 overflow-y-auto">
          <div className="text-xs font-mono whitespace-pre-wrap text-gray-600">
            {logs || 'Waiting for worker to start processing...'}
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-300 text-red-800 px-4 py-3 rounded">
            <strong>Error:</strong> {error}
          </div>
        )}

        {status === 'idle' || status === 'queued' ? (
          <button onClick={onBack} className="btn-secondary w-full">
            Cancel
          </button>
        ) : null}
      </div>

      <p className="mt-4 text-sm text-gray text-center">
        {status === 'queued' && 'Job queued - waiting for worker...'}
        {status === 'processing' && 'Processing automation - please wait...'}
        {status === 'completed' && 'Processing complete! Redirecting to download...'}
        {status === 'failed' && 'Processing failed. Please try again.'}
      </p>
    </div>
  )
}

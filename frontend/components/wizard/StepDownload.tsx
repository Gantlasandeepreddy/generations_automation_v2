'use client'

import { useState, useEffect } from 'react'
import { getJobStatus, getDownloadUrl } from '@/lib/api'

interface StepDownloadProps {
  jobId: string
  onStartOver: () => void
}

export default function StepDownload({ jobId, onStartOver }: StepDownloadProps) {
  const [jobDetails, setJobDetails] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadJobDetails()
  }, [])

  const loadJobDetails = async () => {
    try {
      const response = await getJobStatus(jobId)
      setJobDetails(response)
    } catch (err) {
      console.error('Error loading job details:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    window.location.href = getDownloadUrl(jobId)
  }

  if (loading) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-600">Loading job details...</p>
      </div>
    )
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-6">Download Results</h2>

      <div className="space-y-4">
        <div className="p-6 bg-green-50 border border-green-300 rounded-lg">
          <div className="flex items-center justify-center mb-4">
            <svg
              className="w-16 h-16 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-green-800 text-center mb-2">
            Processing Complete!
          </h3>
          <p className="text-green-700 text-center">
            Your client notes have been processed successfully
          </p>
        </div>

        {jobDetails && (
          <div className="p-4 bg-accent rounded-lg space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Total Clients:</span>
              <span className="font-medium text-navy">
                {jobDetails.total_clients}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Successfully Processed:</span>
              <span className="font-medium text-green-600">
                {jobDetails.processed_clients}
              </span>
            </div>
            {jobDetails.failed_clients > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Failed:</span>
                <span className="font-medium text-red-600">
                  {jobDetails.failed_clients}
                </span>
              </div>
            )}
          </div>
        )}

        <button
          onClick={handleDownload}
          className="btn-primary w-full flex items-center justify-center space-x-2"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          <span>Download Excel File</span>
        </button>

        <button
          onClick={onStartOver}
          className="btn-secondary w-full"
        >
          Start New Automation
        </button>
      </div>

      <p className="mt-4 text-sm text-gray text-center">
        The Excel file contains all processed client data with the KP template mapping
      </p>
    </div>
  )
}

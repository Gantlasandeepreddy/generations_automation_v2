'use client'

import { useState } from 'react'
import StepLogin from '../components/wizard/StepLogin'
import StepConfigure from '../components/wizard/StepConfigure'
import StepProcess from '../components/wizard/StepProcess'
import StepDownload from '../components/wizard/StepDownload'

export default function Home() {
  const [currentStep, setCurrentStep] = useState(1)
  const [token, setToken] = useState('')
  const [credentials, setCredentials] = useState({
    agency_id: '',
    email: '',
    password: '',
  })
  const [dateRange, setDateRange] = useState({
    start_date: '',
    end_date: '',
  })
  const [jobId, setJobId] = useState('')

  const handleLoginSuccess = (authToken: string, creds: any) => {
    setToken(authToken)
    setCredentials(creds)
    setCurrentStep(2)
  }

  const handleConfigureSuccess = (dates: any) => {
    setDateRange(dates)
    setCurrentStep(3)
  }

  const handleJobSubmitted = (id: string) => {
    setJobId(id)
  }

  const handleJobComplete = () => {
    setCurrentStep(4)
  }

  const handleStartOver = () => {
    setCurrentStep(1)
    setToken('')
    setCredentials({ agency_id: '', email: '', password: '' })
    setDateRange({ start_date: '', end_date: '' })
    setJobId('')
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-navy mb-2">
            Generations Automation
          </h1>
          <p className="text-gray-600">
            Automated client notes extraction and processing
          </p>
        </div>

        {/* Progress indicator */}
        <div className="flex justify-between mb-8">
          {[1, 2, 3, 4].map((step) => (
            <div
              key={step}
              className={`flex-1 h-2 rounded ${
                step <= currentStep ? 'bg-primary' : 'bg-gray-300'
              } ${step !== 4 ? 'mr-2' : ''}`}
            />
          ))}
        </div>

        {/* Step content */}
        <div className="card">
          {currentStep === 1 && (
            <StepLogin onSuccess={handleLoginSuccess} />
          )}
          {currentStep === 2 && (
            <StepConfigure
              token={token}
              credentials={credentials}
              onSuccess={handleConfigureSuccess}
              onBack={() => setCurrentStep(1)}
            />
          )}
          {currentStep === 3 && (
            <StepProcess
              token={token}
              credentials={credentials}
              dateRange={dateRange}
              onJobSubmitted={handleJobSubmitted}
              onComplete={handleJobComplete}
              onBack={() => setCurrentStep(2)}
            />
          )}
          {currentStep === 4 && (
            <StepDownload
              jobId={jobId}
              onStartOver={handleStartOver}
            />
          )}
        </div>

        {/* Step labels */}
        <div className="mt-4 text-center text-sm text-gray-600">
          {currentStep === 1 && 'Step 1: Login Validation'}
          {currentStep === 2 && 'Step 2: Configure Date Range'}
          {currentStep === 3 && 'Step 3: Processing'}
          {currentStep === 4 && 'Step 4: Download Results'}
        </div>
      </div>
    </main>
  )
}

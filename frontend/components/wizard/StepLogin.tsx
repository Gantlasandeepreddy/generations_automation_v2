'use client'

import { useState } from 'react'
import { validateCredentials } from '@/lib/api'
import { setToken } from '@/lib/auth'

interface StepLoginProps {
  onSuccess: (token: string, credentials: any) => void
}

export default function StepLogin({ onSuccess }: StepLoginProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    agency_id: '',
    email: '',
    password: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await validateCredentials(formData)
      setToken(response.token)
      onSuccess(response.token, formData)
    } catch (err: any) {
      setError(err.message || 'Invalid credentials. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-navy mb-6">Login to Generations</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray mb-2">
            Agency ID
          </label>
          <input
            type="text"
            className="input-field"
            value={formData.agency_id}
            onChange={(e) =>
              setFormData({ ...formData, agency_id: e.target.value })
            }
            required
            disabled={loading}
            placeholder="Enter your agency ID"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray mb-2">
            Email
          </label>
          <input
            type="email"
            className="input-field"
            value={formData.email}
            onChange={(e) =>
              setFormData({ ...formData, email: e.target.value })
            }
            required
            disabled={loading}
            placeholder="Enter your email"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray mb-2">
            Password
          </label>
          <input
            type="password"
            className="input-field"
            value={formData.password}
            onChange={(e) =>
              setFormData({ ...formData, password: e.target.value })
            }
            required
            disabled={loading}
            placeholder="Enter your password"
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-300 text-red-800 px-4 py-3 rounded">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="btn-primary w-full"
          disabled={loading}
        >
          {loading ? 'Validating...' : 'Validate Credentials'}
        </button>
      </form>

      <p className="mt-4 text-sm text-gray text-center">
        Your credentials will be validated by logging into Generations system
      </p>
    </div>
  )
}

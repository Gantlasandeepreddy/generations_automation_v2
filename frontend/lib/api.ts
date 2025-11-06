// Use relative URLs for Next.js proxy, or absolute URL if specified
// Empty string means relative URLs (/api/*) which Next.js will proxy
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export interface ValidationResponse {
  success: boolean;
  token: string;
  message: string;
}

export interface JobSubmitResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: string;
  total_clients: number;
  processed_clients: number;
  failed_clients: number;
  logs: string;
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export async function validateCredentials(data: {
  agency_id: string;
  email: string;
  password: string;
}): Promise<ValidationResponse> {
  const res = await fetch(`${API_BASE}/api/auth/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Invalid credentials');
  }

  return res.json();
}

export async function submitJob(
  data: {
    agency_id: string;
    email: string;
    password: string;
    start_date: string;
    end_date: string;
  },
  token: string
): Promise<JobSubmitResponse> {
  const res = await fetch(`${API_BASE}/api/jobs/submit`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to submit job');
  }

  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}/status`);

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Failed to get job status');
  }

  return res.json();
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/api/files/${jobId}/download`;
}

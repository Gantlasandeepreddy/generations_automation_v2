// For client-side calls, use the Next.js proxy at /api/backend which forwards to FastAPI
// For server-side calls (like NextAuth), use direct backend URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_PROXY_URL = '/api/backend'; // Next.js proxy route

// Interfaces
export interface AutomationRun {
  run_id: string;
  type: string;
  status: string;
  start_time: string;
  end_time: string | null;
  date_range: {
    start_date: string;
    end_date: string;
  };
  max_clients: number;
  clients_processed: number;
  logs: string[];
  file_path: string | null;
  file_size: number | null;
  error: string | null;
  user_email?: string;
}

export interface ScheduleConfig {
  weekly_enabled: boolean;
  weekly_day: number;
  weekly_hour: number;
  weekly_minute: number;
  monthly_enabled: boolean;
  monthly_day: number;
  monthly_hour: number;
  monthly_minute: number;
}

export interface User {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

// Helper to get auth headers with Bearer token
function getAuthHeaders(token: string): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
}

// Automation APIs
export async function getAutomationHistory(token: string): Promise<AutomationRun[]> {
  const response = await fetch(`${API_PROXY_URL}/automation/history`, {
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch history');
  }

  const data = await response.json();
  return data.runs;
}

export function getDownloadUrl(runId: string): string {
  return `${API_PROXY_URL}/automation/download/${runId}`;
}

export async function getRunLogs(token: string, runId: string): Promise<any> {
  const response = await fetch(`${API_PROXY_URL}/automation/logs/${runId}`, {
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch logs');
  }

  return response.json();
}

export async function runManualAutomation(
  token: string,
  startDate: string,
  endDate: string,
  maxClients: number,
  onLog: (log: string) => void,
  onComplete: (status: string, filePath: string, runId: string) => void
): Promise<void> {
  // Use direct backend URL for SSE (Server-Sent Events) - doesn't work through Next.js proxy
  const response = await fetch(`${API_BASE_URL}/api/automation/run`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      start_date: startDate,
      end_date: endDate,
      max_clients: maxClients,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to start automation');
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error('No response body');
  }

  while (true) {
    const { value, done } = await reader.read();

    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.substring(6));

        if (data.log) {
          onLog(data.log);
        }

        if (data.status) {
          onComplete(data.status, data.file_path, data.run_id);
          return;
        }

        if (data.error) {
          throw new Error(data.error);
        }
      }
    }
  }
}

// Schedule APIs
export async function getSchedule(token: string): Promise<ScheduleConfig> {
  const response = await fetch(`${API_PROXY_URL}/schedule`, {
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch schedule');
  }

  return response.json();
}

export async function updateSchedule(token: string, config: ScheduleConfig): Promise<void> {
  const response = await fetch(`${API_PROXY_URL}/schedule`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    throw new Error('Failed to update schedule');
  }
}

// User Management APIs (Admin only)
export async function getUsers(token: string): Promise<User[]> {
  const response = await fetch(`${API_PROXY_URL}/users`, {
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }

  return response.json();
}

export async function createUser(token: string, email: string, password: string, role: string): Promise<User> {
  const response = await fetch(`${API_PROXY_URL}/users`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ email, password, role }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create user');
  }

  return response.json();
}

export async function updateUser(token: string, userId: number, updates: Partial<User>): Promise<User> {
  const response = await fetch(`${API_PROXY_URL}/users/${userId}`, {
    method: 'PUT',
    headers: getAuthHeaders(token),
    body: JSON.stringify(updates),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update user');
  }

  return response.json();
}

export async function deleteUser(token: string, userId: number): Promise<void> {
  const response = await fetch(`${API_PROXY_URL}/users/${userId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete user');
  }
}

export async function resetUserPassword(token: string, userId: number, newPassword: string): Promise<void> {
  const response = await fetch(`${API_PROXY_URL}/users/${userId}/reset-password`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ new_password: newPassword }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to reset password');
  }
}

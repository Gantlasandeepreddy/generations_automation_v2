const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

export async function login(email: string, password: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error('Invalid credentials');
  }
}

export async function logout(): Promise<void> {
  await fetch(`${API_BASE_URL}/api/logout`, {
    method: 'POST',
  });
}

export async function getAutomationHistory(): Promise<AutomationRun[]> {
  const response = await fetch(`${API_BASE_URL}/api/automation/history`);

  if (!response.ok) {
    throw new Error('Failed to fetch history');
  }

  const data = await response.json();
  return data.runs;
}

export function getDownloadUrl(runId: string): string {
  return `${API_BASE_URL}/api/automation/download/${runId}`;
}

export async function runManualAutomation(
  startDate: string,
  endDate: string,
  maxClients: number,
  onLog: (log: string) => void,
  onComplete: (status: string, filePath: string, runId: string) => void
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/automation/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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

export async function getSchedule(): Promise<ScheduleConfig> {
  const response = await fetch(`${API_BASE_URL}/api/schedule`);

  if (!response.ok) {
    throw new Error('Failed to fetch schedule');
  }

  return response.json();
}

export async function updateSchedule(config: ScheduleConfig): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/schedule`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });

  if (!response.ok) {
    throw new Error('Failed to update schedule');
  }
}

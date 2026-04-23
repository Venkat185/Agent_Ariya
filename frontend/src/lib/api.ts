export type Artifact = {
  type: "image" | "table" | "text" | "plotly";
  title?: string;
  image_base64?: string;
  plotly_json?: Record<string, unknown>;
  columns?: string[];
  rows?: Record<string, unknown>[];
  text?: string;
};

export type AnalyzeResponse = {
  session_id: string;
  query: string;
  summary: string;
  code?: string | null;
  artifacts: Artifact[];
};

export type ColumnProfile = {
  name: string;
  dtype: string;
  null_count: number;
  unique_count: number;
};

export type DatasetProfile = {
  session_id: string;
  filename: string;
  rows: number;
  columns: number;
  file_size_bytes: number;
  column_profiles: ColumnProfile[];
  preview_rows: Record<string, unknown>[];
};

export type DatasetFull = {
  session_id: string;
  filename: string;
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
  returned_rows: number;
};

export type ChatTurn = {
  role: "user" | "assistant";
  content: string;
};

export type AnalysisHistoryItem = {
  query: string;
  summary: string;
  code?: string | null;
  artifacts: Artifact[];
};

export type AnalysisHistory = {
  session_id: string;
  filename: string;
  turns: ChatTurn[];
  analyses: AnalysisHistoryItem[];
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function analyzeDataset(params: {
  query: string;
  file?: File | null;
  sessionId?: string | null;
}): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append("query", params.query);
  if (params.file) {
    form.append("file", params.file);
  }
  if (params.sessionId) {
    form.append("session_id", params.sessionId);
  }

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    body: form
  });

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(errorBody.detail ?? "Analysis request failed.");
  }

  return (await response.json()) as AnalyzeResponse;
}

export async function profileDataset(file: File): Promise<DatasetProfile> {
  const form = new FormData();
  form.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/dataset/profile`, {
    method: "POST",
    body: form
  });

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(errorBody.detail ?? "Dataset profiling failed.");
  }

  return (await response.json()) as DatasetProfile;
}

export async function fetchHistory(sessionId: string): Promise<AnalysisHistory> {
  const response = await fetch(
    `${API_BASE_URL}/api/analysis/history?session_id=${encodeURIComponent(sessionId)}`
  );

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(errorBody.detail ?? "Failed to fetch analysis history.");
  }

  return (await response.json()) as AnalysisHistory;
}

export async function fetchFullDataset(
  sessionId: string,
  limit: number = 5000
): Promise<DatasetFull> {
  const response = await fetch(
    `${API_BASE_URL}/api/dataset/full?session_id=${encodeURIComponent(sessionId)}&limit=${limit}`
  );

  if (!response.ok) {
    const errorBody = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(errorBody.detail ?? "Failed to fetch full dataset.");
  }

  return (await response.json()) as DatasetFull;
}

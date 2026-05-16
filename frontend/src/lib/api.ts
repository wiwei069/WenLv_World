const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchApi<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: { message: res.statusText } }));
    throw new Error(error?.error?.message || `HTTP ${res.status}`);
  }

  return res.json();
}

export const api = {
  // Search
  search: (query: string, projectType?: string) =>
    fetchApi<{ task_id: string; status: string }>("/api/search", {
      method: "POST",
      body: JSON.stringify({ query, project_type: projectType }),
    }),

  getSearchStatus: (taskId: string) =>
    fetchApi<{ status: string; projects_found: number; error_message?: string }>(
      `/api/search/status/${taskId}`
    ),

  // Projects
  listProjects: (page = 1, perPage = 20, search?: string) => {
    const params = new URLSearchParams({ page: String(page), per_page: String(perPage) });
    if (search) params.set("search", search);
    return fetchApi<{
      projects: Array<{
        id: string;
        chinese_name: string;
        name: string;
        location: string;
        project_type: string;
        construction_status: string;
        visitor_count: string;
        annual_revenue: string;
        summary: string;
        created_at: string;
        updated_at: string;
      }>;
      total: number;
      page: number;
      per_page: number;
    }>(`/api/projects?${params}`);
  },

  getProject: (id: string) =>
    fetchApi<{
      project: any;
      sources: any[];
      social_mentions: any[];
      analysis_report: any;
    }>(`/api/projects/${id}`),

  deleteProject: (id: string) =>
    fetchApi<{ status: string }>(`/api/projects/${id}`, { method: "DELETE" }),

  // Analysis
  triggerAnalysis: (projectId: string) =>
    fetchApi<{ task_id: string; status: string }>(
      `/api/projects/${projectId}/analyze`,
      { method: "POST" }
    ),

  getAnalysisStatus: (projectId: string, taskId: string) =>
    fetchApi<{ status: string; error?: string }>(
      `/api/projects/${projectId}/analysis/status/${taskId}`
    ),

  getAnalysisReport: (projectId: string) =>
    fetchApi<any>(`/api/projects/${projectId}/analysis`),

  // Hot Rankings
  getHotRankings: (month?: string) => {
    const params = month ? `?month=${month}` : "";
    return fetchApi<{ rankings: any[]; month: string; total: number; holiday_data: any[] }>(
      `/api/hot-rankings${params}`
    );
  },

  // Stats
  getStats: () => fetchApi<import("@/types").SystemStats>("/api/stats"),

  // Export
  getExportPayload: (projectId: string) =>
    fetchApi<any>(`/api/projects/${projectId}/export`),

  getExportMarkdown: async (projectId: string): Promise<string> => {
    const url = `${API_BASE}/api/projects/${projectId}/export/markdown`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("导出失败");
    return res.text();
  },

  getExportUrls: async (projectId: string): Promise<string> => {
    const url = `${API_BASE}/api/projects/${projectId}/export/urls`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("导出失败");
    return res.text();
  },

  getExportPdf: async (projectId: string, projectName: string): Promise<void> => {
    const url = `${API_BASE}/api/projects/${projectId}/export/pdf`;
    const res = await fetch(url);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "导出失败" }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = `${projectName}_分析报告.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);
  },
};

export interface Project {
  id: string;
  chinese_name: string;
  name: string;
  location: string;
  project_type: string;
  investors: string[];
  planning_firms: string[];
  construction_status: string;
  operational_data: Record<string, string>;
  visitor_count: string;
  annual_revenue: string;
  summary: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectListItem {
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
}

export interface Source {
  id: string;
  project_id: string;
  url: string;
  title: string;
  source_type: string;
  platform: string;
  snippet: string;
  fetch_status: string;
  fetched_at: string | null;
  created_at: string;
}

export interface SocialMention {
  id: string;
  platform: string;
  author: string;
  content: string;
  sentiment: number;
  likes_count: number;
  comments_count: number;
  posted_at: string | null;
  fetched_at: string;
}

export interface AnalysisReport {
  id: string;
  project_id: string;
  summary: string;
  analysis: string;
  confidence_score: number;
  key_findings: string[];
  recommendations: string[];
  model_version: string;
  tokens_used: number;
  created_at: string;
}

export interface ExportPayload {
  project: Project;
  sources: Source[];
  social_mentions: SocialMention[];
  report: AnalysisReport | null;
  all_urls: string[];
}

export interface SearchRequest {
  query: string;
  project_type?: string;
}

export interface SearchResponse {
  task_id: string;
  status: string;
}

export interface SearchStatus {
  status: string;
  projects_found: number;
  error_message?: string;
}

export interface ProjectDetail {
  project: Project;
  sources: Source[];
  social_mentions: SocialMention[];
  analysis_report: AnalysisReport | null;
  images: ProjectImage[];
}

export interface ProjectListResponse {
  projects: ProjectListItem[];
  total: number;
  page: number;
  per_page: number;
}

export const STATUS_LABELS: Record<string, string> = {
  planned: "规划中",
  under_construction: "建设中",
  operating: "运营中",
  closed: "已关闭",
  unknown: "未知",
};

export interface HotRankingItem {
  id: string;
  project_name: string;
  project_type: string;
  rank: number;
  month: string;
  source: string;
  score: number;
  url: string;
  created_at: string;
}

export interface ProjectImage {
  id: string;
  project_id: string;
  url: string;
  alt_text: string;
  source_url: string;
  created_at: string;
}

export const STATUS_COLORS: Record<string, string> = {
  planned: "bg-blue-100 text-blue-800",
  under_construction: "bg-yellow-100 text-yellow-800",
  operating: "bg-green-100 text-green-800",
  closed: "bg-gray-100 text-gray-800",
  unknown: "bg-gray-100 text-gray-500",
};

export interface HolidayTourismItem {
  holiday_name: string;
  period: string;
  total_visitors: string;
  total_revenue: string;
  avg_spend: string;
  source: string;
}

export interface SystemStats {
  total_projects: number;
  total_sources: number;
  total_reports: number;
  sources_by_platform: Record<string, number>;
  sources_by_type: Record<string, number>;
  recent_reports: Array<{
    id: string;
    project_id: string;
    summary: string;
    confidence_score: number;
    model_version: string;
    created_at: string | null;
  }>;
  projects_by_status: Record<string, number>;
  projects_by_type: Record<string, number>;
}

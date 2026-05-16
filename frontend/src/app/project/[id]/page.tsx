"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import StatusBadge from "@/components/StatusBadge";
import SourceTable from "@/components/SourceTable";
import SocialMentions from "@/components/SocialMentions";
import AnalysisReport from "@/components/AnalysisReport";
import ExportButton from "@/components/ExportButton";
import ProjectGallery from "@/components/ProjectGallery";
import { api } from "@/lib/api";
import {
  MapPin,
  Building2,
  Users,
  DollarSign,
  ArrowLeft,
  Loader2,
  AlertCircle,
  Briefcase,
  PencilRuler,
  Globe,
  MessageCircle,
  Bot,
  Download,
  ImageIcon,
} from "lucide-react";
import Link from "next/link";
import type { ProjectDetail } from "@/types";

export default function ProjectDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [data, setData] = useState<ProjectDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    loadProject();
  }, [id]);

  const loadProject = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const detail = await api.getProject(id);
      setData(detail as ProjectDetail);
    } catch (err: any) {
      setError(err.message || "加载失败");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
          <p className="text-muted-foreground">加载项目信息...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <AlertCircle className="h-12 w-12 mx-auto text-destructive" />
          <p className="text-lg font-medium">加载失败</p>
          <p className="text-sm text-muted-foreground">{error || "项目不存在"}</p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-primary hover:underline"
          >
            <ArrowLeft className="h-4 w-4" />
            返回首页
          </Link>
        </div>
      </div>
    );
  }

  const { project, sources, social_mentions, analysis_report, images } = data;
  const parsedInvestors: string[] = Array.isArray(project.investors)
    ? project.investors
    : typeof project.investors === "string"
      ? JSON.parse(project.investors || "[]")
      : [];
  const parsedFirms: string[] = Array.isArray(project.planning_firms)
    ? project.planning_firms
    : typeof project.planning_firms === "string"
      ? JSON.parse(project.planning_firms || "[]")
      : [];

  return (
    <div className="ref-page relative dark" style={{ minHeight: "100vh" }}>
      <div className="ref-grid-bg" />

      {/* Nav Header */}
      <nav className="ref-nav">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center gap-3">
          <Link
            href="/"
            className="flex items-center gap-1 text-xs hover:opacity-70 transition-opacity"
            style={{ color: "var(--ref-accent)" }}
          >
            &larr; 返回
          </Link>
          <div className="flex-1 flex items-center gap-3 min-w-0">
            <h1 className="text-sm font-semibold truncate" style={{ color: "var(--ref-fg)" }}>
              {project.chinese_name}
            </h1>
            <StatusBadge status={project.construction_status} />
          </div>
        </div>
      </nav>

      <div className="ref-content-area">
        <main className="max-w-6xl mx-auto px-4 pt-16 pb-8 space-y-8 w-full">
          {/* Project Info Card */}
          <div className="ref-stats-card p-5">
            <h2 className="text-base font-semibold mb-4" style={{ color: "var(--ref-fg)" }}>{project.chinese_name}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {project.location && (
                <div className="flex items-start gap-2">
                  <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: "var(--ref-accent)" }} />
                  <div>
                    <p className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>所在地</p>
                    <p className="text-sm" style={{ color: "var(--ref-fg)" }}>{project.location}</p>
                  </div>
                </div>
              )}
              {project.project_type && (
                <div className="flex items-start gap-2">
                  <Building2 className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: "var(--ref-accent)" }} />
                  <div>
                    <p className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>项目类型</p>
                    <span className="ref-source-badge text-xs mt-0.5 inline-block">{project.project_type}</span>
                  </div>
                </div>
              )}
              {project.visitor_count && (
                <div className="flex items-start gap-2">
                  <Users className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: "var(--ref-accent)" }} />
                  <div>
                    <p className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>年接待游客</p>
                    <p className="text-sm" style={{ color: "var(--ref-fg)" }}>{project.visitor_count}</p>
                  </div>
                </div>
              )}
              {project.annual_revenue && (
                <div className="flex items-start gap-2">
                  <DollarSign className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: "var(--ref-accent)" }} />
                  <div>
                    <p className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>年收入</p>
                    <p className="text-sm" style={{ color: "var(--ref-fg)" }}>{project.annual_revenue}</p>
                  </div>
                </div>
              )}
              {parsedInvestors.length > 0 && (
                <div className="flex items-start gap-2 md:col-span-2">
                  <Briefcase className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: "var(--ref-accent)" }} />
                  <div>
                    <p className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>投资方</p>
                    <p className="text-sm" style={{ color: "var(--ref-fg)" }}>{parsedInvestors.join("、")}</p>
                  </div>
                </div>
              )}
              {parsedFirms.length > 0 && (
                <div className="flex items-start gap-2 md:col-span-2">
                  <PencilRuler className="h-4 w-4 mt-0.5 flex-shrink-0" style={{ color: "var(--ref-accent)" }} />
                  <div>
                    <p className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>规划设计</p>
                    <p className="text-sm" style={{ color: "var(--ref-fg)" }}>{parsedFirms.join("、")}</p>
                  </div>
                </div>
              )}
            </div>
            {project.summary && (
              <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--ref-border)" }}>
                <p className="text-xs mb-1" style={{ color: "var(--ref-fg-muted)" }}>摘要</p>
                <p className="text-sm leading-relaxed" style={{ color: "var(--ref-fg-muted)" }}>
                  {project.summary}
                </p>
              </div>
            )}
          </div>

          {/* Image Gallery */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <ImageIcon className="h-4 w-4" style={{ color: "var(--ref-accent)" }} />
              <h2 className="text-sm font-semibold" style={{ color: "var(--ref-fg)" }}>项目图片</h2>
              <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>
                ({images?.length || 0} 张)
              </span>
            </div>
            <ProjectGallery images={images || []} projectName={project.chinese_name} />
          </section>

          {/* Sources Section */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Globe className="h-4 w-4" style={{ color: "var(--ref-accent)" }} />
              <h2 className="text-sm font-semibold" style={{ color: "var(--ref-fg)" }}>信息来源</h2>
              <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>
                ({sources.length} 条)
              </span>
            </div>
            <div className="ref-stats-card p-0 overflow-hidden">
              <SourceTable sources={sources} />
            </div>
          </section>

          {/* Social Mentions Section */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <MessageCircle className="h-4 w-4" style={{ color: "var(--ref-accent)" }} />
              <h2 className="text-sm font-semibold" style={{ color: "var(--ref-fg)" }}>社交媒体评价</h2>
              <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>
                ({social_mentions.length} 条)
              </span>
            </div>
            <div className="ref-stats-card p-4">
              <SocialMentions mentions={social_mentions} />
            </div>
          </section>

          {/* Analysis Section */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Bot className="h-4 w-4" style={{ color: "var(--ref-accent)" }} />
              <h2 className="text-sm font-semibold" style={{ color: "var(--ref-fg)" }}>AI 分析</h2>
            </div>
            <div className="ref-stats-card p-4">
              <AnalysisReport projectId={project.id} report={analysis_report} />
            </div>
          </section>

          {/* Export Section */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Download className="h-4 w-4" style={{ color: "var(--ref-accent)" }} />
              <h2 className="text-sm font-semibold" style={{ color: "var(--ref-fg)" }}>导出</h2>
            </div>
            <div className="ref-stats-card p-4">
              <p className="text-xs mb-4" style={{ color: "var(--ref-fg-muted)" }}>
                导出项目信息和分析报告到 NotebookLM，或复制 Markdown / 链接汇总。
              </p>
              <ExportButton
                projectId={project.id}
                projectName={project.chinese_name}
              />
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

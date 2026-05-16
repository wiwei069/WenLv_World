"use client";

import { Suspense, useState, useEffect } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { ProjectListItem, SystemStats } from "@/types";
import {
  Database, Globe2, FileText, BarChart3,
  ExternalLink, MapPin, ChevronRight,
} from "lucide-react";

type TabId = "projects" | "sources" | "reports" | "rankings";

export default function DataPage() {
  return (
    <Suspense fallback={null}>
      <DataPageInner />
    </Suspense>
  );
}

function DataPageInner() {
  const searchParams = useSearchParams();
  const initialTab = (searchParams.get("tab") as TabId) || "projects";
  const [activeTab, setActiveTab] = useState<TabId>(initialTab);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [projectTotal, setProjectTotal] = useState(0);
  const [projectPage, setProjectPage] = useState(1);
  const [rankings, setRankings] = useState<any[]>([]);
  const [rankingsMonth, setRankingsMonth] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [projectPage]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [statsData, projData, rankData] = await Promise.all([
        api.getStats(),
        api.listProjects(projectPage, 20),
        api.getHotRankings(),
      ]);
      setStats(statsData);
      setProjects(projData.projects);
      setProjectTotal(projData.total);
      setRankings(rankData.rankings);
      setRankingsMonth(rankData.month);
    } catch (err) {
      console.error("Failed to load data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const totalPages = Math.ceil(projectTotal / 20);

  return (
    <div className="ref-page relative dark" style={{ minHeight: "100vh" }}>
      <div className="ref-grid-bg" />
      <div className="ref-content-area">
        <div className="max-w-6xl mx-auto px-4 pt-12 pb-16">
          {/* Page header */}
          <div className="mb-8">
            <Link href="/" className="text-xs hover:underline" style={{ color: "var(--ref-accent)" }}>
              &larr; 返回首页
            </Link>
            <h1 className="text-3xl font-bold mt-2" style={{ color: "var(--ref-fg)", fontFamily: "'Noto Serif SC', serif" }}>
              数据中心
            </h1>
          </div>

          {/* Summary cards */}
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
              <div className="ref-stats-card text-center cursor-pointer" onClick={() => setActiveTab("projects")}>
                <div className="flex items-center justify-center gap-2 mb-1">
                  <Database className="h-4 w-4" style={{ color: "var(--ref-accent)" }} />
                  <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>项目数据库</span>
                </div>
                <div className="text-xl font-bold" style={{ color: "var(--ref-fg)" }}>{stats.total_projects}</div>
              </div>
              <div className="ref-stats-card text-center cursor-pointer" onClick={() => setActiveTab("sources")}>
                <div className="flex items-center justify-center gap-2 mb-1">
                  <Globe2 className="h-4 w-4" style={{ color: "var(--ref-accent)" }} />
                  <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>数据源</span>
                </div>
                <div className="text-xl font-bold" style={{ color: "var(--ref-fg)" }}>{stats.total_sources}</div>
              </div>
              <div className="ref-stats-card text-center cursor-pointer" onClick={() => setActiveTab("reports")}>
                <div className="flex items-center justify-center gap-2 mb-1">
                  <FileText className="h-4 w-4" style={{ color: "var(--ref-accent)" }} />
                  <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>AI分析报告</span>
                </div>
                <div className="text-xl font-bold" style={{ color: "var(--ref-fg)" }}>{stats.total_reports}</div>
              </div>
              <div className="ref-stats-card text-center cursor-pointer" onClick={() => setActiveTab("rankings")}>
                <div className="flex items-center justify-center gap-2 mb-1">
                  <BarChart3 className="h-4 w-4" style={{ color: "var(--ref-accent)" }} />
                  <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>月度排行</span>
                </div>
                <div className="text-xl font-bold" style={{ color: "var(--ref-fg)" }}>{rankings.length}</div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabId)}>
            <TabsList className="mb-6" style={{ background: "var(--ref-card)" }}>
              <TabsTrigger value="projects" style={{ color: "var(--ref-fg)" }}>项目数据库</TabsTrigger>
              <TabsTrigger value="sources" style={{ color: "var(--ref-fg)" }}>数据源</TabsTrigger>
              <TabsTrigger value="reports" style={{ color: "var(--ref-fg)" }}>AI分析报告</TabsTrigger>
              <TabsTrigger value="rankings" style={{ color: "var(--ref-fg)" }}>月度排行</TabsTrigger>
            </TabsList>

            {/* Tab: Projects */}
            <TabsContent value="projects">
              <div className="space-y-4">
                <p className="text-sm" style={{ color: "var(--ref-fg-muted)" }}>
                  共 {projectTotal} 个项目
                </p>
                {isLoading ? (
                  <div className="space-y-2">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className="ref-project-card p-4" style={{ height: 60 }}>
                        <div className="animate-pulse h-4 w-1/3" style={{ background: "var(--ref-card-hover)" }} />
                      </div>
                    ))}
                  </div>
                ) : (
                  <>
                    <div className="space-y-2">
                      {projects.map((p) => (
                        <Link
                          key={p.id}
                          href={`/project/${p.id}`}
                          className="ref-project-card flex items-center justify-between p-4 cursor-pointer gap-4"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-sm truncate" style={{ color: "var(--ref-fg)" }}>
                              {p.chinese_name}
                            </div>
                            {p.location && (
                              <div className="flex items-center gap-1 text-xs mt-0.5" style={{ color: "var(--ref-fg-muted)" }}>
                                <MapPin className="h-3 w-3" />
                                <span className="truncate">{p.location}</span>
                              </div>
                            )}
                          </div>
                          <div className="flex items-center gap-3 flex-shrink-0">
                            {p.project_type && (
                              <span className="text-xs px-2 py-0.5 rounded-full" style={{
                                background: "rgba(212, 162, 78, 0.12)",
                                color: "var(--ref-accent)",
                                border: "1px solid rgba(212, 162, 78, 0.3)",
                              }}>
                                {p.project_type}
                              </span>
                            )}
                            <ChevronRight className="h-4 w-4" style={{ color: "var(--ref-fg-muted)" }} />
                          </div>
                        </Link>
                      ))}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex items-center justify-center gap-2 pt-4">
                        <button
                          onClick={() => setProjectPage(Math.max(1, projectPage - 1))}
                          disabled={projectPage <= 1}
                          className="ref-tag text-xs px-3 py-1"
                        >
                          上一页
                        </button>
                        <span className="text-xs px-3" style={{ color: "var(--ref-fg-muted)" }}>
                          {projectPage} / {totalPages}
                        </span>
                        <button
                          onClick={() => setProjectPage(Math.min(totalPages, projectPage + 1))}
                          disabled={projectPage >= totalPages}
                          className="ref-tag text-xs px-3 py-1"
                        >
                          下一页
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </TabsContent>

            {/* Tab: Sources */}
            <TabsContent value="sources">
              {stats ? (
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--ref-fg)" }}>按平台分布</h3>
                    <div className="space-y-2">
                      {Object.entries(stats.sources_by_platform).map(([platform, count]) => (
                        <div key={platform} className="flex items-center justify-between p-3 rounded-lg" style={{
                          background: "var(--ref-card)",
                          border: "1px solid var(--ref-border)",
                        }}>
                          <span className="text-sm" style={{ color: "var(--ref-fg)" }}>{platform}</span>
                          <span className="text-sm font-semibold" style={{ color: "var(--ref-accent)" }}>{count}</span>
                        </div>
                      ))}
                      {Object.keys(stats.sources_by_platform).length === 0 && (
                        <p className="text-sm" style={{ color: "var(--ref-fg-muted)" }}>暂无数据</p>
                      )}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold mb-3" style={{ color: "var(--ref-fg)" }}>按类型分布</h3>
                    <div className="space-y-2">
                      {Object.entries(stats.sources_by_type).map(([type, count]) => (
                        <div key={type} className="flex items-center justify-between p-3 rounded-lg" style={{
                          background: "var(--ref-card)",
                          border: "1px solid var(--ref-border)",
                        }}>
                          <span className="text-sm" style={{ color: "var(--ref-fg)" }}>{type}</span>
                          <span className="text-sm font-semibold" style={{ color: "var(--ref-accent)" }}>{count}</span>
                        </div>
                      ))}
                      {Object.keys(stats.sources_by_type).length === 0 && (
                        <p className="text-sm" style={{ color: "var(--ref-fg-muted)" }}>暂无数据</p>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-sm" style={{ color: "var(--ref-fg-muted)" }}>加载中...</p>
              )}
            </TabsContent>

            {/* Tab: Reports */}
            <TabsContent value="reports">
              {stats ? (
                <div className="space-y-3">
                  {stats.recent_reports.length > 0 ? (
                    stats.recent_reports.map((r) => (
                      <Link
                        key={r.id}
                        href={`/project/${r.project_id}`}
                        className="block p-4 rounded-lg transition-all" style={{
                          background: "var(--ref-card)",
                          border: "1px solid var(--ref-border)",
                        }}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm line-clamp-2" style={{ color: "var(--ref-fg)" }}>
                              {r.summary || "无摘要"}
                            </p>
                            <div className="flex items-center gap-3 mt-1.5">
                              <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>
                                模型: {r.model_version}
                              </span>
                              <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>
                                置信度: {(r.confidence_score * 100).toFixed(0)}%
                              </span>
                              {r.created_at && (
                                <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>
                                  {new Date(r.created_at).toLocaleString("zh-CN")}
                                </span>
                              )}
                            </div>
                          </div>
                          <ExternalLink className="h-4 w-4 flex-shrink-0" style={{ color: "var(--ref-fg-muted)" }} />
                        </div>
                      </Link>
                    ))
                  ) : (
                    <p className="text-sm" style={{ color: "var(--ref-fg-muted)" }}>暂无分析报告</p>
                  )}
                </div>
              ) : (
                <p className="text-sm" style={{ color: "var(--ref-fg-muted)" }}>加载中...</p>
              )}
            </TabsContent>

            {/* Tab: Rankings */}
            <TabsContent value="rankings">
              <div>
                <p className="text-xs mb-4" style={{ color: "var(--ref-fg-muted)" }}>
                  {rankingsMonth} · 全国5A景区品牌传播力排行
                </p>
                {rankings.length > 0 ? (
                  <div className="space-y-2">
                    {rankings.map((item: any, idx: number) => (
                      <div key={item.id} className="flex items-center gap-4 p-3 rounded-lg" style={{
                        background: "var(--ref-card)",
                        border: "1px solid var(--ref-border)",
                      }}>
                        <span className="text-lg font-bold w-8 text-center flex-shrink-0" style={{
                          color: idx < 3 ? "var(--ref-accent)" : "var(--ref-fg-muted)",
                        }}>
                          #{item.rank}
                        </span>
                        <div className="flex-1 min-w-0">
                          <span className="text-sm font-medium" style={{ color: "var(--ref-fg)" }}>
                            {item.project_name}
                          </span>
                          <span className="text-xs ml-2 px-1.5 py-0.5 rounded-full" style={{
                            background: "rgba(255,255,255,0.06)",
                            color: "var(--ref-fg-muted)",
                          }}>
                            {item.project_type || "景区"}
                          </span>
                        </div>
                        {item.score > 0 && (
                          <span className="text-xs flex-shrink-0" style={{ color: "var(--ref-fg-muted)" }}>
                            {item.score.toFixed(1)}
                          </span>
                        )}
                        {item.url && (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:opacity-70 transition-opacity"
                          >
                            <ExternalLink className="h-3.5 w-3.5" style={{ color: "var(--ref-accent)" }} />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm" style={{ color: "var(--ref-fg-muted)" }}>暂无排行数据</p>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

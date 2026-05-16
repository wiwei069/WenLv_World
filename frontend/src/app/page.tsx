"use client";

import { useState, useEffect } from "react";
import SearchBar from "@/components/SearchBar";
import ProjectList from "@/components/ProjectList";
import HotRankings from "@/components/HotRankings";
import { api } from "@/lib/api";
import { Database, Globe2, FileText, BarChart3, ExternalLink, Notebook, Search } from "lucide-react";
import { toast } from "sonner";
import type { ProjectListItem } from "@/types";

const SOURCE_BADGES = [
  { label: "小红书", color: "#ff5a5f" },
  { label: "抖音", color: "#00d4ff" },
  { label: "微信公众号", color: "#07c160" },
  { label: "网站", color: "#d4a24e" },
  { label: "微博", color: "#ff8200" },
  { label: "B站", color: "#fb7299" },
];

function StatsCard({ icon: Icon, label, value, delay, href }: { icon: any; label: string; value: string | number; delay: number; href?: string }) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShow(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const content = (
    <>
      <div className="flex items-center justify-center gap-2 mb-1">
        <Icon className="h-4 w-4" style={{ color: "var(--ref-accent)" }} />
        <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>{label}</span>
      </div>
      <div className="text-lg md:text-xl font-bold" style={{ color: "var(--ref-fg)" }}>
        {show ? value : "—"}
      </div>
    </>
  );

  if (href) {
    return (
      <a href={href} className="ref-stats-card text-center ref-fade-in block cursor-pointer no-underline hover:!border-[var(--ref-accent)] transition-all">
        {content}
      </a>
    );
  }

  return (
    <div className="ref-stats-card text-center ref-fade-in">
      {content}
    </div>
  );
}

export default function HomePage() {
  const [projects, setProjects] = useState<ProjectListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [lastQuery, setLastQuery] = useState("");

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async (search?: string) => {
    try {
      const data = await api.listProjects(1, 50, search);
      setProjects(data.projects);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to load projects:", err);
    }
  };

  const handleSearch = async (query: string) => {
    setLastQuery(query);
    setIsSearching(true);
    try {
      const { task_id } = await api.search(query);
      setIsPolling(true);

      let attempts = 0;
      const maxAttempts = 30;
      while (attempts < maxAttempts) {
        await new Promise((r) => setTimeout(r, 2000));
        const status = await api.getSearchStatus(task_id);
        if (status.status === "complete" || status.status === "error") {
          setIsPolling(false);
          break;
        }
        attempts++;
      }
      await loadProjects();
    } catch (err: any) {
      console.error("Search failed:", err);
      toast.error("搜索失败: " + (err.message || "未知错误，请检查后端服务是否正常运行"));
    } finally {
      setIsSearching(false);
      setIsPolling(false);
    }
  };

  return (
    <div className="ref-page relative dark">
      {/* Grid background */}
      <div className="ref-grid-bg" />

      {/* Floating particles */}
      {[
        { left: "15%", top: "20%", "--dur": "7s", "--delay": "0s" },
        { left: "45%", top: "30%", "--dur": "9s", "--delay": "2s" },
        { right: "20%", top: "25%", "--dur": "8s", "--delay": "4s" },
        { left: "30%", top: "15%", "--dur": "10s", "--delay": "1s" },
        { right: "35%", top: "35%", "--dur": "7.5s", "--delay": "3s" },
      ].map((style, i) => (
        <div key={i} className="ref-particle" style={style as React.CSSProperties} />
      ))}

      {/* Fixed Navbar */}
      <nav className="ref-nav">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="ref-logo-badge">亚</div>
            <div>
              <div className="text-sm font-semibold" style={{ color: "var(--ref-fg)" }}>文旅大视界</div>
              <div className="text-[10px]" style={{ color: "var(--ref-fg-muted)" }}>CulTour Vision</div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <span className="ref-status-dot" />
              <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>引擎在线</span>
            </div>
            <a
              href="https://notebooklm.google.com"
              target="_blank"
              rel="noopener noreferrer"
              className="ref-nb-button"
            >
              <Notebook className="h-4 w-4" />
              NotebookLM
              <ExternalLink className="h-3 w-3 opacity-60" />
            </a>
          </div>
        </div>
      </nav>

      {/* Hero area: stats + search */}
      <div className="ref-content-area">
        <div className="max-w-6xl mx-auto px-4 pt-24 pb-12 md:pt-28 md:pb-16">
          {/* Stats Counter Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-2xl mx-auto mb-8">
            <StatsCard icon={Database} label="项目数据库" value={total || "0"} delay={300} href="/data?tab=projects" />
            <StatsCard icon={Globe2} label="Tavily 数据源" value="3+" delay={600} href="/data?tab=sources" />
            <StatsCard icon={FileText} label="AI 分析报告" value="DeepSeek" delay={900} href="/data?tab=reports" />
            <StatsCard icon={BarChart3} label="月度排行" value="Top 10" delay={1200} href="/data?tab=rankings" />
          </div>

          {/* Brand Title */}
          <div className="text-center mb-8 space-y-3">
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-tight" style={{
              color: "var(--ref-fg)",
              fontFamily: "'Noto Serif SC', serif",
              textShadow: "0 0 40px var(--ref-accent-glow)",
            }}>
              文旅大视界
            </h1>
            <p className="text-sm md:text-base tracking-[0.25em]" style={{ color: "var(--ref-fg-muted)" }}>
              Cultural & Tourism World
            </p>
          </div>

          {/* Search Bar with gold glow */}
          <div className="flex justify-center mb-6">
            <div className="w-full max-w-2xl ref-search-glow rounded-2xl p-[1px]">
              <div style={{ background: "var(--ref-card)", borderRadius: "inherit" }}>
                <div
                  style={{
                    "--background": "var(--ref-card-hover)",
                    "--foreground": "var(--ref-fg)",
                    "--border": "var(--ref-border)",
                    "--input": "var(--ref-card-hover)",
                    "--primary": "var(--ref-accent)",
                    "--primary-foreground": "#080c14",
                    "--muted": "var(--ref-card-hover)",
                    "--muted-foreground": "var(--ref-fg-muted)",
                    "--ring": "var(--ref-accent)",
                    "--radius": "0.75rem",
                    "--accent": "var(--ref-accent)",
                    "--accent-foreground": "#080c14",
                  } as React.CSSProperties}
                >
                  <SearchBar onSearch={handleSearch} isLoading={isSearching || isPolling} />
                </div>
              </div>
            </div>
          </div>

          {/* Source Platform Badges */}
          <div className="flex flex-wrap justify-center gap-2 mb-6">
            {SOURCE_BADGES.map((badge) => (
              <span
                key={badge.label}
                className="ref-source-badge"
                style={{
                  background: `${badge.color}15`,
                  borderColor: `${badge.color}40`,
                  color: badge.color,
                }}
              >
                {badge.label}
              </span>
            ))}
          </div>

          {/* Example search tags */}
          <div className="flex flex-wrap justify-center gap-2">
            <span className="text-xs" style={{ color: "var(--ref-fg-muted)", paddingTop: "4px" }}>试试：</span>
            {["成都文旅", "融创文旅城", "5A景区", "主题公园", "文旅小镇"].map((tag) => (
              <button
                key={tag}
                onClick={() => handleSearch(tag)}
                disabled={isSearching || isPolling}
                className="ref-tag"
              >
                {tag}
              </button>
            ))}
          </div>

          {/* Platform Intro Section */}
          <div className="mt-10 max-w-3xl mx-auto">
            <div className="ref-stats-card p-5">
              <p className="text-xs leading-relaxed text-center" style={{ color: "var(--ref-fg-muted)", maxWidth: "540px", margin: "0 auto" }}>
                <span className="font-semibold" style={{ color: "var(--ref-accent)" }}>文旅大视界</span>
                {' '}专为文旅行业从业者与研究者打造的智能信息平台。聚合政府数据、行业报告、社交媒体评价等多源信息，
                通过 AI 深度分析生成项目洞察报告，助您快速了解亚洲文旅项目的运营状况与行业趋势。
              </p>
              <div className="flex flex-wrap justify-center gap-x-6 gap-y-2 mt-3 text-xs" style={{ color: "var(--ref-fg-muted)" }}>
                <span>搜索项目 · 一键获取全面信息</span>
                <span>AI 分析 · 数据驱动深度洞察</span>
                <span>热门排行 · 掌握行业风向标</span>
                <span>导出报告 · 无缝对接 NotebookLM</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="ref-content-area">
        <div className="max-w-6xl mx-auto px-4 py-8 w-full space-y-10 pb-16">
          {/* Hot Rankings Section */}
          <section>
            <HotRankings />
          </section>

          {/* Search Results */}
          <section>
            {lastQuery && !isSearching && !isPolling && (
              <div className="flex items-center gap-2 mb-4 text-sm" style={{ color: "var(--ref-fg-muted)" }}>
                <Search className="h-4 w-4" style={{ color: "var(--ref-accent)" }} />
                <span>
                  搜索: <span className="font-medium" style={{ color: "var(--ref-fg)" }}>{lastQuery}</span>
                  <span className="ml-2">共 {total} 个项目</span>
                </span>
              </div>
            )}
            <ProjectList
              projects={projects}
              isLoading={isSearching || isPolling}
              total={total}
            />
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="ref-content-area" style={{
        borderTop: "1px solid var(--ref-border)",
        background: "var(--ref-bg-elevated)",
        padding: "24px 16px",
      }}>
        <div className="max-w-6xl mx-auto text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className="ref-logo-badge" style={{ width: 28, height: 28, fontSize: 14 }}>亚</div>
            <span className="text-sm font-semibold" style={{ color: "var(--ref-fg)" }}>文旅大视界</span>
            <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>Cultural & Tourism World</span>
          </div>
          <p className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>
            数据来源: 国家文旅部 · 中国旅游景区协会 · 权威行业机构
          </p>
          <p className="text-xs mt-1" style={{ color: "var(--ref-fg-muted)" }}>
            AI 分析: DeepSeek V4 · 导出: NotebookLM
          </p>
        </div>
      </footer>
    </div>
  );
}

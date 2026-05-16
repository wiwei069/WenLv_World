import { api } from "./api";
import type { ExportPayload } from "@/types";

const STATUS_LABELS: Record<string, string> = {
  planned: "规划中",
  under_construction: "建设中",
  operating: "运营中",
  closed: "已关闭",
  unknown: "未知",
  default: "未知",
};

function sentimentLabel(score: number): string {
  if (score > 0.2) return "😊 正面";
  if (score < -0.2) return "😟 负面";
  return "😐 中性";
}

function assembleMarkdown(payload: ExportPayload): string {
  const lines: string[] = [];

  lines.push(`# ${payload.project.chinese_name} - 文旅大视界项目分析报告`);
  lines.push("");

  lines.push("## 项目信息");
  lines.push(`- **项目名称**: ${payload.project.chinese_name || "待确认"}`);
  if (payload.project.name)
    lines.push(`- **英文名称**: ${payload.project.name}`);
  lines.push(`- **所在地**: ${payload.project.location || "信息收集中"}`);
  lines.push(`- **项目类型**: ${payload.project.project_type || "信息收集中"}`);
  lines.push(
    `- **建设状态**: ${STATUS_LABELS[payload.project.construction_status] || payload.project.construction_status}`
  );
  if (payload.project.investors?.length)
    lines.push(`- **投资方**: ${payload.project.investors.join("、")}`);
  if (payload.project.planning_firms?.length)
    lines.push(
      `- **规划设计**: ${payload.project.planning_firms.join("、")}`
    );
  if (payload.project.visitor_count)
    lines.push(`- **年接待游客**: ${payload.project.visitor_count}`);
  if (payload.project.annual_revenue)
    lines.push(`- **年收入**: ${payload.project.annual_revenue}`);
  lines.push("");

  lines.push("## 来源链接");
  lines.push("");
  payload.sources.forEach((s, i) => {
    const title = s.title || "来源";
    lines.push(`${i + 1}. ${title}`);
    lines.push(`   ${s.url}`);
    lines.push("");
  });

  if (payload.social_mentions?.length) {
    lines.push("## 社交媒体评价");
    lines.push("以下为社交媒体平台收集的用户评价：");
    lines.push("");
    for (const m of payload.social_mentions) {
      const preview = (m.content || "").slice(0, 200);
      lines.push(
        `- **[${m.platform}]** ${m.author || "匿名用户"}: ${preview}`
      );
      lines.push(
        `  - 情感倾向: ${sentimentLabel(m.sentiment)} | ❤️ ${m.likes_count} | 💬 ${m.comments_count}`
      );
    }
    lines.push("");
  }

  if (payload.report) {
    lines.push("## AI 分析报告");
    lines.push("");
    lines.push(payload.report.analysis);
    lines.push("");
    lines.push("---");
    lines.push(
      `*报告生成时间: ${new Date(payload.report.created_at).toLocaleString("zh-CN")}*`
    );
    lines.push(
      `*置信度: ${(payload.report.confidence_score * 100).toFixed(0)}%*`
    );
    lines.push(`*分析模型: ${payload.report.model_version}*`);
  }

  return lines.join("\n");
}

export async function copyToClipboard(projectId: string): Promise<string> {
  const payload: ExportPayload = await api.getExportPayload(projectId);
  const markdown = assembleMarkdown(payload);
  await navigator.clipboard.writeText(markdown);
  return markdown;
}

export async function copyReportOnly(projectId: string): Promise<string> {
  const payload: ExportPayload = await api.getExportPayload(projectId);
  if (!payload.report) {
    await navigator.clipboard.writeText("暂无AI分析报告");
    return "暂无AI分析报告";
  }
  const reportText = `# ${payload.project.chinese_name} - AI 分析报告\n\n${payload.report.analysis}\n\n---\n*报告生成时间: ${new Date(payload.report.created_at).toLocaleString("zh-CN")}*\n*分析模型: ${payload.report.model_version}*`;
  await navigator.clipboard.writeText(reportText);
  return reportText;
}

export async function copySourcesOnly(projectId: string): Promise<string> {
  const payload: ExportPayload = await api.getExportPayload(projectId);
  const lines: string[] = [];
  lines.push(`# ${payload.project.chinese_name} - 来源链接`);
  lines.push("");
  payload.sources.forEach((s, i) => {
    const title = s.title || "来源";
    lines.push(`${i + 1}. ${title}`);
    lines.push(`   ${s.url}`);
    lines.push("");
  });
  const sourceText = lines.join("\n");
  await navigator.clipboard.writeText(sourceText);
  return sourceText;
}

export function openNotebookLM(): void {
  window.open("https://notebooklm.google.com", "_blank");
}

export async function copyAndOpenNotebookLM(projectId: string): Promise<void> {
  const markdown = await copyToClipboard(projectId);
  openNotebookLM();
}

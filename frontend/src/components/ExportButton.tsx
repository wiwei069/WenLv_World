"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { copyReportOnly, copySourcesOnly } from "@/lib/export";
import { api } from "@/lib/api";
import { Copy, ExternalLink, FileDown, Loader2, Eye } from "lucide-react";

interface ExportButtonProps {
  projectId: string;
  projectName: string;
}

export default function ExportButton({ projectId, projectName }: ExportButtonProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [markdownPreview, setMarkdownPreview] = useState<string>("");
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  const handleExportPdf = async () => {
    setIsExporting(true);
    try {
      await api.getExportPdf(projectId, projectName);
      toast.success("PDF 报告已下载");
    } catch (err: any) {
      toast.error("导出失败: " + (err.message || "未知错误"));
    } finally {
      setIsExporting(false);
    }
  };

  const loadPreview = async () => {
    if (markdownPreview) return;
    setIsPreviewLoading(true);
    try {
      const md = await api.getExportMarkdown(projectId);
      setMarkdownPreview(md);
    } catch (err: any) {
      setMarkdownPreview("加载预览失败");
    } finally {
      setIsPreviewLoading(false);
    }
  };

  return (
    <div className="flex flex-wrap gap-2">
      <Button onClick={handleExportPdf} disabled={isExporting} className="gap-2">
        {isExporting ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <FileDown className="h-4 w-4" />
        )}
        导出 PDF 报告
      </Button>

      <Button
        onClick={async () => {
          try {
            await copyReportOnly(projectId);
            toast.success("AI分析报告已复制到剪贴板");
          } catch (err: any) {
            toast.error("复制失败: " + (err.message || "未知错误"));
          }
        }}
        variant="outline"
        className="gap-2"
      >
        <Copy className="h-4 w-4" />
        复制AI分析报告
      </Button>

      <Button
        onClick={async () => {
          try {
            await copySourcesOnly(projectId);
            toast.success("来源链接已复制到剪贴板");
          } catch (err: any) {
            toast.error("复制失败: " + (err.message || "未知错误"));
          }
        }}
        variant="outline"
        className="gap-2"
      >
        <Copy className="h-4 w-4" />
        复制来源链接
      </Button>

      <Dialog>
        <DialogTrigger
          render={
            <Button variant="outline" className="gap-2">
              <Eye className="h-4 w-4" />
              预览导出内容
            </Button>
          }
          onClick={loadPreview}
        />
        <DialogContent className="max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>导出预览 - {projectName}</DialogTitle>
          </DialogHeader>
          <div className="overflow-auto max-h-[60vh]">
            {isPreviewLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : (
              <pre className="text-xs whitespace-pre-wrap font-mono bg-muted p-4 rounded-lg">
                {markdownPreview}
              </pre>
            )}
          </div>
        </DialogContent>
      </Dialog>

      <a
        href="https://notebooklm.google.com"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-foreground hover:text-primary transition-colors"
      >
        <ExternalLink className="h-4 w-4" />
        打开 NotebookLM
      </a>
    </div>
  );
}

"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Bot, Loader2, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import type { AnalysisReport as AnalysisReportType } from "@/types";

interface AnalysisReportProps {
  projectId: string;
  report: AnalysisReportType | null;
}

export default function AnalysisReport({ projectId, report: initialReport }: AnalysisReportProps) {
  const [report, setReport] = useState<AnalysisReportType | null>(initialReport);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { task_id } = await api.triggerAnalysis(projectId);
      // Poll for completion
      let attempts = 0;
      const maxAttempts = 60; // 3 minutes max
      while (attempts < maxAttempts) {
        await new Promise((r) => setTimeout(r, 3000));
        const status = await api.getAnalysisStatus(projectId, task_id);
        if (status.status === "complete") {
          const reportData = await api.getAnalysisReport(projectId);
          setReport(reportData);
          setIsLoading(false);
          return;
        }
        if (status.status === "error") {
          setError(status.error || "分析失败");
          setIsLoading(false);
          return;
        }
        attempts++;
      }
      setError("分析超时，请重试");
      setIsLoading(false);
    } catch (err: any) {
      setError(err.message || "分析请求失败");
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            AI 智能分析
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
            <Loader2 className="h-4 w-4 animate-spin" />
            DeepSeek AI 正在分析数据并生成报告...
          </div>
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-2/3" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            AI 分析
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive mb-4">{error}</p>
          <Button onClick={handleAnalyze} variant="outline">
            重试
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (!report) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            AI 智能分析
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            基于 Tavily 搜索收集到的所有项目信息、网络来源和社交媒体评价，使用 DeepSeek V4 进行综合研判，生成结构化分析报告。
          </p>
          <Button onClick={handleAnalyze}>
            <Bot className="mr-2 h-4 w-4" />
            开始 AI 分析
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            AI 分析报告
          </span>
          <span className="text-xs text-muted-foreground font-normal">
            置信度: {(report.confidence_score * 100).toFixed(0)}% | 模型: {report.model_version}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {report.summary && (
          <div className="bg-muted p-3 rounded-lg mb-4">
            <p className="text-sm font-medium mb-1">摘要</p>
            <p className="text-sm text-muted-foreground">{report.summary}</p>
          </div>
        )}
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <ReactMarkdown>{report.analysis}</ReactMarkdown>
        </div>

        {report.recommendations.length > 0 && (
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
            <p className="text-sm font-medium mb-2">建议</p>
            <ul className="list-disc list-inside space-y-1">
              {report.recommendations.map((r, i) => (
                <li key={i} className="text-sm text-muted-foreground">{r}</li>
              ))}
            </ul>
          </div>
        )}

        <p className="text-xs text-muted-foreground mt-4">
          报告生成时间: {new Date(report.created_at).toLocaleString("zh-CN")}
        </p>
      </CardContent>
    </Card>
  );
}

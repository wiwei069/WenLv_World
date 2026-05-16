import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Globe, Newspaper, Building2, MessageCircle } from "lucide-react";
import type { Source } from "@/types";

const PLATFORM_ICONS: Record<string, React.ReactNode> = {
  government: <Building2 className="h-3.5 w-3.5" />,
  news: <Newspaper className="h-3.5 w-3.5" />,
  social: <MessageCircle className="h-3.5 w-3.5" />,
  company: <Building2 className="h-3.5 w-3.5" />,
  industry: <Globe className="h-3.5 w-3.5" />,
};

const PLATFORM_LABELS: Record<string, string> = {
  government: "政府",
  news: "新闻",
  social: "社交",
  company: "企业",
  industry: "行业",
  tavily: "网页",
};

interface SourceTableProps {
  sources: Source[];
}

export default function SourceTable({ sources }: SourceTableProps) {
  if (sources.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4">暂无来源数据</p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[60%] text-left">来源标题</TableHead>
          <TableHead className="text-left">类型</TableHead>
          <TableHead className="text-left">来源</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {sources.map((source) => (
          <TableRow key={source.id}>
            <TableCell className="font-medium text-left">
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm hover:text-primary hover:underline transition-colors line-clamp-1"
              >
                {source.title || "无标题"}
                <ExternalLink className="h-3 w-3 flex-shrink-0 text-muted-foreground" />
              </a>
            </TableCell>
            <TableCell className="text-left">
              <Badge variant="secondary" className="text-xs flex items-center gap-1 w-fit">
                {PLATFORM_ICONS[source.source_type] || <Globe className="h-3.5 w-3.5" />}
                {PLATFORM_LABELS[source.source_type] || source.source_type}
              </Badge>
            </TableCell>
            <TableCell className="text-sm text-muted-foreground text-left">
              {source.platform}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

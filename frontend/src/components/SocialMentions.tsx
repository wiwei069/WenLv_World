import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { ThumbsUp, MessageSquare, Heart } from "lucide-react";
import type { SocialMention } from "@/types";

interface SocialMentionsProps {
  mentions: SocialMention[];
}

function SentimentBar({ score }: { score: number }) {
  const width = Math.abs(score) * 50;
  const isPositive = score >= 0;
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-muted-foreground w-6 text-right">{isPositive ? "" : ""}</span>
      <div className="w-20 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${isPositive ? "bg-green-400 ml-auto" : "bg-red-400"}`}
          style={{ width: `${Math.min(width, 50)}%` }}
        />
      </div>
      <span className="text-muted-foreground w-6">
        {isPositive ? "😊" : "😟"}
      </span>
    </div>
  );
}

export default function SocialMentions({ mentions }: SocialMentionsProps) {
  const platforms = [...new Set(mentions.map((m) => m.platform))];

  if (mentions.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4">
        暂无社交媒体评价数据。社交媒体数据在搜索时自动采集。
      </p>
    );
  }

  return (
    <Tabs defaultValue={platforms[0] || "all"}>
      <TabsList>
        <TabsTrigger value="all">全部 ({mentions.length})</TabsTrigger>
        {platforms.map((p) => (
          <TabsTrigger key={p} value={p}>
            {p} ({mentions.filter((m) => m.platform === p).length})
          </TabsTrigger>
        ))}
      </TabsList>

      <TabsContent value="all" className="space-y-3 mt-4">
        {mentions.map((m) => (
          <MentionCard key={m.id} mention={m} />
        ))}
      </TabsContent>

      {platforms.map((p) => (
        <TabsContent key={p} value={p} className="space-y-3 mt-4">
          {mentions
            .filter((m) => m.platform === p)
            .map((m) => (
              <MentionCard key={m.id} mention={m} />
            ))}
        </TabsContent>
      ))}
    </Tabs>
  );
}

function MentionCard({ mention }: { mention: SocialMention }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {mention.platform}
            </Badge>
            <span className="text-sm font-medium">{mention.author || "匿名用户"}</span>
          </div>
          <SentimentBar score={mention.sentiment} />
        </div>
        <p className="text-sm text-muted-foreground line-clamp-3 mb-3">
          {mention.content}
        </p>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Heart className="h-3 w-3" /> {mention.likes_count}
          </span>
          <span className="flex items-center gap-1">
            <MessageSquare className="h-3 w-3" /> {mention.comments_count}
          </span>
          {mention.posted_at && (
            <span>{new Date(mention.posted_at).toLocaleDateString("zh-CN")}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function Badge({ className, variant, children }: { className?: string; variant?: string; children: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${className || ""}`}>
      {children}
    </span>
  );
}

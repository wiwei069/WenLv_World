"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { TrendingUp, Medal, RefreshCw, ExternalLink, CalendarDays, Users, DollarSign, BadgePercent } from "lucide-react";
import type { HotRankingItem, HolidayTourismItem } from "@/types";

const TYPE_COLORS: Record<string, string> = {
  文旅街区: "bg-rose-100 text-rose-700 dark:bg-rose-900 dark:text-rose-300",
  历史文化街区: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
  文旅小镇: "bg-violet-100 text-violet-700 dark:bg-violet-900 dark:text-violet-300",
  文旅古城: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900 dark:text-indigo-300",
  民俗风貌区: "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
  文化创意园区: "bg-sky-100 text-sky-700 dark:bg-sky-900 dark:text-sky-300",
  商业文旅街区: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300",
};

const RANK_MEDALS = ["🥇", "🥈", "🥉"];

export default function HotRankings() {
  const [rankings, setRankings] = useState<HotRankingItem[]>([]);
  const [holidayData, setHolidayData] = useState<HolidayTourismItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [month, setMonth] = useState("");

  useEffect(() => {
    loadRankings();
  }, []);

  const loadRankings = async () => {
    setIsLoading(true);
    try {
      const data = await api.getHotRankings();
      setRankings(data.rankings as HotRankingItem[]);
      setHolidayData((data as any).holiday_data || []);
      setMonth(data.month);
    } catch (err) {
      console.error("Failed to load hot rankings:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="border-primary/20 shadow-lg bg-gradient-to-br from-amber-50 via-white to-orange-50 dark:from-amber-950/20 dark:via-background dark:to-orange-950/20">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-amber-500" />
            <span>文旅项目热门排行榜</span>
            <span className="text-xs text-muted-foreground font-normal">
              {month} · 商业/历史/文化项目品牌影响力排行
            </span>
          </span>
          <button
            onClick={loadRankings}
            disabled={isLoading}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-6 w-6 rounded-full" />
                <Skeleton className="h-4 flex-1" />
                <Skeleton className="h-4 w-12" />
              </div>
            ))}
          </div>
        ) : (
          <>
            {/* Rankings */}
            <div className="space-y-2">
              {rankings.slice(0, 10).map((item, idx) => {
                const content = (
                  <>
                    <span className="text-lg w-8 text-center flex-shrink-0">
                      {idx < 3 ? RANK_MEDALS[idx] : `#${item.rank}`}
                    </span>
                    <span className="flex-1 text-sm font-medium truncate">
                      {item.project_name}
                    </span>
                    <Badge
                      className={`text-xs border-0 ${TYPE_COLORS[item.project_type] || "bg-gray-100 text-gray-600"}`}
                    >
                      {item.project_type || "文旅项目"}
                    </Badge>
                    {item.score > 0 && (
                      <span className="text-xs text-muted-foreground flex-shrink-0 w-12 text-right">
                        {item.score.toFixed(1)}
                      </span>
                    )}
                  </>
                );

                if (item.url) {
                  return (
                    <a
                      key={item.id}
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/60 dark:hover:bg-white/5 transition-colors group"
                    >
                      {content}
                      <ExternalLink className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                    </a>
                  );
                }

                return (
                  <div
                    key={item.id}
                    className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/60 dark:hover:bg-white/5 transition-colors"
                  >
                    {content}
                  </div>
                );
              })}
            </div>

            {/* Holiday data */}
            {holidayData.length > 0 && (
              <div className="border-t pt-5" style={{ borderColor: "var(--ref-border)" }}>
                <div className="flex items-center gap-2 mb-3">
                  <CalendarDays className="h-4 w-4 text-amber-500" />
                  <span className="text-sm font-semibold">近期节假日旅游数据</span>
                  <span className="text-xs text-muted-foreground">（来源：文化和旅游部数据中心）</span>
                </div>
                <div className="space-y-2">
                  {holidayData.map((h) => (
                    <div
                      key={h.holiday_name}
                      className="p-3 rounded-lg text-sm"
                      style={{
                        background: "var(--ref-card)",
                        border: "1px solid var(--ref-border)",
                      }}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium" style={{ color: "var(--ref-fg)" }}>{h.holiday_name}</span>
                        <span className="text-xs" style={{ color: "var(--ref-fg-muted)" }}>{h.period}</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="flex items-center gap-1" style={{ color: "var(--ref-fg-muted)" }}>
                          <Users className="h-3 w-3 flex-shrink-0" />
                          <span className="truncate">{h.total_visitors}</span>
                        </div>
                        <div className="flex items-center gap-1" style={{ color: "var(--ref-fg-muted)" }}>
                          <DollarSign className="h-3 w-3 flex-shrink-0" />
                          <span className="truncate">{h.total_revenue}</span>
                        </div>
                        <div className="flex items-center gap-1" style={{ color: "var(--ref-fg-muted)" }}>
                          <BadgePercent className="h-3 w-3 flex-shrink-0" />
                          <span className="truncate">客单价 {h.avg_spend}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

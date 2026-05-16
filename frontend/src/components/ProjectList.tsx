import { useState } from "react";
import ProjectCard from "./ProjectCard";
import { Skeleton } from "@/components/ui/skeleton";
import { Search, ChevronDown, ChevronUp } from "lucide-react";
import type { ProjectListItem } from "@/types";

const INITIAL_DISPLAY_COUNT = 6;

interface ProjectListProps {
  projects: ProjectListItem[];
  isLoading: boolean;
  total: number;
}

export default function ProjectList({ projects, isLoading, total }: ProjectListProps) {
  const [showAll, setShowAll] = useState(false);
  const displayProjects = showAll ? projects : projects.slice(0, INITIAL_DISPLAY_COUNT);
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="rounded-xl border p-5 space-y-3 bg-white/50 dark:bg-card/30">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-2/3" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="text-center py-20 text-muted-foreground">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-muted/50 mb-4">
          <Search className="h-6 w-6" />
        </div>
        <p className="text-lg font-medium">暂无项目数据</p>
        <p className="text-sm mt-1 max-w-sm mx-auto">
          输入关键词搜索亚洲文旅项目，或点击上方推荐标签快速探索
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        共找到 <span className="font-semibold text-foreground">{total}</span> 个项目
      </p>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {displayProjects.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>

      {projects.length > INITIAL_DISPLAY_COUNT && (
        <div className="flex justify-center pt-2">
          <button
            onClick={() => setShowAll(!showAll)}
            className="ref-tag text-xs px-4 py-2 inline-flex items-center gap-1.5"
          >
            {showAll ? (
              <>收起 <ChevronUp className="h-3 w-3" /></>
            ) : (
              <>展开全部 {projects.length} 个项目 <ChevronDown className="h-3 w-3" /></>
            )}
          </button>
        </div>
      )}
    </div>
  );
}

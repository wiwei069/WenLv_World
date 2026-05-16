import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import StatusBadge from "./StatusBadge";
import { MapPin, Users, DollarSign, ChevronRight } from "lucide-react";
import type { ProjectListItem } from "@/types";

interface ProjectCardProps {
  project: ProjectListItem;
}

export default function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Link href={`/project/${project.id}`}>
      <Card className="ref-project-card h-full cursor-pointer">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base leading-tight font-semibold group-hover:text-primary transition-colors">
              {project.chinese_name}
            </CardTitle>
            <StatusBadge status={project.construction_status} />
          </div>
          {project.name && (
            <p className="text-xs text-muted-foreground">{project.name}</p>
          )}
        </CardHeader>
        <CardContent className="space-y-2">
          {project.location && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <MapPin className="h-3 w-3 flex-shrink-0" />
              <span className="truncate">{project.location}</span>
            </div>
          )}
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            {project.visitor_count && (
              <div className="flex items-center gap-1">
                <Users className="h-3 w-3" />
                <span className="truncate max-w-[120px]">{project.visitor_count}</span>
              </div>
            )}
            {project.annual_revenue && (
              <div className="flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                <span className="truncate max-w-[120px]">{project.annual_revenue}</span>
              </div>
            )}
          </div>
          <div className="flex items-center justify-between pt-1">
            <div className="flex items-center gap-2">
              {project.project_type && (
                <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                  {project.project_type}
                </Badge>
              )}
            </div>
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/40 group-hover:text-primary/60 group-hover:translate-x-0.5 transition-all" />
          </div>
          {project.summary && (
            <p className="text-xs text-muted-foreground/70 line-clamp-2 leading-relaxed">
              {project.summary}
            </p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
}

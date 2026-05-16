import { Badge } from "@/components/ui/badge";
import { STATUS_LABELS, STATUS_COLORS } from "@/types";

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const label = STATUS_LABELS[status] || status;
  const colorClass = STATUS_COLORS[status] || "bg-gray-100 text-gray-500";

  return (
    <Badge className={`${colorClass} border-0 font-medium`} variant="outline">
      {label}
    </Badge>
  );
}

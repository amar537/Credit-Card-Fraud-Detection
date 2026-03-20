import { Badge } from "@/components/ui/badge";

type RiskLevel = "high" | "medium" | "low";

interface RiskBadgeProps {
  level: RiskLevel;
  score?: number;
}

const riskConfig = {
  high: {
    label: "High Risk",
    className: "bg-gradient-to-r from-destructive to-destructive/80 text-destructive-foreground shadow-lg",
  },
  medium: {
    label: "Medium Risk",
    className: "bg-gradient-to-r from-warning to-warning/80 text-warning-foreground shadow-lg",
  },
  low: {
    label: "Low Risk",
    className: "bg-gradient-to-r from-success to-success/80 text-success-foreground shadow-lg",
  },
};

export function RiskBadge({ level, score }: RiskBadgeProps) {
  const config = riskConfig[level];
  
  return (
    <Badge className={`${config.className} uppercase text-xs font-semibold px-3 py-1.5`} data-testid={`badge-risk-${level}`}>
      {config.label}
      {score !== undefined && ` (${score}%)`}
    </Badge>
  );
}

import { Badge } from "@/components/ui/badge";

type Status = "fraudulent" | "legitimate" | "pending";

interface StatusBadgeProps {
  status: Status;
}

const statusConfig = {
  fraudulent: {
    label: "Fraudulent",
    className: "bg-gradient-to-r from-destructive to-destructive/80 text-destructive-foreground shadow-md",
  },
  legitimate: {
    label: "Legitimate",
    className: "bg-gradient-to-r from-success to-success/80 text-success-foreground shadow-md",
  },
  pending: {
    label: "Pending",
    className: "bg-gradient-to-r from-muted to-muted/80 text-muted-foreground shadow-md",
  },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status];
  
  return (
    <Badge className={`${config.className} uppercase text-xs font-semibold px-3 py-1`} data-testid={`badge-status-${status}`}>
      {config.label}
    </Badge>
  );
}

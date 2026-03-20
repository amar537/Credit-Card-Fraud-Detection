import { MetricCard } from "../MetricCard";
import { Activity } from "lucide-react";

export default function MetricCardExample() {
  return (
    <div className="p-4 max-w-sm">
      <MetricCard
        title="Total Transactions"
        value="24,587"
        icon={Activity}
        trend={{ value: 12.5, isPositive: true }}
        description="Last 30 days"
      />
    </div>
  );
}

import { Card } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  description?: string;
}

export function MetricCard({ title, value, icon: Icon, trend, description }: MetricCardProps) {
  return (
    <Card className="p-6 hover-elevate relative overflow-hidden group transition-all duration-300 bg-card/50 backdrop-blur-sm border-white/5" data-testid={`metric-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div className="relative">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-muted-foreground/80 uppercase tracking-wide">{title}</p>
            <h3 className="text-4xl font-bold mt-3 text-white" data-testid={`text-${title.toLowerCase().replace(/\s+/g, '-')}-value`}>{value}</h3>
            {description && (
              <p className="text-xs text-muted-foreground/60 mt-2">{description}</p>
            )}
            {trend && (
              <div className="flex items-center gap-1 mt-3 px-3 py-1.5 bg-white/5 backdrop-blur-sm rounded-full w-fit border border-white/10">
                {trend.isPositive ? (
                  <TrendingUp className="w-4 h-4 text-success" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-destructive" />
                )}
                <span className={`text-sm font-semibold ${trend.isPositive ? 'text-success' : 'text-destructive'}`}>
                  {Math.abs(trend.value)}%
                </span>
                <span className="text-xs text-muted-foreground/60 ml-1">vs last</span>
              </div>
            )}
          </div>
          <div className="bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 p-4 rounded-2xl shadow-lg group-hover:shadow-xl group-hover:scale-110 transition-all duration-300">
            <Icon className="w-6 h-6 text-white" />
          </div>
        </div>
      </div>
    </Card>
  );
}

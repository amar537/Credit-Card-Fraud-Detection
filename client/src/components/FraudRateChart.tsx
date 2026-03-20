import { Card } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface FraudRateChartProps {
  data: Array<{ time: string; rate: number }>;
}

export function FraudRateChart({ data }: FraudRateChartProps) {
  return (
    <Card className="p-6 hover-elevate transition-all duration-300 bg-card/50 backdrop-blur-sm border-white/5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Fraud Rate (24 Hours)</h3>
        <div className="px-3 py-1.5 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-full border border-purple-500/30 backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
            <span className="text-xs font-semibold text-purple-300">Live</span>
          </div>
        </div>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="time" 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              tickFormatter={(value) => `${value}%`}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "6px",
              }}
              formatter={(value: number) => [`${value}%`, "Fraud Rate"]}
            />
            <Line 
              type="monotone" 
              dataKey="rate" 
              stroke="hsl(var(--destructive))" 
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

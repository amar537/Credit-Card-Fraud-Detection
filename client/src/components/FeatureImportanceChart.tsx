import { Card } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface FeatureImportanceChartProps {
  data: Array<{ feature: string; importance: number }>;
}

export function FeatureImportanceChart({ data }: FeatureImportanceChartProps) {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Feature Importance</h3>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={12} />
            <YAxis 
              type="category" 
              dataKey="feature" 
              stroke="hsl(var(--muted-foreground))"
              fontSize={12}
              width={120}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "6px",
              }}
              formatter={(value: number) => [`${value}%`, "Importance"]}
            />
            <Bar dataKey="importance" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

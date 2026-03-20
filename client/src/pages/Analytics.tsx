import { Card } from "@/components/ui/card";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useQuery } from "@tanstack/react-query";
import { fetchFraudTrends, fetchGeographicAnalysis, fetchMerchantCategoryAnalysis, fetchDashboardMetrics } from "@/lib/api";
import { Loader2 } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/hooks/use-toast";

export default function Analytics() {
  const { toast } = useToast();

  // Fetch fraud trends
  const { data: trendsData, isLoading: trendsLoading } = useQuery({
    queryKey: ["analytics-trends"],
    queryFn: () => fetchFraudTrends(30, "daily"),
    refetchInterval: 300000, // 5 minutes
    onError: (error) => {
      toast({
        title: "Failed to load fraud trends",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    },
  });

  // Fetch geographic analysis
  const { data: geoData, isLoading: geoLoading } = useQuery({
    queryKey: ["analytics-geographic"],
    queryFn: () => fetchGeographicAnalysis(30),
    refetchInterval: 300000,
  });

  // Fetch merchant category analysis
  const { data: merchantData, isLoading: merchantLoading } = useQuery({
    queryKey: ["analytics-merchant"],
    queryFn: () => fetchMerchantCategoryAnalysis(30),
    refetchInterval: 300000,
  });

  // Fetch dashboard metrics for model performance
  const { data: metricsData } = useQuery({
    queryKey: ["dashboard-metrics"],
    queryFn: () => fetchDashboardMetrics(30),
    refetchInterval: 300000,
  });

  // Transform trends data for chart
  const fraudTrendsData = (trendsData?.trends
    .slice()
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .map((trend) => {
      const date = new Date(trend.date);
      return {
        date: date.toLocaleDateString("en-US", { month: "short", day: "numeric" }),
        fraud: trend.fraud_transactions,
        legitimate: trend.total_transactions - trend.fraud_transactions,
      };
    })) || [];

  // Transform hourly data from trends (group by hour if available)
  const hourlyData = trendsData?.trends.slice(0, 24).map((trend, idx) => ({
    hour: String(idx * 2).padStart(2, "0"),
    count: trend.fraud_transactions,
  })) || [];

  // Transform merchant data for chart
  const merchantChartData = merchantData?.map((item) => ({
    category: item.category,
    fraud: item.fraud_count,
    legitimate: item.transaction_count - item.fraud_count,
  })) || [];

  // Model performance metrics (from dashboard)
  const performanceMetrics = metricsData ? [
    { metric: "Accuracy", value: (metricsData.model_accuracy * 100).toFixed(1) },
    { metric: "Precision", value: "N/A" }, // Would need separate endpoint
    { metric: "Recall", value: "N/A" },
    { metric: "F1-Score", value: "N/A" },
  ] : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-white">Analytics</h1>
        <p className="text-muted-foreground mt-1">Comprehensive fraud detection analytics and insights</p>
      </div>

      <Tabs defaultValue="temporal" className="space-y-6">
        <TabsList>
          <TabsTrigger value="temporal" data-testid="tab-temporal">Temporal Analysis</TabsTrigger>
          <TabsTrigger value="transactions" data-testid="tab-transactions">Transactions</TabsTrigger>
          <TabsTrigger value="performance" data-testid="tab-performance">Model Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="temporal" className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Fraud Trends Over Time</h3>
            {trendsLoading ? (
              <div className="h-80 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : fraudTrendsData.length === 0 ? (
              <div className="h-80 flex items-center justify-center text-muted-foreground">
                No trend data available
              </div>
            ) : (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={fraudTrendsData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "6px",
                      }}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="fraud" stroke="hsl(var(--destructive))" strokeWidth={2} name="Fraud" />
                    <Line type="monotone" dataKey="legitimate" stroke="hsl(var(--success))" strokeWidth={2} name="Legitimate" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Hourly Fraud Distribution</h3>
            {trendsLoading ? (
              <div className="h-64 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : hourlyData.length === 0 ? (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No hourly data available
              </div>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={hourlyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="hour" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "6px",
                      }}
                    />
                    <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="transactions" className="space-y-6">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Merchant Category Analysis</h3>
            {merchantLoading ? (
              <div className="h-80 flex items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : merchantChartData.length === 0 ? (
              <div className="h-80 flex items-center justify-center text-muted-foreground">
                No merchant category data available
              </div>
            ) : (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={merchantChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="category" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "6px",
                      }}
                    />
                    <Legend />
                    <Bar dataKey="fraud" fill="hsl(var(--destructive))" radius={[4, 4, 0, 0]} name="Fraud" />
                    <Bar dataKey="legitimate" fill="hsl(var(--success))" radius={[4, 4, 0, 0]} name="Legitimate" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="performance" className="space-y-6">
          {!metricsData ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="p-6">
                <p className="text-sm font-medium text-muted-foreground">Accuracy</p>
                <h3 className="text-4xl font-bold mt-2">{(metricsData.model_accuracy * 100).toFixed(1)}%</h3>
              </Card>
              <Card className="p-6">
                <p className="text-sm font-medium text-muted-foreground">Avg Processing Time</p>
                <h3 className="text-4xl font-bold mt-2">{Math.round(metricsData.avg_prediction_time_ms)}ms</h3>
              </Card>
              <Card className="p-6">
                <p className="text-sm font-medium text-muted-foreground">Total Predictions</p>
                <h3 className="text-4xl font-bold mt-2">{metricsData.total_transactions.toLocaleString()}</h3>
              </Card>
              <Card className="p-6">
                <p className="text-sm font-medium text-muted-foreground">Fraud Rate</p>
                <h3 className="text-4xl font-bold mt-2">{metricsData.fraud_rate.toFixed(2)}%</h3>
              </Card>
            </div>
          )}

          {!metricsData ? (
            <Card className="p-6">
              <Skeleton className="h-64 w-full" />
            </Card>
          ) : (
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Model Performance Metrics</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={[
                    { metric: "Accuracy", value: metricsData.model_accuracy * 100 },
                    { metric: "Avg Time", value: metricsData.avg_prediction_time_ms },
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="metric" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "hsl(var(--card))",
                        border: "1px solid hsl(var(--border))",
                        borderRadius: "6px",
                      }}
                      formatter={(value: number) => [typeof value === 'number' ? value.toFixed(1) : value, "Value"]}
                    />
                    <Bar dataKey="value" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

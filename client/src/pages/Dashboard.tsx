import { MetricCard } from "@/components/MetricCard";
import { HeroCard } from "@/components/HeroCard";
import { FraudRateChart } from "@/components/FraudRateChart";
import { TransactionDistributionChart } from "@/components/TransactionDistributionChart";
import { RecentAlertsTable } from "@/components/RecentAlertsTable";
import { Activity, ShieldAlert, Target, Clock, TrendingUp, Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchDashboardMetrics, fetchFraudTrends, fetchPredictionHistory, seedTransactions, fetchTransactions, createBatchPredictions } from "@/lib/api";
import { useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

export default function Dashboard() {
  const { toast } = useToast();
  
  // Fetch dashboard metrics
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ["dashboard-metrics"],
    queryFn: () => fetchDashboardMetrics(30),
    refetchInterval: 60000, // Refetch every minute
    onError: (error) => {
      toast({
        title: "Failed to load dashboard metrics",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    },
  });

  // Fetch fraud trends
  const { data: trends } = useQuery({
    queryKey: ["fraud-trends"],
    queryFn: () => fetchFraudTrends(7, "daily"),
    refetchInterval: 300000, // Refetch every 5 minutes
  });

  // Fetch recent predictions for alerts
  const { data: predictions } = useQuery({
    queryKey: ["recent-predictions"],
    queryFn: () => fetchPredictionHistory({ limit: 8, offset: 0 }),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Auto-seed demo data once per session if metrics are empty, and populate alerts by triggering predictions
  useEffect(() => {
    const run = async () => {
      // If metrics still loading, wait
      if (!metrics) return;
      const totalTx = metrics?.total_transactions || 0;
      const userKeyPart = (typeof window !== "undefined" && localStorage.getItem("user_email")) || "anon";
      const seededKey = `seeded_demo_${userKeyPart}`;

      if (totalTx === 0 && typeof window !== "undefined" && !sessionStorage.getItem(seededKey)) {
        try {
          await seedTransactions(30);
        } catch (e) {
          // ignore, will just show empty
          console.error("Dashboard auto-seed failed", e);
        } finally {
          sessionStorage.setItem(seededKey, "1");
        }
      }

      // If no recent predictions, try to create a batch from latest transactions to populate alerts
      const haveAlerts = (predictions?.predictions?.length || 0) > 0;
      if (!haveAlerts) {
        try {
          const txList = await fetchTransactions({ limit: 20 });
          const ids = (txList.transactions || []).map(t => t.id).slice(0, 20);
          if (ids.length > 0) {
            await createBatchPredictions({ transaction_ids: ids });
          }
        } catch (e) {
          console.warn("Dashboard batch predictions seed skipped", e);
        }
      }
    };
    run();
    // Only when metrics or predictions change
  }, [metrics, predictions]);

  // Transform trends data for chart
  const fraudRateData = trends?.trends.map((trend) => {
    const date = new Date(trend.date);
    return {
      time: date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      rate: trend.fraud_rate,
    };
  }) || [];

  // Transform predictions to alerts format
  const recentAlerts = predictions?.predictions.slice(0, 8).map((pred) => {
    const date = new Date(pred.timestamp);
    const minutesAgo = Math.floor((Date.now() - date.getTime()) / 60000);
    return {
      id: pred.transaction_id.slice(0, 8).toUpperCase(),
      amount: 0, // Would need to fetch transaction details
      timestamp: minutesAgo < 60 ? `${minutesAgo} min ago` : `${Math.floor(minutesAgo / 60)} hour${Math.floor(minutesAgo / 60) > 1 ? "s" : ""} ago`,
      riskScore: Math.round(pred.fraud_probability * 100),
      status: pred.is_fraud ? ("fraudulent" as const) : ("pending" as const),
    };
  }) || [];

  if (metricsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const totalTx = metrics?.total_transactions || 0;
  const fraudCount = metrics?.fraud_count || 0;
  const fraudRate = metrics?.fraud_rate || 0;
  const accuracy = metrics?.model_accuracy || 0;
  const avgTime = metrics?.avg_prediction_time_ms || 0;

  return (
    <div className="space-y-8">
      <HeroCard
        title="How are your transactions today?"
        description="Track fraud patterns and discover insights that protect your business"
        icon={TrendingUp}
        stats={[
          { label: "Model accuracy", value: `${(accuracy * 100).toFixed(1)}%` },
          { label: "Active monitoring", value: "24/7" },
        ]}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Transactions"
          value={totalTx.toLocaleString()}
          icon={Activity}
          trend={{ value: 0, isPositive: true }}
          description="Last 30 days"
        />
        <MetricCard
          title="Fraud Cases Detected"
          value={fraudCount.toLocaleString()}
          icon={ShieldAlert}
          trend={{ value: 0, isPositive: false }}
          description={`${fraudRate.toFixed(2)}% of total`}
        />
        <MetricCard
          title="Detection Accuracy"
          value={`${(accuracy * 100).toFixed(1)}%`}
          icon={Target}
          trend={{ value: 0, isPositive: true }}
          description="Model performance"
        />
        <MetricCard
          title="Avg Processing Time"
          value={`${Math.round(avgTime)}ms`}
          icon={Clock}
          trend={{ value: 0, isPositive: false }}
          description="Per transaction"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FraudRateChart data={fraudRateData} />
        <TransactionDistributionChart 
          legitimate={totalTx - fraudCount} 
          fraudulent={fraudCount} 
        />
      </div>

      <RecentAlertsTable alerts={recentAlerts} />
    </div>
  );
}

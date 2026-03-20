import { FraudDetectionForm } from "@/components/FraudDetectionForm";
import { PredictionResult } from "@/components/PredictionResult";
import { FeatureImportanceChart } from "@/components/FeatureImportanceChart";
import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { fetchTransactions, createPrediction, PredictionResponse, createTransaction, seedTransactions, TransactionCreateRequest } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Loader2 } from "lucide-react";

export default function FraudDetection() {
  const { toast } = useToast();
  const [predictionResult, setPredictionResult] = useState<PredictionResponse | null>(null);
  const [selectedTransactionId, setSelectedTransactionId] = useState<string>("");
  const [currency, setCurrency] = useState<string>("INR");
  const [showFeatureImportance, setShowFeatureImportance] = useState<boolean>(true);
  const moneyFmt = useMemo(() => {
    const c = currency === "USD" ? "USD" : "INR";
    const locale = c === "USD" ? "en-US" : "en-IN";
    return new Intl.NumberFormat(locale, { style: "currency", currency: c });
  }, [currency]);

  useEffect(() => {
    try {
      const s = JSON.parse(localStorage.getItem("settings") || "{}");
      if (s?.ui?.currency) setCurrency(s.ui.currency);
      if (typeof s?.ui?.showFeatureImportance === "boolean") setShowFeatureImportance(s.ui.showFeatureImportance);
    } catch {}
    const handler = () => {
      try {
        const s = JSON.parse(localStorage.getItem("settings") || "{}");
        if (s?.ui?.currency) setCurrency(s.ui.currency);
        if (typeof s?.ui?.showFeatureImportance === "boolean") setShowFeatureImportance(s.ui.showFeatureImportance);
      } catch {}
    };
    window.addEventListener("settings-changed", handler);
    return () => window.removeEventListener("settings-changed", handler);
  }, []);

  // Fetch recent transactions for selection
  const { data: transactionsData, isLoading: transactionsLoading } = useQuery({
    queryKey: ["recent-transactions"],
    queryFn: () => fetchTransactions({ limit: 20, skip: 0 }),
  });

  // Create prediction mutation
  const predictionMutation = useMutation({
    mutationFn: (transactionId: string) => createPrediction({ transaction_id: transactionId }),
    onSuccess: (data) => {
      setPredictionResult(data);
      toast({
        title: "Prediction completed",
        description: `Transaction analyzed: ${data.is_fraud ? "Fraud detected" : "Legitimate"}`,
      });
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("prediction-created"));
      }
    },
    onError: (error) => {
      toast({
        title: "Prediction failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    },
  });

  const handleFormSubmit = async (data: any) => {
    try {
      // If a transaction is selected, analyze it directly
      if (selectedTransactionId) {
        predictionMutation.mutate(selectedTransactionId);
        return;
      }

      // Otherwise create a new transaction from manual input, then analyze
      let cardId = transactionsData?.transactions?.[0]?.card_id;
      if (!cardId) {
        const seeded = await seedTransactions(1);
        cardId = seeded.card_id;
      }

      const payload: TransactionCreateRequest = {
        card_id: cardId!,
        amount: Number(data.amount) || 0,
        merchant_name: data.merchant || undefined,
        merchant_category: data.category || undefined,
        transaction_type: "purchase",
        location: "India",
        transaction_date: new Date().toISOString(),
      };

      const created = await createTransaction(payload);
      setSelectedTransactionId(created.id);
      predictionMutation.mutate(created.id);
    } catch (error: any) {
      toast({
        title: "Manual analysis failed",
        description: error?.message || "Could not create transaction for analysis",
        variant: "destructive",
      });
    }
  };

  const featureChartData = useMemo(() => {
    if (!predictionResult?.feature_importance) {
      return null;
    }

    return Object.entries(predictionResult.feature_importance).map(([feature, importance]) => ({
      feature,
      importance: Number(importance.toFixed ? importance.toFixed(2) : importance),
    }));
  }, [predictionResult]);

  return (
    <div className="space-y-6 bg-background">
      <div>
        <h1 className="text-3xl font-semibold text-white">Fraud Detection</h1>
        <p className="text-muted-foreground mt-1">Analyze individual transactions for fraud risk</p>
      </div>

      {transactionsLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-semibold">Select Transaction</label>
              <select
                className="w-full p-3 border-2 rounded-md bg-background focus:outline-none focus:border-primary"
                value={selectedTransactionId}
                onChange={(e) => setSelectedTransactionId(e.target.value)}
              >
                <option value="">-- Select a transaction --</option>
                {transactionsData?.transactions.map((tx) => (
                  <option key={tx.id} value={tx.id}>
                    {tx.merchant_name || "Unknown"} - {moneyFmt.format(Number(tx.amount || 0))} - {new Date(tx.transaction_date).toLocaleDateString()}
                  </option>
                ))}
              </select>
            </div>
            {selectedTransactionId && (
              <div className="p-4 border rounded-lg bg-muted/30">
                <h4 className="text-sm font-semibold mb-2">Selected Transaction</h4>
                {(() => {
                  const tx = transactionsData?.transactions.find(t => t.id === selectedTransactionId);
                  if (!tx) return null;
                  return (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                      <div>
                        <div className="text-muted-foreground">Merchant</div>
                        <div>{tx.merchant_name || "Unknown"}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Amount</div>
                        <div>{moneyFmt.format(Number(tx.amount || 0))}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Date</div>
                        <div>{new Date(tx.transaction_date).toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Category</div>
                        <div>{tx.merchant_category || "N/A"}</div>
                      </div>
                    </div>
                  );
                })()}
              </div>
            )}
            <FraudDetectionForm onSubmit={handleFormSubmit} />
          </div>
          
          <div className="space-y-6">
            {predictionMutation.isPending && (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            )}
            {predictionResult && (
              <>
                <PredictionResult
                  fraudProbability={predictionResult.fraud_probability * 100}
                  confidence={predictionResult.confidence_score * 100}
                  recommendation={
                    predictionResult.is_fraud
                      ? `High risk transaction detected (${predictionResult.risk_level.toUpperCase()}). Manual review is strongly recommended. Fraud probability: ${(predictionResult.fraud_probability * 100).toFixed(1)}%`
                      : `Transaction appears legitimate (${predictionResult.risk_level.toUpperCase()} risk). Confidence: ${(predictionResult.confidence_score * 100).toFixed(1)}%`
                  }
                />
                {showFeatureImportance ? (
                  featureChartData && featureChartData.length > 0 ? (
                    <FeatureImportanceChart data={featureChartData} />
                  ) : (
                    <div className="p-6 border rounded-lg text-sm text-muted-foreground">
                      Feature importance data is not available for this prediction.
                    </div>
                  )
                ) : null}
              </>
            )}
          </div>
        </div>
      )}
      
    </div>
  );
}

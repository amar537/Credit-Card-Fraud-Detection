import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/StatusBadge";
import { Search, Download, Eye, Loader2 } from "lucide-react";
import { useState, useMemo, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchPredictionHistory, type PredictionHistory, PredictionResponse } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";

type HistoryRecord = {
  timestamp: string;
  transactionId: string;
  cardNumber: string;
  amount: number;
  result: "fraudulent" | "legitimate" | "pending";
  confidence: number;
  processingTime: number;
  prediction: PredictionResponse;
};

export default function History() {
  const { toast } = useToast();
  const [searchTerm, setSearchTerm] = useState("");
  const [page, setPage] = useState(0);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const limit = 20;

  const { data, isLoading, isError, error, refetch } = useQuery<PredictionHistory>({
    queryKey: ["prediction-history", page],
    queryFn: () => fetchPredictionHistory({ limit, offset: page * limit }),
    refetchInterval: 60000, // Refetch every minute
  });

  useEffect(() => {
    if (isError && error) {
      toast({
        title: "Failed to load history",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    }
  }, [isError, error, toast]);

  // Listen for new predictions and refresh immediately
  useEffect(() => {
    const handler = () => {
      refetch();
    };
    if (typeof window !== "undefined") {
      window.addEventListener("prediction-created", handler);
    }
    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("prediction-created", handler);
      }
    };
  }, [refetch]);

  const historyData: HistoryRecord[] = useMemo(() => {
    if (!data?.predictions) return [];
    
    return data.predictions.map((pred) => {
      const date = new Date(pred.timestamp);
      const result: HistoryRecord["result"] = pred.is_fraud
        ? "fraudulent"
        : pred.fraud_probability > 0.5
        ? "pending"
        : "legitimate";

      return {
        timestamp: date.toLocaleString(),
        transactionId: pred.transaction_id.slice(0, 8).toUpperCase(),
        cardNumber: `**** ${pred.transaction_id.slice(-4)}`,
        amount: 0, // Would need transaction details
        result,
        confidence: pred.confidence_score * 100,
        processingTime: pred.processing_time_ms,
        prediction: pred,
      };
    });
  }, [data]);

  // Show latest predictions only; when you upload a CSV and analyze on Fraud Detection, records appear here automatically.

  const filteredData = useMemo(() => {
    if (!searchTerm) return historyData;
    const term = searchTerm.toLowerCase();
    return historyData.filter(
      (record) =>
        record.transactionId.toLowerCase().includes(term) ||
        record.cardNumber.includes(term)
    );
  }, [historyData, searchTerm]);

  const handleExport = () => {
    const csv = [
      ["Timestamp", "Transaction ID", "Card", "Result", "Confidence", "Processing Time"],
      ...filteredData.map((record) => [
        record.timestamp,
        record.transactionId,
        record.cardNumber,
        record.result,
        record.confidence.toFixed(1),
        record.processingTime.toString(),
      ]),
    ]
      .map((row) => row.join(","))
      .join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fraud-detection-history-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast({
      title: "Export successful",
      description: "History exported to CSV",
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold text-white">Detection History</h1>
        <p className="text-muted-foreground mt-1">Complete audit trail of fraud detection activities</p>
      </div>

      <Card className="p-6">
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="flex-1">
            <Label htmlFor="search-history">Search</Label>
            <div className="relative mt-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                id="search-history"
                placeholder="Search by Transaction ID or Card Number..."
                className="pl-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                data-testid="input-search-history"
              />
            </div>
          </div>
          <div className="flex items-end gap-2">
            <Button onClick={handleExport} data-testid="button-export-csv">
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </Button>
          </div>
        </div>

        {isError && (
          <Card className="p-4 border-destructive text-destructive mb-4">
            Unable to load history. <Button variant="ghost" onClick={() => refetch()}>Try again</Button>
          </Card>
        )}

        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Transaction ID</TableHead>
                    <TableHead>Card</TableHead>
                    <TableHead>Result</TableHead>
                    <TableHead>Confidence</TableHead>
                    <TableHead>Processing Time</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredData.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                        {searchTerm ? "No results found" : "No prediction history available"}
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredData.map((record) => (
                      <>
                        <TableRow key={record.prediction.prediction_id} data-testid={`row-history-${record.transactionId}`}>
                          <TableCell className="text-sm">{record.timestamp}</TableCell>
                          <TableCell className="font-mono text-sm">{record.transactionId}</TableCell>
                          <TableCell className="font-mono text-sm">{record.cardNumber}</TableCell>
                          <TableCell>
                            <StatusBadge status={record.result} />
                          </TableCell>
                          <TableCell className="font-medium">{record.confidence.toFixed(1)}%</TableCell>
                          <TableCell className="text-sm text-muted-foreground">{record.processingTime}ms</TableCell>
                          <TableCell>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              data-testid={`button-view-${record.transactionId}`}
                              onClick={() => setExpanded((prev) => ({ ...prev, [record.transactionId]: !prev[record.transactionId] }))}
                              aria-expanded={!!expanded[record.transactionId]}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                        {expanded[record.transactionId] && (
                          <TableRow key={`${record.prediction.prediction_id}-details`}>
                            <TableCell colSpan={7} className="bg-muted/30">
                              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                                <div>
                                  <div className="text-muted-foreground">Prediction ID</div>
                                  <div className="font-mono">{record.prediction.prediction_id}</div>
                                </div>
                                <div>
                                  <div className="text-muted-foreground">Risk Level</div>
                                  <div className="capitalize">{record.prediction.risk_level}</div>
                                </div>
                                <div>
                                  <div className="text-muted-foreground">Model Version</div>
                                  <div>{record.prediction.model_version}</div>
                                </div>
                                <div>
                                  <div className="text-muted-foreground">Fraud Probability</div>
                                  <div>{(record.prediction.fraud_probability * 100).toFixed(1)}%</div>
                                </div>
                                <div>
                                  <div className="text-muted-foreground">Confidence</div>
                                  <div>{(record.prediction.confidence_score * 100).toFixed(1)}%</div>
                                </div>
                                <div>
                                  <div className="text-muted-foreground">Timestamp</div>
                                  <div>{new Date(record.prediction.timestamp).toLocaleString()}</div>
                                </div>
                              </div>
                            </TableCell>
                          </TableRow>
                        )}
                      </>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
            
            {data && data.has_more && (
              <div className="flex justify-center gap-2 mt-4">
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  Previous
                </Button>
                <span className="flex items-center px-4 text-sm text-muted-foreground">
                  Page {page + 1}
                </span>
                <Button
                  variant="outline"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!data.has_more}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}

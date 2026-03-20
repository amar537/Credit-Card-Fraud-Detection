import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { TransactionsTable } from "@/components/TransactionsTable";
import { TransactionFilters } from "@/components/TransactionFilters";
import { fetchTransactions, seedTransactions, uploadTransactionsCsv, type TransactionListApiResponse } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

type TableTransaction = {
  id: string;
  date: string;
  cardNumber: string;
  amount: number;
  merchant: string;
  location: string;
  riskScore: number;
  status: "fraudulent" | "legitimate" | "pending";
};

function mapTransactions(data?: TransactionListApiResponse): TableTransaction[] {
  if (!data) return [];

  return data.transactions.map((txn) => {
    const amount = Number(txn.amount ?? 0);
    const riskScore = txn.fraud_score ? Math.round(txn.fraud_score * 100) : 0;
    const status: TableTransaction["status"] = txn.is_fraud
      ? "fraudulent"
      : riskScore > 60
      ? "pending"
      : "legitimate";

    const cardSuffix = txn.card_id ? txn.card_id.slice(-4) : "0000";

    return {
      id: txn.id,
      date: new Date(txn.transaction_date).toLocaleString(),
      cardNumber: `**** **** **** ${cardSuffix}`,
      amount,
      merchant: txn.merchant_name ?? "Unknown Merchant",
      location: txn.location ?? "Unknown",
      riskScore,
      status,
    };
  });
}

export default function Transactions() {
  const { toast } = useToast();
  const [filters, setFilters] = useState<{
    searchId?: string;
    status?: string;
    riskLevel?: string;
  }>({});
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const queryParams = useMemo(() => {
    const params: Record<string, string | boolean> = {};
    if (filters.status && filters.status !== "all") {
      params.is_fraud = filters.status === "fraudulent";
    }
    return params;
  }, [filters]);

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["transactions", queryParams],
    queryFn: () => fetchTransactions(queryParams),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Auto-seed demo data once per session for this user if empty
  useEffect(() => {
    const run = async () => {
      if (isLoading || isFetching || isError) return;
      const count = (data as any)?.transactions?.length ?? 0;
      if (count > 0) return;
      const userKeyPart = (typeof window !== "undefined" && localStorage.getItem("user_email")) || "anon";
      const seededKey = `seeded_demo_${userKeyPart}`;
      if (typeof window !== "undefined" && !sessionStorage.getItem(seededKey)) {
        try {
          await seedTransactions(30);
        } catch (e) {
          console.error("Failed to auto-seed demo data", e);
        } finally {
          sessionStorage.setItem(seededKey, "1");
          await refetch();
        }
      }
    };
    run();
  }, [data, isLoading, isFetching, isError, refetch]);

  const allTransactions = useMemo(() => mapTransactions(data), [data]);

  const filteredTransactions = useMemo(() => {
    let filtered = allTransactions;

    if (filters.searchId) {
      filtered = filtered.filter((tx) =>
        tx.id.toLowerCase().includes(filters.searchId!.toLowerCase())
      );
    }

    if (filters.status && filters.status !== "all") {
      filtered = filtered.filter((tx) => tx.status === filters.status);
    }

    if (filters.riskLevel && filters.riskLevel !== "all") {
      const riskMap: Record<string, [number, number]> = {
        high: [70, 100],
        medium: [40, 69],
        low: [0, 39],
      };
      const [min, max] = riskMap[filters.riskLevel] || [0, 100];
      filtered = filtered.filter(
        (tx) => tx.riskScore >= min && tx.riskScore <= max
      );
    }

    return filtered;
  }, [allTransactions, filters]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between relative z-10">
        <div>
          <h1 className="text-3xl font-semibold text-white">Transaction Monitor</h1>
          <p className="text-muted-foreground mt-1">
            Real-time transaction monitoring and analysis pulled from the API
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            className="text-sm text-primary hover:underline"
            onClick={() => refetch()}
            disabled={isLoading || isFetching}
          >
            Refresh
          </button>
        </div>
      </div>

      <TransactionFilters onFilterChange={setFilters} />

      <Card className="p-4">
        <div className="flex flex-col md:flex-row items-start md:items-center gap-3">
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files && e.target.files[0] ? e.target.files[0] : null)}
            data-testid="input-upload-transactions"
          />
          <Button
            onClick={async () => {
              if (!file) return;
              setIsUploading(true);
              try {
                const res = await uploadTransactionsCsv(file);
                setFile(null);
                toast({
                  title: "Import completed",
                  description: `Imported ${res.created} transactions`,
                });
                await refetch();
              } catch (e: any) {
                console.error("Upload failed", e);
                toast({
                  title: "Upload failed",
                  description: e?.message || "Could not import CSV",
                  variant: "destructive",
                });
              } finally {
                setIsUploading(false);
              }
            }}
            disabled={!file || isUploading || isLoading || isFetching}
            data-testid="button-upload-transactions"
          >
            {isUploading ? "Uploading..." : "Upload File"}
          </Button>
        </div>
      </Card>

      {isError && (
        <Card className="p-4 border-destructive text-destructive">
          Unable to load transactions. Please try refreshing.
        </Card>
      )}

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : (
        <div className="flex flex-col md:flex-row gap-6">
          <TransactionsTable transactions={filteredTransactions} />
        </div>
      )}
    </div>
  );
}

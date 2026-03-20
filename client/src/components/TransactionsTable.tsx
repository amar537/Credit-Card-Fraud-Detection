import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { RiskBadge } from "./RiskBadge";
import { StatusBadge } from "./StatusBadge";
import { Eye, ChevronLeft, ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";

interface Transaction {
  id: string;
  date: string;
  cardNumber: string;
  amount: number;
  merchant: string;
  location: string;
  riskScore: number;
  status: "fraudulent" | "legitimate" | "pending";
}

interface TransactionsTableProps {
  transactions: Transaction[];
  onViewDetails?: (id: string) => void;
}

export function TransactionsTable({ transactions, onViewDetails }: TransactionsTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const itemsPerPage = 10;
  const totalPages = Math.ceil(transactions.length / itemsPerPage);
  const inr = useMemo(() => new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }), []);
  
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentTransactions = useMemo(() => transactions.slice(startIndex, endIndex), [transactions, startIndex, endIndex]);

  const getRiskLevel = (score: number): "high" | "medium" | "low" => {
    if (score >= 70) return "high";
    if (score >= 40) return "medium";
    return "low";
  };

  return (
    <Card className="p-6">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Transaction ID</TableHead>
              <TableHead>Date & Time</TableHead>
              <TableHead>Card Number</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Merchant</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Risk Score</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {currentTransactions.map((transaction) => (
              <>
                <TableRow key={transaction.id} data-testid={`row-transaction-${transaction.id}`}>
                  <TableCell className="font-mono text-sm">{transaction.id}</TableCell>
                  <TableCell className="text-sm">{transaction.date}</TableCell>
                  <TableCell className="font-mono text-sm">{transaction.cardNumber}</TableCell>
                  <TableCell className="font-semibold">{inr.format(transaction.amount)}</TableCell>
                  <TableCell>{transaction.merchant}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{transaction.location}</TableCell>
                  <TableCell>
                    <RiskBadge level={getRiskLevel(transaction.riskScore)} score={transaction.riskScore} />
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={transaction.status} />
                  </TableCell>
                  <TableCell>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => {
                        if (onViewDetails) return onViewDetails(transaction.id);
                        setExpanded((prev) => ({ ...prev, [transaction.id]: !prev[transaction.id] }));
                      }}
                      aria-expanded={!!expanded[transaction.id]}
                      data-testid={`button-view-details-${transaction.id}`}
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                  </TableCell>
                </TableRow>
                {expanded[transaction.id] && (
                  <TableRow key={`${transaction.id}-details`}>
                    <TableCell colSpan={9} className="bg-muted/30">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-muted-foreground">Transaction ID</div>
                          <div className="font-mono">{transaction.id}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Card</div>
                          <div className="font-mono">{transaction.cardNumber}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Amount</div>
                          <div className="font-semibold">{inr.format(transaction.amount)}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Merchant</div>
                          <div>{transaction.merchant}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Location</div>
                          <div>{transaction.location}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Risk Score</div>
                          <div>{transaction.riskScore}</div>
                        </div>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between mt-4">
        <p className="text-sm text-muted-foreground">
          Showing {startIndex + 1}-{Math.min(endIndex, transactions.length)} of {transactions.length}
        </p>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            data-testid="button-prev-page"
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            data-testid="button-next-page"
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}

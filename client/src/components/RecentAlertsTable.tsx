import React from "react";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { RiskBadge } from "./RiskBadge";
import { StatusBadge } from "./StatusBadge";
import { Button } from "@/components/ui/button";
import { Eye } from "lucide-react";
import { useState } from "react";

interface Alert {
  id: string;
  amount: number;
  timestamp: string;
  riskScore: number;
  status: "fraudulent" | "legitimate" | "pending";
}

interface RecentAlertsTableProps {
  alerts: Alert[];
  onViewDetails?: (id: string) => void;
}

export function RecentAlertsTable({ alerts, onViewDetails }: RecentAlertsTableProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const getRiskLevel = (score: number): "high" | "medium" | "low" => {
    if (score >= 70) return "high";
    if (score >= 40) return "medium";
    return "low";
  };

  return (
    <Card className="p-6 hover-elevate transition-all duration-300 bg-card/50 backdrop-blur-sm border-white/5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Recent Fraud Alerts</h3>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-destructive/10 rounded-full border border-destructive/30">
          <div className="w-2 h-2 bg-destructive rounded-full animate-pulse" />
          <span className="text-xs text-destructive/90 font-medium">Real-time</span>
        </div>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Transaction ID</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Time</TableHead>
            <TableHead>Risk Score</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {alerts.map((alert) => (
            <React.Fragment key={alert.id}>
              <TableRow key={`${alert.id}-row`} data-testid={`row-alert-${alert.id}`}>
                <TableCell className="font-mono text-sm">{alert.id}</TableCell>
                <TableCell className="font-semibold">${alert.amount.toFixed(2)}</TableCell>
                <TableCell className="text-sm text-muted-foreground">{alert.timestamp}</TableCell>
                <TableCell>
                  <RiskBadge level={getRiskLevel(alert.riskScore)} score={alert.riskScore} />
                </TableCell>
                <TableCell>
                  <StatusBadge status={alert.status} />
                </TableCell>
                <TableCell>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => {
                      if (onViewDetails) return onViewDetails(alert.id);
                      setExpanded((prev) => ({ ...prev, [alert.id]: !prev[alert.id] }));
                    }}
                    aria-expanded={!!expanded[alert.id]}
                    data-testid={`button-view-${alert.id}`}
                  >
                    <Eye className="w-4 h-4" />
                  </Button>
                </TableCell>
              </TableRow>
              {expanded[alert.id] && (
                <TableRow key={`${alert.id}-details`}>
                  <TableCell colSpan={6} className="bg-muted/30">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <div className="text-muted-foreground">Alert ID</div>
                        <div className="font-mono">{alert.id}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Amount</div>
                        <div className="font-semibold">${alert.amount.toFixed(2)}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Time</div>
                        <div>{alert.timestamp}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Risk Score</div>
                        <div>{alert.riskScore}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Status</div>
                        <div>{alert.status}</div>
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </React.Fragment>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}

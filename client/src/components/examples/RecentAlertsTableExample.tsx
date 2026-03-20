import { RecentAlertsTable } from "../RecentAlertsTable";

export default function RecentAlertsTableExample() {
  const mockAlerts = [
    { id: "TXN-8492", amount: 2450.00, timestamp: "2 min ago", riskScore: 95, status: "fraudulent" as const },
    { id: "TXN-8491", amount: 125.50, timestamp: "5 min ago", riskScore: 85, status: "fraudulent" as const },
    { id: "TXN-8490", amount: 890.25, timestamp: "12 min ago", riskScore: 78, status: "pending" as const },
  ];

  return (
    <div className="p-4">
      <RecentAlertsTable 
        alerts={mockAlerts} 
        onViewDetails={(id) => console.log("View details:", id)}
      />
    </div>
  );
}

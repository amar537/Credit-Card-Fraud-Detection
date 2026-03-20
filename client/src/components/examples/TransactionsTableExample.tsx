import { TransactionsTable } from "../TransactionsTable";

export default function TransactionsTableExample() {
  const mockTransactions = [
    {
      id: "TXN-8492",
      date: "Nov 7, 2025 14:32",
      cardNumber: "**** **** **** 1234",
      amount: 2450.00,
      merchant: "Electronics Store",
      location: "New York, NY",
      riskScore: 95,
      status: "fraudulent" as const,
    },
    {
      id: "TXN-8491",
      date: "Nov 7, 2025 14:15",
      cardNumber: "**** **** **** 5678",
      amount: 125.50,
      merchant: "Coffee Shop",
      location: "San Francisco, CA",
      riskScore: 12,
      status: "legitimate" as const,
    },
  ];

  return (
    <div className="p-4">
      <TransactionsTable 
        transactions={mockTransactions}
        onViewDetails={(id) => console.log("View details:", id)}
      />
    </div>
  );
}

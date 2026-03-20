import { FeatureImportanceChart } from "../FeatureImportanceChart";

export default function FeatureImportanceChartExample() {
  const mockData = [
    { feature: "Transaction Amount", importance: 85 },
    { feature: "Time Since Last", importance: 72 },
    { feature: "Distance from Last", importance: 65 },
    { feature: "Merchant Category", importance: 58 },
    { feature: "Transaction Frequency", importance: 45 },
  ];

  return (
    <div className="p-4">
      <FeatureImportanceChart data={mockData} />
    </div>
  );
}

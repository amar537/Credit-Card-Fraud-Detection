import { TransactionDistributionChart } from "../TransactionDistributionChart";

export default function TransactionDistributionChartExample() {
  return (
    <div className="p-4">
      <TransactionDistributionChart legitimate={23840} fraudulent={747} />
    </div>
  );
}

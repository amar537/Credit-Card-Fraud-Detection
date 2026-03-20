import { FraudRateChart } from "../FraudRateChart";

export default function FraudRateChartExample() {
  const mockData = [
    { time: "00:00", rate: 2.1 },
    { time: "04:00", rate: 1.8 },
    { time: "08:00", rate: 3.2 },
    { time: "12:00", rate: 2.5 },
    { time: "16:00", rate: 3.8 },
    { time: "20:00", rate: 2.9 },
  ];

  return (
    <div className="p-4">
      <FraudRateChart data={mockData} />
    </div>
  );
}

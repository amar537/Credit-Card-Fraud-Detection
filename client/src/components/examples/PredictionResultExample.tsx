import { PredictionResult } from "../PredictionResult";

export default function PredictionResultExample() {
  return (
    <div className="p-4 max-w-md">
      <PredictionResult
        fraudProbability={85.5}
        confidence={92.3}
        recommendation="High risk transaction. Manual review recommended before approval."
      />
    </div>
  );
}

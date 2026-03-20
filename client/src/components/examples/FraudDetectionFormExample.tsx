import { FraudDetectionForm } from "../FraudDetectionForm";

export default function FraudDetectionFormExample() {
  return (
    <div className="p-4 max-w-2xl">
      <FraudDetectionForm onSubmit={(data) => console.log("Form data:", data)} />
    </div>
  );
}

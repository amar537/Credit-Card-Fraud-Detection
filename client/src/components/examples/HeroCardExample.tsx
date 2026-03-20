import { HeroCard } from "../HeroCard";
import { Shield } from "lucide-react";

export default function HeroCardExample() {
  return (
    <div className="p-4">
      <HeroCard
        title="How are your transactions today?"
        description="Real-time fraud detection monitoring and insights"
        icon={Shield}
        stats={[
          { label: "7-day average", value: "96.8%" },
          { label: "Today's accuracy", value: "98.2%" },
        ]}
      />
    </div>
  );
}

import { RiskBadge } from "../RiskBadge";

export default function RiskBadgeExample() {
  return (
    <div className="p-4 flex gap-2">
      <RiskBadge level="high" score={95} />
      <RiskBadge level="medium" score={65} />
      <RiskBadge level="low" score={15} />
    </div>
  );
}

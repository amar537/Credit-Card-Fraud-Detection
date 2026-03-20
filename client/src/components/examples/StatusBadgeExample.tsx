import { StatusBadge } from "../StatusBadge";

export default function StatusBadgeExample() {
  return (
    <div className="p-4 flex gap-2">
      <StatusBadge status="fraudulent" />
      <StatusBadge status="legitimate" />
      <StatusBadge status="pending" />
    </div>
  );
}

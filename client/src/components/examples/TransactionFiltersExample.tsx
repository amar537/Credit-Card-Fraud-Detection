import { TransactionFilters } from "../TransactionFilters";

export default function TransactionFiltersExample() {
  return (
    <div className="p-4">
      <TransactionFilters onFilterChange={(filters) => console.log("Filters:", filters)} />
    </div>
  );
}

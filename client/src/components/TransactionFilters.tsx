import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Search, SlidersHorizontal } from "lucide-react";
import { useState } from "react";

interface TransactionFiltersProps {
  onFilterChange?: (filters: any) => void;
}

export function TransactionFilters({ onFilterChange }: TransactionFiltersProps) {
  const [searchId, setSearchId] = useState("");
  const [status, setStatus] = useState("all");
  const [riskLevel, setRiskLevel] = useState("all");

  const handleApplyFilters = () => {
    onFilterChange?.({ searchId, status, riskLevel });
    console.log("Filters applied:", { searchId, status, riskLevel });
  };

  return (
    <Card className="p-6">
      <div className="flex items-center gap-2 mb-4">
        <SlidersHorizontal className="w-5 h-5 text-muted-foreground" />
        <h3 className="text-lg font-semibold">Filters</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="space-y-2">
          <Label htmlFor="search-id">Transaction ID</Label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              id="search-id"
              placeholder="Search ID..."
              className="pl-9"
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              data-testid="input-search-id"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="status">Status</Label>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger id="status" data-testid="select-status">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="fraudulent">Fraudulent</SelectItem>
              <SelectItem value="legitimate">Legitimate</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="risk">Risk Level</Label>
          <Select value={riskLevel} onValueChange={setRiskLevel}>
            <SelectTrigger id="risk" data-testid="select-risk">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-end">
          <Button onClick={handleApplyFilters} className="w-full" data-testid="button-apply-filters">
            Apply Filters
          </Button>
        </div>
      </div>
    </Card>
  );
}

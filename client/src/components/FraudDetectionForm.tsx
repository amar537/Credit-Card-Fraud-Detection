import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useState } from "react";

interface FraudDetectionFormProps {
  onSubmit?: (data: any) => void;
}

export function FraudDetectionForm({ onSubmit }: FraudDetectionFormProps) {
  const [cardNumber, setCardNumber] = useState("");
  const [amount, setAmount] = useState("");
  const [merchant, setMerchant] = useState("");
  const [category, setCategory] = useState("retail");
  const [isForeign, setIsForeign] = useState(false);
  const [isOnline, setIsOnline] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const formData = {
      cardNumber,
      amount: parseFloat(amount),
      merchant,
      category,
      isForeign,
      isOnline,
    };
    onSubmit?.(formData);
    console.log("Form submitted:", formData);
  };

  const formatCardNumber = (value: string) => {
    const cleaned = value.replace(/\s/g, "");
    const chunks = cleaned.match(/.{1,4}/g) || [];
    return chunks.join(" ");
  };

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-6">Transaction Details</h3>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Card Information</h4>
          
          <div className="space-y-2">
            <Label htmlFor="card-number">Card Number</Label>
            <Input
              id="card-number"
              placeholder="1234 5678 9012 3456"
              maxLength={19}
              value={cardNumber}
              onChange={(e) => setCardNumber(formatCardNumber(e.target.value))}
              data-testid="input-card-number"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="amount">Transaction Amount (₹)</Label>
            <Input
              id="amount"
              type="number"
              step="0.01"
              placeholder="₹0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              data-testid="input-amount"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="merchant">Merchant Name</Label>
            <Input
              id="merchant"
              placeholder="Store Name"
              value={merchant}
              onChange={(e) => setMerchant(e.target.value)}
              data-testid="input-merchant"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="category">Merchant Category</Label>
            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger id="category" data-testid="select-category">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="retail">Retail</SelectItem>
                <SelectItem value="restaurants">Restaurants</SelectItem>
                <SelectItem value="travel">Travel</SelectItem>
                <SelectItem value="entertainment">Entertainment</SelectItem>
                <SelectItem value="utilities">Utilities</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Advanced Features</h4>
          
          <div className="flex items-center justify-between">
            <Label htmlFor="foreign">Foreign Transaction</Label>
            <Switch
              id="foreign"
              checked={isForeign}
              onCheckedChange={setIsForeign}
              data-testid="switch-foreign"
            />
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="online">Online Transaction</Label>
            <Switch
              id="online"
              checked={isOnline}
              onCheckedChange={setIsOnline}
              data-testid="switch-online"
            />
          </div>
        </div>

        <Button type="submit" className="w-full" data-testid="button-analyze">
          Analyze Transaction
        </Button>
      </form>
    </Card>
  );
}

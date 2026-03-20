import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { RiskBadge } from "./RiskBadge";
import { AlertTriangle, CheckCircle2 } from "lucide-react";

interface PredictionResultProps {
  fraudProbability: number;
  confidence: number;
  recommendation: string;
}

export function PredictionResult({ fraudProbability, confidence, recommendation }: PredictionResultProps) {
  const isFraud = fraudProbability >= 50;
  const getRiskLevel = (score: number): "high" | "medium" | "low" => {
    if (score >= 70) return "high";
    if (score >= 40) return "medium";
    return "low";
  };

  return (
    <Card className="p-6 relative overflow-hidden shadow-xl border-2">
      <div className={`absolute inset-0 bg-gradient-to-br ${isFraud ? 'from-destructive/5 to-transparent' : 'from-success/5 to-transparent'}`} />
      <div className="relative">
        <h3 className="text-lg font-semibold mb-6">Prediction Results</h3>
        
        <div className="flex flex-col items-center justify-center py-8">
          <div className={`relative ${isFraud ? 'animate-pulse' : ''}`}>
            {isFraud ? (
              <div className="relative">
                <div className="absolute inset-0 bg-destructive/20 rounded-full blur-xl" />
                <AlertTriangle className="w-24 h-24 text-destructive relative" />
              </div>
            ) : (
              <div className="relative">
                <div className="absolute inset-0 bg-success/20 rounded-full blur-xl" />
                <CheckCircle2 className="w-24 h-24 text-success relative" />
              </div>
            )}
          </div>
          
          <h4 className={`text-5xl font-bold mb-2 mt-4 bg-gradient-to-br ${isFraud ? 'from-destructive to-destructive/70' : 'from-success to-success/70'} bg-clip-text text-transparent`} data-testid="text-fraud-probability">
            {fraudProbability.toFixed(1)}%
          </h4>
          <p className="text-sm text-muted-foreground mb-4">Fraud Probability</p>
          
          <RiskBadge level={getRiskLevel(fraudProbability)} />
        </div>
      </div>

      <div className="space-y-4 mt-6">
        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-muted-foreground">Fraud Probability</span>
            <span className="font-semibold">{fraudProbability.toFixed(1)}%</span>
          </div>
          <Progress value={fraudProbability} className="h-2" />
        </div>

        <div>
          <div className="flex justify-between text-sm mb-2">
            <span className="text-muted-foreground">Model Confidence</span>
            <span className="font-semibold">{confidence.toFixed(1)}%</span>
          </div>
          <Progress value={confidence} className="h-2" />
        </div>

        <div className="bg-muted p-4 rounded-lg mt-6">
          <h5 className="text-sm font-semibold mb-2">Recommendation</h5>
          <p className="text-sm text-muted-foreground">{recommendation}</p>
        </div>
      </div>
    </Card>
  );
}

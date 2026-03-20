import { Card } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";
import { useState } from "react";

export default function ModelInfo() {
  const [openSections, setOpenSections] = useState({
    whatIsLSTM: true,
    howDetects: true,
    advantages: true,
  });

  const toggleSection = (section: keyof typeof openSections) => {
    setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-semibold text-white">LSTM-RNN Model Information</h1>
        <p className="text-muted-foreground mt-1">Technical details and architecture overview</p>
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Model Architecture</h3>
        <div className="bg-muted/30 p-8 rounded-lg">
          <div className="flex items-center justify-around">
            <div className="text-center">
              <div className="bg-primary/10 border-2 border-primary rounded-lg p-4 w-24 h-24 flex items-center justify-center">
                <span className="text-sm font-semibold">Input<br/>Layer</span>
              </div>
              <p className="text-xs text-muted-foreground mt-2">32 features</p>
            </div>
            <div className="text-2xl text-muted-foreground">→</div>
            <div className="text-center">
              <div className="bg-primary/20 border-2 border-primary rounded-lg p-4 w-24 h-24 flex items-center justify-center">
                <span className="text-sm font-semibold">LSTM<br/>Layer 1</span>
              </div>
              <p className="text-xs text-muted-foreground mt-2">128 units</p>
            </div>
            <div className="text-2xl text-muted-foreground">→</div>
            <div className="text-center">
              <div className="bg-primary/20 border-2 border-primary rounded-lg p-4 w-24 h-24 flex items-center justify-center">
                <span className="text-sm font-semibold">LSTM<br/>Layer 2</span>
              </div>
              <p className="text-xs text-muted-foreground mt-2">64 units</p>
            </div>
            <div className="text-2xl text-muted-foreground">→</div>
            <div className="text-center">
              <div className="bg-primary/10 border-2 border-primary rounded-lg p-4 w-24 h-24 flex items-center justify-center">
                <span className="text-sm font-semibold">Output<br/>Layer</span>
              </div>
              <p className="text-xs text-muted-foreground mt-2">Binary</p>
            </div>
          </div>
        </div>
      </Card>

      <p className="italic text-sm text-muted-foreground">Developed by Karthik & Team</p>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Model Specifications</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Training Dataset</p>
            <p className="font-semibold">284,807 transactions</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Epochs</p>
            <p className="font-semibold">50</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Batch Size</p>
            <p className="font-semibold">256</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Learning Rate</p>
            <p className="font-semibold">0.001</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Optimizer</p>
            <p className="font-semibold">Adam</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Loss Function</p>
            <p className="font-semibold">Binary Crossentropy</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Training Split</p>
            <p className="font-semibold">80/20</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Model Version</p>
            <p className="font-semibold">v2.1.0</p>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Performance Metrics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-muted/30 rounded-lg">
            <p className="text-3xl font-bold text-primary">96.8%</p>
            <p className="text-sm text-muted-foreground mt-1">Accuracy</p>
          </div>
          <div className="text-center p-4 bg-muted/30 rounded-lg">
            <p className="text-3xl font-bold text-primary">94.2%</p>
            <p className="text-sm text-muted-foreground mt-1">Precision</p>
          </div>
          <div className="text-center p-4 bg-muted/30 rounded-lg">
            <p className="text-3xl font-bold text-primary">91.5%</p>
            <p className="text-sm text-muted-foreground mt-1">Recall</p>
          </div>
          <div className="text-center p-4 bg-muted/30 rounded-lg">
            <p className="text-3xl font-bold text-primary">92.8%</p>
            <p className="text-sm text-muted-foreground mt-1">F1-Score</p>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div>
            <p className="text-sm text-muted-foreground">Training Time</p>
            <p className="font-semibold">2.5 hours</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Inference Time</p>
            <p className="font-semibold">47ms per transaction</p>
          </div>
        </div>
      </Card>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Educational Content</h3>
        
        <Collapsible open={openSections.whatIsLSTM} onOpenChange={() => toggleSection("whatIsLSTM")}>
          <Card className="p-6">
            <CollapsibleTrigger className="flex items-center justify-between w-full text-left" data-testid="button-toggle-lstm">
              <h4 className="font-semibold">What is LSTM-RNN?</h4>
              <ChevronDown className={`w-5 h-5 transition-transform ${openSections.whatIsLSTM ? 'rotate-180' : ''}`} />
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-4 text-sm text-muted-foreground space-y-2">
              <p>
                Long Short-Term Memory (LSTM) is a type of Recurrent Neural Network (RNN) architecture designed to learn from sequential data. Unlike traditional neural networks, LSTMs can remember information over long sequences, making them ideal for time-series analysis.
              </p>
              <p>
                In fraud detection, LSTM networks excel at identifying patterns in transaction sequences, detecting anomalies based on historical spending behavior, and adapting to new fraud patterns over time.
              </p>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        <Collapsible open={openSections.howDetects} onOpenChange={() => toggleSection("howDetects")}>
          <Card className="p-6">
            <CollapsibleTrigger className="flex items-center justify-between w-full text-left" data-testid="button-toggle-detection">
              <h4 className="font-semibold">How It Detects Fraud</h4>
              <ChevronDown className={`w-5 h-5 transition-transform ${openSections.howDetects ? 'rotate-180' : ''}`} />
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-4 text-sm text-muted-foreground space-y-2">
              <ol className="list-decimal list-inside space-y-2">
                <li><strong>Data Preprocessing:</strong> Transaction data is normalized and sequenced based on temporal patterns.</li>
                <li><strong>Feature Extraction:</strong> The model analyzes 32 features including amount, merchant category, location, and time-based patterns.</li>
                <li><strong>Pattern Recognition:</strong> LSTM layers identify normal vs. anomalous spending patterns.</li>
                <li><strong>Risk Scoring:</strong> The output layer generates a probability score (0-100%) indicating fraud likelihood.</li>
                <li><strong>Decision Making:</strong> Transactions above the 70% threshold are flagged for review.</li>
              </ol>
            </CollapsibleContent>
          </Card>
        </Collapsible>

        <Collapsible open={openSections.advantages} onOpenChange={() => toggleSection("advantages")}>
          <Card className="p-6">
            <CollapsibleTrigger className="flex items-center justify-between w-full text-left" data-testid="button-toggle-advantages">
              <h4 className="font-semibold">Advantages Over Traditional Methods</h4>
              <ChevronDown className={`w-5 h-5 transition-transform ${openSections.advantages ? 'rotate-180' : ''}`} />
            </CollapsibleTrigger>
            <CollapsibleContent className="mt-4 text-sm text-muted-foreground space-y-2">
              <ul className="list-disc list-inside space-y-2">
                <li><strong>Temporal Analysis:</strong> Understands transaction sequences and time-based patterns, unlike rule-based systems.</li>
                <li><strong>Adaptive Learning:</strong> Continuously improves as it processes more transactions, adapting to new fraud tactics.</li>
                <li><strong>Higher Accuracy:</strong> 96.8% accuracy vs. 85-90% for traditional statistical methods.</li>
                <li><strong>Reduced False Positives:</strong> Better at distinguishing legitimate unusual transactions from fraud.</li>
                <li><strong>Real-time Processing:</strong> 47ms inference time enables immediate fraud detection.</li>
              </ul>
            </CollapsibleContent>
          </Card>
        </Collapsible>
      </div>
    </div>
  );
}

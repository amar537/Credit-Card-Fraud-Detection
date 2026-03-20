import { Card } from "@/components/ui/card";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

export default function Settings() {
  const [currency, setCurrency] = useState<string>("INR");
  const [showFeatureImportance, setShowFeatureImportance] = useState<boolean>(true);
  const [historyItems, setHistoryItems] = useState<number>(20);
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true);
  const [refreshSec, setRefreshSec] = useState<number>(60);

  useEffect(() => {
    try {
      const s = JSON.parse(localStorage.getItem("settings") || "{}");
      if (s?.ui?.currency) setCurrency(s.ui.currency);
      if (typeof s?.ui?.showFeatureImportance === "boolean") setShowFeatureImportance(s.ui.showFeatureImportance);
      if (s?.history?.itemsPerPage) setHistoryItems(Number(s.history.itemsPerPage));
      if (typeof s?.history?.autoRefresh === "boolean") setAutoRefresh(s.history.autoRefresh);
      if (s?.history?.refreshSec) setRefreshSec(Number(s.history.refreshSec));
    } catch {}
  }, []);

  const save = () => {
    const next = {
      ui: { currency, showFeatureImportance },
      history: { itemsPerPage: historyItems, autoRefresh, refreshSec },
    };
    localStorage.setItem("settings", JSON.stringify(next));
    if (typeof window !== "undefined") {
      window.dispatchEvent(new Event("settings-changed"));
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-3xl font-semibold text-white">Settings</h1>
        <p className="text-muted-foreground mt-1">Configure the required features and preferences for this application</p>
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">User Settings</h3>
        <div className="space-y-4 text-sm">
          <div>
            <div className="font-medium mb-1">Currency</div>
            <select className="w-full p-2 rounded bg-background border" value={currency} onChange={(e) => setCurrency(e.target.value)}>
              <option value="INR">INR (₹)</option>
              <option value="USD">USD ($)</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <input id="featImp" type="checkbox" className="w-4 h-4" checked={showFeatureImportance} onChange={(e) => setShowFeatureImportance(e.target.checked)} />
            <label htmlFor="featImp">Show feature importance on Fraud Detection</label>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="md:col-span-1">
              <div className="font-medium mb-1">History: items per page</div>
              <select className="w-full p-2 rounded bg-background border" value={historyItems} onChange={(e) => setHistoryItems(Number(e.target.value))}>
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </div>
            <div className="md:col-span-1 flex items-center gap-2">
              <input id="autoRef" type="checkbox" className="w-4 h-4" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} />
              <label htmlFor="autoRef">History: auto refresh</label>
            </div>
            <div className="md:col-span-1">
              <div className="font-medium mb-1">History: refresh interval (sec)</div>
              <input type="number" min={5} className="w-full p-2 rounded bg-background border" value={refreshSec} onChange={(e) => setRefreshSec(Number(e.target.value) || 60)} />
            </div>
          </div>
          <div>
            <Button onClick={save}>Save Settings</Button>
          </div>
        </div>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Application Features (Required)</h3>
        <ul className="list-disc pl-6 space-y-1 text-sm">
          <li>Authentication with JWT (access & refresh tokens)</li>
          <li>Optional Google OAuth login</li>
          <li>Transactions: list, filter, details, CSV import</li>
          <li>Fraud Prediction: single-transaction analysis</li>
          <li>Prediction History: user-scoped records</li>
          <li>Analytics: dashboard metrics and trends</li>
          <li>INR currency formatting across UI</li>
          <li>Feature importance visualization for predictions</li>
        </ul>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-2">Authentication Settings</h3>
        <ul className="list-disc pl-6 space-y-1 text-sm">
          <li>Session expiry: 30 minutes (access), 7 days (refresh)</li>
          <li>Google OAuth: enable/disable, client ID/secret, redirect URI</li>
          <li>Password policy: strong passwords recommended</li>
        </ul>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-2">Data & Localization</h3>
        <ul className="list-disc pl-6 space-y-1 text-sm">
          <li>Currency: INR (₹) for display</li>
          <li>CSV import columns: amount, merchant_name, merchant_category, transaction_type, location, ip_address, transaction_date</li>
          <li>Max CSV upload size: 10 MB</li>
          <li>Duplicate transaction guard: 1-minute window</li>
        </ul>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-2">Predictions</h3>
        <ul className="list-disc pl-6 space-y-1 text-sm">
          <li>Model: LSTM/RNN (TensorFlow)</li>
          <li>Risk levels: low, medium, high, critical</li>
          <li>Auto-create fraud alerts on high/critical</li>
          <li>Show feature importance if available</li>
        </ul>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-2">History</h3>
        <ul className="list-disc pl-6 space-y-1 text-sm">
          <li>Displays predictions generated by the current user</li>
          <li>Auto-refresh on new prediction events</li>
          <li>Pagination: 20 records per page (default)</li>
        </ul>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-2">Analytics</h3>
        <ul className="list-disc pl-6 space-y-1 text-sm">
          <li>Dashboard KPIs: totals, fraud rate, average amount, alerts</li>
          <li>Trends: time-series fraud rate and amounts</li>
          <li>Breakdowns: geography and merchant categories</li>
        </ul>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-2">Security & Access</h3>
        <ul className="list-disc pl-6 space-y-1 text-sm">
          <li>CORS: allow localhost frontend origin</li>
          <li>Rate limits: per-minute and per-hour caps</li>
          <li>Authorization checks on user-owned resources</li>
        </ul>
      </Card>

      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-2">UI Preferences</h3>
        <ul className="list-disc pl-6 space-y-1 text-sm">
          <li>Theme: dark (default)</li>
          <li>Date format: locale-based</li>
          <li>Number formatting: en-IN for currency</li>
        </ul>
      </Card>
    </div>
  );
}

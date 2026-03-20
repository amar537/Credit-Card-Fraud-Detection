import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Shield, Lock, Mail, Sparkles, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { login, storeAuthTokens, API_BASE_URL } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export default function Login() {
  const [, setLocation] = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  // Handle Google OAuth callback tokens passed via URL fragment
  useEffect(() => {
    if (typeof window === "undefined") return;
    const hash = window.location.hash?.replace(/^#/, "");
    if (!hash) return;
    const params = new URLSearchParams(hash);
    const access = params.get("access_token");
    const refresh = params.get("refresh_token");
    const emailFromOAuth = params.get("email");
    const nameFromOAuth = params.get("name") || "User";
    if (access && refresh) {
      try {
        localStorage.setItem("access_token", access);
        localStorage.setItem("refresh_token", refresh);
        if (emailFromOAuth) localStorage.setItem("user_email", emailFromOAuth);
        if (nameFromOAuth) localStorage.setItem("user_name", nameFromOAuth);
        window.history.replaceState({}, document.title, window.location.pathname);
        window.dispatchEvent(new Event("auth-changed"));
        setLocation("/");
      } catch (e) {
        console.error("Failed to store OAuth tokens", e);
      }
    }
  }, [setLocation]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const data = await login({ email, password });
      storeAuthTokens(data);

      if (rememberMe) {
        localStorage.setItem("remembered_email", email);
      } else {
        localStorage.removeItem("remembered_email");
      }

      window.dispatchEvent(new Event("auth-changed"));
      setLocation("/");
    } catch (error) {
      const description =
        error instanceof Error ? error.message : "Unable to sign in. Please try again.";
      toast({ title: "Login failed", description, variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-background">
      
      <Card className="w-full max-w-md p-8 relative shadow-2xl border-2 backdrop-blur-sm bg-card/95">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2">
          <div className="bg-gradient-to-br from-primary to-chart-2 p-6 rounded-2xl shadow-xl">
            <Shield className="w-12 h-12 text-primary-foreground" />
          </div>
        </div>

        <div className="flex flex-col items-center mb-8 mt-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-primary via-chart-2 to-primary bg-clip-text text-transparent">
            Fraud Detection System
          </h1>
          <div className="flex items-center gap-1 mt-2">
            <Sparkles className="w-4 h-4 text-primary" />
            <p className="text-sm text-muted-foreground">Analytics Platform</p>
            <Sparkles className="w-4 h-4 text-chart-2" />
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-sm font-semibold">Email Address</Label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                id="email"
                type="email"
                placeholder="admin@frauddetect.com"
                className="pl-10 h-12 border-2 focus:border-primary transition-all"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                data-testid="input-email"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-sm font-semibold">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                className="pl-10 h-12 border-2 focus:border-primary transition-all"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                data-testid="input-password"
              />
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="remember"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="w-4 h-4 rounded border-input"
              data-testid="checkbox-remember"
            />
            <Label htmlFor="remember" className="text-sm font-normal cursor-pointer">
              Remember me for 30 days
            </Label>
          </div>

          <Button
            type="submit"
            className="w-full h-12 text-base font-semibold bg-gradient-to-r from-primary to-chart-2 hover:opacity-90 transition-all shadow-lg hover:shadow-xl"
            data-testid="button-login"
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Signing In...
              </span>
            ) : (
              "Sign In"
            )}
          </Button>
        </form>

        <div className="mt-8">
          <Button
            type="button"
            variant="outline"
            className="w-full h-12 text-base font-semibold flex items-center justify-center gap-3"
            onClick={() => {
              const url = `${API_BASE_URL.replace(/\/$/, "")}/api/v1/auth/google/login`;
              window.location.href = url;
            }}
            data-testid="button-google"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" className="w-5 h-5">
              <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.1 29.3 35 24 35c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 3.1l5.7-5.7C34.6 3.5 29.6 1.5 24 1.5 11.5 1.5 1.5 11.5 1.5 24S11.5 46.5 24 46.5 46.5 36.5 46.5 24c0-1.1-.1-2.2-.3-3.5z"/>
              <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16.2 19 13 24 13c3.1 0 5.9 1.1 8.1 3.1l5.7-5.7C34.6 3.5 29.6 1.5 24 1.5 15.4 1.5 8.2 6.2 6.3 14.7z"/>
              <path fill="#4CAF50" d="M24 46.5c5.2 0 10-1.9 13.6-5.1l-6.3-5.2C29 37.7 26.6 38.5 24 38.5 18.7 38.5 14.3 35.6 12.7 31l-6.5 5C8.1 42 15.4 46.5 24 46.5z"/>
              <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-1.3 3.3-4.2 5.7-7.7 6.6l6.3 5.2C37.3 37.8 40.5 31.4 40.5 24c0-1.1-.1-2.2-.3-3.5z"/>
            </svg>
            Continue with Google
          </Button>
        </div>
      </Card>
    </div>
  );
}

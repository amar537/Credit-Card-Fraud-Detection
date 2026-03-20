import { useEffect, useState, type CSSProperties } from "react";
import { Switch, Route, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ProfileDropdown } from "@/components/ProfileDropdown";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import Dashboard from "@/pages/Dashboard";
import Transactions from "@/pages/Transactions";
import FraudDetection from "@/pages/FraudDetection";
import Analytics from "@/pages/Analytics";
import ModelInfo from "@/pages/ModelInfo";
import History from "@/pages/History";
import Settings from "@/pages/Settings";
import Login from "@/pages/Login";
import Profile from "@/pages/Profile";
import NotFound from "@/pages/not-found";

function Redirect({ to }: { to: string }) {
  const [, setLocation] = useLocation();

  useEffect(() => {
    setLocation(to);
  }, [setLocation, to]);

  return null;
}

function AuthenticatedRoutes() {
  return (
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/transactions" component={Transactions} />
      <Route path="/detect" component={FraudDetection} />
      <Route path="/analytics" component={Analytics} />
      <Route path="/model" component={ModelInfo} />
      <Route path="/history" component={History} />
      <Route path="/settings" component={Settings} />
      <Route path="/profile" component={Profile} />
      <Route path="/login" component={() => <Redirect to="/" />} />
      <Route component={NotFound} />
    </Switch>
  );
}

function UnauthenticatedRoutes() {
  return (
    <Switch>
      <Route path="/login" component={Login} />
      <Route component={() => <Redirect to="/login" />} />
    </Switch>
  );
}

function useAuthState() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    Boolean(localStorage.getItem("access_token")),
  );

  useEffect(() => {
    const handler = () => setIsAuthenticated(Boolean(localStorage.getItem("access_token")));
    window.addEventListener("storage", handler);
    window.addEventListener("auth-changed", handler);
    return () => {
      window.removeEventListener("storage", handler);
      window.removeEventListener("auth-changed", handler);
    };
  }, []);

  return isAuthenticated;
}

type CSSVars = CSSProperties & Record<string, string>;

export default function App() {
  const isAuthenticated = useAuthState();
  const style: CSSVars = {
    "--sidebar-width": "16rem",
    "--sidebar-width-icon": "3rem",
  };

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <div className="dark min-h-screen">
            {isAuthenticated ? (
              <SidebarProvider style={style}>
                <div className="flex h-screen w-full bg-background">
                  <AppSidebar />
                  <div className="flex flex-col flex-1">
                    <header className="flex items-center justify-between p-4 border-b border-white/5 bg-card/50">
                      <SidebarTrigger data-testid="button-sidebar-toggle" />
                      <div className="flex items-center gap-2">
                        <ThemeToggle />
                        <ProfileDropdown />
                      </div>
                    </header>
                    <main className="flex-1 overflow-auto p-8">
                      <ErrorBoundary>
                        <AuthenticatedRoutes />
                      </ErrorBoundary>
                    </main>
                  </div>
                </div>
              </SidebarProvider>
            ) : (
              <UnauthenticatedRoutes />
            )}
            <Toaster />
          </div>
        </TooltipProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

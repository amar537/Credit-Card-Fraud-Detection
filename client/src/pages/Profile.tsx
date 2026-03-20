import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Shield, Mail, MapPin, Calendar, Bell, Lock, User, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchUserProfile, updateUserProfile, changePassword, UserProfile } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { Skeleton } from "@/components/ui/skeleton";

export default function Profile() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Fetch user profile
  const { data: profile, isLoading: profileLoading } = useQuery({
    queryKey: ["user-profile"],
    queryFn: fetchUserProfile,
    onError: (error) => {
      toast({
        title: "Failed to load profile",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    },
  });

  // Local state for form fields
  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Update local state when profile loads
  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name || "");
      setUsername(profile.username || "");
      setEmail(profile.email || "");
    }
  }, [profile]);

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: (data: { full_name?: string; username?: string }) => updateUserProfile(data),
    onSuccess: (data) => {
      queryClient.setQueryData(["user-profile"], data);
      toast({
        title: "Profile updated",
        description: "Your profile has been successfully updated",
      });
    },
    onError: (error) => {
      toast({
        title: "Update failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    },
  });

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) => changePassword(data),
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      toast({
        title: "Password changed",
        description: "Your password has been successfully updated. Please login again.",
      });
      // Redirect to login after password change
      setTimeout(() => {
        window.location.href = "/login";
      }, 2000);
    },
    onError: (error) => {
      toast({
        title: "Password change failed",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    },
  });

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfileMutation.mutate({
      full_name: fullName,
      username: username,
    });
  };

  const handleSaveSecurity = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      toast({
        title: "Password mismatch",
        description: "New password and confirmation do not match",
        variant: "destructive",
      });
      return;
    }

    if (newPassword.length < 8) {
      toast({
        title: "Password too short",
        description: "Password must be at least 8 characters long",
        variant: "destructive",
      });
      return;
    }

    changePasswordMutation.mutate({
      current_password: currentPassword,
      new_password: newPassword,
    });
  };

  if (profileLoading) {
    return (
      <div className="space-y-6 max-w-4xl">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const displayName = profile?.full_name || profile?.username || "User";
  const initials = displayName.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2) || "U";
  const joinDate = profile?.created_at ? new Date(profile.created_at).toLocaleDateString("en-US", { month: "short", year: "numeric" }) : "N/A";

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-semibold text-white">Profile Settings</h1>
        <p className="text-muted-foreground mt-1">Manage your account and preferences</p>
      </div>

      <Card className="p-6 relative overflow-hidden shadow-lg bg-card/50 backdrop-blur-sm border-white/5">
        <div className="flex flex-col md:flex-row gap-6 items-start relative">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-primary to-chart-2 rounded-full blur-md opacity-50" />
            <Avatar className="w-24 h-24 relative border-4 border-background shadow-xl">
              <AvatarFallback className="text-2xl bg-gradient-to-br from-primary to-chart-2 text-primary-foreground">
                {initials}
              </AvatarFallback>
            </Avatar>
          </div>
          <div className="flex-1">
            <h2 className="text-2xl font-semibold">{displayName}</h2>
            <p className="text-muted-foreground">{email}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              {profile?.is_superuser && (
                <Badge variant="secondary">
                  <Shield className="w-3 h-3 mr-1" />
                  Admin
                </Badge>
              )}
              <Badge variant={profile?.is_verified ? "default" : "secondary"}>
                {profile?.is_verified ? "Verified" : "Unverified"}
              </Badge>
              <Badge variant="secondary">
                <Calendar className="w-3 h-3 mr-1" />
                Joined {joinDate}
              </Badge>
            </div>
          </div>
        </div>
      </Card>

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList>
          <TabsTrigger value="general" data-testid="tab-general">
            <User className="w-4 h-4 mr-2" />
            General
          </TabsTrigger>
          <TabsTrigger value="security" data-testid="tab-security">
            <Lock className="w-4 h-4 mr-2" />
            Security
          </TabsTrigger>
          <TabsTrigger value="notifications" data-testid="tab-notifications">
            <Bell className="w-4 h-4 mr-2" />
            Notifications
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-6">Personal Information</h3>
            <form onSubmit={handleSaveProfile} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  data-testid="input-full-name"
                  placeholder="Enter your full name"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  data-testid="input-username"
                  placeholder="Enter your username"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    className="pl-9"
                    value={email}
                    disabled
                    data-testid="input-email"
                  />
                </div>
                <p className="text-xs text-muted-foreground">Email cannot be changed</p>
              </div>

              <div className="flex justify-end gap-3">
                <Button type="button" variant="outline" data-testid="button-cancel">
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  data-testid="button-save-profile"
                  disabled={updateProfileMutation.isPending}
                >
                  {updateProfileMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    "Save Changes"
                  )}
                </Button>
              </div>
            </form>
          </Card>
        </TabsContent>

        <TabsContent value="security">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-6">Security Settings</h3>
            <form onSubmit={handleSaveSecurity} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="currentPassword">Current Password</Label>
                <Input
                  id="currentPassword"
                  type="password"
                  placeholder="Enter current password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  data-testid="input-current-password"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="newPassword">New Password</Label>
                <Input
                  id="newPassword"
                  type="password"
                  placeholder="Enter new password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  data-testid="input-new-password"
                  required
                  minLength={8}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  data-testid="input-confirm-password"
                  required
                  minLength={8}
                />
              </div>

              <div className="bg-muted/50 p-4 rounded-lg">
                <h4 className="text-sm font-semibold mb-2">Password Requirements</h4>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• At least 8 characters long</li>
                  <li>• Contains uppercase and lowercase letters</li>
                  <li>• Includes at least one number</li>
                  <li>• Contains at least one special character</li>
                </ul>
              </div>

              <div className="flex justify-end gap-3">
                <Button 
                  type="button" 
                  variant="outline" 
                  data-testid="button-cancel-security"
                  onClick={() => {
                    setCurrentPassword("");
                    setNewPassword("");
                    setConfirmPassword("");
                  }}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  data-testid="button-update-password"
                  disabled={changePasswordMutation.isPending}
                >
                  {changePasswordMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Updating...
                    </>
                  ) : (
                    "Update Password"
                  )}
                </Button>
              </div>
            </form>
          </Card>
        </TabsContent>

        <TabsContent value="notifications">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-6">Notification Preferences</h3>
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Fraud Alerts</p>
                  <p className="text-sm text-muted-foreground">Receive alerts when high-risk transactions are detected</p>
                </div>
                <input type="checkbox" defaultChecked className="w-5 h-5 rounded" data-testid="checkbox-fraud-alerts" />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Daily Summary</p>
                  <p className="text-sm text-muted-foreground">Get daily summary of fraud detection activities</p>
                </div>
                <input type="checkbox" defaultChecked className="w-5 h-5 rounded" data-testid="checkbox-daily-summary" />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Model Updates</p>
                  <p className="text-sm text-muted-foreground">Notifications about LSTM model improvements</p>
                </div>
                <input type="checkbox" className="w-5 h-5 rounded" data-testid="checkbox-model-updates" />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">System Alerts</p>
                  <p className="text-sm text-muted-foreground">Important system notifications and maintenance updates</p>
                </div>
                <input type="checkbox" defaultChecked className="w-5 h-5 rounded" data-testid="checkbox-system-alerts" />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="outline" data-testid="button-cancel-notifications">
                  Cancel
                </Button>
                <Button data-testid="button-save-notifications">
                  Save Preferences
                </Button>
              </div>
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

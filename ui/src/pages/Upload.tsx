import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import Header from "@/components/Header";
import FileUpload from "@/components/FileUpload";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Link2, Play, Loader2, CheckCircle, AlertCircle, LogOut } from "lucide-react";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";
import { useToast } from "@/components/ui/use-toast";

const Upload = () => {
  const { user, isAuthenticated, login, logout } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [isScraping, setIsScraping] = useState(false);
  const { toast } = useToast();
  const navigate = useNavigate();

  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      await login();
    } catch (error) {
      console.error("Login failed:", error);
      toast({
        title: "Login Failed",
        description: "Failed to sign in with Google. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartScraping = async () => {
    try {
      setIsScraping(true);
      // TODO: Implement actual scraping logic
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate API call
      
      toast({
        title: "Scraping Started",
        description: "We've started processing your data. This may take a few minutes.",
      });
    } catch (error) {
      console.error("Scraping failed:", error);
      toast({
        title: "Scraping Failed",
        description: "Failed to start the scraping process. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsScraping(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      toast({
        title: "Signed out successfully",
        description: "You have been signed out of your Google account.",
      });
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-12">
        <div className="container mx-auto px-4 max-w-4xl">
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">Import Data</h1>
            <p className="text-muted-foreground">
              Upload addresses or connect to Google Sheets to start scraping property data
            </p>
          </div>

          <div className="grid gap-6 mb-8">
            <FileUpload />

            <Card className="shadow-elevation-3">
              <CardHeader>
                <CardTitle>Google Sheets Integration</CardTitle>
                <CardDescription>
                  {isAuthenticated 
                    ? "Connected to Google Sheets" 
                    : "Connect your Google Sheets for seamless data synchronization"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isAuthenticated ? (
                  <div className="flex flex-col items-center space-y-4 p-6 border border-green-500/20 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <div className="flex items-center space-x-4">
                      <Avatar className="h-12 w-12">
                        {user?.photos?.[0]?.value ? (
                          <AvatarImage src={user.photos[0].value} alt={user.displayName} />
                        ) : (
                          <AvatarFallback>
                            {user?.displayName?.charAt(0) || 'U'}
                          </AvatarFallback>
                        )}
                      </Avatar>
                      <div>
                        <p className="font-medium">{user?.displayName || 'User'}</p>
                        <p className="text-sm text-muted-foreground">
                          {user?.emails?.[0]?.value || 'No email available'}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center text-sm text-green-600 dark:text-green-400">
                      <CheckCircle className="h-4 w-4 mr-1" />
                      Successfully connected to Google
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center p-8 border-2 border-dashed border-border rounded-lg">
                    <Link2 className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-lg font-medium mb-2">Connect to Google Sheets</p>
                    <p className="text-sm text-muted-foreground mb-4 text-center max-w-md">
                      Sync your property addresses directly from Google Sheets and export results back automatically
                    </p>
                    <Button 
                      variant="default" 
                      className="gap-2"
                      onClick={handleGoogleLogin}
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          Connecting...
                        </>
                      ) : (
                        <>
                          <Link2 className="h-4 w-4" />
                          Connect Google Account
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </CardContent>
              {isAuthenticated && (
                <CardFooter className="border-t px-6 py-4">
                  <Button 
                    variant="ghost" 
                    className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                    onClick={handleLogout}
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Disconnect Account
                  </Button>
                </CardFooter>
              )}
            </Card>
          </div>

          <Card className="bg-primary text-primary-foreground shadow-elevation-3">
            <CardContent className="p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-lg mb-2">Ready to process your data?</h3>
                  <p className="text-sm text-primary-foreground/90 mb-4">
                    {isAuthenticated 
                      ? "Start the scraping process to extract property assessment data."
                      : "Please connect your Google Account to start scraping."}
                  </p>
                  <Button 
                    variant="secondary" 
                    className="gap-2"
                    onClick={handleStartScraping}
                    disabled={!isAuthenticated || isScraping}
                  >
                    {isScraping ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4" />
                        Start Scraping
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Upload;

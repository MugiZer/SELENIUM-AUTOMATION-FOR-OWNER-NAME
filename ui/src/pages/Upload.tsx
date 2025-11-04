import Header from "@/components/Header";
import FileUpload from "@/components/FileUpload";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Link2, Play } from "lucide-react";

const Upload = () => {
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
                  Connect your Google Sheets for seamless data synchronization
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-border rounded-lg">
                  <Link2 className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-lg font-medium mb-2">Connect to Google Sheets</p>
                  <p className="text-sm text-muted-foreground mb-4 text-center max-w-md">
                    Sync your property addresses directly from Google Sheets and export results back automatically
                  </p>
                  <Button variant="default" className="gap-2">
                    <Link2 className="h-4 w-4" />
                    Connect Google Account
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-primary text-primary-foreground shadow-elevation-3">
            <CardContent className="p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="font-semibold text-lg mb-2">Ready to process your data?</h3>
                  <p className="text-sm text-primary-foreground/90 mb-4">
                    Once you've uploaded your addresses, start the scraping process to extract property assessment data.
                  </p>
                  <Button variant="secondary" className="gap-2">
                    <Play className="h-4 w-4" />
                    Start Scraping
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

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

const FileUpload = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const { toast } = useToast();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    handleFiles(files);
  }, []);

  const handleFiles = (files: File[]) => {
    const csvFile = files.find(file => file.name.endsWith('.csv'));
    
    if (!csvFile) {
      toast({
        title: "Invalid file type",
        description: "Please upload a CSV file",
        variant: "destructive"
      });
      setUploadStatus("error");
      return;
    }

    setUploadStatus("uploading");
    
    // Simulate upload
    setTimeout(() => {
      setUploadStatus("success");
      toast({
        title: "File uploaded successfully",
        description: `${csvFile.name} has been uploaded and is ready for processing`,
      });
    }, 2000);
  };

  return (
    <Card className="shadow-elevation-3">
      <CardHeader>
        <CardTitle>Upload Property Addresses</CardTitle>
        <CardDescription>
          Upload a CSV file with property addresses to begin scraping assessment data
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            relative border-2 border-dashed rounded-lg p-12 text-center transition-all
            ${isDragging ? 'border-accent bg-accent/5' : 'border-border'}
            ${uploadStatus === 'success' ? 'border-success bg-success/5' : ''}
            ${uploadStatus === 'error' ? 'border-destructive bg-destructive/5' : ''}
          `}
        >
          <input
            type="file"
            accept=".csv"
            onChange={handleFileInput}
            className="hidden"
            id="file-upload"
          />

          {uploadStatus === "idle" && (
            <div className="space-y-4">
              <div className="flex justify-center">
                <Upload className="h-12 w-12 text-muted-foreground" />
              </div>
              <div>
                <p className="text-lg font-medium mb-2">Drag and drop your CSV file here</p>
                <p className="text-sm text-muted-foreground mb-4">or</p>
                <label htmlFor="file-upload">
                  <Button variant="secondary" asChild>
                    <span>Browse Files</span>
                  </Button>
                </label>
              </div>
              <p className="text-xs text-muted-foreground">
                Supports CSV files up to 10,000 rows
              </p>
            </div>
          )}

          {uploadStatus === "uploading" && (
            <div className="space-y-4">
              <div className="flex justify-center">
                <FileSpreadsheet className="h-12 w-12 text-accent animate-pulse" />
              </div>
              <p className="text-lg font-medium">Uploading file...</p>
            </div>
          )}

          {uploadStatus === "success" && (
            <div className="space-y-4">
              <div className="flex justify-center">
                <CheckCircle2 className="h-12 w-12 text-success" />
              </div>
              <div>
                <p className="text-lg font-medium mb-2">File uploaded successfully!</p>
                <p className="text-sm text-muted-foreground mb-4">
                  Your addresses are ready for processing
                </p>
                <Button onClick={() => setUploadStatus("idle")} variant="outline">
                  Upload Another File
                </Button>
              </div>
            </div>
          )}

          {uploadStatus === "error" && (
            <div className="space-y-4">
              <div className="flex justify-center">
                <AlertCircle className="h-12 w-12 text-destructive" />
              </div>
              <div>
                <p className="text-lg font-medium mb-2">Upload failed</p>
                <p className="text-sm text-muted-foreground mb-4">
                  Please try again with a valid CSV file
                </p>
                <Button onClick={() => setUploadStatus("idle")} variant="outline">
                  Try Again
                </Button>
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 p-4 bg-muted rounded-lg">
          <h4 className="font-semibold text-sm mb-2">CSV Format Requirements:</h4>
          <ul className="text-sm text-muted-foreground space-y-1">
            <li>• Column header: "address"</li>
            <li>• One address per row</li>
            <li>• Include street number, street name, and "Montreal" or postal code</li>
            <li>• Example: "1234 Rue Sainte-Catherine O, Montreal"</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default FileUpload;

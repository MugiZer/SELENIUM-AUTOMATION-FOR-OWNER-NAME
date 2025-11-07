import { useState, useCallback, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Upload, CheckCircle2, AlertCircle, Download, Loader2, X, FileSpreadsheet } from "lucide-react";
import { useToast } from "@/components/ui/use-toast";
import Papa, { ParseResult } from 'papaparse';

type UploadStatus = "idle" | "uploading" | "success" | "error";

interface PropertyData {
  address: string;
  ownerName: string;
  [key: string]: any;
}

interface CSVStats {
  totalRows: number;
  validRows: number;
  invalidRows: number;
  headers: string[];
}

const EXPECTED_COLUMNS = ['address', 'ownerName'];

const FileUpload = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>("idle");
  const [processedData, setProcessedData] = useState<PropertyData[]>([]);
  const [originalFileName, setOriginalFileName] = useState<string>("");
  const [csvStats, setCsvStats] = useState<CSVStats | null>(null);
  const [previewData, setPreviewData] = useState<PropertyData[]>([]);
  const { toast } = useToast();

  // Generate a clean filename from the original
  const outputFileName = useMemo(() => {
    if (!originalFileName) return 'processed_properties';
    const baseName = originalFileName.replace(/\.[^/.]+$/, '');
    return `${baseName}_processed_${new Date().toISOString().split('T')[0]}`;
  }, [originalFileName]);

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
    // Reset the input value to allow selecting the same file again
    e.target.value = '';
  }, []);

  const validateRow = (row: any): boolean => {
    // Check if required fields exist and are not empty
    return EXPECTED_COLUMNS.every(
      field => row[field] !== undefined && 
              row[field] !== null && 
              String(row[field]).trim() !== ''
    );
  };

  const processCSV = (results: ParseResult<Record<string, unknown>>): { validData: PropertyData[], stats: CSVStats } => {
    const validData: PropertyData[] = [];
    const invalidRows: any[] = [];
    
    results.data.forEach((row, index) => {
      // Skip empty rows
      if (Object.keys(row).length === 0) return;
      
      if (validateRow(row)) {
        // Ensure consistent property names (case-insensitive)
        const processedRow: PropertyData = {
          address: row.address || row.Address || '',
          ownerName: row.ownerName || row.ownername || row.OwnerName || row.owner_name || '',
          // Preserve all other fields
          ...Object.entries(row).reduce((acc, [key, value]) => {
            const lowerKey = key.toLowerCase();
            if (!['address', 'ownername', 'owner_name'].includes(lowerKey)) {
              acc[key] = value;
            }
            return acc;
          }, {} as Record<string, any>)
        };
        validData.push(processedRow);
      } else {
        invalidRows.push({ row: index + 1, data: row });
      }
    });

    const stats: CSVStats = {
      totalRows: results.data.length,
      validRows: validData.length,
      invalidRows: invalidRows.length,
      headers: results.meta.fields || []
    };

    return { validData, stats };
  };

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

    setOriginalFileName(csvFile.name);
    setUploadStatus("uploading");
    
    // Parse the CSV file
    Papa.parse(csvFile, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        try {
          const { validData, stats } = processCSV(results);
          setProcessedData(validData);
          setCsvStats(stats);
          setPreviewData(validData.slice(0, 5)); // Show first 5 rows as preview
          setUploadStatus("success");
          
          // Show success message with stats
          toast({
            title: "File processed successfully",
            description: `Processed ${stats.validRows} valid rows` + 
                        (stats.invalidRows > 0 ? ` (${stats.invalidRows} invalid rows skipped)` : ''),
          });
          
          if (stats.invalidRows > 0) {
            toast({
              title: "Some rows were skipped",
              description: `${stats.invalidRows} rows were missing required fields and were not processed.`,
              variant: "destructive"
            });
          }
        } catch (error) {
          console.error('Error processing CSV:', error);
          setUploadStatus("error");
          toast({
            title: "Error processing file",
            description: "There was an error processing your CSV file. Please check the format and try again.",
            variant: "destructive"
          });
        }
      },
      error: (error) => {
        console.error('Error parsing CSV:', error);
        setUploadStatus("error");
        toast({
          title: "Error parsing file",
          description: "There was an error reading your CSV file. Please check the format and try again.",
          variant: "destructive"
        });
      }
    });
  };

  const handleDownload = () => {
    if (processedData.length === 0) return;
    
    try {
      // Convert data to CSV with proper formatting
      const csv = Papa.unparse(processedData, {
        quotes: true,
        header: true,
        delimiter: ","
      });
      
      // Create a blob and download link
      const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${outputFileName}.csv`;
      document.body.appendChild(link);
      link.click();
      
      // Clean up
      setTimeout(() => {
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      }, 100);
      
      toast({
        title: "Download started",
        description: `Your file "${outputFileName}.csv" is being downloaded.`
      });
      
    } catch (error) {
      console.error('Error generating CSV:', error);
      toast({
        title: "Error generating file",
        description: "There was an error generating the CSV file. Please try again.",
        variant: "destructive"
      });
    }
  };
  
  const resetForm = () => {
    setProcessedData([]);
    setPreviewData([]);
    setCsvStats(null);
    setUploadStatus("idle");
    // Reset file input
    const fileInput = document.getElementById('file-upload') as HTMLInputElement;
    if (fileInput) fileInput.value = '';
  };

  // Render the appropriate content based on upload status
  const renderContent = () => {
    switch (uploadStatus) {
      case 'uploading':
        return (
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <p className="text-lg font-medium">Processing your file...</p>
            <p className="text-sm text-muted-foreground">This may take a moment</p>
          </div>
        );
        
      case 'success':
        return (
          <div className="space-y-6">
            <div className="rounded-lg bg-green-50 dark:bg-green-900/20 p-4 border border-green-200 dark:border-green-800">
              <div className="flex items-center">
                <CheckCircle2 className="h-5 w-5 text-green-500 mr-2" />
                <p className="text-green-800 dark:text-green-200 font-medium">
                  File processed successfully! Ready to download.
                </p>
              </div>
              
              {csvStats && (
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  <div className="text-green-700 dark:text-green-300">
                    <span className="font-medium">Total Rows:</span> {csvStats.totalRows}
                  </div>
                  <div className="text-green-700 dark:text-green-300">
                    <span className="font-medium">Valid Rows:</span> {csvStats.validRows}
                  </div>
                  {csvStats.invalidRows > 0 && (
                    <div className="text-amber-600 dark:text-amber-400 col-span-2">
                      <span className="font-medium">Skipped Rows:</span> {csvStats.invalidRows} (missing required fields)
                    </div>
                  )}
                </div>
              )}
              
              <div className="mt-4 flex flex-wrap gap-3">
                <Button 
                  onClick={handleDownload} 
                  variant="default" 
                  className="gap-2"
                >
                  <Download className="h-4 w-4" />
                  Download Processed CSV
                </Button>
                <Button 
                  onClick={resetForm} 
                  variant="outline"
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Process Another File
                </Button>
              </div>
            </div>
            
            {previewData.length > 0 && (
              <div className="border rounded-lg overflow-hidden">
                <div className="bg-muted/50 px-4 py-2 border-b">
                  <h3 className="font-medium text-sm">Preview (first {previewData.length} rows)</h3>
                </div>
                <div className="overflow-x-auto max-h-96">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-muted/50">
                        {csvStats?.headers.map((header) => (
                          <th key={header} className="text-left p-2 border-b font-medium">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.map((row, rowIndex) => (
                        <tr key={rowIndex} className="border-b hover:bg-muted/20">
                          {csvStats?.headers.map((header) => (
                            <td key={`${rowIndex}-${header}`} className="p-2 truncate max-w-xs">
                              {String(row[header] || '').slice(0, 50)}
                              {String(row[header] || '').length > 50 ? '...' : ''}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        );
        
      case 'error':
        return (
          <div className="flex flex-col items-center justify-center py-12 space-y-4 text-center">
            <AlertCircle className="h-12 w-12 text-destructive" />
            <p className="text-lg font-medium">Error Processing File</p>
            <p className="text-muted-foreground">There was a problem with your file. Please try again.</p>
            <Button 
              onClick={resetForm} 
              variant="outline" 
              className="mt-2"
            >
              <Upload className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          </div>
        );
        
      default: // idle
        return (
          <div 
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`
              relative border-2 border-dashed rounded-lg p-12 text-center transition-colors
              ${isDragging ? 'border-primary bg-primary/5' : 'border-border'}
            `}
          >
            <input
              type="file"
              accept=".csv"
              onChange={handleFileInput}
              className="hidden"
              id="file-upload"
              disabled={uploadStatus === "uploading"}
            />
            
            <div className="space-y-4">
              <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Upload className="h-6 w-6 text-primary" />
              </div>
              
              <div>
                <p className="text-lg font-medium mb-1">
                  {isDragging ? 'Drop your CSV file here' : 'Drag and drop your CSV file'}
                </p>
                <p className="text-sm text-muted-foreground mb-4">
                  or
                </p>
                <label htmlFor="file-upload">
                  <Button variant="outline" asChild>
                    <span>Select CSV File</span>
                  </Button>
                </label>
              </div>
              
              <p className="text-xs text-muted-foreground">
                Supports .csv files with address and owner information
              </p>
              
              <div className="text-xs text-muted-foreground text-left mt-6 p-3 bg-muted/30 rounded-md">
                <p className="font-medium mb-1">Expected CSV format:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>First row should contain headers (e.g., address, ownerName)</li>
                  <li>At minimum, include an 'address' column</li>
                  <li>Additional columns will be preserved in the output</li>
                </ul>
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <Card className="shadow-elevation-3">
      <CardHeader>
        <div className="flex flex-col space-y-2 sm:flex-row sm:justify-between sm:items-center">
          <div>
            <CardTitle>Process Property Data</CardTitle>
            <CardDescription className="mt-1">
              {uploadStatus === 'success' 
                ? 'Your data is ready to download' 
                : 'Upload a CSV file to process property information'}
            </CardDescription>
          </div>
          
          {uploadStatus === 'success' && csvStats && (
            <div className="flex items-center space-x-2">
              <Button 
                onClick={resetForm} 
                variant="outline" 
                size="sm"
                className="gap-1.5"
              >
                <X className="h-4 w-4" />
                <span className="hidden sm:inline">Clear</span>
              </Button>
              <Button 
                onClick={handleDownload} 
                variant="default" 
                size="sm"
                className="gap-1.5"
              >
                <Download className="h-4 w-4" />
                <span className="hidden sm:inline">Download</span>
                <span className="sm:hidden">CSV</span>
              </Button>
            </div>
          )}
        </div>
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
            disabled={uploadStatus === "uploading"}
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
                    <span>Select CSV File</span>
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

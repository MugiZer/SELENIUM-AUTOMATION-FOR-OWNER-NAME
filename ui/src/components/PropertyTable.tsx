import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Search, Download, Eye } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface Property {
  id: string;
  address: string;
  assessedValue: number;
  landValue: number;
  buildingValue: number;
  status: "success" | "pending" | "error";
  lastUpdated: string;
}

const mockProperties: Property[] = [
  {
    id: "1",
    address: "1234 Rue Sainte-Catherine O, Montreal",
    assessedValue: 450000,
    landValue: 180000,
    buildingValue: 270000,
    status: "success",
    lastUpdated: "2024-01-15"
  },
  {
    id: "2",
    address: "5678 Boulevard Saint-Laurent, Montreal",
    assessedValue: 680000,
    landValue: 250000,
    buildingValue: 430000,
    status: "success",
    lastUpdated: "2024-01-15"
  },
  {
    id: "3",
    address: "910 Avenue du Parc, Montreal",
    assessedValue: 525000,
    landValue: 200000,
    buildingValue: 325000,
    status: "pending",
    lastUpdated: "2024-01-14"
  },
  {
    id: "4",
    address: "1122 Rue Sherbrooke E, Montreal",
    assessedValue: 890000,
    landValue: 320000,
    buildingValue: 570000,
    status: "success",
    lastUpdated: "2024-01-15"
  },
  {
    id: "5",
    address: "3344 Chemin de la Côte-des-Neiges, Montreal",
    assessedValue: 0,
    landValue: 0,
    buildingValue: 0,
    status: "error",
    lastUpdated: "2024-01-14"
  }
];

const PropertyTable = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);

  const filteredProperties = mockProperties.filter(property =>
    property.address.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD',
      minimumFractionDigits: 0
    }).format(value);
  };

  const getStatusBadge = (status: Property["status"]) => {
    const variants = {
      success: { variant: "default" as const, className: "bg-success hover:bg-success/90 text-success-foreground" },
      pending: { variant: "secondary" as const, className: "bg-warning hover:bg-warning/90 text-warning-foreground" },
      error: { variant: "destructive" as const, className: "" }
    };

    const config = variants[status];
    
    return (
      <Badge variant={config.variant} className={config.className}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by address..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button variant="outline" className="gap-2">
          <Download className="h-4 w-4" />
          Export CSV
        </Button>
      </div>

      <div className="rounded-lg border border-border shadow-elevation-2 overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead className="font-semibold">Address</TableHead>
              <TableHead className="font-semibold">Assessed Value</TableHead>
              <TableHead className="font-semibold">Status</TableHead>
              <TableHead className="font-semibold">Last Updated</TableHead>
              <TableHead className="text-right font-semibold">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredProperties.map((property) => (
              <TableRow key={property.id} className="hover:bg-muted/30 transition-colors">
                <TableCell className="font-medium">{property.address}</TableCell>
                <TableCell className="font-mono">
                  {property.status === "error" ? "—" : formatCurrency(property.assessedValue)}
                </TableCell>
                <TableCell>{getStatusBadge(property.status)}</TableCell>
                <TableCell className="text-muted-foreground">{property.lastUpdated}</TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedProperty(property)}
                    className="gap-2"
                  >
                    <Eye className="h-4 w-4" />
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Dialog open={!!selectedProperty} onOpenChange={() => setSelectedProperty(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Property Details</DialogTitle>
            <DialogDescription>
              Comprehensive assessment data for this property
            </DialogDescription>
          </DialogHeader>
          {selectedProperty && (
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-sm text-muted-foreground mb-1">Address</h4>
                <p className="text-base">{selectedProperty.address}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold text-sm text-muted-foreground mb-1">Assessed Value</h4>
                  <p className="text-2xl font-bold font-mono">{formatCurrency(selectedProperty.assessedValue)}</p>
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-muted-foreground mb-1">Status</h4>
                  {getStatusBadge(selectedProperty.status)}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold text-sm text-muted-foreground mb-1">Land Value</h4>
                  <p className="text-lg font-mono">{formatCurrency(selectedProperty.landValue)}</p>
                </div>
                <div>
                  <h4 className="font-semibold text-sm text-muted-foreground mb-1">Building Value</h4>
                  <p className="text-lg font-mono">{formatCurrency(selectedProperty.buildingValue)}</p>
                </div>
              </div>
              <div>
                <h4 className="font-semibold text-sm text-muted-foreground mb-1">Last Updated</h4>
                <p className="text-base">{selectedProperty.lastUpdated}</p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PropertyTable;

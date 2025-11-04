import Header from "@/components/Header";
import PropertyTable from "@/components/PropertyTable";

const Properties = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-12">
        <div className="container mx-auto px-4">
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">All Properties</h1>
            <p className="text-muted-foreground">
              View and manage all scraped property assessment data
            </p>
          </div>

          <div className="bg-card rounded-lg border border-border p-6 shadow-elevation-2">
            <PropertyTable />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Properties;

import Header from "@/components/Header";
import MetricCard from "@/components/MetricCard";
import PropertyTable from "@/components/PropertyTable";
import { Database, TrendingUp, AlertCircle, Clock } from "lucide-react";

const Dashboard = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="pt-24 pb-12">
        <div className="container mx-auto px-4">
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">Dashboard</h1>
            <p className="text-muted-foreground">
              Monitor your property assessment scraping activity and results
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <MetricCard
              title="Total Properties"
              value="1,247"
              change="+12.5% from last month"
              icon={Database}
              trend="up"
            />
            <MetricCard
              title="Success Rate"
              value="94.2%"
              change="+2.1% from last week"
              icon={TrendingUp}
              trend="up"
            />
            <MetricCard
              title="Pending Scrapes"
              value="23"
              change="In queue"
              icon={Clock}
              trend="neutral"
            />
            <MetricCard
              title="Failed Requests"
              value="8"
              change="Requires attention"
              icon={AlertCircle}
              trend="down"
            />
          </div>

          <div className="bg-card rounded-lg border border-border p-6 shadow-elevation-2">
            <h2 className="text-2xl font-semibold mb-6">Recent Properties</h2>
            <PropertyTable />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;

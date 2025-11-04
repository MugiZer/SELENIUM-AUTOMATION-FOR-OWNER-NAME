import { Button } from "@/components/ui/button";
import { ArrowRight, Database, TrendingUp, Shield } from "lucide-react";
import { Link } from "react-router-dom";
import heroImage from "@/assets/hero-montreal.jpg";

const Hero = () => {
  return (
    <div className="relative min-h-screen flex items-center">
      {/* Background image with overlay */}
      <div 
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: `url(${heroImage})` }}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-primary/95 via-primary/85 to-accent/75" />
      </div>

      {/* Content */}
      <div className="relative container mx-auto px-4 py-20">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-accent/20 border border-accent/30 mb-8 animate-fade-in">
            <Shield className="h-4 w-4 text-accent-foreground" />
            <span className="text-sm font-medium text-accent-foreground">Trusted by 500+ real estate professionals</span>
          </div>

          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-primary-foreground mb-6 animate-fade-in">
            Extract Montreal Property Data in Minutes
          </h1>
          
          <p className="text-xl md:text-2xl text-primary-foreground/90 mb-8 animate-fade-in">
            Access comprehensive property tax assessments, valuations, and municipal data with our automated scraping platform. Save hours of manual research.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 mb-12 animate-fade-in">
            <Link to="/upload">
              <Button size="lg" variant="secondary" className="group">
                Get Started
                <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
            <Link to="/dashboard">
              <Button size="lg" variant="outline" className="bg-primary-foreground/10 border-primary-foreground/30 text-primary-foreground hover:bg-primary-foreground/20">
                View Dashboard
              </Button>
            </Link>
          </div>

          {/* Feature highlights */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-in">
            <div className="flex items-start gap-3 bg-primary-foreground/10 backdrop-blur-sm rounded-lg p-4 border border-primary-foreground/20">
              <div className="p-2 rounded-lg bg-accent">
                <Database className="h-5 w-5 text-accent-foreground" />
              </div>
              <div>
                <h3 className="font-semibold text-primary-foreground mb-1">Bulk Processing</h3>
                <p className="text-sm text-primary-foreground/80">Process up to 10,000 properties at once</p>
              </div>
            </div>

            <div className="flex items-start gap-3 bg-primary-foreground/10 backdrop-blur-sm rounded-lg p-4 border border-primary-foreground/20">
              <div className="p-2 rounded-lg bg-success">
                <TrendingUp className="h-5 w-5 text-success-foreground" />
              </div>
              <div>
                <h3 className="font-semibold text-primary-foreground mb-1">Real-time Updates</h3>
                <p className="text-sm text-primary-foreground/80">Track progress with live status updates</p>
              </div>
            </div>

            <div className="flex items-start gap-3 bg-primary-foreground/10 backdrop-blur-sm rounded-lg p-4 border border-primary-foreground/20">
              <div className="p-2 rounded-lg bg-secondary">
                <Shield className="h-5 w-5 text-secondary-foreground" />
              </div>
              <div>
                <h3 className="font-semibold text-primary-foreground mb-1">Secure & Compliant</h3>
                <p className="text-sm text-primary-foreground/80">GDPR compliant with audit logs</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Hero;

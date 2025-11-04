import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Building2, Menu } from "lucide-react";
import { useState } from "react";

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border shadow-elevation-1">
      <nav className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-foreground hover:text-primary transition-colors">
          <Building2 className="h-6 w-6" />
          <span className="font-bold text-lg">Montreal Property Scraper</span>
        </Link>
        
        <div className="hidden md:flex items-center gap-6">
          <Link to="/dashboard" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Dashboard
          </Link>
          <Link to="/properties" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Properties
          </Link>
          <Link to="/upload" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
            Upload
          </Link>
          <Button variant="default" size="sm">
            Sign In
          </Button>
        </div>

        <button
          className="md:hidden"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          <Menu className="h-6 w-6" />
        </button>
      </nav>

      {isMenuOpen && (
        <div className="md:hidden bg-background border-b border-border py-4 animate-fade-in">
          <div className="container mx-auto px-4 flex flex-col gap-4">
            <Link to="/dashboard" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Dashboard
            </Link>
            <Link to="/properties" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Properties
            </Link>
            <Link to="/upload" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              Upload
            </Link>
            <Button variant="default" size="sm" className="w-full">
              Sign In
            </Button>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;

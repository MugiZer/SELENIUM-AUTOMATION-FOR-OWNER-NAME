import { Link } from "react-router-dom";
import { Building2, Menu } from "lucide-react";
import { useState } from "react";

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-sm border-b border-border shadow-elevation-1">
      <nav className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-foreground hover:text-primary transition-colors">
          <Building2 className="h-6 w-6" />
          <span className="font-bold text-lg">Property Data Processor</span>
        </Link>
        
        <div className="hidden md:flex items-center gap-6">
          <Link to="/upload" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">
            Process Data
          </Link>
        </div>

        <button
          className="md:hidden"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label="Toggle menu"
        >
          <Menu className="h-6 w-6" />
        </button>
      </nav>

      {isMenuOpen && (
        <div className="md:hidden bg-background border-b border-border py-4 animate-fade-in">
          <div className="container mx-auto px-4 flex flex-col gap-4">
            <Link 
              to="/upload" 
              className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium"
              onClick={() => setIsMenuOpen(false)}
            >
              Process Data
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};

export default Header;

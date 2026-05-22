import { Link } from "react-router-dom";
import { Logo } from "@/components/Logo";

const Footer = () => {
  return (
    <footer className="border-t py-8 mt-auto">
      <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Logo size={20} />
          <p className="font-display font-bold text-foreground">Marathi Mitra</p>
        </div>
        <p className="mb-3">Making Marathi learning joyful for kids everywhere.</p>
        <nav className="flex items-center justify-center gap-4 font-display font-bold">
          <Link to="/about" className="hover:text-primary hover:underline">
            About Us
          </Link>
          <span aria-hidden="true">·</span>
          <Link to="/contact" className="hover:text-primary hover:underline">
            Contact Us
          </Link>
        </nav>
      </div>
    </footer>
  );
};

export default Footer;

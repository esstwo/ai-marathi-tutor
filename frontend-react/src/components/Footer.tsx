import { Link } from "react-router-dom";
import { Logo } from "@/components/Logo";

const Footer = () => {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t py-8 mt-auto">
      <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Logo size={20} />
          <p className="font-display font-bold text-foreground">Marathi Mitra</p>
        </div>
        <p className="mb-3">Making Marathi learning joyful for kids everywhere.</p>
        <nav className="flex items-center justify-center gap-4 font-display font-bold mb-6">
          <Link to="/about" className="hover:text-primary hover:underline">
            About Us
          </Link>
          <span aria-hidden="true">·</span>
          <Link to="/contact" className="hover:text-primary hover:underline">
            Contact Us
          </Link>
        </nav>

        <div className="max-w-3xl mx-auto border-t pt-5 text-xs leading-relaxed text-muted-foreground/80 space-y-2">
          <p>
            <span className="font-bold text-foreground/80">Disclaimer:</span> All content is
            AI-generated and may contain errors. Marathi Mitra is not liable for any educational
            outcomes, inaccuracies, or damages resulting from use of this platform. Educational
            content should be verified by qualified educators or parents.
          </p>
          <p>
            Use of this service constitutes acceptance of our Terms of Service and Privacy Policy.
          </p>
          <p className="pt-2">© {year} Marathi Mitra. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

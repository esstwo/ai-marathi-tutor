import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X, Flower2, Sparkles, LogOut, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [showChildMenu, setShowChildMenu] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, activeChild, children, selectChild, logout } = useAuth();

  const navItems = isAuthenticated && activeChild
    ? [
        { label: "Home", path: "/home" },
        { label: "Lessons", path: "/lessons" },
        { label: "Chats", path: "/chats" },
        { label: "Progress", path: "/progress" },
        { label: "Parents", path: "/parents" },
      ]
    : [{ label: "Home", path: "/" }];

  const handleLogout = () => {
    logout();
    navigate("/");
    setIsOpen(false);
  };

  return (
    <nav className="sticky top-0 z-50 bg-card/80 backdrop-blur-md border-b border-border/50">
      <div className="container mx-auto flex items-center justify-between h-16 px-4">
        <Link to={isAuthenticated ? "/home" : "/"} className="flex items-center gap-2 group">
          <div className="h-9 w-9 rounded-xl bg-primary/15 flex items-center justify-center group-hover:animate-wiggle transition-transform">
            <Flower2 className="w-5 h-5 text-primary" />
          </div>
          <span className="font-display text-xl font-bold text-gradient">Marathi Mitra</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {navItems.map((item) => (
            <Link key={item.path} to={item.path}>
              <Button
                variant={location.pathname === item.path ? "soft" : "ghost"}
                size="sm"
                className="font-display font-bold text-[15px] rounded-xl px-4"
              >
                {item.label}
              </Button>
            </Link>
          ))}

          {isAuthenticated ? (
            <div className="relative ml-3 flex items-center gap-2">
              {activeChild && children.length > 1 ? (
                <div className="relative">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="rounded-xl font-bold font-display gap-1"
                    onClick={() => setShowChildMenu(!showChildMenu)}
                  >
                    <span className="text-lg">{activeChild.avatar}</span>
                    {activeChild.name}
                    <ChevronDown className="w-3 h-3" />
                  </Button>
                  {showChildMenu && (
                    <div className="absolute right-0 top-full mt-1 bg-card border rounded-xl shadow-lg p-2 min-w-[160px] z-50">
                      {children.map((child) => (
                        <button
                          key={child.id}
                          onClick={() => {
                            selectChild(child);
                            setShowChildMenu(false);
                          }}
                          className={`w-full text-left px-3 py-2 rounded-lg text-sm font-display font-bold flex items-center gap-2 hover:bg-muted/60 ${
                            child.id === activeChild.id ? "bg-primary/10 text-primary" : ""
                          }`}
                        >
                          <span>{child.avatar}</span>
                          {child.name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : activeChild ? (
                <span className="text-sm font-display font-bold flex items-center gap-1">
                  <span className="text-lg">{activeChild.avatar}</span>
                  {activeChild.name}
                </span>
              ) : null}
              <Button
                variant="ghost"
                size="icon"
                className="rounded-xl"
                onClick={handleLogout}
              >
                <LogOut className="w-4 h-4" />
              </Button>
            </div>
          ) : (
            <Link to="/login" className="ml-3">
              <Button variant="hero" size="sm" className="rounded-xl font-bold">
                <Sparkles className="w-4 h-4 mr-1" />
                Sign In
              </Button>
            </Link>
          )}
        </div>

        {/* Mobile toggle */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden rounded-xl"
          onClick={() => setIsOpen(!isOpen)}
        >
          {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div className="md:hidden border-t bg-card/95 backdrop-blur-md animate-fade-in-up">
          <div className="flex flex-col p-4 gap-1">
            {navItems.map((item) => (
              <Link key={item.path} to={item.path} onClick={() => setIsOpen(false)}>
                <Button
                  variant={location.pathname === item.path ? "soft" : "ghost"}
                  className="w-full justify-start font-display font-bold text-base rounded-xl h-12"
                >
                  {item.label}
                </Button>
              </Link>
            ))}

            {isAuthenticated ? (
              <>
                {activeChild && (
                  <div className="px-3 py-2 text-sm font-display font-bold text-muted-foreground flex items-center gap-2 mt-2">
                    <span className="text-lg">{activeChild.avatar}</span>
                    {activeChild.name}
                  </div>
                )}
                <Button
                  variant="ghost"
                  className="w-full justify-start font-display font-bold text-base rounded-xl h-12 text-destructive"
                  onClick={handleLogout}
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Log Out
                </Button>
              </>
            ) : (
              <Link to="/login" onClick={() => setIsOpen(false)} className="mt-2">
                <Button variant="hero" className="w-full rounded-xl h-12 font-bold">
                  <Sparkles className="w-4 h-4 mr-1" />
                  Sign In
                </Button>
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;

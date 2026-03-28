import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Flower2, Sparkles, Rocket } from "lucide-react";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/contexts/AuthContext";

const Login = () => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login, signup } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || (isSignUp && !name)) {
      toast.error("Please fill in all fields");
      return;
    }

    setLoading(true);
    try {
      if (isSignUp) {
        await signup(name, email, password);
        toast.success("Account created! Let's set up your child's profile.");
        navigate("/child-setup");
      } else {
        const { children } = await login(email, password);
        toast.success("Welcome back!");
        navigate(children.length > 0 ? "/home" : "/child-setup");
      }
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || err?.message || "Something went wrong";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="gradient-card rounded-3xl border-2 border-border/50 p-8 fun-shadow animate-pop">
            <div className="text-center mb-8">
              <div className="w-16 h-16 rounded-2xl bg-primary/15 flex items-center justify-center mx-auto mb-4 animate-bounce-gentle">
                <Flower2 className="w-8 h-8 text-primary" />
              </div>
              <h1 className="font-display text-2xl font-bold text-foreground">
                {isSignUp ? "Join the Fun!" : "Welcome Back!"}
              </h1>
              <p className="text-muted-foreground mt-2 text-sm font-display font-medium">
                {isSignUp
                  ? "Start your Marathi adventure today!"
                  : "Let's continue learning Marathi!"}
              </p>
            </div>

            <form className="space-y-4" onSubmit={handleSubmit}>
              {isSignUp && (
                <div className="space-y-2">
                  <Label htmlFor="name" className="font-display font-bold">
                    Your Name
                  </Label>
                  <Input
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="What should we call you?"
                    className="bg-background rounded-xl h-12 text-base"
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="email" className="font-display font-bold">
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="bg-background rounded-xl h-12 text-base"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="font-display font-bold">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Shh... it's secret!"
                  className="bg-background rounded-xl h-12 text-base"
                />
              </div>

              <Button
                variant="hero"
                className="w-full mt-6 rounded-2xl h-13 text-base font-bold fun-shadow"
                size="lg"
                type="submit"
                disabled={loading}
              >
                {loading ? (
                  "Please wait..."
                ) : isSignUp ? (
                  <>
                    <Rocket className="w-5 h-5 mr-1" /> Let's Go!
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5 mr-1" /> Sign In
                  </>
                )}
              </Button>
            </form>

            <p className="text-center text-sm text-muted-foreground mt-6 font-display font-medium">
              {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
              <button
                onClick={() => setIsSignUp(!isSignUp)}
                className="text-primary font-bold hover:underline"
              >
                {isSignUp ? "Sign In" : "Sign Up"}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

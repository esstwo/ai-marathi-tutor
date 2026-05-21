import { useCallback, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sparkles, Rocket, Mail, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import { Logo } from "@/components/Logo";
import { Turnstile } from "@/components/Turnstile";
import { useAuth } from "@/contexts/AuthContext";
import { resendVerification } from "@/services/api";

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY as string | undefined;

const ResendLink = ({
  resending,
  resendDone,
  onClick,
}: {
  resending: boolean;
  resendDone: boolean;
  onClick: () => void;
}) => {
  if (resendDone) {
    return (
      <p className="text-emerald-700 font-bold mt-2 inline-flex items-center gap-1">
        <CheckCircle2 className="w-4 h-4" /> Email re-sent
      </p>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={resending}
      className="text-primary font-bold hover:underline mt-2 inline-flex items-center gap-1 disabled:opacity-60"
    >
      {resending ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" /> Sending...
        </>
      ) : (
        <>Resend verification email</>
      )}
    </button>
  );
};

const Login = () => {
  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [verificationSentTo, setVerificationSentTo] = useState<string | null>(null);
  const [unverifiedError, setUnverifiedError] = useState(false);
  const [resending, setResending] = useState(false);
  const [resendDone, setResendDone] = useState(false);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const justVerified = searchParams.get("verified") === "1";
  const { login, signup } = useAuth();

  const handleCaptchaVerify = useCallback((token: string) => {
    setCaptchaToken(token);
  }, []);

  const handleCaptchaExpire = useCallback(() => {
    setCaptchaToken(null);
  }, []);

  const handleResend = async () => {
    const target = verificationSentTo ?? email;
    if (!target) {
      toast.error("Enter your email first, then try again.");
      return;
    }
    setResending(true);
    try {
      await resendVerification(target, captchaToken);
      setResendDone(true);
      toast.success(`Verification email re-sent to ${target}.`);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || "Couldn't resend right now";
      toast.error(msg);
    } finally {
      setResending(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || (isSignUp && !name)) {
      toast.error("Please fill in all fields");
      return;
    }
    if (TURNSTILE_SITE_KEY && !captchaToken) {
      toast.error("Please complete the verification challenge");
      return;
    }

    setLoading(true);
    setUnverifiedError(false);
    try {
      if (isSignUp) {
        const { emailVerificationRequired } = await signup(
          name,
          email,
          password,
          captchaToken
        );
        if (emailVerificationRequired) {
          setVerificationSentTo(email);
          setResendDone(false);
          setIsSignUp(false);
          setPassword("");
          setCaptchaToken(null);
        } else {
          toast.success("Account created! Let's set up your child's profile.");
          navigate("/child-setup");
        }
      } else {
        const { children } = await login(email, password, captchaToken);
        toast.success("Welcome back!");
        navigate(children.length > 0 ? "/home" : "/child-setup");
      }
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail || err?.message || "Something went wrong";
      // Supabase returns "Email not confirmed" when an unverified user tries to log in.
      if (!isSignUp && /email\s+not\s+confirmed/i.test(msg)) {
        setUnverifiedError(true);
        setVerificationSentTo(email);
        setResendDone(false);
      } else {
        toast.error(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md space-y-4">
          {justVerified && !verificationSentTo && !unverifiedError && (
            <div
              role="status"
              className="flex items-start gap-3 rounded-2xl border-2 border-mint/60 bg-mint/20 p-4 fun-shadow animate-pop"
            >
              <CheckCircle2 className="w-5 h-5 mt-0.5 flex-shrink-0 text-emerald-700" />
              <div className="text-sm font-display">
                <p className="font-bold text-foreground">Email verified!</p>
                <p className="text-muted-foreground mt-0.5">
                  Sign in below to start learning.
                </p>
              </div>
            </div>
          )}

          {verificationSentTo && !unverifiedError && (
            <div
              role="status"
              className="flex items-start gap-3 rounded-2xl border-2 border-lemon/60 bg-lemon/20 p-4 fun-shadow animate-pop"
            >
              <Mail className="w-5 h-5 mt-0.5 flex-shrink-0 text-foreground" />
              <div className="text-sm font-display flex-1">
                <p className="font-bold text-foreground">Verification email sent</p>
                <p className="text-muted-foreground mt-0.5">
                  We sent a link to <span className="font-bold text-foreground">{verificationSentTo}</span>.
                  Click it to activate your account, then come back here to sign in.
                </p>
                <ResendLink
                  resending={resending}
                  resendDone={resendDone}
                  onClick={handleResend}
                />
              </div>
            </div>
          )}

          {unverifiedError && (
            <div
              role="alert"
              className="flex items-start gap-3 rounded-2xl border-2 border-destructive/40 bg-destructive/10 p-4 fun-shadow animate-pop"
            >
              <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0 text-destructive" />
              <div className="text-sm font-display flex-1">
                <p className="font-bold text-foreground">Your email isn't verified yet</p>
                <p className="text-muted-foreground mt-0.5">
                  Check your inbox{verificationSentTo ? <> at <span className="font-bold text-foreground">{verificationSentTo}</span></> : null} for the verification link, then try signing in again.
                </p>
                <ResendLink
                  resending={resending}
                  resendDone={resendDone}
                  onClick={handleResend}
                />
              </div>
            </div>
          )}

          <div className="gradient-card rounded-3xl border-2 border-border/50 p-8 fun-shadow animate-pop">
            <div className="text-center mb-8">
              <div className="mx-auto mb-4 animate-bounce-gentle inline-block">
                <Logo size={64} />
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

              {TURNSTILE_SITE_KEY && (
                <div className="pt-2">
                  <Turnstile
                    sitekey={TURNSTILE_SITE_KEY}
                    onVerify={handleCaptchaVerify}
                    onExpire={handleCaptchaExpire}
                  />
                </div>
              )}

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
                onClick={() => {
                  setIsSignUp(!isSignUp);
                  setUnverifiedError(false);
                  setVerificationSentTo(null);
                  setResendDone(false);
                }}
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

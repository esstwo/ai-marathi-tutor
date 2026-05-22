import { useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Mail, Send, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

const Contact = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !message) {
      toast.error("Please fill in all fields");
      return;
    }
    setLoading(true);
    // Wired to backend in Phase 2 — for now, optimistic local-only confirmation.
    setTimeout(() => {
      setLoading(false);
      setSent(true);
    }, 500);
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      <main className="flex-1">
        <section className="gradient-hero">
          <div className="container mx-auto px-4 py-12 md:py-16 text-center">
            <div className="mx-auto mb-4 inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-lemon/40 animate-bounce-gentle">
              <Mail className="w-8 h-8 text-foreground" />
            </div>
            <h1 className="font-display text-4xl md:text-5xl font-bold text-foreground">
              Get in <span className="text-gradient">Touch</span>
            </h1>
            <p className="text-muted-foreground text-lg mt-3 max-w-xl mx-auto">
              Questions, feedback, ideas, or just want to say hi? We'd love to hear from you.
            </p>
          </div>
        </section>

        <section className="container mx-auto px-4 py-12 max-w-xl">
          <div className="gradient-card rounded-3xl border-2 border-border/50 p-8 fun-shadow animate-pop">
            {sent ? (
              <div className="text-center py-6">
                <div className="mx-auto mb-4 inline-flex items-center justify-center w-16 h-16 rounded-full bg-mint/40">
                  <CheckCircle2 className="w-8 h-8 text-emerald-700" />
                </div>
                <h2 className="font-display text-2xl font-bold text-foreground mb-2">
                  Message sent!
                </h2>
                <p className="text-muted-foreground">
                  Thanks for reaching out — we'll get back to you at{" "}
                  <span className="font-bold text-foreground">{email}</span> soon.
                </p>
                <Button
                  variant="soft"
                  className="mt-6 rounded-2xl font-bold"
                  onClick={() => {
                    setSent(false);
                    setName("");
                    setEmail("");
                    setMessage("");
                  }}
                >
                  Send another message
                </Button>
              </div>
            ) : (
              <form className="space-y-4" onSubmit={handleSubmit}>
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
                  <Label htmlFor="message" className="font-display font-bold">
                    Message
                  </Label>
                  <textarea
                    id="message"
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Tell us what's on your mind..."
                    rows={6}
                    className="w-full bg-background rounded-xl border border-input px-3 py-3 text-base resize-y focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                </div>
                <Button
                  variant="hero"
                  className="w-full mt-2 rounded-2xl h-13 text-base font-bold fun-shadow"
                  size="lg"
                  type="submit"
                  disabled={loading}
                >
                  {loading ? (
                    "Sending..."
                  ) : (
                    <>
                      <Send className="w-5 h-5 mr-1" /> Send Message
                    </>
                  )}
                </Button>
              </form>
            )}
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Contact;

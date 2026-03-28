import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Flower2, Rocket, Users } from "lucide-react";
import { toast } from "sonner";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/contexts/AuthContext";

const AVATARS = ["🐘", "🦁", "🦜", "🐢", "🦋", "🐒"];

const ChildSetup = () => {
  const { children, addChild, selectChild } = useAuth();
  const navigate = useNavigate();

  const [showForm, setShowForm] = useState(children.length === 0);
  const [name, setName] = useState("");
  const [age, setAge] = useState(7);
  const [avatar, setAvatar] = useState("🐘");
  const [loading, setLoading] = useState(false);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Please enter a name");
      return;
    }
    setLoading(true);
    try {
      await addChild(name.trim(), age, avatar);
      toast.success(`${name}'s profile created!`);
      navigate("/home");
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to create profile");
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (child: typeof children[0]) => {
    selectChild(child);
    navigate("/home");
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          {/* Existing children selector */}
          {children.length > 0 && !showForm && (
            <div className="gradient-card rounded-3xl border-2 border-border/50 p-8 fun-shadow animate-pop">
              <div className="text-center mb-6">
                <div className="w-16 h-16 rounded-2xl bg-primary/15 flex items-center justify-center mx-auto mb-4 animate-bounce-gentle">
                  <Users className="w-8 h-8 text-primary" />
                </div>
                <h1 className="font-display text-2xl font-bold text-foreground">
                  Who's Learning Today?
                </h1>
              </div>

              <div className="grid grid-cols-2 gap-3 mb-6">
                {children.map((child) => (
                  <button
                    key={child.id}
                    onClick={() => handleSelect(child)}
                    className="flex flex-col items-center gap-2 p-4 rounded-2xl border-2 border-border/50 hover:border-primary/30 hover:fun-shadow-hover hover:-translate-y-1 transition-all bg-card"
                  >
                    <span className="text-4xl">{child.avatar}</span>
                    <span className="font-display font-bold text-sm">{child.name}</span>
                  </button>
                ))}
              </div>

              <Button
                variant="outline"
                className="w-full rounded-2xl h-12 font-bold font-display"
                onClick={() => setShowForm(true)}
              >
                + Add New Learner
              </Button>
            </div>
          )}

          {/* Create child form */}
          {(showForm || children.length === 0) && (
            <div className="gradient-card rounded-3xl border-2 border-border/50 p-8 fun-shadow animate-pop">
              <div className="text-center mb-8">
                <div className="w-16 h-16 rounded-2xl bg-primary/15 flex items-center justify-center mx-auto mb-4 animate-bounce-gentle">
                  <Flower2 className="w-8 h-8 text-primary" />
                </div>
                <h1 className="font-display text-2xl font-bold text-foreground">
                  Create a Learner Profile
                </h1>
                <p className="text-muted-foreground mt-2 text-sm font-display font-medium">
                  Tell us about the young learner!
                </p>
              </div>

              <form className="space-y-5" onSubmit={handleCreate}>
                <div className="space-y-2">
                  <Label className="font-display font-bold">Name</Label>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Child's name"
                    className="bg-background rounded-xl h-12 text-base"
                  />
                </div>

                <div className="space-y-2">
                  <Label className="font-display font-bold">Age: {age}</Label>
                  <input
                    type="range"
                    min={5}
                    max={12}
                    value={age}
                    onChange={(e) => setAge(Number(e.target.value))}
                    className="w-full accent-primary"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground font-display">
                    <span>5</span>
                    <span>12</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="font-display font-bold">Pick an Avatar</Label>
                  <div className="flex gap-3 justify-center flex-wrap">
                    {AVATARS.map((a) => (
                      <button
                        key={a}
                        type="button"
                        onClick={() => setAvatar(a)}
                        className={`text-3xl p-3 rounded-2xl transition-all ${
                          avatar === a
                            ? "bg-primary/15 ring-2 ring-primary scale-110"
                            : "hover:bg-muted/60 hover:scale-105"
                        }`}
                      >
                        {a}
                      </button>
                    ))}
                  </div>
                </div>

                <Button
                  variant="hero"
                  className="w-full rounded-2xl h-13 text-base font-bold fun-shadow"
                  size="lg"
                  type="submit"
                  disabled={loading}
                >
                  {loading ? (
                    "Creating..."
                  ) : (
                    <>
                      <Rocket className="w-5 h-5 mr-1" /> Start Learning!
                    </>
                  )}
                </Button>

                {children.length > 0 && (
                  <Button
                    variant="ghost"
                    className="w-full rounded-xl font-display font-bold"
                    type="button"
                    onClick={() => setShowForm(false)}
                  >
                    Back to Profiles
                  </Button>
                )}
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChildSetup;

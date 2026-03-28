import Navbar from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";
import { BookOpen, MessageCircle, BarChart3, Users, Sparkles, Star, Rocket, Flower2 } from "lucide-react";
import marathiMitra from "@/assets/marathi-mitra.png";

const features = [
  {
    icon: BookOpen,
    title: "Fun Lessons",
    description: "Learn Marathi words with pictures, sounds, and games. It's like playing!",
    color: "bg-peach/40",
    iconColor: "text-foreground",
  },
  {
    icon: MessageCircle,
    title: "Chat with Mitra",
    description: "Talk to your AI friend who knows Marathi and helps you practice!",
    color: "bg-mint/40",
    iconColor: "text-foreground",
  },
  {
    icon: BarChart3,
    title: "See How You Grow",
    description: "Earn stars, level up, and watch your Marathi skills grow every day!",
    color: "bg-lavender/40",
    iconColor: "text-foreground",
  },
  {
    icon: Users,
    title: "For Parents",
    description: "Parents can see what you're learning and help you along the way.",
    color: "bg-sky/40",
    iconColor: "text-foreground",
  },
];

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {/* Hero */}
      <section className="gradient-hero">
        <div className="container mx-auto px-4 py-14 md:py-20">
          <div className="flex flex-col md:flex-row items-center gap-10 md:gap-16">
            <div className="flex-1 text-center md:text-left space-y-6">
              <div className="inline-flex items-center gap-2 bg-lemon/40 text-foreground px-4 py-2 rounded-full text-sm font-display font-bold animate-bounce-gentle">
                <Star className="w-4 h-4 text-primary" />
                Learning Marathi is fun!
              </div>
              <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold leading-tight text-foreground">
                Learn Marathi with your
                <span className="text-gradient block">AI Best Friend!</span>
              </h1>
              <p className="text-muted-foreground text-lg max-w-lg mx-auto md:mx-0 leading-relaxed">
                Marathi Mitra makes learning Marathi super fun and easy! Play games, chat with your buddy, and become a Marathi superstar!
              </p>
              <div className="flex gap-3 justify-center md:justify-start">
                <Link to="/login">
                  <Button variant="hero" size="lg" className="text-base px-8 rounded-2xl h-14 text-lg font-bold fun-shadow hover:fun-shadow-hover transition-shadow">
                    <Rocket className="w-5 h-5 mr-1" />
                    Let's Go!
                  </Button>
                </Link>
                <Link to="/login">
                  <Button variant="soft" size="lg" className="text-base rounded-2xl h-14 text-lg font-bold">
                    Try a Lesson
                  </Button>
                </Link>
              </div>
            </div>

            <div className="flex-shrink-0">
              <div className="relative">
                <div className="absolute -inset-6 bg-lemon/30 rounded-full blur-3xl" />
                <div className="absolute -inset-8 bg-mint/20 rounded-full blur-3xl animate-float" style={{ animationDelay: "1s" }} />
                <img
                  src={marathiMitra}
                  alt="Marathi Mitra - Your AI Marathi learning friend"
                  width={340}
                  height={340}
                  className="relative animate-float drop-shadow-xl"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-14 md:py-20">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-lavender/30 text-foreground px-4 py-2 rounded-full text-sm font-display font-bold mb-4">
            <Sparkles className="w-4 h-4 text-primary" />
            So much to explore!
          </div>
          <h2 className="font-display text-3xl md:text-4xl font-bold text-foreground">
            Everything You Need to Learn
          </h2>
          <p className="text-muted-foreground mt-3 max-w-md mx-auto text-lg">
            Games, chats, lessons — learning Marathi has never been this exciting!
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, i) => (
            <div
              key={feature.title}
              className="gradient-card rounded-3xl border p-7 hover:fun-shadow-hover hover:-translate-y-2 transition-all duration-300 group"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className={`${feature.color} w-14 h-14 rounded-2xl flex items-center justify-center mb-5 group-hover:animate-wiggle`}>
                <feature.icon className={`w-7 h-7 ${feature.iconColor}`} />
              </div>
              <h3 className="font-display text-lg font-bold text-foreground mb-2">{feature.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-muted/40">
        <div className="container mx-auto px-4 py-14 text-center">
          <div className="inline-flex items-center gap-2 bg-peach/40 text-foreground px-4 py-2 rounded-full text-sm font-display font-bold mb-4 animate-bounce-gentle">
            <Rocket className="w-4 h-4" />
            Join the adventure!
          </div>
          <h2 className="font-display text-3xl font-bold text-foreground mb-4">
            Ready to become a Marathi Superstar?
          </h2>
          <p className="text-muted-foreground mb-8 max-w-md mx-auto text-lg">
            Thousands of kids are already learning with Mitra. Come join the fun!
          </p>
          <Link to="/login">
            <Button variant="hero" size="lg" className="text-lg px-10 rounded-2xl h-14 font-bold fun-shadow hover:fun-shadow-hover transition-shadow">
              <Sparkles className="w-5 h-5 mr-1" />
              Start My Adventure
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <div className="flex items-center justify-center gap-2 mb-1">
            <Flower2 className="w-4 h-4 text-primary" />
            <p className="font-display font-bold text-foreground">Marathi Mitra</p>
          </div>
          <p>Making Marathi learning joyful for kids everywhere.</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;

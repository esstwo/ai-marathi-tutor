import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { Logo } from "@/components/Logo";
import { Heart, Sparkles, Globe2 } from "lucide-react";

const About = () => {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      <main className="flex-1">
        <section className="gradient-hero">
          <div className="container mx-auto px-4 py-14 md:py-20 text-center">
            <div className="mx-auto mb-6 inline-block animate-bounce-gentle">
              <Logo size={96} />
            </div>
            <h1 className="font-display text-4xl md:text-5xl font-bold text-foreground">
              About <span className="text-gradient">Marathi Mitra</span>
            </h1>
            <p className="text-muted-foreground text-lg mt-4 max-w-2xl mx-auto leading-relaxed">
              A friendly AI buddy that helps kids speak Marathi with confidence — through play,
              chat, and stories.
            </p>
          </div>
        </section>

        <section className="container mx-auto px-4 py-12 md:py-16 max-w-3xl space-y-10">
          <div>
            <h2 className="font-display text-2xl font-bold text-foreground mb-3">
              Why we built this
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Lots of diaspora kids understand Marathi when their parents or grandparents speak
              to them — but they answer back in English. The words are there. The confidence
              isn't. Traditional lessons feel like homework, and there's nowhere safe for a
              5- to 12-year-old to just <em>practice speaking</em> without being judged.
              Marathi Mitra is that safe space.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="gradient-card rounded-3xl border p-6 fun-shadow">
              <div className="bg-peach/40 w-12 h-12 rounded-2xl flex items-center justify-center mb-4">
                <Sparkles className="w-6 h-6 text-foreground" />
              </div>
              <h3 className="font-display text-lg font-bold mb-2">Play, don't drill</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Short lessons, picture-based vocabulary, and quick quizzes. Kids earn XP and
                streaks — the way they're used to learning anything fun.
              </p>
            </div>
            <div className="gradient-card rounded-3xl border p-6 fun-shadow">
              <div className="bg-mint/40 w-12 h-12 rounded-2xl flex items-center justify-center mb-4">
                <Heart className="w-6 h-6 text-foreground" />
              </div>
              <h3 className="font-display text-lg font-bold mb-2">Conversations that feel real</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Mitra is an AI friend who chats in Marathi, gently encourages, and never
                makes a kid feel bad for getting a word wrong.
              </p>
            </div>
            <div className="gradient-card rounded-3xl border p-6 fun-shadow">
              <div className="bg-lavender/40 w-12 h-12 rounded-2xl flex items-center justify-center mb-4">
                <Globe2 className="w-6 h-6 text-foreground" />
              </div>
              <h3 className="font-display text-lg font-bold mb-2">Culturally grounded</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Missions are set in scenes kids recognize — visiting Ajji, shopping at the
                market, celebrating Ganpati. The language sticks because the context does.
              </p>
            </div>
          </div>

          <div>
            <h2 className="font-display text-2xl font-bold text-foreground mb-3">
              For parents
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Parents get a weekly digest — what their child learned, conversations they had,
              and gentle suggestions for words to use at home. The aim isn't to replace family
              time. It's to give kids a safe place to practice so when grandma calls, they're
              ready.
            </p>
          </div>

          <div>
            <h2 className="font-display text-2xl font-bold text-foreground mb-3">
              Who's behind it
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Marathi Mitra is built by a Marathi-speaking parent and developer who watched
              their own kid drift away from the language. It's a labor of love for the
              diaspora community — and we'd love your feedback. Drop us a note on the{" "}
              <a href="/contact" className="text-primary font-bold hover:underline">
                Contact page
              </a>
              .
            </p>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default About;

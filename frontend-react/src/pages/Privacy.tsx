import { Link } from "react-router-dom";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { ShieldCheck, Info } from "lucide-react";

const LAST_UPDATED = "May 21, 2026";

const Privacy = () => {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Navbar />
      <main className="flex-1">
        <section className="gradient-hero">
          <div className="container mx-auto px-4 py-12 md:py-16 text-center">
            <div className="mx-auto mb-4 inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-mint/40 animate-bounce-gentle">
              <ShieldCheck className="w-8 h-8 text-foreground" />
            </div>
            <h1 className="font-display text-4xl md:text-5xl font-bold text-foreground">
              Privacy <span className="text-gradient">Policy</span>
            </h1>
            <p className="text-muted-foreground mt-3 text-sm">Last updated: {LAST_UPDATED}</p>
          </div>
        </section>

        <section className="container mx-auto px-4 py-10 max-w-3xl">
          <div className="rounded-2xl border border-border bg-muted/30 p-4 mb-8 flex items-start gap-3 text-sm">
            <Info className="w-5 h-5 mt-0.5 flex-shrink-0 text-foreground" />
            <p className="text-muted-foreground">
              This is a starter template written in plain English. It is not legal advice. We
              will revise it as the product evolves and would welcome any questions through
              our{" "}
              <Link to="/contact" className="text-primary font-bold hover:underline">
                Contact page
              </Link>
              .
            </p>
          </div>

          <article className="space-y-8 text-foreground/90 leading-relaxed">
            <section>
              <h2 className="font-display text-2xl font-bold mb-2">Who we are</h2>
              <p>
                Marathi Mitra is a learning app that helps diaspora kids (ages 5–12) build
                confidence speaking Marathi. A parent or guardian creates the account and
                sets up profiles for their child.
              </p>
            </section>

            <section>
              <h2 className="font-display text-2xl font-bold mb-2">What we collect</h2>
              <ul className="list-disc pl-6 space-y-1.5 text-muted-foreground">
                <li>
                  <span className="text-foreground font-semibold">Parent account:</span> name
                  and email address you provide at signup.
                </li>
                <li>
                  <span className="text-foreground font-semibold">Child profile:</span> the
                  child's first name, age, and emoji avatar — created by you, not by the child.
                </li>
                <li>
                  <span className="text-foreground font-semibold">Learning activity:</span>{" "}
                  lessons completed, quiz scores, XP, streaks, and chat messages exchanged
                  with the AI tutor.
                </li>
                <li>
                  <span className="text-foreground font-semibold">Voice input (optional):</span>{" "}
                  if the child uses voice chat, the audio is transcribed and discarded; the
                  resulting text is treated like any other chat message.
                </li>
                <li>
                  <span className="text-foreground font-semibold">Technical:</span> IP address
                  (used only for abuse prevention and rate-limiting) and standard server logs.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="font-display text-2xl font-bold mb-2">How we use it</h2>
              <ul className="list-disc pl-6 space-y-1.5 text-muted-foreground">
                <li>Run the service and save your child's progress.</li>
                <li>Generate AI tutor responses by sending chat messages to our language-model provider.</li>
                <li>Send you a weekly email digest summarizing your child's activity.</li>
                <li>Detect and prevent abuse (rate-limiting, spam, scraping).</li>
                <li>Improve the product. We never sell your data and do not show your child third-party advertising.</li>
              </ul>
            </section>

            <section>
              <h2 className="font-display text-2xl font-bold mb-2">Children's privacy</h2>
              <p className="mb-2 text-muted-foreground">
                Marathi Mitra is designed to be used by children only with a parent's account.
                We follow these rules:
              </p>
              <ul className="list-disc pl-6 space-y-1.5 text-muted-foreground">
                <li>Only an adult parent or guardian can create an account.</li>
                <li>We never ask the child for their email, phone, address, or other personal contact information.</li>
                <li>We do not knowingly sell children's data or share it with advertisers.</li>
                <li>Parents can review, export, or delete their child's data at any time by writing to us through the{" "}
                  <Link to="/contact" className="text-primary font-bold hover:underline">Contact page</Link>.
                </li>
              </ul>
            </section>

            <section>
              <h2 className="font-display text-2xl font-bold mb-2">Who we share data with</h2>
              <p className="mb-2 text-muted-foreground">
                We use a small set of trusted vendors to operate the service. They process
                data only on our instructions:
              </p>
              <ul className="list-disc pl-6 space-y-1.5 text-muted-foreground">
                <li><span className="font-semibold text-foreground">Supabase</span> — database and authentication.</li>
                <li><span className="font-semibold text-foreground">Sarvam AI</span> — generates the Marathi tutor's chat responses.</li>
                <li><span className="font-semibold text-foreground">Google Cloud</span> — text-to-speech audio.</li>
                <li><span className="font-semibold text-foreground">Groq</span> — speech-to-text transcription (when voice input is used).</li>
                <li><span className="font-semibold text-foreground">Resend</span> — delivers transactional and digest emails.</li>
                <li><span className="font-semibold text-foreground">Cloudflare</span> — bot protection (Turnstile) on sign-in.</li>
                <li><span className="font-semibold text-foreground">Vercel and Render</span> — host the website and backend.</li>
              </ul>
            </section>

            <section>
              <h2 className="font-display text-2xl font-bold mb-2">Cookies and local storage</h2>
              <p className="text-muted-foreground">
                We use your browser's local storage to keep you signed in. We do not use
                third-party tracking cookies or advertising trackers.
              </p>
            </section>

            <section>
              <h2 className="font-display text-2xl font-bold mb-2">Data retention</h2>
              <p className="text-muted-foreground">
                We keep account and learning data for as long as your account is active. If
                you ask us to delete your data, we will remove it from our active systems
                within 30 days. Encrypted backups roll off shortly after.
              </p>
            </section>

            <section>
              <h2 className="font-display text-2xl font-bold mb-2">Your rights</h2>
              <p className="text-muted-foreground">
                You can ask us to access, correct, export, or delete your or your child's
                personal information. Write to us through the{" "}
                <Link to="/contact" className="text-primary font-bold hover:underline">Contact page</Link>{" "}
                and we will respond as quickly as we can.
              </p>
            </section>

            <section>
              <h2 className="font-display text-2xl font-bold mb-2">Changes to this policy</h2>
              <p className="text-muted-foreground">
                We may update this page from time to time. When we make a material change we
                will update the "Last updated" date above. If the change affects how we handle
                children's data, we will email account holders.
              </p>
            </section>

            <section>
              <h2 className="font-display text-2xl font-bold mb-2">Questions?</h2>
              <p className="text-muted-foreground">
                Reach us through the{" "}
                <Link to="/contact" className="text-primary font-bold hover:underline">Contact page</Link>.
              </p>
            </section>
          </article>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Privacy;

import type { Metadata } from "next";
import { Inter, Instrument_Serif, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import { Mark } from "@/components/Mark";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const serif = Instrument_Serif({
  variable: "--font-instrument-serif",
  subsets: ["latin"],
  weight: "400",
  style: ["normal", "italic"],
});
const mono = JetBrains_Mono({ variable: "--font-jetbrains-mono", subsets: ["latin"] });

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3001";
const repoUrl = "https://github.com/JiveFish2/pricetrail";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: "PriceTrail", template: "%s · PriceTrail" },
  description:
    "Daily price history for games and hardware across several stores, with email alerts when a price drops.",
};

const links = [
  { href: "/", label: "Products" },
  { href: "/status", label: "Status" },
  { href: "/api", label: "API" },
] as const;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} ${serif.variable} ${mono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <header className="border-b border-rule bg-sheet/70 backdrop-blur">
          <nav aria-label="Main" className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-3.5">
            <Link href="/" className="flex items-center gap-2.5 font-semibold tracking-tight">
              <Mark />
              <span>
                Price<span className="text-trail">Trail</span>
              </span>
            </Link>
            <div className="flex items-center gap-0.5 text-sm">
              {links.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="rounded-full px-2.5 py-2 text-ink-2 transition-colors hover:bg-paper hover:text-ink sm:px-3"
                >
                  {link.label}
                </Link>
              ))}
              <a
                href={repoUrl}
                className="ml-1 hidden rounded-full border border-rule px-3.5 py-2 font-mono text-xs uppercase tracking-wider text-ink transition-colors hover:border-ink sm:inline-block"
              >
                GitHub
              </a>
            </div>
          </nav>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-10">{children}</main>
        <footer className="mt-10 border-t border-rule">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-6 text-sm text-ink-2">
            <p>
              Public product data only, collected once a day with an identified user agent.{" "}
              <Link href="/status" className="text-ink underline decoration-rule underline-offset-4 hover:decoration-ink">
                How collection works
              </Link>
            </p>
            <p>
              <a href={repoUrl} className="text-ink underline decoration-rule underline-offset-4 hover:decoration-ink">
                Source on GitHub
              </a>
              {" · "}Built by{" "}
              <a href="https://github.com/JiveFish2" className="text-ink underline decoration-rule underline-offset-4 hover:decoration-ink">
                Daniel Garcia
              </a>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

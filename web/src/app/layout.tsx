import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3001";
const repoUrl = "https://github.com/JiveFish2/pricetrail";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: { default: "PriceTrail", template: "%s · PriceTrail" },
  description:
    "Daily price history for games, merch and hardware across several stores, with email alerts when a price drops.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <header className="border-b border-line">
          <nav
            aria-label="Main"
            className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4"
          >
            <Link href="/" className="font-semibold tracking-tight">
              Price<span className="text-a">Trail</span>
            </Link>
            <div className="flex items-center gap-1 text-sm">
              <Link href="/" className="rounded-full px-3 py-2 text-fg/85 hover:bg-fg/10">
                Products
              </Link>
              <Link href="/status" className="rounded-full px-3 py-2 text-fg/85 hover:bg-fg/10">
                Status
              </Link>
              <Link href="/api" className="rounded-full px-3 py-2 text-fg/85 hover:bg-fg/10">
                API
              </Link>
              <a
                href={repoUrl}
                className="ml-1 rounded-full border border-line px-3.5 py-2 font-mono text-xs uppercase tracking-wider text-a hover:border-a"
              >
                GitHub
              </a>
            </div>
          </nav>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-10">{children}</main>
        <footer className="border-t border-line">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-6 text-sm text-mute">
            <p>
              Public product data only, collected once a day with an identified user agent.{" "}
              <Link href="/status" className="text-fg/80 underline-offset-4 hover:underline">
                How collection works
              </Link>
            </p>
            <p>
              Built by{" "}
              <a href="https://github.com/JiveFish2" className="text-fg/80 underline-offset-4 hover:underline">
                Daniel Garcia
              </a>
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

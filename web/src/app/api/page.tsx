import Link from "next/link";

export const metadata = { title: "API", description: "Read-only JSON API for PriceTrail data." };

const endpoints = [
  { path: "/api/products", what: "Every product with the latest price per store and the 30-day range." },
  { path: "/api/products/{slug}", what: "One product with its daily price history per store." },
  { path: "/api/status", what: "Health of each source: last run, success rate, average time." },
];

export default function ApiPage() {
  return (
    <section className="max-w-3xl">
      <p className="eyebrow">API</p>
      <h1 className="mt-3 text-5xl">Read-only JSON, <em className="text-trail">no key.</em></h1>
      <p className="mt-4 text-lg text-ink-2">
        The same data the pages show, refreshed after each daily run. Please cache responses and
        keep it to a few requests a minute.
      </p>
      <ul className="mt-8 space-y-4">
        {endpoints.map((e) => (
          <li key={e.path} className="sheet p-5">
            <Link href={e.path.replace("{slug}", "elden-ring")} className="font-mono text-trail hover:underline">
              GET {e.path}
            </Link>
            <p className="mt-1 text-sm text-ink-2">{e.what}</p>
          </li>
        ))}
      </ul>
      <pre className="mt-8 overflow-x-auto rounded-md bg-ink p-5 font-mono text-xs leading-relaxed text-paper">
{`curl -s ${process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3001"}/api/products/elden-ring | jq '.offers[] | {sourceName, currency, price, low30}'`}
      </pre>
    </section>
  );
}

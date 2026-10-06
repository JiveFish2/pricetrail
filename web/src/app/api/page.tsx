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
      <h1 className="mt-3 text-4xl font-semibold tracking-tight">Read-only JSON, no key.</h1>
      <p className="mt-4 text-lg text-mute">
        The same data the pages show, refreshed after each daily run. Please cache responses and
        keep it to a few requests a minute.
      </p>
      <ul className="mt-8 space-y-4">
        {endpoints.map((e) => (
          <li key={e.path} className="card p-5">
            <Link href={e.path.replace("{slug}", "elden-ring")} className="font-mono text-b hover:underline">
              GET {e.path}
            </Link>
            <p className="mt-1 text-sm text-mute">{e.what}</p>
          </li>
        ))}
      </ul>
      <pre className="card mt-8 overflow-x-auto p-5 font-mono text-xs leading-relaxed text-mute">
{`curl -s ${process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3001"}/api/products/elden-ring | jq '.offers[] | {sourceName, currency, price, low30}'`}
      </pre>
    </section>
  );
}

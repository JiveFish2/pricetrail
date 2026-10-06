import Link from "next/link";
import { Suspense } from "react";
import { connection } from "next/server";
import { sql } from "@/lib/db";
import { money } from "@/lib/format";

export const metadata = { title: "Alert confirmed", robots: { index: false } };

export default function ConfirmPage({ params }: PageProps<"/alerts/confirm/[token]">) {
  return (
    <Suspense fallback={<section className="mx-auto max-w-xl py-10 text-center text-mute">Working…</section>}>
      <Result params={params} />
    </Suspense>
  );
}

// The database write happens here, outside the prerendered shell.
async function Result({ params }: { params: PageProps<"/alerts/confirm/[token]">["params"] }) {
  await connection();
  const { token } = await params;
  const [alert] = await sql<
    { product: string; source: string; currency: string; target_price: string; unsubscribe_token: string }[]
  >`
    update alerts a set confirmed_at = coalesce(a.confirmed_at, now())
    from offers o join sources s on s.id = o.source_id join products p on p.id = o.product_id
    where a.confirm_token = ${token} and o.id = a.offer_id
    returning p.name as product, s.name as source, s.currency, a.target_price, a.unsubscribe_token
  `;

  return (
    <section className="mx-auto max-w-xl py-10 text-center">
      {alert ? (
        <>
          <p className="eyebrow">Alert confirmed</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight">You&apos;re set.</h1>
          <p className="mt-4 text-mute">
            We&apos;ll email you once when <strong className="text-fg">{alert.product}</strong> at{" "}
            {alert.source} goes at or below{" "}
            <span className="font-mono text-fg">{money(alert.target_price, alert.currency)}</span>.
            Prices are checked once a day.
          </p>
          <p className="mt-6 text-sm text-mute">
            Changed your mind?{" "}
            <Link href={`/alerts/unsubscribe/${alert.unsubscribe_token}`} className="text-b hover:underline">
              Remove this alert
            </Link>
          </p>
        </>
      ) : (
        <>
          <p className="eyebrow">Link not found</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight">This link is no longer valid.</h1>
          <p className="mt-4 text-mute">The alert may have been removed. You can create a new one from any product page.</p>
        </>
      )}
      <Link href="/" className="btn mt-8">Back to products</Link>
    </section>
  );
}

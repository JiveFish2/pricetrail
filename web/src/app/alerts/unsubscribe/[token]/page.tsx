import Link from "next/link";
import { Suspense } from "react";
import { connection } from "next/server";
import { sql } from "@/lib/db";

export const metadata = { title: "Alert removed", robots: { index: false } };

export default function UnsubscribePage({ params }: PageProps<"/alerts/unsubscribe/[token]">) {
  return (
    <Suspense fallback={<section className="mx-auto max-w-xl py-10 text-center text-ink-2">Working…</section>}>
      <Result params={params} />
    </Suspense>
  );
}

// The database write happens here, outside the prerendered shell.
async function Result({ params }: { params: PageProps<"/alerts/unsubscribe/[token]">["params"] }) {
  await connection();
  const { token } = await params;
  const removed = await sql`delete from alerts where unsubscribe_token = ${token} returning id`;

  return (
    <section className="mx-auto max-w-xl py-10 text-center">
      <p className="eyebrow">{removed.length ? "Alert removed" : "Nothing to remove"}</p>
      <h1 className="mt-3 text-4xl">
        {removed.length ? "You won't hear from us about this one." : "This alert was already removed."}
      </h1>
      <Link href="/" className="btn mt-8">Back to products</Link>
    </section>
  );
}

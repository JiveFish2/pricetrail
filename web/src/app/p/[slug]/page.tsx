import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { AlertForm } from "@/components/AlertForm";
import { PriceChart } from "@/components/PriceChart";
import { getProduct, listSlugs } from "@/lib/data";
import { Ago } from "@/components/Ago";
import { discount, money } from "@/lib/format";

export async function generateStaticParams() {
  return (await listSlugs()).map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: PageProps<"/p/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) return {};
  const cheapest = product.offers.find((o) => o.price !== null);
  return {
    title: product.name,
    description: cheapest
      ? `${product.name}: ${money(cheapest.price, cheapest.currency)} at ${cheapest.sourceName}. Price history and alerts.`
      : `${product.name} price history and alerts.`,
  };
}

export default function ProductPage({ params }: PageProps<"/p/[slug]">) {
  return (
    <Suspense fallback={<Skeleton />}>
      <ProductDetails params={params} />
    </Suspense>
  );
}

// Listed slugs are prerendered; an unlisted one streams in behind the skeleton.
async function ProductDetails({ params }: { params: PageProps<"/p/[slug]">["params"] }) {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) notFound();

  return (
    <>
      <nav aria-label="Breadcrumb" className="mb-6 text-sm text-mute">
        <Link href="/" className="hover:text-fg">
          Products
        </Link>{" "}
        / {product.category}
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">{product.name}</h1>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Current prices">
        {product.offers.map((offer) => {
          const off = discount(offer.price, offer.listPrice);
          return (
            <article key={offer.id} className="card p-5">
              <p className="eyebrow">{offer.sourceName}</p>
              <p className="mt-2 font-mono text-2xl tabular-nums">
                {offer.available === false ? (
                  <span className="text-mute">Unavailable</span>
                ) : (
                  money(offer.price, offer.currency)
                )}
              </p>
              <dl className="mt-3 space-y-1 text-sm text-mute">
                {off !== null && (
                  <div className="flex justify-between">
                    <dt>List price</dt>
                    <dd className="font-mono">
                      <s>{money(offer.listPrice, offer.currency)}</s>{" "}
                      <span className="text-ok">-{off}%</span>
                    </dd>
                  </div>
                )}
                <div className="flex justify-between">
                  <dt>30-day low</dt>
                  <dd className="font-mono">{money(offer.low30, offer.currency)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>30-day high</dt>
                  <dd className="font-mono">{money(offer.high30, offer.currency)}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Checked</dt>
                  <dd><Ago iso={offer.observedAt} /></dd>
                </div>
              </dl>
              <a
                href={offer.url}
                rel="noopener nofollow"
                className="mt-4 inline-block text-sm text-b underline-offset-4 hover:underline"
              >
                Open at {offer.sourceName} →
              </a>
            </article>
          );
        })}
      </section>

      <section className="mt-10" aria-labelledby="history">
        <h2 id="history" className="eyebrow mb-4">
          Price history
        </h2>
        <PriceChart offers={product.offers} history={product.history} />
      </section>

      <section className="mt-10 max-w-2xl">
        <AlertForm offers={product.offers} />
      </section>
    </>
  );
}

function Skeleton() {
  return (
    <div aria-busy="true" aria-label="Loading product">
      <div className="mb-6 h-4 w-32 rounded bg-line" />
      <div className="h-10 w-2/3 rounded bg-line" />
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="card h-56" />
        <div className="card h-56" />
      </div>
    </div>
  );
}

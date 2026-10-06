import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { Ago } from "@/components/Ago";
import { AlertForm } from "@/components/AlertForm";
import { PriceChart } from "@/components/PriceChart";
import { ProductImage } from "@/components/ProductImage";
import { getProduct, listSlugs } from "@/lib/data";
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
    openGraph: product.imageUrl ? { images: [product.imageUrl] } : undefined,
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
      <nav aria-label="Breadcrumb" className="mb-6 font-mono text-xs uppercase tracking-wider text-ink-3">
        <Link href="/" className="hover:text-ink">
          Products
        </Link>{" "}
        / {product.category}
      </nav>

      <section className="grid gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-start">
        <div>
          <ProductImage
            src={product.imageUrl}
            alt={product.name}
            category={product.category}
            priority
            sizes="(min-width: 1024px) 45vw, 100vw"
          />
        </div>
        <div>
          <h1 className="text-4xl leading-tight sm:text-5xl">{product.name}</h1>
          <div className="mt-6 grid gap-3 sm:grid-cols-2" aria-label="Current prices">
            {product.offers.map((offer) => {
              const off = discount(offer.price, offer.listPrice);
              return (
                <article key={offer.id} className={`sheet p-4 ${off !== null ? "on-sale" : ""}`}>
                  <p className="eyebrow">{offer.sourceName}</p>
                  <p className="num mt-2 text-2xl">
                    {offer.available === false ? (
                      <span className="text-ink-3">Unavailable</span>
                    ) : (
                      money(offer.price, offer.currency)
                    )}
                    {off !== null && <span className="tag tag-gold ml-2 align-middle">−{off}%</span>}
                  </p>
                  <dl className="dashed mt-3 space-y-1 pt-3 text-sm text-ink-2">
                    {off !== null && (
                      <div className="flex justify-between">
                        <dt>List price</dt>
                        <dd className="num">
                          <s>{money(offer.listPrice, offer.currency)}</s>
                        </dd>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <dt>30-day low</dt>
                      <dd className="num">{money(offer.low30, offer.currency)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt>30-day high</dt>
                      <dd className="num">{money(offer.high30, offer.currency)}</dd>
                    </div>
                    <div className="flex justify-between">
                      <dt>Checked</dt>
                      <dd>
                        <Ago iso={offer.observedAt} />
                      </dd>
                    </div>
                  </dl>
                  <a
                    href={offer.url}
                    rel="noopener nofollow"
                    className="mt-3 inline-block text-sm text-trail underline decoration-trail/30 underline-offset-4 hover:decoration-trail"
                  >
                    Open at {offer.sourceName} →
                  </a>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <section className="mt-12" aria-labelledby="history">
        <div className="mb-4 flex items-baseline gap-4">
          <h2 id="history" className="display text-2xl">
            Price history
          </h2>
          <span aria-hidden="true" className="dashed flex-1" />
        </div>
        <PriceChart offers={product.offers} history={product.history} />
      </section>

      <section className="mt-12 max-w-2xl">
        <AlertForm offers={product.offers} />
      </section>
    </>
  );
}

function Skeleton() {
  return (
    <div aria-busy="true" aria-label="Loading product">
      <div className="mb-6 h-3 w-32 rounded bg-rule" />
      <div className="grid gap-8 lg:grid-cols-[1fr_1.1fr]">
        <div className="aspect-[16/9] rounded-md bg-rule" />
        <div>
          <div className="h-12 w-3/4 rounded bg-rule" />
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <div className="sheet h-48" />
            <div className="sheet h-48" />
          </div>
        </div>
      </div>
    </div>
  );
}

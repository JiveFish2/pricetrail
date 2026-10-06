import { ProductCard } from "@/components/ProductCard";
import { listProducts } from "@/lib/data";

export default async function HomePage() {
  const products = await listProducts();
  const categories = [...new Set(products.map((p) => p.category))];
  const sources = new Set(products.flatMap((p) => p.offers.map((o) => o.sourceId)));
  const drops = products.filter((p) =>
    p.offers.some((o) => o.listPrice && o.price && Number(o.listPrice) > Number(o.price)),
  ).length;

  return (
    <>
      <section className="mb-12 grid gap-8 md:grid-cols-[1.4fr_1fr] md:items-end">
        <div>
          <p className="eyebrow">Price history, one check a day</p>
          <h1 className="mt-3 text-5xl leading-[1.02] sm:text-6xl">
            Prices leave a trail.
            <br />
            <em className="text-trail">Follow it</em> before you buy.
          </h1>
        </div>
        <dl className="sheet grid grid-cols-3 divide-x divide-rule p-1 text-center">
          {[
            [products.length, "products"],
            [sources.size, "stores"],
            [drops, "on sale now"],
          ].map(([value, label]) => (
            <div key={label} className="px-3 py-4">
              <dt className="order-last font-mono text-[11px] uppercase tracking-wider text-ink-3">{label}</dt>
              <dd className="num text-3xl">{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      {categories.map((category, i) => (
        <section key={category} className="mb-12" aria-labelledby={`cat-${category}`}>
          <div className="mb-5 flex items-baseline gap-4">
            <h2 id={`cat-${category}`} className="display text-2xl">
              {category}
            </h2>
            <span aria-hidden="true" className="dashed flex-1" />
            <span className="font-mono text-xs text-ink-3">
              {products.filter((p) => p.category === category).length}
            </span>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {products
              .filter((p) => p.category === category)
              .map((product, j) => (
                <ProductCard key={product.id} product={product} priority={i === 0 && j < 3} />
              ))}
          </div>
        </section>
      ))}
    </>
  );
}

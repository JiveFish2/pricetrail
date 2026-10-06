import { ProductCard } from "@/components/ProductCard";
import { listProducts } from "@/lib/data";

export default async function HomePage() {
  const products = await listProducts();
  const categories = [...new Set(products.map((p) => p.category))];
  const sources = new Set(products.flatMap((p) => p.offers.map((o) => o.sourceId)));

  return (
    <>
      <section className="mb-12 max-w-3xl">
        <p className="eyebrow">Price history, one check a day</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">
          Watch prices across stores without refreshing tabs.
        </h1>
        <p className="mt-4 text-lg text-mute">
          {products.length} products tracked in {sources.size} sources. Open a product to see
          its history, the lowest price of the last 30 days, and set an email alert for the
          price you want.
        </p>
      </section>

      {categories.map((category) => (
        <section key={category} className="mb-12" aria-labelledby={`cat-${category}`}>
          <div className="mb-5 flex items-center gap-4">
            <h2 id={`cat-${category}`} className="eyebrow">
              {category}
            </h2>
            <span aria-hidden="true" className="h-px flex-1 bg-line" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {products
              .filter((p) => p.category === category)
              .map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
          </div>
        </section>
      ))}
    </>
  );
}

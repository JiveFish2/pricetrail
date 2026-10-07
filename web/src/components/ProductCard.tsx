import Link from "next/link";
import { Ago } from "@/components/Ago";
import { ProductImage } from "@/components/ProductImage";
import type { ProductSummary } from "@/lib/data";
import { change, discount, money } from "@/lib/format";

export function ProductCard({ product, priority = false }: { product: ProductSummary; priority?: boolean }) {
  const updated = product.offers.find((o) => o.observedAt)?.observedAt ?? null;
  const onSale = product.offers.some((o) => discount(o.price, o.listPrice) !== null);
  return (
    <Link
      href={`/p/${product.slug}`}
      className={`sheet group flex flex-col gap-4 p-4 transition-[transform,box-shadow] hover:-translate-y-0.5 ${
        onSale ? "on-sale" : ""
      }`}
    >
      <ProductImage src={product.imageUrl} alt="" category={product.category} priority={priority} />
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="eyebrow">{product.category}</p>
          <h3 className="mt-1 text-lg font-medium leading-snug group-hover:underline group-hover:decoration-rule group-hover:underline-offset-4">
            {product.name}
          </h3>
        </div>
        {onSale && <span className="tag tag-gold mt-0.5 shrink-0">On sale</span>}
      </div>
      <ul className="dashed mt-auto pt-3">
        {product.offers.map((offer) => {
          const off = discount(offer.price, offer.listPrice);
          const delta = change(offer.price, offer.previousPrice);
          const atLow =
            offer.price !== null && offer.low30 !== null && offer.price === offer.low30 && offer.high30 !== offer.low30;
          return (
            <li key={offer.id} className="flex items-baseline justify-between gap-3 py-1 text-sm">
              <span className="text-ink-2">{offer.sourceName}</span>
              <span className="flex items-baseline gap-2">
                {off !== null && <span className="tag tag-gold">−{off}%</span>}
                {delta !== null && delta < 0 && <span className="tag tag-drop">↓ {delta}%</span>}
                {delta !== null && delta > 0 && <span className="tag tag-rise">↑ +{delta}%</span>}
                {atLow && off === null && delta === null && <span className="tag tag-drop">30-day low</span>}
                <span className={`num ${offer.available === false ? "text-ink-3 line-through" : ""}`}>
                  {offer.available === false ? "unavailable" : money(offer.price, offer.currency)}
                </span>
              </span>
            </li>
          );
        })}
      </ul>
      <p className="font-mono text-[11px] uppercase tracking-wider text-ink-3">
        Checked <Ago iso={updated} />
      </p>
    </Link>
  );
}

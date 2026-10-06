import Link from "next/link";
import type { ProductSummary } from "@/lib/data";
import { Ago } from "@/components/Ago";
import { discount, money } from "@/lib/format";

export function ProductCard({ product }: { product: ProductSummary }) {
  return (
    <Link
      href={`/p/${product.slug}`}
      className="card flex flex-col gap-4 p-5 transition-colors hover:border-a/60"
    >
      <div>
        <p className="eyebrow">{product.category}</p>
        <h3 className="mt-1 text-lg font-semibold leading-snug">{product.name}</h3>
      </div>
      <ul className="mt-auto space-y-2">
        {product.offers.map((offer) => {
          const off = discount(offer.price, offer.listPrice);
          const atLow = offer.price !== null && offer.low30 !== null && offer.price === offer.low30;
          return (
            <li key={offer.id} className="flex items-baseline justify-between gap-3 text-sm">
              <span className="text-mute">{offer.sourceName}</span>
              <span className="flex items-baseline gap-2 text-right">
                {off !== null && (
                  <span className="rounded-full bg-ok/15 px-2 py-0.5 font-mono text-[11px] text-ok">
                    -{off}%
                  </span>
                )}
                {atLow && off === null && offer.high30 !== offer.low30 && (
                  <span className="rounded-full bg-a/15 px-2 py-0.5 font-mono text-[11px] text-b">
                    30-day low
                  </span>
                )}
                <span
                  className={`font-mono tabular-nums ${offer.available === false ? "text-mute line-through" : ""}`}
                >
                  {offer.available === false ? "unavailable" : money(offer.price, offer.currency)}
                </span>
              </span>
            </li>
          );
        })}
      </ul>
      <p className="text-xs text-mute">
        Updated <Ago iso={product.offers.find((o) => o.observedAt)?.observedAt ?? null} />
      </p>
    </Link>
  );
}

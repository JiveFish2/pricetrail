import { cacheLife, cacheTag } from "next/cache";
import { sql } from "@/lib/db";

// Every read is cached for hours and tagged "prices"; the collector calls
// /api/revalidate after each run so the site refreshes right after new data.

export type OfferSummary = {
  id: number;
  sourceId: string;
  sourceName: string;
  sourceKind: string;
  currency: string;
  url: string;
  price: string | null;
  listPrice: string | null;
  available: boolean | null;
  observedAt: string | null;
  low30: string | null;
  high30: string | null;
};

export type ProductSummary = {
  id: number;
  slug: string;
  name: string;
  category: string;
  imageUrl: string | null;
  offers: OfferSummary[];
};

export type PricePoint = { day: string; price: string | null; available: boolean };

export type ProductDetail = ProductSummary & {
  history: Record<number, PricePoint[]>; // keyed by offer id
};

export type SourceStatus = {
  id: string;
  name: string;
  kind: string;
  currency: string;
  offersTracked: number;
  lastRunAt: string | null;
  lastStatus: string | null;
  lastOffersOk: number | null;
  lastOffersTotal: number | null;
  lastError: string | null;
  runs7d: number;
  okRate7d: number | null;
  avgSeconds7d: string | null;
};

type OfferRow = {
  product_id: number;
  id: number;
  source_id: string;
  source_name: string;
  source_kind: string;
  currency: string;
  url: string;
  price: string | null;
  list_price: string | null;
  available: boolean | null;
  observed_at: Date | null;
  low30: string | null;
  high30: string | null;
};

type ProductRow = { id: number; slug: string; name: string; category: string; image_url: string | null };

function toProduct(row: ProductRow) {
  return { id: row.id, slug: row.slug, name: row.name, category: row.category, imageUrl: row.image_url };
}

// Latest price point per offer plus the 30-day range, for one or all products.
async function offerRows(productId?: number): Promise<OfferRow[]> {
  return sql<OfferRow[]>`
    with latest as (
      select distinct on (offer_id) offer_id, price, list_price, available, observed_at
      from price_points
      order by offer_id, observed_at desc
    ),
    range as (
      select offer_id, min(price) as low30, max(price) as high30
      from price_points
      where observed_at > now() - interval '30 days' and price is not null
      group by offer_id
    )
    select o.product_id, o.id, o.source_id, s.name as source_name, s.kind as source_kind,
           s.currency, o.url, l.price, l.list_price, l.available, l.observed_at,
           r.low30, r.high30
    from offers o
    join sources s on s.id = o.source_id
    left join latest l on l.offer_id = o.id
    left join range r on r.offer_id = o.id
    ${productId ? sql`where o.product_id = ${productId}` : sql``}
    order by o.product_id, s.currency, s.id
  `;
}

function toOffer(row: OfferRow): OfferSummary {
  return {
    id: row.id,
    sourceId: row.source_id,
    sourceName: row.source_name,
    sourceKind: row.source_kind,
    currency: row.currency,
    url: row.url,
    price: row.price,
    listPrice: row.list_price,
    available: row.available,
    observedAt: row.observed_at?.toISOString() ?? null,
    low30: row.low30,
    high30: row.high30,
  };
}

export async function listProducts(): Promise<ProductSummary[]> {
  "use cache";
  cacheLife("hours");
  cacheTag("prices");

  const products = await sql<ProductRow[]>`
    select id, slug, name, category, image_url from products order by category, name
  `;
  const offers = await offerRows();
  return products.map((product) => ({
    ...toProduct(product),
    offers: offers.filter((row) => row.product_id === product.id).map(toOffer),
  }));
}

export async function getProduct(slug: string): Promise<ProductDetail | null> {
  "use cache";
  cacheLife("hours");
  cacheTag("prices");

  const [product] = await sql<ProductRow[]>`
    select id, slug, name, category, image_url from products where slug = ${slug}
  `;
  if (!product) return null;

  const offers = (await offerRows(product.id)).map(toOffer);
  // One point per offer per day (the last observation of the day).
  const points = await sql<{ offer_id: number; day: string; price: string | null; available: boolean }[]>`
    select distinct on (offer_id, day) offer_id, day::text, price, available
    from (
      select offer_id, (observed_at at time zone 'UTC')::date as day, price, available, observed_at
      from price_points
      where offer_id in (select id from offers where product_id = ${product.id})
    ) daily
    order by offer_id, day, observed_at desc
  `;
  const history: Record<number, PricePoint[]> = {};
  for (const offer of offers) history[offer.id] = [];
  for (const point of points) {
    history[point.offer_id]?.push({ day: point.day, price: point.price, available: point.available });
  }
  return { ...toProduct(product), offers, history };
}

export async function listSlugs(): Promise<string[]> {
  "use cache";
  cacheLife("hours");
  cacheTag("prices");
  const rows = await sql<{ slug: string }[]>`select slug from products order by slug`;
  return rows.map((row) => row.slug);
}

export async function getStatus(): Promise<SourceStatus[]> {
  "use cache";
  cacheLife("hours");
  cacheTag("prices");

  const rows = await sql<
    {
      id: string;
      name: string;
      kind: string;
      currency: string;
      offers_tracked: string;
      last_run_at: Date | null;
      last_status: string | null;
      last_offers_ok: number | null;
      last_offers_total: number | null;
      last_error: string | null;
      runs_7d: string;
      ok_rate_7d: string | null;
      avg_seconds_7d: string | null;
    }[]
  >`select * from source_status`;

  return rows.map((row) => ({
    id: row.id,
    name: row.name,
    kind: row.kind,
    currency: row.currency,
    offersTracked: Number(row.offers_tracked),
    lastRunAt: row.last_run_at?.toISOString() ?? null,
    lastStatus: row.last_status,
    lastOffersOk: row.last_offers_ok,
    lastOffersTotal: row.last_offers_total,
    lastError: row.last_error,
    runs7d: Number(row.runs_7d),
    okRate7d: row.ok_rate_7d === null ? null : Number(row.ok_rate_7d),
    avgSeconds7d: row.avg_seconds_7d,
  }));
}

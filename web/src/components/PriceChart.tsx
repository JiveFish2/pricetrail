import type { OfferSummary, PricePoint } from "@/lib/data";
import { money, shortDate } from "@/lib/format";

// A server-rendered SVG line chart: one line per offer, no client JavaScript.
// Offers in different currencies get their own scale, so lines are only
// comparable within a currency; the legend says which is which.

const COLORS = ["#4f8cff", "#8ec1ff", "#5fd39a", "#f0b072", "#ff6b7a"];
const W = 720;
const H = 240;
const PAD = { top: 16, right: 16, bottom: 28, left: 56 };

type Series = { offer: OfferSummary; points: PricePoint[]; color: string };

export function PriceChart({
  offers,
  history,
}: {
  offers: OfferSummary[];
  history: Record<number, PricePoint[]>;
}) {
  const series: Series[] = offers.map((offer, i) => ({
    offer,
    points: (history[offer.id] ?? []).filter((p) => p.price !== null),
    color: COLORS[i % COLORS.length],
  }));
  const days = [...new Set(series.flatMap((s) => s.points.map((p) => p.day)))].sort();
  if (days.length < 2) {
    return (
      <p className="card p-6 text-sm text-mute">
        The chart appears after two days of data. Collected so far: {days.length} day
        {days.length === 1 ? "" : "s"}.
      </p>
    );
  }

  const x = (day: string) =>
    PAD.left + (days.indexOf(day) / (days.length - 1)) * (W - PAD.left - PAD.right);

  // Scale per currency so BRL and USD lines are each readable.
  const scales = new Map<string, (v: number) => number>();
  for (const currency of new Set(series.map((s) => s.offer.currency))) {
    const values = series
      .filter((s) => s.offer.currency === currency)
      .flatMap((s) => s.points.map((p) => Number(p.price)));
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max - min || max * 0.1 || 1;
    scales.set(currency, (v) => {
      const t = (v - (min - span * 0.1)) / (span * 1.2);
      return H - PAD.bottom - t * (H - PAD.top - PAD.bottom);
    });
  }

  const tickDays = days.filter((_, i) => i % Math.max(1, Math.ceil(days.length / 6)) === 0);
  const first = series[0];
  const firstScale = scales.get(first.offer.currency)!;
  const firstValues = first.points.map((p) => Number(p.price));
  const yTicks = [Math.min(...firstValues), Math.max(...firstValues)];

  return (
    <figure className="card p-4 sm:p-6">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Price history" className="w-full">
        {tickDays.map((day) => (
          <g key={day}>
            <line x1={x(day)} x2={x(day)} y1={PAD.top} y2={H - PAD.bottom} stroke="#16223a" />
            <text x={x(day)} y={H - 8} textAnchor="middle" fontSize="11" fill="#8494b5">
              {shortDate(day)}
            </text>
          </g>
        ))}
        {yTicks.map((value) => (
          <text
            key={value}
            x={PAD.left - 8}
            y={firstScale(value) + 4}
            textAnchor="end"
            fontSize="11"
            fill="#8494b5"
            fontFamily="var(--font-mono)"
          >
            {money(value, first.offer.currency)}
          </text>
        ))}
        {series.map((s) => {
          const scale = scales.get(s.offer.currency)!;
          const d = s.points
            .map((p, i) => `${i ? "L" : "M"}${x(p.day).toFixed(1)},${scale(Number(p.price)).toFixed(1)}`)
            .join(" ");
          const last = s.points.at(-1);
          return (
            <g key={s.offer.id}>
              <path d={d} fill="none" stroke={s.color} strokeWidth="2" strokeLinejoin="round" />
              {last && (
                <circle cx={x(last.day)} cy={scale(Number(last.price))} r="3.5" fill={s.color} />
              )}
            </g>
          );
        })}
      </svg>
      <figcaption className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm">
        {series.map((s) => (
          <span key={s.offer.id} className="inline-flex items-center gap-2">
            <span aria-hidden="true" className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
            {s.offer.sourceName}
            <span className="font-mono text-xs text-mute">{s.offer.currency}</span>
          </span>
        ))}
      </figcaption>
    </figure>
  );
}

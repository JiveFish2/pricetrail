import type { OfferSummary, PricePoint } from "@/lib/data";
import { money, shortDate } from "@/lib/format";

// Server-rendered SVG step charts, no client JavaScript. One panel per
// currency so the axes are honest: a BRL line and a USD line never share a scale.
// A price holds until the next observation, hence steps rather than slopes.

const COLORS = ["#0f7a53", "#1b1d1a", "#b7791a", "#b8432b", "#3b6ea5"];
const W = 720;
const H = 220;
const PAD = { top: 18, right: 20, bottom: 30, left: 88 };

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
      <p className="sheet p-6 text-sm text-ink-2">
        The chart appears after two days of data. Collected so far: {days.length} day
        {days.length === 1 ? "" : "s"}.
      </p>
    );
  }

  const currencies = [...new Set(series.map((s) => s.offer.currency))];
  return (
    <div className="grid gap-4">
      {currencies.map((currency) => (
        <Panel
          key={currency}
          currency={currency}
          days={days}
          series={series.filter((s) => s.offer.currency === currency && s.points.length)}
        />
      ))}
    </div>
  );
}

function Panel({ currency, days, series }: { currency: string; days: string[]; series: Series[] }) {
  const x = (day: string) => PAD.left + (days.indexOf(day) / (days.length - 1)) * (W - PAD.left - PAD.right);

  const values = series.flatMap((s) => s.points.map((p) => Number(p.price)));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || max * 0.1 || 1;
  const lo = min - span * 0.12;
  const hi = max + span * 0.12;
  const y = (v: number) => H - PAD.bottom - ((v - lo) / (hi - lo)) * (H - PAD.top - PAD.bottom);

  const xTicks = days.filter((_, i) => i % Math.max(1, Math.ceil(days.length / 6)) === 0);
  const yTicks = min === max ? [min] : [min, (min + max) / 2, max];

  return (
    <figure className="sheet p-4 sm:p-6">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Price history in ${currency}`} className="w-full">
        {yTicks.map((value) => (
          <g key={value}>
            <line x1={PAD.left} x2={W - PAD.right} y1={y(value)} y2={y(value)} stroke="#ddd6c4" strokeDasharray="2 4" />
            <text
              x={PAD.left - 10}
              y={y(value) + 4}
              textAnchor="end"
              fontSize="11"
              fill="#9a9f95"
              fontFamily="var(--font-mono)"
            >
              {money(value, currency)}
            </text>
          </g>
        ))}
        {xTicks.map((day) => (
          <text key={day} x={x(day)} y={H - 9} textAnchor="middle" fontSize="11" fill="#9a9f95">
            {shortDate(day)}
          </text>
        ))}
        {series.map((s) => {
          const d = s.points
            .map((p, i) => {
              const px = x(p.day).toFixed(1);
              const py = y(Number(p.price)).toFixed(1);
              return i === 0 ? `M${px},${py}` : `H${px} V${py}`;
            })
            .join(" ");
          const last = s.points.at(-1)!;
          return (
            <g key={s.offer.id}>
              <path d={d} fill="none" stroke={s.color} strokeWidth="2" strokeLinejoin="round" />
              <circle cx={x(last.day)} cy={y(Number(last.price))} r="3.5" fill={s.color} />
            </g>
          );
        })}
      </svg>
      <figcaption className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1 text-sm">
        <span className="font-mono text-xs text-ink-3">{currency}</span>
        {series.map((s) => (
          <span key={s.offer.id} className="inline-flex items-center gap-2">
            <span aria-hidden="true" className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
            {s.offer.sourceName}
          </span>
        ))}
      </figcaption>
    </figure>
  );
}

import { getStatus } from "@/lib/data";
import { Ago } from "@/components/Ago";

export const metadata = {
  title: "Status",
  description: "Health of every PriceTrail source: last run, success rate and how collection works.",
};

const STATUS_STYLE: Record<string, string> = {
  ok: "tag-drop",
  partial: "tag-amber",
  failed: "tag-rise",
  running: "tag-ink",
};

export default async function StatusPage() {
  const sources = await getStatus();

  return (
    <>
      <section className="mb-10 max-w-3xl">
        <p className="eyebrow">Status</p>
        <h1 className="mt-3 text-5xl">Every source, <em className="text-trail">every day.</em></h1>
        <p className="mt-4 text-lg text-ink-2">
          A collector that breaks quietly is worse than none. Each run is recorded per source so a
          store that changed its page shows up here before anyone notices stale prices.
        </p>
      </section>

      <div className="sheet overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left font-mono text-[11px] uppercase tracking-wider text-ink-3">
            <tr className="border-b border-rule">
              <th className="px-5 py-3 font-medium">Source</th>
              <th className="px-5 py-3 font-medium">Kind</th>
              <th className="px-5 py-3 font-medium">Last run</th>
              <th className="px-5 py-3 font-medium">Read</th>
              <th className="px-5 py-3 font-medium">7-day success</th>
              <th className="px-5 py-3 font-medium">Avg time</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.id} className="border-b border-dashed border-rule last:border-0">
                <td className="px-5 py-3">
                  <div className="font-medium">{s.name}</div>
                  {s.lastError && <div className="mt-0.5 text-xs text-amber">{s.lastError}</div>}
                </td>
                <td className="px-5 py-3 font-mono text-xs uppercase text-ink-3">{s.kind}</td>
                <td className="px-5 py-3">
                  {s.lastStatus ? (
                    <span className="inline-flex items-center gap-2">
                      <span className={`tag ${STATUS_STYLE[s.lastStatus] ?? "tag-ink"}`}>
                        {s.lastStatus}
                      </span>
                      <span className="text-ink-2"><Ago iso={s.lastRunAt} /></span>
                    </span>
                  ) : (
                    <span className="text-ink-3">not running yet</span>
                  )}
                </td>
                <td className="num px-5 py-3">
                  {s.lastStatus ? `${s.lastOffersOk}/${s.lastOffersTotal}` : `0/${s.offersTracked}`}
                </td>
                <td className="num px-5 py-3">
                  {s.runs7d ? `${s.okRate7d}% of ${s.runs7d}` : "—"}
                </td>
                <td className="num px-5 py-3">{s.avgSeconds7d ? `${s.avgSeconds7d}s` : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <section className="mt-12 grid gap-6 md:grid-cols-2" aria-labelledby="how">
        <div>
          <h2 id="how" className="display mb-3 text-2xl">How collection works</h2>
          <ul className="space-y-2 text-sm text-ink-2">
            <li>One run a day, from a scheduled GitHub Actions job; no server stays up.</li>
            <li>Every request carries an identified user agent and waits a second before the next one.</li>
            <li>Sources are read the way they publish data: official API, structured data on product pages, or a product feed.</li>
            <li>A product missing from a page or feed is skipped, never recorded with a guessed price.</li>
          </ul>
        </div>
        <div>
          <h2 className="display mb-3 text-2xl">What is collected</h2>
          <ul className="space-y-2 text-sm text-ink-2">
            <li>Public product data only: name, price, list price, availability.</li>
            <li>No personal data from any store. Alert emails are confirmed by link and removed by link.</li>
            <li>robots.txt and terms are checked before a source is added.</li>
            <li>The collector and this site are one open repository on GitHub.</li>
          </ul>
        </div>
      </section>
    </>
  );
}

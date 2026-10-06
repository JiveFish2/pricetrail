"use client";

import { useActionState } from "react";
import { createAlert, type AlertState } from "@/app/p/[slug]/actions";
import type { OfferSummary } from "@/lib/data";

export function AlertForm({ offers }: { offers: OfferSummary[] }) {
  const [state, action, pending] = useActionState<AlertState, FormData>(createAlert, {
    status: "idle",
  });
  const candidates = offers.filter((o) => o.price !== null);
  if (candidates.length === 0) return null;

  return (
    <form action={action} className="sheet p-5 sm:p-6">
      <h2 className="display text-2xl">Email me when it drops</h2>
      <p className="mt-1 text-sm text-ink-2">
        No account. You confirm by link and every email has an unsubscribe link.
      </p>
      <div className="mt-5 grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
        <label className="grid gap-1.5 text-sm">
          <span>Store</span>
          <select name="offer" className="field" defaultValue={candidates[0].id}>
            {candidates.map((offer) => (
              <option key={offer.id} value={offer.id}>
                {offer.sourceName} ({offer.currency})
              </option>
            ))}
          </select>
        </label>
        <label className="grid gap-1.5 text-sm">
          <span>Target price</span>
          <input
            name="target"
            type="number"
            inputMode="decimal"
            min="0.01"
            step="0.01"
            required
            placeholder={candidates[0].price ?? ""}
            className="field num"
          />
        </label>
        <label className="grid gap-1.5 text-sm sm:col-span-2">
          <span>Email</span>
          <input name="email" type="email" required autoComplete="email" className="field" />
        </label>
        <div className="hidden" aria-hidden="true">
          <label>
            Website <input name="website" type="text" tabIndex={-1} autoComplete="off" />
          </label>
        </div>
        <button type="submit" disabled={pending} className="btn sm:col-start-3 sm:row-start-2">
          {pending ? "Sending…" : "Create alert"}
        </button>
      </div>
      <p
        role="status"
        aria-live="polite"
        className={`mt-4 min-h-5 text-sm ${
          state.status === "ok" ? "text-trail" : state.status === "idle" ? "" : "text-rise"
        }`}
      >
        {state.message}
      </p>
    </form>
  );
}

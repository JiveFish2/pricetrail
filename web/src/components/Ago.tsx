"use client";

import { useSyncExternalStore } from "react";

// "today", "yesterday", "3 days ago" depends on the viewer's clock, so the
// server shell shows the absolute date and the client swaps in the relative one.
export function Ago({ iso }: { iso: string | null }) {
  const label = useSyncExternalStore(
    subscribe,
    () => (iso ? relative(iso) : "never"),
    () => (iso ? absolute(iso) : "never"),
  );
  return <>{label}</>;
}

function subscribe() {
  return () => {};
}

function relative(iso: string): string {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  return days <= 0 ? "today" : days === 1 ? "yesterday" : `${days} days ago`;
}

function absolute(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
}

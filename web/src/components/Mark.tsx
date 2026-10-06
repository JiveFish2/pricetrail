// The PriceTrail mark: a price trail stepping down to a final dot.
export function Mark({ size = 22 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      className="shrink-0"
    >
      <rect x="1" y="1" width="22" height="22" rx="6" fill="var(--color-ink)" />
      <path
        d="M5 7.5h4.5v4H14v4h4"
        stroke="var(--color-sheet)"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="18.5" cy="15.5" r="2" fill="var(--color-trail)" stroke="var(--color-sheet)" strokeWidth="1" />
    </svg>
  );
}

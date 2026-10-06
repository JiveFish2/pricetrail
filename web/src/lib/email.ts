// Transactional email through Resend's HTTP API. Without RESEND_API_KEY the
// message is logged instead of sent, so local development needs no account.

export async function sendEmail(input: { to: string; subject: string; text: string }) {
  const key = process.env.RESEND_API_KEY;
  const from = process.env.ALERT_FROM ?? "PriceTrail <alerts@example.com>";
  if (!key) {
    console.info(`[email not sent: RESEND_API_KEY unset] to=${input.to} subject=${input.subject}\n${input.text}`);
    return;
  }
  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from, to: [input.to], subject: input.subject, text: input.text }),
  });
  if (!response.ok) {
    throw new Error(`Resend answered ${response.status}: ${await response.text()}`);
  }
}

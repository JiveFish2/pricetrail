// Transactional email through Resend's HTTP API. Without RESEND_API_KEY the
// message is logged instead of sent, so local development needs no account.

export async function sendEmail(input: { to: string; subject: string; text: string; html?: string }) {
  const key = process.env.RESEND_API_KEY;
  const from = process.env.ALERT_FROM ?? "PriceTrail <alerts@example.com>";
  if (!key) {
    console.info(`[email not sent: RESEND_API_KEY unset] to=${input.to} subject=${input.subject}\n${input.text}`);
    return;
  }
  const response = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ from, to: [input.to], subject: input.subject, text: input.text, html: input.html }),
  });
  if (!response.ok) {
    throw new Error(`Resend answered ${response.status}: ${await response.text()}`);
  }
}

// The HTML version follows the site and the price-drop email the collector
// sends (src/pricetrail/notify.py): warm paper, dark ink, a serif headline,
// mono for numbers. Tables and inline styles only, which every mail client
// renders the same way.
const SERIF = "Georgia, 'Times New Roman', serif";
const SANS = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif";
const MONO = "ui-monospace, Menlo, Consolas, monospace";

const ENTITIES: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
const escape = (value: string) => value.replace(/[&<>"']/g, (ch) => ENTITIES[ch]);

export function confirmationHtml(input: {
  product: string;
  source: string;
  target: string;
  imageUrl: string | null;
  confirmUrl: string;
  siteUrl: string;
}): string {
  const product = escape(input.product);
  const image = input.imageUrl
    ? `<tr><td style="padding:0 0 20px"><img src="${escape(input.imageUrl)}" alt="${product}" width="512" style="display:block;width:100%;max-width:512px;height:auto;border:1px solid #ddd6c4;border-radius:6px;background:#ffffff"></td></tr>`
    : "";
  const body = `
<tr><td style="padding:0 0 6px;font:600 11px/1.4 ${MONO};letter-spacing:.12em;text-transform:uppercase;color:#b7791a">One step left</td></tr>
<tr><td style="padding:0 0 20px;font:400 30px/1.15 ${SERIF};color:#1b1d1a">Confirm your price alert</td></tr>
${image}
<tr><td style="padding:0 0 22px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;border-top:1px solid #ddd6c4;border-bottom:1px solid #ddd6c4">
<tr>
<td style="padding:14px 0;font:400 12px/1.4 ${SANS};color:#5f655d">${escape(input.source)}<br>
<span style="font:500 16px/1.4 ${SANS};color:#1b1d1a">${product}</span></td>
<td align="right" style="padding:14px 0;font:400 12px/1.4 ${SANS};color:#5f655d">Email me at or below<br>
<span style="font:600 22px/1.3 ${MONO};color:#0f7a53">${escape(input.target)}</span></td>
</tr></table></td></tr>
<tr><td style="padding:0 0 22px"><a href="${escape(input.confirmUrl)}" style="display:inline-block;padding:12px 22px;border-radius:999px;background:#1b1d1a;color:#fffdf7;font:600 14px/1 ${SANS};text-decoration:none">Confirm alert</a></td></tr>
<tr><td style="font:400 13px/1.6 ${SANS};color:#5f655d">Prices are checked once a day. You get one email when the price reaches your target, then the alert stops.</td></tr>`;
  const footer = "If you did not ask for this, ignore this message and nothing will be sent.";
  return layout(`Confirm your alert for ${product}`, body, footer, input.siteUrl);
}

function layout(preheader: string, body: string, footer: string, siteUrl: string): string {
  const home = escape(siteUrl);
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light"></head>
<body style="margin:0;padding:0;background:#f4f0e6">
<div style="display:none;max-height:0;overflow:hidden">${preheader}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f0e6">
<tr><td align="center" style="padding:32px 16px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px">
<tr><td style="padding:0 4px 16px;font:700 17px/1 ${SANS};letter-spacing:-.01em;color:#1b1d1a">
<a href="${home}" style="color:#1b1d1a;text-decoration:none">Price<span style="color:#0f7a53">Trail</span></a></td></tr>
<tr><td style="background:#fffdf7;border:1px solid #ddd6c4;border-radius:10px;padding:28px 24px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">${body}</table>
</td></tr>
<tr><td style="padding:18px 4px 0;font:400 12px/1.6 ${SANS};color:#9a9f95">${footer}<br>
Public product data, collected once a day.
<a href="${home}/status" style="color:#9a9f95">How collection works</a></td></tr>
</table></td></tr></table></body></html>`;
}

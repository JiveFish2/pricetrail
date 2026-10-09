"use server";

import { randomBytes } from "node:crypto";
import { sql } from "@/lib/db";
import { confirmationHtml, sendEmail } from "@/lib/email";
import { money } from "@/lib/format";

export type AlertState = { status: "idle" | "ok" | "invalid" | "error"; message?: string };

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_ALERTS_PER_EMAIL = 20;

export async function createAlert(_prev: AlertState, formData: FormData): Promise<AlertState> {
  // Bots fill every field; people never see this one.
  if (formData.get("website")) return { status: "ok" };

  const email = String(formData.get("email") ?? "").trim().toLowerCase();
  const offerId = Number(formData.get("offer"));
  const target = Number(String(formData.get("target") ?? "").replace(",", "."));
  if (!EMAIL.test(email) || !Number.isInteger(offerId) || !(target > 0)) {
    return { status: "invalid", message: "Check the email address and the target price." };
  }

  try {
    const [offer] = await sql<
      {
        id: number;
        url: string;
        currency: string;
        source: string;
        product: string;
        slug: string;
        image_url: string | null;
      }[]
    >`
      select o.id, o.url, s.currency, s.name as source, p.name as product, p.slug, p.image_url
      from offers o join sources s on s.id = o.source_id join products p on p.id = o.product_id
      where o.id = ${offerId}
    `;
    if (!offer) return { status: "invalid", message: "That offer does not exist." };

    const [{ count }] = await sql<{ count: string }[]>`
      select count(*) from alerts where email = ${email} and notified_at is null
    `;
    if (Number(count) >= MAX_ALERTS_PER_EMAIL) {
      return { status: "invalid", message: `You already have ${MAX_ALERTS_PER_EMAIL} active alerts.` };
    }

    const confirmToken = randomBytes(24).toString("base64url");
    const unsubscribeToken = randomBytes(24).toString("base64url");
    // A repeated request for the same offer updates the target and re-sends the link.
    const [alert] = await sql<{ confirm_token: string; confirmed_at: Date | null }[]>`
      insert into alerts (offer_id, email, target_price, confirm_token, unsubscribe_token)
      values (${offerId}, ${email}, ${target.toFixed(2)}, ${confirmToken}, ${unsubscribeToken})
      on conflict (offer_id, email) do update
        set target_price = excluded.target_price, notified_at = null
      returning confirm_token, confirmed_at
    `;

    const base = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3001";
    if (!alert.confirmed_at) {
      const confirmUrl = `${base}/alerts/confirm/${alert.confirm_token}`;
      await sendEmail({
        to: email,
        subject: `Confirm your PriceTrail alert for ${offer.product}`,
        text: [
          `You asked to be told when ${offer.product} at ${offer.source} goes at or below ${money(target, offer.currency)}.`,
          "",
          `Confirm this alert: ${confirmUrl}`,
          "",
          "If you did not request this, ignore this message and nothing will be sent.",
        ].join("\n"),
        html: confirmationHtml({
          product: offer.product,
          source: offer.source,
          target: money(target, offer.currency),
          imageUrl: offer.image_url,
          confirmUrl,
          siteUrl: base,
        }),
      });
      return { status: "ok", message: "Check your inbox for a confirmation link." };
    }
    return { status: "ok", message: `Alert updated: we will email you at or below ${money(target, offer.currency)}.` };
  } catch (error) {
    console.error("createAlert failed", error);
    return { status: "error", message: "Something went wrong on our side. Try again in a minute." };
  }
}

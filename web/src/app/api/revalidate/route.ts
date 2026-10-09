import { revalidateTag } from "next/cache";

// Called by the collector after each run. The tag expires at once, so the first
// visit after a run already gets the new prices instead of the stale ones.
export async function POST(request: Request) {
  const secret = process.env.REVALIDATE_SECRET;
  const given = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "");
  if (!secret || given !== secret) {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }
  revalidateTag("prices", { expire: 0 });
  return Response.json({ revalidated: true, at: new Date().toISOString() });
}

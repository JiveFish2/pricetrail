import { revalidateTag } from "next/cache";

// Called by the collector after each run so cached pages pick up new prices.
export async function POST(request: Request) {
  const secret = process.env.REVALIDATE_SECRET;
  const given = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "");
  if (!secret || given !== secret) {
    return Response.json({ error: "unauthorized" }, { status: 401 });
  }
  revalidateTag("prices", "max");
  return Response.json({ revalidated: true, at: new Date().toISOString() });
}

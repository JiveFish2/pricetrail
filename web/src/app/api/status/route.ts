import { getStatus } from "@/lib/data";

export async function GET() {
  const sources = await getStatus();
  return Response.json(
    { sources },
    { headers: { "Cache-Control": "public, max-age=60, s-maxage=600" } },
  );
}

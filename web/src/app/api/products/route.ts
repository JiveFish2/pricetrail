import { listProducts } from "@/lib/data";

export async function GET() {
  const products = await listProducts();
  return Response.json(
    { products },
    { headers: { "Cache-Control": "public, max-age=300, s-maxage=3600" } },
  );
}

import { listProducts } from "@/lib/data";

export async function GET() {
  const products = await listProducts();
  return Response.json(
    { products },
    { headers: { "Cache-Control": "public, max-age=60, s-maxage=300" } },
  );
}

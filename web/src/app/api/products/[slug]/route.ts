import { getProduct } from "@/lib/data";

export async function GET(_request: Request, { params }: RouteContext<"/api/products/[slug]">) {
  const { slug } = await params;
  const product = await getProduct(slug);
  if (!product) return Response.json({ error: "not_found" }, { status: 404 });
  return Response.json(product, {
    headers: { "Cache-Control": "public, max-age=60, s-maxage=300" },
  });
}

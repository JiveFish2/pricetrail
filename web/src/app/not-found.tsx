import Link from "next/link";

export default function NotFound() {
  return (
    <section className="mx-auto max-w-xl py-16 text-center">
      <p className="eyebrow">404</p>
      <h1 className="mt-3 text-4xl">Nothing tracked at this address.</h1>
      <Link href="/" className="btn mt-8">Back to products</Link>
    </section>
  );
}

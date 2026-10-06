import Image from "next/image";

// Store images differ in shape: Steam headers are wide banners, merch and
// hardware shots are near-square product photos on white. Games fill the frame;
// everything else sits inside it on the sheet colour.
export function ProductImage({
  src,
  alt,
  category,
  priority = false,
  sizes = "(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw",
}: {
  src: string | null;
  alt: string;
  category: string;
  priority?: boolean;
  sizes?: string;
}) {
  const cover = category === "Games";
  return (
    <div
      className={`relative aspect-[16/9] w-full overflow-hidden rounded-md border border-rule ${
        cover ? "bg-ink" : "bg-white"
      }`}
    >
      {src ? (
        <Image
          src={src}
          alt={alt}
          fill
          sizes={sizes}
          priority={priority}
          className={cover ? "object-cover" : "object-contain p-4"}
        />
      ) : (
        <div className="absolute inset-0 grid place-items-center font-mono text-xs text-ink-3">
          no image yet
        </div>
      )}
    </div>
  );
}

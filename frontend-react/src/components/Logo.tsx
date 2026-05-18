interface LogoProps {
  /** Rendered pixel size on a 1× display. Picks the best @2x PNG automatically. */
  size?: number;
  className?: string;
  alt?: string;
}

const SIZES = [16, 32, 48, 64, 96, 180, 192, 512] as const;

function pickSrc(displayPx: number): string {
  const target = displayPx * 2;
  const best = SIZES.find((s) => s >= target) ?? SIZES[SIZES.length - 1];
  return `/mm-logo-${best}.png`;
}

export function Logo({ size = 32, className, alt = "MarathiMitra" }: LogoProps) {
  return (
    <img
      src={pickSrc(size)}
      alt={alt}
      width={size}
      height={size}
      className={className}
      draggable={false}
    />
  );
}

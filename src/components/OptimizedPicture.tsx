"use client";

import React from "react";

interface OptimizedPictureProps {
  src: string;
  alt: string;
  className?: string;
  priority?: boolean;
  draggable?: boolean;
}

export function toWebpSrc(src: string): string | null {
  if (!src || src.startsWith("data:") || src.includes(".svg") || src.includes(".webp")) {
    return null;
  }
  // Reemplaza .png por .webp preservando parámetros de consulta (e.g. ?v=2.0)
  return src.replace(/\.png(\?.*)?$/i, (_, query) => `.webp${query || ""}`);
}

export function OptimizedPicture({
  src,
  alt,
  className = "",
  priority = false,
  draggable = true,
}: OptimizedPictureProps) {
  const webp = toWebpSrc(src);

  return (
    <picture className="contents">
      {webp && <source srcSet={webp} type="image/webp" />}
      <img
        src={src}
        alt={alt}
        loading={priority ? "eager" : "lazy"}
        decoding="async"
        fetchPriority={priority ? "high" : "low"}
        draggable={draggable}
        className={className}
      />
    </picture>
  );
}

"use client";

import React, { useEffect, useRef } from "react";
import { Download, X } from "lucide-react";
import { toWebpSrc } from "./OptimizedPicture";

export interface LightboxAsset {
  src: string;
  title: string;
  caption?: string;
}

interface ImageLightboxDialogProps {
  asset: LightboxAsset | null;
  onClose: () => void;
}

export function ImageLightboxDialog({ asset, onClose }: ImageLightboxDialogProps) {
  const dialogRef = useRef<HTMLDialogElement | null>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (asset && !dialog.open) {
      dialog.showModal();
    } else if (!asset && dialog.open) {
      dialog.close();
    }
  }, [asset]);

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      onClick={(e) => {
        if (e.target === dialogRef.current) onClose();
      }}
      className="m-auto w-[min(94vw,1120px)] rounded-2xl border border-(--hairline) bg-(--surface-elevated) p-0 text-(--ink) shadow-2xl backdrop:backdrop-blur-md"
    >
      {asset && (
        <div className="flex flex-col">
          <div className="flex items-center justify-between gap-4 border-b border-(--hairline) px-5 py-3.5">
            <div className="min-w-0">
              <h3 className="truncate font-display text-base font-semibold text-(--ink)">
                {asset.title}
              </h3>
              {asset.caption && (
                <p className="mt-0.5 truncate font-mono text-xs text-(--ink-muted)">
                  {asset.caption}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <a
                href={asset.src}
                download
                className="inline-flex items-center gap-1.5 rounded-lg border border-(--hairline) bg-(--surface) px-3 py-1.5 font-mono text-xs font-medium text-(--ink) transition hover:border-sky-500/60 active:scale-[0.98]"
              >
                <Download className="h-3.5 w-3.5" /> Descargar
              </a>
              <button
                type="button"
                onClick={onClose}
                aria-label="Cerrar modal"
                className="rounded-lg border border-(--hairline) bg-(--surface) p-1.5 text-(--ink-muted) transition hover:text-(--ink) active:scale-[0.98]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="flex max-h-[80vh] items-center justify-center overflow-auto bg-black/5 p-4 dark:bg-zinc-950/70 sm:p-6">
            <picture className="flex justify-center">
              {toWebpSrc(asset.src) && (
                <source srcSet={toWebpSrc(asset.src) as string} type="image/webp" />
              )}
              <img
                src={asset.src}
                alt={asset.title}
                decoding="async"
                className="max-h-[72vh] w-auto rounded-lg border border-white/10 object-contain shadow-xl"
              />
            </picture>
          </div>
        </div>
      )}
    </dialog>
  );
}

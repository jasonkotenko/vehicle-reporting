import { useState } from "react";
import type { ImageRef } from "@/api/types";

interface ImageGalleryProps {
  imageRefs: ImageRef[];
}

export function ImageGallery({ imageRefs }: ImageGalleryProps) {
  const [lightbox, setLightbox] = useState<string | null>(null);

  if (imageRefs.length === 0) {
    return <p className="text-sm text-slate-500">No images available.</p>;
  }

  return (
    <>
      <div className="flex gap-3 overflow-x-auto pb-2">
        {imageRefs.map((ref, index) => {
          const src = ref.signed_url;
          const failed = ref.status === "fetch_failed";
          const pending = ref.status === "pending";

          return (
            <button
              key={`${ref.source_url ?? index}-${index}`}
              type="button"
              onClick={() => src && setLightbox(src)}
              className="h-28 w-40 shrink-0 overflow-hidden rounded-lg border border-slate-200 bg-slate-100"
            >
              {src ? (
                <img src={src} alt={`Frame ${index + 1}`} className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center p-2 text-center text-xs text-slate-500">
                  {failed ? "Fetch failed" : pending ? "Pending…" : "No preview"}
                </div>
              )}
            </button>
          );
        })}
      </div>
      {lightbox && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
          onClick={() => setLightbox(null)}
        >
          <img
            src={lightbox}
            alt="Enlarged frame"
            className="max-h-full max-w-full rounded-lg"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </>
  );
}

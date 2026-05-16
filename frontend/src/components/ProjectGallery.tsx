"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ImageIcon, X, ChevronLeft, ChevronRight } from "lucide-react";
import type { ProjectImage } from "@/types";

interface ProjectGalleryProps {
  images: ProjectImage[];
  projectName: string;
}

export default function ProjectGallery({ images, projectName }: ProjectGalleryProps) {
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);

  if (!images || images.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        <ImageIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">暂无项目图片</p>
      </div>
    );
  }

  const handlePrev = () => {
    setSelectedIdx((prev) => (prev === 0 ? images.length - 1 : prev! - 1));
  };

  const handleNext = () => {
    setSelectedIdx((prev) => (prev === images.length - 1 ? 0 : prev! + 1));
  };

  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {images.slice(0, 8).map((img, idx) => (
          <Dialog key={img.id}>
            <DialogTrigger
              onClick={() => setSelectedIdx(idx)}
              render={
                <button className="group relative aspect-video rounded-lg overflow-hidden border bg-muted hover:ring-2 hover:ring-primary/50 transition-all cursor-pointer">
                  <img
                    src={img.url}
                    alt={img.alt_text || `${projectName} 图片`}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    loading="lazy"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = "none";
                      (e.target as HTMLImageElement).parentElement!.classList.add("flex", "items-center", "justify-center");
                      (e.target as HTMLImageElement).parentElement!.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-image-off h-6 w-6 text-muted-foreground"><line x1="2" x2="22" y1="2" y2="22"/><path d="M10.41 10.41a2 2 0 1 1 2.83 2.83"/><path d="M13.5 13.5 12 15l-3-3-4 4"/><path d="M5 5h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2"/></svg>';
                    }}
                  />
                  {idx === 7 && images.length > 8 && (
                    <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                      <span className="text-white text-lg font-bold">+{images.length - 8}</span>
                    </div>
                  )}
                </button>
              }
            />
            <DialogContent className="max-w-4xl p-0 bg-black/90 border-0">
              <div className="relative flex items-center justify-center min-h-[50vh]">
                {images.length > 1 && (
                  <>
                    <button
                      onClick={handlePrev}
                      className="absolute left-2 z-10 p-2 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
                    >
                      <ChevronLeft className="h-6 w-6" />
                    </button>
                    <button
                      onClick={handleNext}
                      className="absolute right-2 z-10 p-2 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors"
                    >
                      <ChevronRight className="h-6 w-6" />
                    </button>
                  </>
                )}
                {selectedIdx !== null && (
                  <img
                    src={images[selectedIdx].url}
                    alt={images[selectedIdx].alt_text || `${projectName} 图片 ${selectedIdx + 1}`}
                    className="max-w-full max-h-[80vh] object-contain"
                  />
                )}
              </div>
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white/70 text-xs">
                {selectedIdx !== null && `${selectedIdx + 1} / ${images.length}`}
              </div>
            </DialogContent>
          </Dialog>
        ))}
      </div>
    </div>
  );
}

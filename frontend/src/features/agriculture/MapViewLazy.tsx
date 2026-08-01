import { lazy, Suspense } from "react";
import type { GeoJsonGeometry, NdviHeatmapResponse } from "./types/api";

const MapViewInner = lazy(() =>
  import("./components/MapView").then((m) => ({ default: m.MapView })),
);

interface MapViewLazyProps {
  parcelGeometry: GeoJsonGeometry | null;
  neighborGeometries: GeoJsonGeometry[];
  ndviOverlay: NdviHeatmapResponse | null;
  onSelectPoint: (lat: number, lon: number) => void;
}

export function MapViewLazy(props: MapViewLazyProps) {
  return (
    <Suspense
      fallback={
        <div className="h-full w-full flex items-center justify-center bg-gradient-sky text-sky-foreground text-sm font-medium">
          Chargement de la carte…
        </div>
      }
    >
      <MapViewInner {...props} />
    </Suspense>
  );
}

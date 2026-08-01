import { createFileRoute } from "@tanstack/react-router";
import { MapIcon, Sprout } from "lucide-react";
import { useCallback, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { ApiError, getNdviHeatmap } from "@/features/agriculture/api/client";
import { AgricultureDashboard } from "@/features/agriculture/components/Agriculture/AgricultureDashboard";
import { Chatbot } from "@/features/agriculture/components/Chatbot/Chatbot";
import { MapViewLazy } from "@/features/agriculture/MapViewLazy";
import { ReportModal } from "@/features/agriculture/components/Report/ReportModal";
import { useAdvise } from "@/features/agriculture/hooks/useAdvise";
import { useParcelSelection } from "@/features/agriculture/hooks/useParcelSelection";
import type { NdviHeatmapResponse } from "@/features/agriculture/types/api";
import "@/features/agriculture/agri-embed.css";

export const Route = createFileRoute("/agriculture")({
  head: () => ({
    meta: [{ title: "Cultures — AgriGuide" }],
  }),
  component: Page,
});

type Tab = "carte" | "conseiller";

function Page() {
  const [tab, setTab] = useState<Tab>("carte");
  const { point, parcel, neighbors, status, message, selectPoint } = useParcelSelection();
  const { report, loading: adviseLoading, error: adviseError, runAdvise, reset: resetAdvise } = useAdvise();
  const [ndviOverlay, setNdviOverlay] = useState<NdviHeatmapResponse | null>(null);
  const [ndviLoading, setNdviLoading] = useState(false);
  const [ndviError, setNdviError] = useState<string | null>(null);

  const handleSelectPoint = useCallback(
    (lat: number, lon: number) => {
      setNdviOverlay(null);
      setNdviError(null);
      resetAdvise();
      selectPoint(lat, lon);
    },
    [selectPoint, resetAdvise],
  );

  const handleToggleNdvi = useCallback(async () => {
    if (ndviOverlay) {
      setNdviOverlay(null);
      return;
    }
    if (!point) return;
    setNdviLoading(true);
    setNdviError(null);
    try {
      const overlay = await getNdviHeatmap(point);
      setNdviOverlay(overlay);
    } catch (err) {
      setNdviError(err instanceof ApiError ? err.message : "Impossible de charger le NDVI.");
    } finally {
      setNdviLoading(false);
    }
  }, [point, ndviOverlay]);

  const handleAdvise = useCallback(() => {
    if (!point) return;
    runAdvise(point);
  }, [point, runAdvise]);

  return (
    <AppShell>
      <div className="agri-embed">
        <div className="flex items-center gap-3 mb-2">
          <div className="h-11 w-11 rounded-2xl bg-harvest/15 text-harvest flex items-center justify-center">
            <Sprout className="h-6 w-6" />
          </div>
          <div>
            <h1 className="font-display text-3xl md:text-4xl font-semibold leading-none">Cultures</h1>
            <p className="text-muted-foreground mt-1">
              {parcel?.parcel_id ? `Parcelle ${parcel.parcel_id}` : "Sélectionnez une parcelle sur la carte"}
            </p>
          </div>
        </div>

        <div className="agri-tabs mt-6">
          <button className={`agri-tab${tab === "carte" ? " active" : ""}`} onClick={() => setTab("carte")}>
            <MapIcon className="h-4 w-4" /> Carte
          </button>
          <button className={`agri-tab${tab === "conseiller" ? " active" : ""}`} onClick={() => setTab("conseiller")}>
            <Sprout className="h-4 w-4" /> Conseiller
          </button>
        </div>

        {tab === "carte" && (
          <div className="grid gap-5 md:grid-cols-[1fr_320px]">
            <div className="agri-map-frame">
              <MapViewLazy
                parcelGeometry={parcel?.geometry ?? null}
                neighborGeometries={neighbors?.neighbors.map((n) => n.geometry) ?? []}
                ndviOverlay={ndviOverlay}
                onSelectPoint={handleSelectPoint}
              />
            </div>

            <div className="card-soft p-5 flex flex-col gap-4 h-fit">
              <div className="flex items-center gap-2 text-sm">
                <span
                  className={`h-2 w-2 rounded-full ${
                    status === "ready" ? "bg-primary" : status === "error" ? "bg-destructive" : status === "loading" ? "bg-harvest" : "bg-muted-foreground"
                  }`}
                />
                <span className="text-muted-foreground">{message ?? "Cliquez sur une parcelle pour commencer."}</span>
              </div>

              {ndviError && <p className="text-xs text-destructive">{ndviError}</p>}

              {parcel && (
                <div className="flex flex-col gap-2">
                  <button
                    className="rounded-xl border border-border px-4 py-2.5 text-sm font-medium hover:bg-secondary transition-colors disabled:opacity-50"
                    onClick={handleToggleNdvi}
                    disabled={ndviLoading}
                  >
                    {ndviLoading ? "🛰️ Chargement…" : ndviOverlay ? "🛰️ Masquer NDVI" : "🛰️ Afficher NDVI"}
                  </button>
                  <button
                    className="rounded-xl bg-primary text-primary-foreground px-4 py-2.5 text-sm font-semibold hover:opacity-90 transition-opacity disabled:opacity-50"
                    onClick={handleAdvise}
                    disabled={adviseLoading}
                  >
                    {adviseLoading ? "🔍 Analyse…" : "🔍 Obtenir les recommandations"}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {tab === "conseiller" && (
          <AgricultureDashboard
            parcel={parcel}
            report={report}
            loading={adviseLoading}
            error={adviseError}
            ndviOverlay={ndviOverlay}
            ndviLoading={ndviLoading}
            onRequestNdvi={handleToggleNdvi}
            onAdvise={handleAdvise}
            onGoToMap={() => setTab("carte")}
          />
        )}

        <ReportModal report={report} loading={adviseLoading} error={adviseError} onClose={resetAdvise} />

        <Chatbot
          parcel={parcel}
          neighbors={neighbors}
          reportMarkdown={report?.report_markdown ?? null}
          ndviAvailable={ndviOverlay !== null}
        />
      </div>
    </AppShell>
  );
}
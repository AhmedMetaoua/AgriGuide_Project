/**
 * Client de l'orchestrateur (backend/orchestrator, port 8000).
 *
 * Seule route utilisée pour l'instant : POST /orchestrator/journey/monitoring,
 * qui relaie « décision Business confirmée → briefing Monitoring » côté serveur
 * (traduction allocations → crops[] et sensibilité hydrique incluses).
 *
 * URL : `VITE_ORCHESTRATOR_URL` (défaut http://localhost:8000).
 */

import { SKIP_AUTH } from "@/lib/auth-context";
import {
  analyzeMonitoringDay,
  type AnalyzeRequest,
  type AnalyzeResponse,
} from "@/lib/monitoringApi";

const ORCHESTRATOR_BASE_URL: string =
  (import.meta.env.VITE_ORCHESTRATOR_URL as string | undefined) ?? "http://localhost:8000";

export class OrchestratorApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "OrchestratorApiError";
  }
}

type JourneyMonitoringResponse = {
  decision: Record<string, unknown>;
  briefing: AnalyzeResponse;
};

async function fetchJourneyMonitoring(
  request: AnalyzeRequest,
  token: string,
): Promise<AnalyzeResponse> {
  if (!request.terrain_id) {
    throw new OrchestratorApiError("terrain_id requis pour le relais orchestrateur.");
  }

  let response: Response;
  try {
    response = await fetch(`${ORCHESTRATOR_BASE_URL}/orchestrator/journey/monitoring`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        terrain_id: request.terrain_id,
        farmer_name: request.farmer_name,
        location: request.location,
        hardware_inventory: request.hardware_inventory ?? [],
      }),
    });
  } catch {
    throw new OrchestratorApiError(`Orchestrateur injoignable (${ORCHESTRATOR_BASE_URL}).`);
  }

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new OrchestratorApiError(
      detail && typeof detail === "object" && "detail" in detail
        ? String((detail as { detail: unknown }).detail)
        : `Erreur ${response.status} de l'orchestrateur`,
      response.status,
    );
  }

  const data = (await response.json()) as JourneyMonitoringResponse;
  return data.briefing;
}

/**
 * Briefing du jour. Chemin normal : orchestrateur (JWT réel requis).
 *
 * Repli direct vers Monitoring — avec `request.crops` construit côté client,
 * sensibilité hydrique comprise — quand l'orchestrateur ne peut pas servir la
 * requête : mode dev sans auth (`VITE_SKIP_AUTH`, pas de vrai JWT), service
 * injoignable, 401 (session expirée), ou décision connue seulement en local
 * (404 côté serveur). Si le repli échoue aussi, son erreur est celle remontée.
 */
export async function loadDailyBriefing(
  request: AnalyzeRequest,
  token: string | null,
): Promise<AnalyzeResponse> {
  if (token && !SKIP_AUTH) {
    try {
      return await fetchJourneyMonitoring(request, token);
    } catch (err) {
      if (import.meta.env.DEV) {
        console.warn("[aujourd-hui] orchestrateur indisponible, repli direct Monitoring :", err);
      }
    }
  }
  return analyzeMonitoringDay(request);
}

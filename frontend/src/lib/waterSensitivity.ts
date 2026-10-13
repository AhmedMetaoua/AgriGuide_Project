/**
 * Sensibilité hydrique d'une culture (low | moderate | high), dérivée du besoin
 * d'irrigation calculé par l'agent Agriculture (`besoins_irrigation`).
 *
 * Miroir de backend/orchestrator/app/water_sensitivity.py — GARDER LES MÊMES
 * SEUILS. Le chemin normal passe par l'orchestrateur (qui relit le profil
 * persisté côté serveur) ; ce helper sert au chemin de repli direct vers
 * Monitoring (mode dev sans auth, orchestrateur injoignable).
 *
 * Remplace l'ancien `mapWaterSensitivity`, qui lisait `besoins_irrigation.niveau`
 * — un champ qu'Agriculture n'a jamais renvoyé, donc toujours `undefined`.
 *
 * Seuils de départ (décision produit, pas une norme agronomique) : besoin net
 * ramené en mm/jour sur la fenêtre de prévision (~16 jours).
 */

export type WaterSensitivity = "low" | "moderate" | "high";

export const WATER_LOW_MAX_MM_PER_DAY = 1.0;
export const WATER_HIGH_MIN_MM_PER_DAY = 2.5;

export function waterSensitivityFromIrrigation(
  besoinsIrrigation: Record<string, unknown> | null | undefined,
): WaterSensitivity | undefined {
  if (!besoinsIrrigation || typeof besoinsIrrigation !== "object") return undefined;
  const need = besoinsIrrigation["irrigation_need_mm"];
  const window = besoinsIrrigation["irrigation_window_days"];
  if (typeof need !== "number" || !Number.isFinite(need)) return undefined;
  if (typeof window !== "number" || !Number.isFinite(window) || window <= 0) return undefined;

  const perDay = need / window;
  if (perDay < WATER_LOW_MAX_MM_PER_DAY) return "low";
  if (perDay < WATER_HIGH_MIN_MM_PER_DAY) return "moderate";
  return "high";
}

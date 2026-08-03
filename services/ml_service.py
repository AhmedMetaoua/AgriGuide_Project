"""
Section 6's tabular half (kept — only the CNN/image part of Section 6
is deferred). Crop suitability scoring from soil + weather features.

No real labeled training set exists yet, so this ships as a documented
rule-based scorer with the exact same output shape a trained
RandomForestClassifier would produce — swap `_score_rule_based` for a
loaded `.predict_proba()` call once you have RPG-labeled training data,
with zero changes needed anywhere else in the pipeline.

Factors used, and why each is/isn't crop-differentiated:
- pH, mean temp: crop-specific tolerance ranges (as before).
- Nitrogen (total N) + CEC: crop-specific ranges reflecting relative
  nutrient demand (maize/colza are heavier feeders than orge/tournesol).
  These are broad, illustrative ranges — same placeholder rigor as the
  pH/temp ranges, not calibrated agronomic thresholds.
- Bulk density + coarse fragments ("workability"): scored the SAME way
  for every crop. There's no defensible per-crop tolerance data for
  soil compaction/rockiness at this project's scope, so this factor
  answers "is this land workable at all" rather than "which crop suits
  it better" — it nudges every crop's score together rather than
  re-ranking them.
- Precipitation: built from Open-Meteo's 16-day FORECAST, not
  season-long climatology — it's a near-term water-availability signal,
  not a real growing-season water balance. Weighted lightly for exactly
  that reason, and labeled as such in reasoning_features so this
  limitation is visible to anyone reading the score breakdown (same
  honesty pattern as the NDVI "descriptive, not predictive" framing
  elsewhere in this project).

Crop-pool expansion (potato, sugar beet, soybean, field pea): same
placeholder rigor as the original 5, ranges sourced from ARVALIS/Terres
Inovia/ITB reference material rather than a calibrated model. Soybean
and field pea are legumes — their nitrogen_range is deliberately set
LOW (they fix their own atmospheric N and don't need/want high soil N
to perform well, unlike the other crops here where a higher range means
a heavier feeder). This range only affects the suitability SCORE; the
fertilizer-dose implication (near-zero synthetic N need) is handled
separately in agro_calc_service.py's legume branch, not here.
"""
from schemas import SoilData, WeatherData, CropRecommendation

# Simplified agronomic tolerance ranges — placeholder domain knowledge
# until replaced by a trained model on real RPG + climate data.
_CROP_PROFILES = {
    "ble_tendre": {
        "ph_range": (6.0, 7.5), "temp_range": (10, 20),
        "nitrogen_range": (1.0, 3.0), "cec_range": (10, 25),
        "precip_range": (1.0, 4.0),
    },
    "mais": {
        "ph_range": (5.5, 7.5), "temp_range": (15, 27),
        "nitrogen_range": (1.5, 3.5), "cec_range": (12, 25),
        "precip_range": (1.5, 5.0),
    },
    "colza": {
        "ph_range": (6.0, 7.5), "temp_range": (8, 20),
        "nitrogen_range": (1.5, 3.5), "cec_range": (12, 25),
        "precip_range": (1.2, 4.5),
    },
    "orge": {
        "ph_range": (6.0, 7.8), "temp_range": (8, 20),
        "nitrogen_range": (0.8, 2.5), "cec_range": (8, 22),
        "precip_range": (0.8, 3.5),
    },
    "tournesol": {
        "ph_range": (6.0, 8.0), "temp_range": (18, 28),
        "nitrogen_range": (0.7, 2.2), "cec_range": (8, 20),
        "precip_range": (0.5, 3.0),
    },
    # --- Crop-pool expansion ---
    "pomme_de_terre": {
        # Prefers slightly acidic soil (also limits common scab); needs
        # loose, well-drained soil for tuber development; heavy feeder
        # given very high fresh-weight yield; high water demand.
        "ph_range": (5.0, 6.5), "temp_range": (14, 22),
        "nitrogen_range": (1.2, 3.0), "cec_range": (10, 25),
        "precip_range": (1.5, 5.0),
    },
    "betterave_sucriere": {
        # Sensitive to acidity (poor nodule/root development below ~6.5,
        # ARVALIS/ITB reference), tolerates near-neutral to mildly
        # alkaline soils well; moderate-to-warm season crop.
        "ph_range": (6.5, 7.8), "temp_range": (12, 24),
        "nitrogen_range": (1.0, 2.8), "cec_range": (12, 25),
        "precip_range": (1.0, 4.0),
    },
    "soja": {
        # Warm-season legume. Low nitrogen_range is deliberate — it
        # fixes its own N via rhizobia and performs best (and nodulates
        # best) on moderate, not high, background soil N.
        "ph_range": (6.0, 7.0), "temp_range": (18, 28),
        "nitrogen_range": (0.3, 1.8), "cec_range": (10, 22),
        "precip_range": (1.2, 4.5),
    },
    "pois_proteagineux": {
        # Cool-season legume (spring-sown), tolerant of a wider temp
        # band than soja. Low nitrogen_range for the same reason as
        # soja — self-fixing, doesn't want/need high background soil N.
        "ph_range": (6.0, 7.5), "temp_range": (8, 20),
        "nitrogen_range": (0.3, 1.8), "cec_range": (8, 20),
        "precip_range": (0.8, 3.5),
    },
}

# Component weights — must sum to 1.0. pH/temp still dominate since
# they're the best-supported factors; the newly-added ones are real
# signal but weighted lightly given their weaker evidentiary basis.
_WEIGHTS = {
    "ph": 0.28, "temp": 0.28, "nitrogen": 0.14,
    "cec": 0.10, "precip": 0.10, "workability": 0.10,
}


def _in_range_score(value: float | None, low: float, high: float) -> float:
    if value is None:
        return 0.5  # unknown -> neutral, don't penalize missing data
    if low <= value <= high:
        return 1.0
    span = high - low
    dist = min(abs(value - low), abs(value - high))
    return max(0.0, 1 - dist / span)


def _workability_score(bulk_density: float | None, coarse_fragments_pct: float | None) -> float:
    """Same scoring for every crop — soil compaction/rockiness affects
    workability generally, not one crop over another at this level of
    detail."""
    bd_score = _in_range_score(bulk_density, 1.0, 1.5)
    if coarse_fragments_pct is None:
        cf_score = 0.5
    else:
        cf_score = max(0.0, 1 - coarse_fragments_pct / 50)
    return round((bd_score + cf_score) / 2, 3)


def _mean_precip(weather: WeatherData) -> float | None:
    if not weather.daily_precip_mm:
        return None
    valid = [p for p in weather.daily_precip_mm if p is not None]
    return sum(valid) / len(valid) if valid else None


def recommend_crops(soil: SoilData, weather: WeatherData) -> list[CropRecommendation]:
    mean_temp = None
    if weather.daily_temp_mean_c:
        valid_temps = [t for t in weather.daily_temp_mean_c if t is not None]
        if valid_temps:
            mean_temp = sum(valid_temps) / len(valid_temps)

    mean_precip = _mean_precip(weather)
    workability = _workability_score(soil.bulk_density_kg_dm3, soil.coarse_fragments_pct)

    recs = []
    for crop, profile in _CROP_PROFILES.items():
        ph_score = _in_range_score(soil.ph, *profile["ph_range"])
        temp_score = _in_range_score(mean_temp, *profile["temp_range"])
        nitrogen_score = _in_range_score(soil.nitrogen_g_kg, *profile["nitrogen_range"])
        cec_score = _in_range_score(soil.cec_cmolkg, *profile["cec_range"])
        precip_score = _in_range_score(mean_precip, *profile["precip_range"])

        overall = round(
            ph_score * _WEIGHTS["ph"]
            + temp_score * _WEIGHTS["temp"]
            + nitrogen_score * _WEIGHTS["nitrogen"]
            + cec_score * _WEIGHTS["cec"]
            + precip_score * _WEIGHTS["precip"]
            + workability * _WEIGHTS["workability"],
            3,
        )

        recs.append(
            CropRecommendation(
                crop=crop,
                suitability_score=overall,
                reasoning_features={
                    "soil_ph": soil.ph,
                    "mean_temp_c": round(mean_temp, 1) if mean_temp is not None else None,
                    "nitrogen_g_kg": soil.nitrogen_g_kg,
                    "cec_cmolkg": soil.cec_cmolkg,
                    "mean_daily_precip_mm_forecast": round(mean_precip, 2) if mean_precip is not None else None,
                    "precip_note": "16-day forecast only, not a season-long water balance",
                    "ph_score": round(ph_score, 3),
                    "temp_score": round(temp_score, 3),
                    "nitrogen_score": round(nitrogen_score, 3),
                    "cec_score": round(cec_score, 3),
                    "precip_score": round(precip_score, 3),
                    "workability_score": workability,
                    "weights": _WEIGHTS,
                    "method": "rule_based_placeholder",  # flip to "random_forest" once trained
                },
            )
        )
    return sorted(recs, key=lambda r: r.suitability_score, reverse=True)

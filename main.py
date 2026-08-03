"""
Orchestrator. This is the "agent" from Section 4 — currently a fixed
parallel-then-sequential flow rather than a true tool-calling agent
loop, which is the right MVP simplification (Section 11): same data
contracts, easy to swap in real agentic tool-selection later without
changing any service module.
"""
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from schemas import ParcelRequest, ParcelResolution, AdvisorReport, NeighborCropContext, AgroCalcEstimate, YieldEstimate, NdviHeatmapResponse
from services import parcel_service, soil_service, weather_service, satellite_service, ml_service, rag_service, synthesis_service, dl_service, agro_calc_service, yield_service

app = FastAPI(title="AI Agricultural Advisor")

_STATIC_DIR = Path(__file__).parent / "static"
_STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# Crop-pool expansion took the scored pool from 5 crops to 9. Stage 2's
# report prompt loops over EVERY entry in crop_recommendations to build
# the "## Cultures recommandées" section, so passing all 9 through would
# turn that section into a 9-block wall rather than a useful ranked
# shortlist. Capping the displayed list here — not in ml_service.py,
# which should keep scoring the full pool for the top-pick logic below.
_MAX_DISPLAYED_CROPS = 5


@app.get("/")
async def root():
    return FileResponse(str(_STATIC_DIR / "index.html"))


@app.post("/parcel/resolve", response_model=ParcelResolution)
async def resolve_parcel_only(req: ParcelRequest):
    return await parcel_service.resolve_parcel(req)


@app.post("/parcel/neighbors", response_model=NeighborCropContext)
async def get_neighbors(req: ParcelRequest, radius_m: float = 800):
    parcel = await parcel_service.resolve_parcel(req)
    centroid = parcel.centroid or req.point
    return await parcel_service.get_neighboring_crop_context(
        centroid, radius_m=radius_m, exclude_parcel_id=parcel.rpg_id_parcel
    )


@app.post("/parcel/ndvi_heatmap", response_model=NdviHeatmapResponse)
async def ndvi_heatmap(req: ParcelRequest):
    """
    Backs the map frontend's "Afficher la carte NDVI" toggle. Was
    previously missing entirely — the button called this exact route
    but nothing on the server handled it, so every click 404'd.
    """
    parcel = await parcel_service.resolve_parcel(req)
    if not parcel.resolved or not parcel.geometry:
        raise HTTPException(
            status_code=422,
            detail=parcel.warning or "Could not resolve a parcel boundary for the NDVI heatmap.",
        )
    result = await satellite_service.get_ndvi_heatmap_png(parcel.geometry)
    if result.get("warning") and not result.get("image_base64"):
        raise HTTPException(status_code=502, detail=result["warning"])
    return NdviHeatmapResponse(**result)


@app.post("/advise", response_model=AdvisorReport)
async def advise(req: ParcelRequest):
    parcel = await parcel_service.resolve_parcel(req)
    if not parcel.resolved:
        raise HTTPException(
            status_code=422,
            detail=parcel.warning or "Could not resolve a parcel boundary.",
        )

    # Satellite NDVI and the DL classifier both need the actual polygon
    # (not just centroid), so they only run if we have geometry — fall
    # back gracefully otherwise, same pattern for both.
    soil, weather, vegetation, dl_observation = await asyncio.gather(
        soil_service.get_soil_data(parcel.centroid),
        weather_service.get_weather_data(parcel.centroid),
        satellite_service.get_ndvi(parcel.geometry) if parcel.geometry else asyncio.sleep(0, result=None),
        dl_service.predict_crop(parcel.geometry) if parcel.geometry else asyncio.sleep(0, result=None),
    )
    if vegetation is None:
        from schemas import VegetationData
        vegetation = VegetationData(source="unavailable", warning="No parcel geometry available for satellite lookup.")
    if dl_observation is None:
        from schemas import DLCropObservation
        dl_observation = DLCropObservation(source="unavailable", warning="No parcel geometry available for satellite lookup.")

    # Score the FULL crop pool (now 9 with the expansion) so the top
    # pick is chosen from everything, then trim what actually reaches
    # the report to the top 5 — see _MAX_DISPLAYED_CROPS above.
    crop_recs_all = ml_service.recommend_crops(soil, weather)
    crop_recs = crop_recs_all[:_MAX_DISPLAYED_CROPS]
    top_crop = crop_recs_all[0].crop if crop_recs_all else None

    yield_estimate = (
        yield_service.estimate_yield(crop_recs_all[0])
        if crop_recs_all else YieldEstimate(crop="", warning="Aucune culture recommandée disponible.")
    )

    agro_calc = (
        agro_calc_service.estimate_fertilizer_and_irrigation(
            top_crop, soil, weather, yield_objective_q_ha=yield_estimate.yield_estimate_q_ha
        )
        if top_crop else AgroCalcEstimate(crop="", warning="Aucune culture recommandée disponible.")
    )

    # rag_service.retrieve() is synchronous (it calls the blocking Mistral
    # embed SDK under the hood) — run it in a worker thread so it doesn't
    # block the asyncio event loop for every other request/user.
    chunks = await asyncio.to_thread(
        rag_service.retrieve,
        query=f"bonnes pratiques agronomiques pour {top_crop}" if top_crop else "bonnes pratiques agronomiques",
        crop_filter=top_crop,
    )
    if not chunks and top_crop:
        chunks = await asyncio.to_thread(
            rag_service.retrieve,
            query=f"bonnes pratiques agronomiques pour {top_crop}",
            crop_filter=None,
        )

    synthesis = await synthesis_service.synthesize_stage1(parcel, soil, weather, crop_recs, chunks, vegetation, dl_observation, agro_calc, yield_estimate)
    report = await synthesis_service.generate_report(synthesis, parcel)

    return report


@app.get("/health")
async def health():
    return {"status": "ok"}

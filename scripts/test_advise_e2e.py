"""
End-to-end smoke test for the full pipeline, including the new Phase B
DL wiring. Run this AFTER starting your server (`uvicorn main:app --reload`
in one terminal), from a second terminal:

    python test_advise_e2e.py

Uses a real coordinate — swap COORD for a parcel you know is
RPG-registered with a declared crop, so you can actually see the
declared-vs-observed comparison exercised (a parcel with no RPG
declaration will only tell you the DL/vegetation paths work, not the
mismatch-note path).
"""
import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

# Swap for a real French agricultural parcel's lat/lon — this is just a
# placeholder near Chartres, same area used in check_satellite.py.
COORD = {"lat": 44.0195, "lon": 5.0728}


def check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    return condition


def main():
    client = httpx.Client(timeout=60)
    all_ok = True

    # 1. Health check
    r = client.get(f"{BASE_URL}/health")
    all_ok &= check("server is up", r.status_code == 200)

    # 2. Parcel resolution
    r = client.post(f"{BASE_URL}/parcel/resolve", json={"point": COORD})
    all_ok &= check("parcel/resolve returns 200", r.status_code == 200, r.text[:300])
    if r.status_code != 200:
        print("Cannot continue without a resolved parcel — stopping.")
        return
    parcel = r.json()
    print(f"  parcel: resolved={parcel.get('resolved')}, source={parcel.get('source')}, "
          f"parcel_id={parcel.get('parcel_id')}, rpg_id_parcel={parcel.get('rpg_id_parcel')}, "
          f"area_ha={parcel.get('area_ha')}, crop_declared={parcel.get('crop_declared')}")
    all_ok &= check("parcel resolved successfully", parcel.get("resolved") is True)
    all_ok &= check("area_ha is present (regression check for the earlier area-dropped bug)", parcel.get("area_ha") is not None)

    # 3. Neighbors — regression check for the rpg_id_parcel exclusion fix
    r = client.post(f"{BASE_URL}/parcel/neighbors", json={"point": COORD})
    if r.status_code == 200:
        neighbors = r.json()
        n = neighbors.get("neighbor_count", 0)
        print(f"  neighbors: count={n}")
        all_ok &= check("neighbor lookup returns 200", True)
    else:
        print(f"  [WARN] neighbors returned {r.status_code} — not fatal, continuing")

    # 4. Full /advise — the main event
    r = client.post(f"{BASE_URL}/advise", json={"point": COORD})
    all_ok &= check("advise returns 200", r.status_code == 200, r.text[:500])
    if r.status_code != 200:
        print("Cannot continue without a report — stopping.")
        return
    report = r.json()

    md = report.get("report_markdown", "")
    warnings = report.get("warnings", [])
    unverified = report.get("unverified_figures", [])

    print(f"\n  report length: {len(md)} chars")
    print(f"  warnings ({len(warnings)}): {warnings}")
    print(f"  unverified_figures ({len(unverified)}): {unverified}")

    all_ok &= check("report_markdown is non-empty", len(md) > 200)
    all_ok &= check(
        "no unverified figures flagged (if this fails, it's either a real invented "
        "number OR the weather-audit gap we haven't fixed yet — inspect the list above)",
        len(unverified) == 0,
    )
    all_ok &= check("## Résumé section present", "## Résumé" in md)
    all_ok &= check("## Sol section present", "## Sol" in md)
    all_ok &= check("## Météo section present", "## Météo" in md)
    all_ok &= check("## Végétation section present", "## Végétation" in md)
    all_ok &= check("## Cultures recommandées section present", "## Cultures recommand" in md)
    all_ok &= check("## Fertilisation et irrigation section present", "## Fertilisation" in md)
    all_ok &= check("## Rendement estimé section present", "## Rendement estim" in md)
    all_ok &= check("## Conseils pratiques section present", "## Conseils pratiques" in md or "## Conseils" in md)
    all_ok &= check("## Alertes section present", "## Alertes" in md)
    all_ok &= check("## Données manquantes section present", "## Donn" in md)

    # DL-specific checks — these will legitimately be absent if you haven't
    # dropped tempcnn_finetuned.pth into dl_checkpoints/ yet, so they're
    # reported as INFO rather than failing the whole run.
    has_dl_bullet = "observée par satellite" in md.lower()
    print(f"\n  [INFO] DL prediction bullet detected in Végétation section: {has_dl_bullet}")
    if not has_dl_bullet:
        print("  (expected if no checkpoint is in place yet, or if the parcel has <5 cloud-free "
              "Sentinel-2 L1C acquisitions in the last 120 days — check server logs for a "
              "DLCropObservation warning)")

    has_n_cap = "plafonnée" in md.lower()
    print(f"  [INFO] N-dose regulatory cap triggered on this report: {has_n_cap}")
    if has_n_cap:
        print("  (expected only on a high-suitability parcel with a high yield estimate — "
              "confirm the capped dose printed in ## Fertilisation looks realistic, not just capped)")

    print("\n--- Full report markdown ---\n")
    print(md)

    print("\n" + ("ALL CHECKS PASSED" if all_ok else "SOME CHECKS FAILED — see [FAIL] lines above"))


if __name__ == "__main__":
    main()

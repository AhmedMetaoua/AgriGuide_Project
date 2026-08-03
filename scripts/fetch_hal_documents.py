"""
Automates Section 7.1's document sourcing from HAL — queries HAL's free
public search API, filters to open-access records that actually have a
downloadable PDF (fileMain_s), and saves them into ./corpus/ so
ingest_rag_corpus.py can chunk/embed them.

No key, no auth, no cost — HAL's search API is fully public.

Usage:
    python -m scripts.fetch_hal_documents --query "ble tendre fertilisation" \
        --coll INRAE --rows 30 --out ./corpus

    # Broader agronomy sweep across several topics in one run:
    python -m scripts.fetch_hal_documents --query "agronomie irrigation" --coll INRAE --rows 50

    # Drop the collection filter if a crop returns too few candidates
    # (some crops' open literature isn't tagged collCode_s:INRAE even
    # when INRAE-affiliated — see note below):
    python -m scripts.fetch_hal_documents --query "pomme de terre fertilisation azote" --rows 30
"""
import argparse
import re
import time
from pathlib import Path
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

HAL_SEARCH_URL = "https://api.archives-ouvertes.fr/search/"


def _safe_filename(hal_id: str, title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", title.strip())[:60]
    return f"{hal_id}_{slug}.pdf"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _search_hal(query: str, coll: str | None, rows: int, start: int) -> dict:
    params = {
        "q": query,
        "wt": "json",
        "rows": rows,
        "start": start,
        # fl = fields to return: id, title, PDF link, doc type, date, collection
        "fl": "halId_s,title_s,fileMain_s,docType_s,producedDateY_i,collCode_s",
        # No explicit "sort" -> HAL's default is relevance-score order.
        # A previous version of this script forced sort=producedDateY_i
        # desc (newest-first), which silently defeats relevance ranking:
        # the newest record containing ANY query term can outrank an
        # older record that's actually about the query topic. Caught
        # live — a "pomme de terre fertilisation azote" query surfaced
        # an unrelated 2023 wheat/Lebanon paper as the top (and only)
        # downloadable result. Don't reintroduce a date sort here
        # without also switching to a relevance-first query (e.g. HAL's
        # edismax-style params), or the same failure mode comes back.
    }
    if coll:
        params["fq"] = f"collCode_s:{coll}"

    with httpx.Client(timeout=15) as client:
        resp = client.get(HAL_SEARCH_URL, params=params)
        resp.raise_for_status()
        return resp.json()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def _download_pdf(url: str, dest: Path) -> None:
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)


def fetch_hal_documents(query: str, coll: str | None, rows: int, out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    data = _search_hal(query, coll, rows, start=0)
    docs = data.get("response", {}).get("docs", [])
    total_found = data.get("response", {}).get("numFound", len(docs))

    print(f"Query matched {total_found} record(s) in HAL{' (collCode=' + coll + ')' if coll else ''}; "
          f"inspecting top {len(docs)}.\n")

    downloaded = 0
    skipped_no_pdf = 0

    for doc in docs:
        pdf_url = doc.get("fileMain_s")  # absent when the record has no open full text
        hal_id = doc.get("halId_s", "unknown")
        title = doc.get("title_s", ["untitled"])
        title = title[0] if isinstance(title, list) else title
        year = doc.get("producedDateY_i", "?")

        if not pdf_url:
            skipped_no_pdf += 1
            print(f"  [no open PDF] {hal_id} ({year}) — {title}")
            continue

        dest = out_dir / _safe_filename(hal_id, title)
        if dest.exists():
            print(f"  [already have] {hal_id} ({year}) — {title}")
            continue  # already fetched in a previous run

        # Printed BEFORE download, on purpose: check relevance here, not
        # after it's already sitting in your corpus folder about to get
        # embedded into the RAG store.
        print(f"  [downloading] {hal_id} ({year}) — {title}")

        try:
            _download_pdf(pdf_url, dest)
            downloaded += 1
            time.sleep(0.5)  # be polite to a free public service, no rate-limit stated but avoid hammering it
        except httpx.HTTPError as e:
            print(f"    Failed to download {hal_id}: {e}")

    print(f"\nDone. {downloaded} PDFs downloaded, {skipped_no_pdf} records had no open full text.")
    if downloaded > 0:
        print("Check the titles above before running ingest_rag_corpus.py — delete any file in "
              "./corpus that isn't actually about the target crop/topic; a mismatched PDF getting "
              "chunked and embedded is worse than a smaller corpus.")
    return downloaded


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help='e.g. "ble tendre fertilisation"')
    ap.add_argument("--coll", default=None, help='HAL collection code, e.g. "INRAE" to restrict to INRAE')
    ap.add_argument("--rows", type=int, default=30, help="max records to fetch (HAL default cap ~1000/request)")
    ap.add_argument("--out", default="./corpus", help="output folder for downloaded PDFs")
    args = ap.parse_args()

    fetch_hal_documents(args.query, args.coll, args.rows, Path(args.out))


if __name__ == "__main__":
    main()

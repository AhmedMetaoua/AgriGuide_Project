"""
Standalone cleanup for the persisted chroma_store — for when a wrong
or mismatched document made it into the RAG index (like hal-00886225,
a UK potato CHIPS-model paper that ended up tagged crop=pois_proteagineux
instead of pomme_de_terre/uncertain).

ingest_rag_corpus.py has no delete path — it only skips re-indexing a
file already present (dedup by source_document filename). Once
something's in the store with the wrong tag, moving the PDF between
local folders does nothing; it has to be removed from Chroma directly.

Usage:
    # See what's actually indexed for a crop, source doc, or both
    python manage_rag_store.py --list --crop pois_proteagineux
    python manage_rag_store.py --list --source hal-00886225

    # Delete all chunks from a specific source document (any crop tag)
    python manage_rag_store.py --delete --source hal-00886225_Constructing_a_water-use_model_for_input_to_the_water_cloud_.pdf

    # After deleting, re-run ingest_rag_corpus.py normally (no --force
    # needed for a NEW file; --force needed only if re-adding a file
    # whose source_document name is still recognized from a previous
    # index attempt that didn't fully clear)
"""
import argparse
from services.rag_service import _collection


def list_by(crop: str | None, source: str | None):
    where = {}
    if crop and source:
        where = {"$and": [{"crop": crop}, {"source_document": {"$eq": source}}]}
    elif crop:
        where = {"crop": crop}
    elif source:
        where = {"source_document": {"$eq": source}}

    result = _collection.get(where=where if where else None, limit=1000)
    ids = result.get("ids", [])
    metadatas = result.get("metadatas", [])

    if not ids:
        print("No matching chunks found.")
        return

    by_source = {}
    for meta in metadatas:
        key = (meta.get("source_document"), meta.get("crop"))
        by_source[key] = by_source.get(key, 0) + 1

    print(f"{len(ids)} chunk(s) found across {len(by_source)} document(s):\n")
    for (src, crop_tag), count in sorted(by_source.items()):
        print(f"  {count:4d} chunks  crop={crop_tag!r:25s}  {src}")


def delete_by_source(source: str):
    existing = _collection.get(where={"source_document": {"$eq": source}}, limit=1000)
    ids = existing.get("ids", [])
    if not ids:
        print(f"No chunks found for source_document={source!r} — nothing to delete.")
        return
    _collection.delete(ids=ids)
    print(f"Deleted {len(ids)} chunk(s) from source_document={source!r}.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--delete", action="store_true")
    ap.add_argument("--crop", default=None)
    ap.add_argument("--source", default=None, help="Exact filename as stored in source_document metadata")
    args = ap.parse_args()

    if args.delete:
        if not args.source:
            print("--delete requires --source <exact filename>")
        else:
            delete_by_source(args.source)
    elif args.list:
        list_by(args.crop, args.source)
    else:
        print("Specify --list or --delete.")

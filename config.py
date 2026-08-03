"""
Central config. All values pull from environment variables so nothing
sensitive is hardcoded. Every default here points at a free/no-key
service per the project's academic constraint.
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # --- LLM (Mistral) ---
    mistral_api_key: str = ""  # free tier key from console.mistral.ai
    mistral_model: str = "mistral-small-latest"
    mistral_embed_model: str = "mistral-embed"

    # --- Fallback embeddings (used if no Mistral key / quota hit) ---
    local_embed_model: str = "intfloat/multilingual-e5-base"

    # --- Free geodata / API endpoints ---
    cadastre_api_base: str = "https://apicarto.ign.fr/api/cadastre"
    rpg_wfs_base: str = "https://data.geopf.fr/wfs/ows"
    soilgrids_base: str = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    open_meteo_base: str = "https://api.open-meteo.com/v1/forecast"
    hal_api_base: str = "https://api.archives-ouvertes.fr/search/"

    # --- Storage ---
    chroma_persist_dir: str = str(Path(__file__).parent / "chroma_store")
    chroma_collection: str = "agri_rag_corpus"

    # --- Retrieval ---
    retrieval_top_k: int = 6
    chunk_min_tokens: int = 200
    chunk_max_tokens: int = 500
    chunk_overlap_ratio: float = 0.12

    # --- Satellite (Copernicus Data Space Ecosystem — free account required) ---
    copernicus_client_id: str = ""
    copernicus_client_secret: str = ""

    # --- Phase B: DL crop classifier (BreizhCrops-pretrained TempCNN, fine-tuned) ---
    dl_checkpoint_path: str = str(Path(__file__).parent / "dl_checkpoints" / "tempcnn_finetuned.pth")
    dl_sequence_length: int = 45  # fixed input length the pretrained TempCNN architecture expects

    # --- Qdrant Cloud (push_to_qdrant.py) — same hybrid dense+sparse shape
    # as the Government Regulations feature's collections, so all
    # collections stay queryable the same way. ---
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection: str = "Agricultural Advisor"
    qdrant_timeout_seconds: int = 60
    qdrant_dense_vector_name: str = "text-dense"
    qdrant_sparse_vector_name: str = "text-sparse"
    qdrant_dense_dim: int = 1024  # must match mistral-embed's output dim — same value ingest already assumes
    qdrant_sparse_model: str = "Qdrant/bm25"  # fastembed model, same one the Regulations feature uses

    class Config:
        env_file = ".env"


settings = Settings()
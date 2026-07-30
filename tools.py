import pandas as pd
import glob
from langchain_core.tools import tool

@tool
def analyze_price_trends(crops: list[str], region: str, season: str) -> str:
    """
    Analyse les tendances de prix historiques (2020-2026) pour une liste de cultures.
    """
    # 1. Corrected Column Names based on actual CSV contents
    COL_REGION = "GEOGRAPHIE_LIB" 
    COL_CROP = "IPPAP_DIM2_LIB"  # This is the column with the actual text!
    COL_PRICE = "VALEUR"

    csv_files = glob.glob("data/FDS_IPPAP_*.csv")
    
    if not csv_files:
        return "Erreur : Aucun fichier FDS_IPPAP trouvé dans le dossier 'data'."

    try:
        df = pd.concat([pd.read_csv(f, sep=';', encoding='utf-8') for f in csv_files], ignore_index=True)
    except Exception as e:
        return f"Erreur de lecture des fichiers CSV : {e}"

    # 2. Fix the crop text matching
    # We remove the strict "Bretagne" filter because the file only contains "FR metro - France metropolitaine".
    # We use a flexible regex to catch names like "____Carotte (production)" or "___Pomme de terre".
    
    # Map input crops to the way they appear in the CSV (e.g., "Navet" -> "Navets")
    search_terms = []
    for c in crops:
        if c.lower() == "navet":
            search_terms.append("navets")
        else:
            search_terms.append(c.lower())
            
    pattern_crops = '|'.join(search_terms)

    try:
        filtered_df = df[
            (df[COL_CROP].str.lower().str.contains(pattern_crops, na=False))
        ]
    except KeyError as e:
        return f"Erreur : Colonne {e} introuvable."

    if filtered_df.empty:
        return f"Aucune donnée de marché disponible pour les cultures demandées."

    # 3. Fix the French decimal commas to dots, then convert to numeric
    filtered_df = filtered_df.copy() # Avoid SettingWithCopyWarning
    filtered_df[COL_PRICE] = pd.to_numeric(
        filtered_df[COL_PRICE].astype(str).str.replace(',', '.'), 
        errors='coerce'
    )

    # 4. Calculate average prices per crop
    averages = filtered_df.groupby(COL_CROP)[COL_PRICE].mean().reset_index()
    
    # 5. Format the output for Mistral
    report = f"Données du marché (Moyenne Nationale France - Base 100) :\n"
    for _, row in averages.iterrows():
        # Clean up the INSEE underscores for the AI's prompt
        clean_name = row[COL_CROP].replace('_', '').strip()
        report += f"- {clean_name} : Indice de prix moyen {row[COL_PRICE]:.2f}\n"
        
    return report
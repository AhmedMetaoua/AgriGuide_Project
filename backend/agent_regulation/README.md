# Agent Régulation

**Rôle** : conseiller sur lois/certifications/aides financières selon la
localisation du terrain, et aider à préparer les dossiers (Cerfa, etc).

## Architecture RAG obligatoire
Pas de LLM "sec" sur ce module — risque trop élevé d'hallucination sur du
contenu légal. Pipeline :
1. Scraping/ingestion périodique du corpus : Code Rural, textes SRDEA,
   formulaires Cerfa, data.gouv.fr, pages FranceAgriMer.
2. Génération d'embeddings → stockage dans `regulation_documents.embedding`
   (pgvector).
3. À chaque question : recherche de similarité → contexte injecté dans le
   prompt Mistral → réponse générée UNIQUEMENT à partir du contexte récupéré.
4. Chaque réponse doit citer sa source (`sources_citees` dans
   `regulation_chat_history`).

## Disclaimer obligatoire
Chaque réponse doit inclure : "Ceci n'est pas un conseil juridique définitif,
vérifiez auprès de votre chambre d'agriculture."

## Génération de dossiers
`dossiers_administratifs` : pré-remplir les champs connus (via LandProfile,
décisions confirmées) pour réduire le travail du farmer.

## Pipeline de mise à jour du corpus
Les lois/aides changent souvent — prévoir un job planifié (mensuel minimum)
qui rafraîchit `regulation_documents`.

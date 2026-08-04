package com.example.myapplication.model;

import com.google.gson.JsonElement;
import com.google.gson.annotations.SerializedName;

public class InsectAnalysis {
    @SerializedName("nom_insecte")
    private String insectName;

    @SerializedName("impact_agricole")
    private JsonElement agriculturalImpact;

    @SerializedName("est_nuisible")
    private boolean isHarmful;

    public String getInsectName() { return insectName != null ? insectName : "Inconnu"; }
    
    public String getAgriculturalImpact() { 
        if (agriculturalImpact == null) return "Information non disponible";
        if (agriculturalImpact.isJsonPrimitive()) {
            return agriculturalImpact.getAsString();
        }
        return agriculturalImpact.toString(); 
    }

    public boolean isHarmful() { return isHarmful; }
}

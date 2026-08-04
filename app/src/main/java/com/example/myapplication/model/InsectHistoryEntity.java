package com.example.myapplication.model;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "insect_history")
public class InsectHistoryEntity {
    @PrimaryKey(autoGenerate = true)
    private int id;
    
    private String insectName;
    private String impactDetails;
    private boolean isHarmful;
    private long timestamp;

    public InsectHistoryEntity(String insectName, String impactDetails, boolean isHarmful, long timestamp) {
        this.insectName = insectName;
        this.impactDetails = impactDetails;
        this.isHarmful = isHarmful;
        this.timestamp = timestamp;
    }

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }
    public String getInsectName() { return insectName; }
    public String getImpactDetails() { return impactDetails; }
    public boolean isHarmful() { return isHarmful; }
    public long getTimestamp() { return timestamp; }
}

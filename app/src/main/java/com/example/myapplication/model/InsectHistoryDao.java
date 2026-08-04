package com.example.myapplication.model;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.Query;

import java.util.List;

@Dao
public interface InsectHistoryDao {
    @Insert
    void insert(InsectHistoryEntity entity);

    @Query("SELECT * FROM insect_history ORDER BY timestamp DESC")
    LiveData<List<InsectHistoryEntity>> getAllHistory();

    @Query("DELETE FROM insect_history")
    void deleteAll();
}

package com.example.myapplication.viewmodel;

import android.app.Application;

import androidx.annotation.NonNull;
import androidx.lifecycle.AndroidViewModel;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;

import com.example.myapplication.model.AppDatabase;
import com.example.myapplication.model.InsectAnalysis;
import com.example.myapplication.model.InsectHistoryEntity;
import com.example.myapplication.repository.MistralRepository;

import java.util.List;

public class InsectViewModel extends AndroidViewModel {
    private final MistralRepository repository;
    private final MutableLiveData<Boolean> isLoading = new MutableLiveData<>(false);
    private final MutableLiveData<String> statusMessage = new MutableLiveData<>("");
    private final MutableLiveData<String> stepDetail = new MutableLiveData<>("");
    private final MutableLiveData<String> errorMessage = new MutableLiveData<>();
    private final MutableLiveData<InsectAnalysis> analysisResult = new MutableLiveData<>();
    private final LiveData<List<InsectHistoryEntity>> history;

    public InsectViewModel(@NonNull Application application) {
        super(application);
        AppDatabase db = AppDatabase.getInstance(application);
        this.repository = new MistralRepository(db.insectHistoryDao());
        this.history = repository.getHistory();
    }

    public LiveData<Boolean> getIsLoading() {
        return isLoading;
    }

    public LiveData<String> getStatusMessage() {
        return statusMessage;
    }

    public LiveData<String> getStepDetail() {
        return stepDetail;
    }

    public LiveData<String> getErrorMessage() {
        return errorMessage;
    }

    public LiveData<InsectAnalysis> getAnalysisResult() {
        return analysisResult;
    }

    public LiveData<List<InsectHistoryEntity>> getHistory() {
        return history;
    }

    public void analyzeImage(String base64Image) {
        isLoading.setValue(true);
        statusMessage.setValue("Initialisation...");
        stepDetail.setValue("Préparation de l'image");
        repository.analyzeInsect(base64Image, statusMessage, stepDetail).observeForever(result -> {
            isLoading.setValue(false);
            if (result != null) {
                analysisResult.setValue(result);
            } else {
                errorMessage.setValue("L'analyse a échoué.");
            }
        });
    }

    public void resetResult() {
        analysisResult.setValue(null);
    }
}


package com.example.myapplication.repository;

import com.example.myapplication.BuildConfig;
import com.example.myapplication.model.InsectAnalysis;
import com.example.myapplication.model.InsectHistoryDao;
import com.example.myapplication.model.InsectHistoryEntity;
import com.example.myapplication.network.MistralApiService;
import com.example.myapplication.network.MistralRequest;
import com.example.myapplication.network.MistralResponse;
import com.google.gson.Gson;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import okhttp3.OkHttpClient;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public class MistralRepository {
    private static final String BASE_URL = "https://api.mistral.ai/";
    private final MistralApiService apiService;
    private final String apiKey = BuildConfig.MISTRAL_API_KEY;
    private final InsectHistoryDao historyDao;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    public MistralRepository(InsectHistoryDao historyDao) {
        this.historyDao = historyDao;
        HttpLoggingInterceptor logging = new HttpLoggingInterceptor();
        logging.setLevel(HttpLoggingInterceptor.Level.BODY);
        OkHttpClient client = new OkHttpClient.Builder()
                .addInterceptor(logging)
                .build();

        Retrofit retrofit = new Retrofit.Builder()
                .baseUrl(BASE_URL)
                .addConverterFactory(GsonConverterFactory.create())
                .client(client)
                .build();

        apiService = retrofit.create(MistralApiService.class);
    }

    public LiveData<InsectAnalysis> analyzeInsect(String base64Image, MutableLiveData<String> statusMessage, MutableLiveData<String> stepDetail) {
        MutableLiveData<InsectAnalysis> result = new MutableLiveData<>();

        statusMessage.postValue("AgriGuard IA");
        stepDetail.postValue("Génération du prompt expert...");
        
        String prompt = "Tu es un expert en entomologie agricole de précision. " +
                "INSTRUCTIONS STRICTES : " +
                "1. Analyse l'insecte présent sur cette photo. " +
                "2. Réponds UNIQUEMENT par un objet JSON. " +
                "3. Utilise exactement ces clés : \"nom_insecte\", \"impact_agricole\", \"est_nuisible\". " +
                "4. Si l'insecte n'est pas identifiable, mets \"Inconnu\" dans le nom. " +
                "Ne commence jamais par 'Voici le JSON' ou autre texte.";

        stepDetail.postValue("Encodage de l'image (Base64)...");
        
        List<MistralRequest.Content> contents = new ArrayList<>();
        contents.add(new MistralRequest.Content("text", prompt));
        contents.add(new MistralRequest.Content("image_url", new MistralRequest.ImageUrl("data:image/jpeg;base64," + base64Image)));

        MistralRequest.Message message = new MistralRequest.Message("user", contents);
        List<MistralRequest.Message> messages = new ArrayList<>();
        messages.add(message);

        MistralRequest request = new MistralRequest(messages);

        stepDetail.postValue("Connexion aux serveurs Mistral...");

        apiService.getCompletion("Bearer " + apiKey, request).enqueue(new Callback<MistralResponse>() {
            @Override
            public void onResponse(Call<MistralResponse> call, Response<MistralResponse> response) {
                if (response.isSuccessful() && response.body() != null && !response.body().getChoices().isEmpty()) {
                    stepDetail.postValue("Analyse de la réponse reçue...");
                    String content = response.body().getChoices().get(0).getMessage().getContent();
                    
                    android.util.Log.d("MistralRaw", "Content: " + content);
                    
                    String jsonPart = content;
                    if (content.contains("{")) {
                        jsonPart = content.substring(content.indexOf("{"), content.lastIndexOf("}") + 1);
                    }
                    
                    try {
                        stepDetail.postValue("Extraction des données biologiques...");
                        InsectAnalysis analysis = new Gson().fromJson(jsonPart, InsectAnalysis.class);
                        if (analysis != null) {
                            stepDetail.postValue("Finalisation et sauvegarde...");
                            saveToHistory(analysis);
                            result.postValue(analysis);
                        } else {
                            stepDetail.postValue("Échec : Données corrompues");
                            result.postValue(null);
                        }
                    } catch (Exception e) {
                        android.util.Log.e("MistralError", "Parsing error: " + e.getMessage(), e);
                        stepDetail.postValue("Erreur : Format IA non reconnu");
                        result.postValue(null);
                    }
                } else {
                    stepDetail.postValue("Erreur API : " + response.code());
                    result.postValue(null);
                }
            }

            @Override
            public void onFailure(Call<MistralResponse> call, Throwable t) {
                stepDetail.postValue("Erreur : Connexion impossible");
                result.postValue(null);
            }
        });

        return result;
    }

    private void saveToHistory(InsectAnalysis analysis) {
        executor.execute(() -> {
            historyDao.insert(new InsectHistoryEntity(
                    analysis.getInsectName(),
                    analysis.getAgriculturalImpact(),
                    analysis.isHarmful(),
                    System.currentTimeMillis()
            ));
        });
    }

    public LiveData<List<InsectHistoryEntity>> getHistory() {
        return historyDao.getAllHistory();
    }
}

package com.example.myapplication.network;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.Header;
import retrofit2.http.POST;

public interface MistralApiService {
    @POST("v1/chat/completions")
    Call<MistralResponse> getCompletion(
        @Header("Authorization") String authorization,
        @Body MistralRequest request
    );
}

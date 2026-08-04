package com.example.myapplication.network;

import com.google.gson.annotations.SerializedName;
import java.util.List;

public class MistralResponse {
    @SerializedName("choices")
    private List<Choice> choices;

    public List<Choice> getChoices() { return choices; }

    public static class Choice {
        @SerializedName("message")
        private MessageResponse message;

        public MessageResponse getMessage() { return message; }
    }

    public static class MessageResponse {
        @SerializedName("content")
        private String content;

        public String getContent() { return content; }
    }
}

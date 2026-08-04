package com.example.myapplication.network;

import com.google.gson.annotations.SerializedName;
import java.util.List;

public class MistralRequest {
    @SerializedName("model")
    private String model = "pixtral-12b-2409";

    @SerializedName("messages")
    private List<Message> messages;

    @SerializedName("response_format")
    private ResponseFormat responseFormat = new ResponseFormat("json_object");

    @SerializedName("max_tokens")
    private int maxTokens = 1024;

    public MistralRequest(List<Message> messages) {
        this.messages = messages;
    }

    public static class Message {
        @SerializedName("role")
        private String role;
        @SerializedName("content")
        private List<Content> content;

        public Message(String role, List<Content> content) {
            this.role = role;
            this.content = content;
        }
    }

    public static class Content {
        @SerializedName("type")
        private String type;
        @SerializedName("text")
        private String text;
        @SerializedName("image_url")
        private ImageUrl imageUrl;

        public Content(String type, String text) {
            this.type = type;
            this.text = text;
        }

        public Content(String type, ImageUrl imageUrl) {
            this.type = type;
            this.imageUrl = imageUrl;
        }
    }

    public static class ImageUrl {
        @SerializedName("url")
        private String url;

        public ImageUrl(String url) {
            this.url = url;
        }
    }

    public static class ResponseFormat {
        @SerializedName("type")
        private String type;

        public ResponseFormat(String type) {
            this.type = type;
        }
    }
}

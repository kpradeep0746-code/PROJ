package com.example.ailecturesummarizer.model;

import com.google.gson.annotations.SerializedName;

/**
 * Response model for the AI Assistant /ask API.
 * Maps to: { "answer": "..." }
 */
public class ChatResponse {

    @SerializedName("answer")
    public String answer;

    public ChatResponse(String answer) {
        this.answer = answer;
    }
}

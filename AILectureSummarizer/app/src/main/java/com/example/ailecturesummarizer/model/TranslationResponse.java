package com.example.ailecturesummarizer.model;

import com.google.gson.annotations.SerializedName;

public class TranslationResponse {

    @SerializedName("success")
    public boolean success;

    @SerializedName("translated_transcript")
    public String translatedTranscript;

    @SerializedName("message")
    public String message;
}

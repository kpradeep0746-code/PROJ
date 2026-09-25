package com.example.ailecturesummarizer.model;

import com.google.gson.annotations.SerializedName;

public class TranslationRequest {

    @SerializedName("transcript")
    private String transcript;

    @SerializedName("source_language")
    private String sourceLanguage;

    @SerializedName("target_language")
    private String targetLanguage;

    public TranslationRequest(String transcript, String sourceLanguage, String targetLanguage) {
        this.transcript = transcript;
        this.sourceLanguage = sourceLanguage;
        this.targetLanguage = targetLanguage;
    }

    public TranslationRequest(String transcript, String targetLanguage) {
        this(transcript, "Auto Detect", targetLanguage);
    }

    public String getTranscript() {
        return transcript;
    }

    public void setTranscript(String transcript) {
        this.transcript = transcript;
    }

    public String getSourceLanguage() {
        return sourceLanguage;
    }

    public void setSourceLanguage(String sourceLanguage) {
        this.sourceLanguage = sourceLanguage;
    }

    public String getTargetLanguage() {
        return targetLanguage;
    }

    public void setTargetLanguage(String targetLanguage) {
        this.targetLanguage = targetLanguage;
    }
}

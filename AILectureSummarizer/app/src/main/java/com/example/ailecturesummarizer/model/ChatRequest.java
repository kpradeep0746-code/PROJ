package com.example.ailecturesummarizer.model;

import com.google.gson.annotations.SerializedName;

/**
 * Request body model for the AI Assistant /ask API.
 * Maps to: { "student_id": "...", "lecture_id": "...", "question": "..." }
 */
public class ChatRequest {

    @SerializedName("student_id")
    public final String studentId;

    @SerializedName("lecture_id")
    public final String lectureId;

    @SerializedName("question")
    public final String question;

    public ChatRequest(String studentId, String lectureId, String question) {
        this.studentId = studentId;
        this.lectureId = lectureId;
        this.question  = question;
    }
}

package com.example.ailecturesummarizer.model;

/**
 * Model representing note creation request.
 */
public class NoteRequest {
    public final String student_id;
    public final String title;
    public final String content;

    public NoteRequest(String student_id, String title, String content) {
        this.student_id = student_id;
        this.title = title;
        this.content = content;
    }
}

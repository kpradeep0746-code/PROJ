package com.example.ailecturesummarizer.model;

/**
 * Model representing note update request.
 */
public class NoteUpdateRequest {
    public final String title;
    public final String content;

    public NoteUpdateRequest(String title, String content) {
        this.title = title;
        this.content = content;
    }
}

package com.example.ailecturesummarizer.model;

/**
 * Model representing note database response.
 */
public class NoteResponse {
    private int id;
    private String student_id;
    private String title;
    private String content;
    private String created_at;
    private String updated_at;

    public NoteResponse(int id, String student_id, String title, String content, String created_at, String updated_at) {
        this.id = id;
        this.student_id = student_id;
        this.title = title;
        this.content = content;
        this.created_at = created_at;
        this.updated_at = updated_at;
    }

    public int getId() {
        return id;
    }

    public String getStudentId() {
        return student_id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public String getCreatedAt() {
        return created_at;
    }

    public String getUpdatedAt() {
        return updated_at;
    }
}

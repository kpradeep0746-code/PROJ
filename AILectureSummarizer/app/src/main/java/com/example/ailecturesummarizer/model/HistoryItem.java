package com.example.ailecturesummarizer.model;

/**
 * POJO representing a single history entry in the sidebar.
 */
public class HistoryItem {

    private final String title;
    private final String url;
    private final String action; // e.g. "Summarize", "Transcript", etc.

    public HistoryItem(String title, String url, String action) {
        this.title = title;
        this.url = url;
        this.action = action;
    }

    public String getTitle() {
        return title;
    }

    public String getUrl() {
        return url;
    }

    public String getAction() {
        return action;
    }
}

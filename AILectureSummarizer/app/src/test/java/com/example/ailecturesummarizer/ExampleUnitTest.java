package com.example.ailecturesummarizer;

import org.junit.Test;
import com.example.ailecturesummarizer.model.NoteResponse;

import static org.junit.Assert.*;

/**
 * Local unit tests for NOA AI Lecture Summarizer.
 */
public class ExampleUnitTest {

    @Test
    public void addition_isCorrect() {
        assertEquals(4, 2 + 2);
    }

    @Test
    public void extractVideoId_standardUrl_returnsVideoId() {
        String url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";
        String videoId = MainActivity.extractVideoId(url);
        assertEquals("dQw4w9WgXcQ", videoId);
    }

    @Test
    public void extractVideoId_shortUrl_returnsVideoId() {
        String url = "https://youtu.be/dQw4w9WgXcQ";
        String videoId = MainActivity.extractVideoId(url);
        assertEquals("dQw4w9WgXcQ", videoId);
    }

    @Test
    public void extractVideoId_shortsUrl_returnsVideoId() {
        String url = "https://www.youtube.com/shorts/dQw4w9WgXcQ";
        String videoId = MainActivity.extractVideoId(url);
        assertEquals("dQw4w9WgXcQ", videoId);
    }

    @Test
    public void extractVideoId_invalidUrl_returnsNull() {
        String url = "https://example.com/not_a_video";
        String videoId = MainActivity.extractVideoId(url);
        assertNull(videoId);
    }

    @Test
    public void noteResponseModel_gettersAndSettersWork() {
        NoteResponse note = new NoteResponse(1, "stud_1", "Title", "Content", "2026-09-24T10:00:00", "2026-09-24T10:05:00");
        assertEquals(1, note.getId());
        assertEquals("stud_1", note.getStudentId());
        assertEquals("Title", note.getTitle());
        assertEquals("Content", note.getContent());

        note.setTitle("New Title");
        note.setContent("New Content");
        assertEquals("New Title", note.getTitle());
        assertEquals("New Content", note.getContent());
    }
}
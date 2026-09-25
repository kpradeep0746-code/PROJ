package com.example.ailecturesummarizer.api;

import com.example.ailecturesummarizer.model.AnalyzeResponse;
import com.example.ailecturesummarizer.model.SummaryResponse;
import com.example.ailecturesummarizer.model.TimestampResponse;
import com.example.ailecturesummarizer.model.TranscriptResponse;
import com.example.ailecturesummarizer.model.UrlRequest;

import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.POST;

import com.example.ailecturesummarizer.model.ChatRequest;
import com.example.ailecturesummarizer.model.ChatResponse;
import com.example.ailecturesummarizer.model.TranslationRequest;
import com.example.ailecturesummarizer.model.TranslationResponse;
import com.example.ailecturesummarizer.model.NoteRequest;
import com.example.ailecturesummarizer.model.NoteResponse;
import com.example.ailecturesummarizer.model.NoteUpdateRequest;

import java.util.List;
import retrofit2.http.PUT;
import retrofit2.http.DELETE;
import retrofit2.http.Path;
import retrofit2.http.Query;

/**
 * Retrofit API interface matching all endpoints in backend/app.py
 * and ai_assistant/app.py.
 *
 * Base URL: http://<LAN_IP>:5000/  (set in RetrofitClient)
 * Base URL for AI: http://<LAN_IP>:8000/
 */

public interface ApiService {

    /** Health check — confirms the Flask server is running. */
    @GET("/")
    Call<Void> healthCheck();

    /**
     * POST /api/transcript
     * Body: { "url": "<youtube_url>" }
     * Response: { "success": bool, "video_id": str, "transcript": str }
     */
    @POST("api/transcript")
    Call<TranscriptResponse> getTranscript(@Body UrlRequest request);

    /**
     * POST /api/transcript/formatted  (on ai_assistant:8000)
     * Fetches raw transcript and uses the local LLM to reformat it into
     * well-structured Markdown with headings, paragraphs, and punctuation.
     * Body: { "url": "<youtube_url>" }
     * Response: { "success": bool, "video_id": str, "transcript": str, "warning": str }
     */
    @POST("api/transcript/formatted")
    Call<TranscriptResponse> getFormattedTranscript(@Body UrlRequest request);

    /**
     * POST /api/summary
     * Body: { "url": "<youtube_url>" }
     * Response: { "success": bool, "video_id": str, "summary": str }
     */
    @POST("api/summary")
    Call<SummaryResponse> getSummary(@Body UrlRequest request);

    /**
     * POST /api/timestamps
     * Body: { "url": "<youtube_url>" }
     * Response: { "success": bool, "video_id": str, "timestamps": [{"time": str, "topic": str}] }
     */
    @POST("api/timestamps")
    Call<TimestampResponse> getTimestamps(@Body UrlRequest request);

    /**
     * POST /api/analyze
     * Body: { "url": "<youtube_url>" }
     * Response: { "success": bool, "video_id": str, "summary": str,
     *             "timestamps": [...], "summary_error": str, "timestamps_error": str }
     */
    @POST("api/analyze")
    Call<AnalyzeResponse> getAnalyze(@Body UrlRequest request);

    /**
     * POST /api/translate
     * Body: { "transcript": str, "source_language": str, "target_language": str }
     * Response: { "success": bool, "translated_transcript": str }
     */
    @POST("api/translate")
    Call<TranslationResponse> translateTranscript(@Body TranslationRequest request);

    /**
     * POST /ask (on ai_assistant:8000)
     * Body: { "student_id": str, "lecture_id": str, "question": str }
     * Response: { "answer": str }
     */
    @POST("ask")
    Call<ChatResponse> ask(@Body ChatRequest request);

    /**
     * GET /api/notes
     * Query: student_id, q (optional)
     * Response: List<NoteResponse>
     */
    @GET("api/notes")
    Call<List<NoteResponse>> getNotes(
        @Query("student_id") String studentId,
        @Query("q") String searchQuery
    );

    /**
     * POST /api/notes
     * Body: NoteRequest
     * Response: NoteResponse
     */
    @POST("api/notes")
    Call<NoteResponse> createNote(@Body NoteRequest request);

    /**
     * PUT /api/notes/{note_id}
     * Path: note_id
     * Body: NoteUpdateRequest
     * Response: NoteResponse
     */
    @PUT("api/notes/{note_id}")
    Call<NoteResponse> updateNote(
        @Path("note_id") int noteId,
        @Body NoteUpdateRequest request
    );

    /**
     * DELETE /api/notes/{note_id}
     * Path: note_id
     * Response: Void
     */
    @DELETE("api/notes/{note_id}")
    Call<Void> deleteNote(@Path("note_id") int noteId);
}
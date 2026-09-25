package com.example.ailecturesummarizer;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.TextUtils;
import android.text.TextWatcher;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.ailecturesummarizer.adapter.NotesAdapter;
import com.example.ailecturesummarizer.api.RetrofitClient;
import com.example.ailecturesummarizer.model.NoteRequest;
import com.example.ailecturesummarizer.model.NoteResponse;
import com.example.ailecturesummarizer.model.NoteUpdateRequest;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.android.material.floatingactionbutton.FloatingActionButton;

import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

/**
 * NotesActivity — Manages the personal learning notes of a student.
 */
public class NotesActivity extends AppCompatActivity implements NotesAdapter.OnNoteActionListener {

    private Toolbar notesToolbar;
    private EditText etNotesSearch;
    private RecyclerView rvNotes;
    private LinearLayout llNotesEmptyState;
    private FloatingActionButton fabAddNote;

    private NotesAdapter notesAdapter;
    private String studentId = "student_user";

    private final Handler searchHandler = new Handler(Looper.getMainLooper());
    private Runnable searchRunnable;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_notes);

        // Fetch user session email
        SharedPreferences prefs = getSharedPreferences("noa_session", Context.MODE_PRIVATE);
        studentId = prefs.getString("user_email", "student_user");

        bindViews();
        setupToolbar();
        setupRecyclerView();
        setupSearch();

        fabAddNote.setOnClickListener(v -> showNoteEditorDialog(null));

        // Load notes initially
        loadNotes("");
    }

    private void bindViews() {
        notesToolbar = findViewById(R.id.notesToolbar);
        etNotesSearch = findViewById(R.id.etNotesSearch);
        rvNotes = findViewById(R.id.rvNotes);
        llNotesEmptyState = findViewById(R.id.llNotesEmptyState);
        fabAddNote = findViewById(R.id.fabAddNote);
    }

    private void setupToolbar() {
        setSupportActionBar(notesToolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle("Personal Notes");
        }
        notesToolbar.setNavigationOnClickListener(v -> finish());
    }

    private void setupRecyclerView() {
        notesAdapter = new NotesAdapter();
        notesAdapter.setOnNoteActionListener(this);
        rvNotes.setLayoutManager(new LinearLayoutManager(this));
        rvNotes.setAdapter(notesAdapter);
    }

    private void setupSearch() {
        etNotesSearch.addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {}

            @Override
            public void afterTextChanged(Editable s) {
                // Debounce search input to avoid hitting backend API on every character immediately
                if (searchRunnable != null) {
                    searchHandler.removeCallbacks(searchRunnable);
                }
                searchRunnable = () -> loadNotes(s.toString().trim());
                searchHandler.postDelayed(searchRunnable, 300);
            }
        });
    }

    private void loadNotes(String query) {
        RetrofitClient.getAiApiService().getNotes(studentId, query).enqueue(new Callback<List<NoteResponse>>() {
            @Override
            public void onResponse(@NonNull Call<List<NoteResponse>> call, @NonNull Response<List<NoteResponse>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    List<NoteResponse> notes = response.body();
                    notesAdapter.setNotes(notes);
                    if (notes.isEmpty()) {
                        llNotesEmptyState.setVisibility(View.VISIBLE);
                        rvNotes.setVisibility(View.GONE);
                    } else {
                        llNotesEmptyState.setVisibility(View.GONE);
                        rvNotes.setVisibility(View.VISIBLE);
                    }
                } else {
                    Toast.makeText(NotesActivity.this, "Failed to load notes (HTTP " + response.code() + ")", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(@NonNull Call<List<NoteResponse>> call, @NonNull Throwable t) {
                Toast.makeText(NotesActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void showNoteEditorDialog(final NoteResponse existingNote) {
        View dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_note, null);
        TextView tvTitle = dialogView.findViewById(R.id.tvDialogTitle);
        final EditText etTitle = dialogView.findViewById(R.id.etDialogNoteTitle);
        final EditText etContent = dialogView.findViewById(R.id.etDialogNoteContent);

        if (existingNote != null) {
            tvTitle.setText("Edit Note");
            etTitle.setText(existingNote.getTitle());
            etContent.setText(existingNote.getContent());
        } else {
            tvTitle.setText("New Note");
        }

        new MaterialAlertDialogBuilder(this)
                .setView(dialogView)
                .setPositiveButton("Save", (dialog, which) -> {
                    String title = etTitle.getText().toString().trim();
                    String content = etContent.getText().toString().trim();

                    if (TextUtils.isEmpty(title) || TextUtils.isEmpty(content)) {
                        Toast.makeText(NotesActivity.this, "Title and content cannot be empty", Toast.LENGTH_SHORT).show();
                        return;
                    }

                    if (existingNote != null) {
                        performUpdateNote(existingNote.getId(), title, content);
                    } else {
                        performCreateNote(title, content);
                    }
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void performCreateNote(String title, String content) {
        NoteRequest request = new NoteRequest(studentId, title, content);
        RetrofitClient.getAiApiService().createNote(request).enqueue(new Callback<NoteResponse>() {
            @Override
            public void onResponse(@NonNull Call<NoteResponse> call, @NonNull Response<NoteResponse> response) {
                if (response.isSuccessful()) {
                    Toast.makeText(NotesActivity.this, "Note saved", Toast.LENGTH_SHORT).show();
                    loadNotes(etNotesSearch.getText().toString().trim());
                } else {
                    Toast.makeText(NotesActivity.this, "Failed to create note", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(@NonNull Call<NoteResponse> call, @NonNull Throwable t) {
                Toast.makeText(NotesActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void performUpdateNote(int noteId, String title, String content) {
        NoteUpdateRequest request = new NoteUpdateRequest(title, content);
        RetrofitClient.getAiApiService().updateNote(noteId, request).enqueue(new Callback<NoteResponse>() {
            @Override
            public void onResponse(@NonNull Call<NoteResponse> call, @NonNull Response<NoteResponse> response) {
                if (response.isSuccessful()) {
                    Toast.makeText(NotesActivity.this, "Note updated", Toast.LENGTH_SHORT).show();
                    loadNotes(etNotesSearch.getText().toString().trim());
                } else {
                    Toast.makeText(NotesActivity.this, "Failed to update note", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(@NonNull Call<NoteResponse> call, @NonNull Throwable t) {
                Toast.makeText(NotesActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    public void onEditNote(NoteResponse note) {
        showNoteEditorDialog(note);
    }

    @Override
    public void onDeleteNote(final NoteResponse note) {
        new MaterialAlertDialogBuilder(this)
                .setTitle("Delete Note")
                .setMessage("Are you sure you want to delete this note?")
                .setPositiveButton("Delete", (dialog, which) -> performDeleteNote(note.getId()))
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void performDeleteNote(int noteId) {
        RetrofitClient.getAiApiService().deleteNote(noteId).enqueue(new Callback<Void>() {
            @Override
            public void onResponse(@NonNull Call<Void> call, @NonNull Response<Void> response) {
                if (response.isSuccessful()) {
                    Toast.makeText(NotesActivity.this, "Note deleted", Toast.LENGTH_SHORT).show();
                    loadNotes(etNotesSearch.getText().toString().trim());
                } else {
                    Toast.makeText(NotesActivity.this, "Failed to delete note", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(@NonNull Call<Void> call, @NonNull Throwable t) {
                Toast.makeText(NotesActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
}

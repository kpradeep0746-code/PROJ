package com.example.ailecturesummarizer.adapter;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageButton;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.ailecturesummarizer.R;
import com.example.ailecturesummarizer.model.NoteResponse;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

/**
 * Adapter to display {@link NoteResponse} objects in a RecyclerView.
 */
public class NotesAdapter extends RecyclerView.Adapter<NotesAdapter.NoteViewHolder> {

    private final List<NoteResponse> notesList = new ArrayList<>();
    private OnNoteActionListener actionListener;

    public interface OnNoteActionListener {
        void onEditNote(NoteResponse note);
        void onDeleteNote(NoteResponse note);
    }

    public void setOnNoteActionListener(OnNoteActionListener actionListener) {
        this.actionListener = actionListener;
    }

    public void setNotes(List<NoteResponse> newNotes) {
        notesList.clear();
        if (newNotes != null) {
            notesList.addAll(newNotes);
        }
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public NoteViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_note, parent, false);
        return new NoteViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull NoteViewHolder holder, int position) {
        holder.bind(notesList.get(position));
    }

    @Override
    public int getItemCount() {
        return notesList.size();
    }

    class NoteViewHolder extends RecyclerView.ViewHolder {
        private final TextView tvTitle;
        private final TextView tvContent;
        private final TextView tvDate;
        private final ImageButton btnEdit;
        private final ImageButton btnDelete;

        NoteViewHolder(@NonNull View itemView) {
            super(itemView);
            tvTitle = itemView.findViewById(R.id.tvNoteTitle);
            tvContent = itemView.findViewById(R.id.tvNoteContent);
            tvDate = itemView.findViewById(R.id.tvNoteDate);
            btnEdit = itemView.findViewById(R.id.btnEditNote);
            btnDelete = itemView.findViewById(R.id.btnDeleteNote);

            btnEdit.setOnClickListener(v -> {
                int pos = getAdapterPosition();
                if (actionListener != null && pos != RecyclerView.NO_POSITION) {
                    actionListener.onEditNote(notesList.get(pos));
                }
            });

            btnDelete.setOnClickListener(v -> {
                int pos = getAdapterPosition();
                if (actionListener != null && pos != RecyclerView.NO_POSITION) {
                    actionListener.onDeleteNote(notesList.get(pos));
                }
            });
        }

        void bind(NoteResponse note) {
            tvTitle.setText(note.getTitle());
            tvContent.setText(note.getContent());

            String displayDate = formatIsoDate(note.getUpdatedAt());
            if (displayDate.isEmpty()) {
                displayDate = formatIsoDate(note.getCreatedAt());
            }
            tvDate.setText("Updated: " + displayDate);
        }

        private String formatIsoDate(String isoString) {
            if (isoString == null || isoString.trim().isEmpty()) {
                return "";
            }
            try {
                // Remove nanosecond/fractional part if present for parsing compatibility
                String parsedIso = isoString;
                if (isoString.contains(".")) {
                    parsedIso = isoString.split("\\.")[0];
                }
                SimpleDateFormat isoFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US);
                isoFormat.setTimeZone(TimeZone.getTimeZone("UTC"));
                Date date = isoFormat.parse(parsedIso);
                if (date != null) {
                    SimpleDateFormat displayFormat = new SimpleDateFormat("MMM dd, yyyy, hh:mm a", Locale.getDefault());
                    return displayFormat.format(date);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
            return isoString; // fallback to raw string if parsing fails
        }
    }
}

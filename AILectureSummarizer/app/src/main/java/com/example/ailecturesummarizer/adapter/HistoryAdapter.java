package com.example.ailecturesummarizer.adapter;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.example.ailecturesummarizer.R;
import com.example.ailecturesummarizer.model.HistoryItem;

import java.util.ArrayList;
import java.util.List;

/**
 * Adapter to display a list of {@link HistoryItem} objects in a {@link RecyclerView}.
 * Uses the item_history.xml layout for each row.
 */
public class HistoryAdapter extends RecyclerView.Adapter<HistoryAdapter.HistoryViewHolder> {

    private final List<HistoryItem> items = new ArrayList<>();
    private OnItemClickListener listener;

    public interface OnItemClickListener {
        void onItemClick(HistoryItem item);
    }

    public void setOnItemClickListener(OnItemClickListener listener) {
        this.listener = listener;
    }

    /**
     * Add a new history entry and scroll/notify at top.
     */
    public void addItem(HistoryItem item) {
        items.add(0, item);
        notifyItemInserted(0);
    }

    public void setItems(List<HistoryItem> newItems) {
        items.clear();
        if (newItems != null) {
            items.addAll(newItems);
        }
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public HistoryViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_history, parent, false);
        return new HistoryViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull HistoryViewHolder holder, int position) {
        holder.bind(items.get(position));
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    class HistoryViewHolder extends RecyclerView.ViewHolder {
        private final TextView tvTitle;
        private final TextView tvUrl;

        HistoryViewHolder(@NonNull View itemView) {
            super(itemView);
            tvTitle = itemView.findViewById(R.id.tvHistoryTitle);
            tvUrl = itemView.findViewById(R.id.tvHistoryUrl);
            itemView.setOnClickListener(v -> {
                int pos = getAdapterPosition();
                if (listener != null && pos != RecyclerView.NO_POSITION) {
                    listener.onItemClick(items.get(pos));
                }
            });
        }

        void bind(HistoryItem item) {
            tvTitle.setText(item.getTitle());
            tvUrl.setText(item.getUrl());
        }
    }
}

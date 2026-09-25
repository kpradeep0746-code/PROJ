package com.example.ailecturesummarizer;

import android.app.Dialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.TextUtils;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.InputMethodManager;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.example.ailecturesummarizer.adapter.ChatAdapter;
import com.example.ailecturesummarizer.api.RetrofitClient;
import com.example.ailecturesummarizer.model.ChatMessage;
import com.example.ailecturesummarizer.model.ChatRequest;
import com.example.ailecturesummarizer.model.ChatResponse;
import com.google.android.material.bottomsheet.BottomSheetBehavior;
import com.google.android.material.bottomsheet.BottomSheetDialog;
import com.google.android.material.bottomsheet.BottomSheetDialogFragment;
import com.google.android.material.textfield.TextInputEditText;
import com.google.gson.Gson;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import okhttp3.ResponseBody;
import okio.BufferedSource;

/**
 * ChatBottomSheetFragment — A premium bottom sheet dialog for video-aware AI chatbot conversations.
 * Supports token-by-token streaming (SSE) from the FastAPI backend.
 */
public class ChatBottomSheetFragment extends BottomSheetDialogFragment {

    private static final String TAG = "ChatBottomSheetFragment";
    private static final String ARG_VIDEO_URL   = "video_url";
    private static final String ARG_VIDEO_TITLE = "video_title";

    private RecyclerView      rvChatMessages;
    private TextInputEditText etChatMessage;
    private ImageButton       btnSend;
    private TextView          tvChatSubtitle;

    private ChatAdapter chatAdapter;
    private String      videoUrl   = "";
    private String      videoTitle = "";
    private String      studentId  = "student_user";

    private OkHttpClient activeOkHttpClient;
    private Call         currentStreamCall;
    private boolean      isStreaming = false;

    // Track list of messages in memory to manage state dynamically
    private final List<ChatMessage> chatMessagesList = new ArrayList<>();

    public static ChatBottomSheetFragment newInstance(String videoUrl, String videoTitle) {
        ChatBottomSheetFragment fragment = new ChatBottomSheetFragment();
        Bundle args = new Bundle();
        args.putString(ARG_VIDEO_URL, videoUrl);
        args.putString(ARG_VIDEO_TITLE, videoTitle);
        fragment.setArguments(args);
        return fragment;
    }

    @Override
    public void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // Clean, rounded style defined in material components
        setStyle(STYLE_NORMAL, com.google.android.material.R.style.Theme_Design_Light_BottomSheetDialog);

        if (getArguments() != null) {
            videoUrl   = getArguments().getString(ARG_VIDEO_URL, "");
            videoTitle = getArguments().getString(ARG_VIDEO_TITLE, "");
        }

        // Get user session email to act as student_id
        SharedPreferences prefs = requireContext().getSharedPreferences("noa_session", Context.MODE_PRIVATE);
        studentId = prefs.getString("user_email", "student_user");

        // Single client instance configured for infinite read timeout (suitable for SSE streams)
        activeOkHttpClient = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(0, TimeUnit.MILLISECONDS) // 0 means infinite timeout (crucial for SSE streams)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build();
    }

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.dialog_chat_bottom_sheet, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        rvChatMessages = view.findViewById(R.id.rvChatMessages);
        etChatMessage  = view.findViewById(R.id.etChatMessage);
        btnSend        = view.findViewById(R.id.btnSendChatMessage);
        tvChatSubtitle = view.findViewById(R.id.tvChatSubtitle);

        if (!TextUtils.isEmpty(videoTitle)) {
            tvChatSubtitle.setText(videoTitle);
        } else {
            tvChatSubtitle.setText("Ask questions about this video");
        }

        // Setup Chat List
        chatAdapter = new ChatAdapter();
        LinearLayoutManager llm = new LinearLayoutManager(requireContext());
        llm.setStackFromEnd(true);
        rvChatMessages.setLayoutManager(llm);
        rvChatMessages.setAdapter(chatAdapter);

        // Add welcome message if empty
        if (chatMessagesList.isEmpty()) {
            addMessageToView("Hello! I am your AI study assistant. Ask me anything about this lecture video, and I'll answer based on its transcript.", ChatMessage.TYPE_BOT);
        } else {
            chatAdapter.setMessages(chatMessagesList);
        }

        btnSend.setOnClickListener(v -> handleSendMessage());

        // Bind prompt chips
        View chipSummary = view.findViewById(R.id.chipPromptSummary);
        View chipKey = view.findViewById(R.id.chipPromptKeyTakeaways);
        View chipExam = view.findViewById(R.id.chipPromptExamPrep);

        if (chipSummary != null) {
            chipSummary.setOnClickListener(v -> {
                etChatMessage.setText("Can you summarize the core concept of this lecture?");
                handleSendMessage();
            });
        }
        if (chipKey != null) {
            chipKey.setOnClickListener(v -> {
                etChatMessage.setText("What are the key takeaways from this lecture?");
                handleSendMessage();
            });
        }
        if (chipExam != null) {
            chipExam.setOnClickListener(v -> {
                etChatMessage.setText("Generate 3 practice exam questions based on this video.");
                handleSendMessage();
            });
        }

    }

    @Override
    public void onStart() {
        super.onStart();
        // Force fully expanded bottom sheet state by default
        Dialog dialog = getDialog();
        if (dialog instanceof BottomSheetDialog) {
            View bottomSheet = ((BottomSheetDialog) dialog).findViewById(com.google.android.material.R.id.design_bottom_sheet);
            if (bottomSheet != null) {
                BottomSheetBehavior<View> behavior = BottomSheetBehavior.from(bottomSheet);
                behavior.setState(BottomSheetBehavior.STATE_EXPANDED);
                behavior.setSkipCollapsed(true);
            }
        }
    }

    private void handleSendMessage() {
        if (isStreaming) {
            Toast.makeText(requireContext(), "Streaming answer in progress...", Toast.LENGTH_SHORT).show();
            return;
        }

        String question = etChatMessage.getText() != null ? etChatMessage.getText().toString().trim() : "";
        if (TextUtils.isEmpty(question)) {
            return;
        }

        if (TextUtils.isEmpty(videoUrl)) {
            Toast.makeText(requireContext(), "Error: No video context loaded.", Toast.LENGTH_LONG).show();
            return;
        }

        // 1. Add user message
        addMessageToView(question, ChatMessage.TYPE_USER);
        etChatMessage.setText("");
        scrollToBottom();

        // Hide keyboard
        View focusView = etChatMessage.findFocus();
        if (focusView != null) {
            InputMethodManager imm = (InputMethodManager) requireContext().getSystemService(Context.INPUT_METHOD_SERVICE);
            imm.hideSoftInputFromWindow(focusView.getWindowToken(), 0);
        }

        // 2. Add temporary bot "Thinking..." placeholder
        addMessageToView("Thinking...", ChatMessage.TYPE_BOT);
        scrollToBottom();

        // 3. Initiate SSE stream call
        startStreamingQuery(question);
    }

    private void startStreamingQuery(String question) {
        isStreaming = true;
        btnSend.setEnabled(false);

        // Resolve assistant base url from main base url (replace :5000/ with :8000/)
        String mainBaseUrl = RetrofitClient.getBaseUrl();
        String aiBaseUrl = mainBaseUrl.replace(":5000/", ":8000/");
        String sseUrl = aiBaseUrl + "ask/stream";

        // Create ChatRequest JSON body
        ChatRequest chatRequest = new ChatRequest(studentId, videoUrl, question);
        String jsonPayload = new Gson().toJson(chatRequest);
        RequestBody body = RequestBody.create(jsonPayload, MediaType.parse("application/json; charset=utf-8"));

        Request request = new Request.Builder()
                .url(sseUrl)
                .post(body)
                .header("Accept", "text/event-stream")
                .header("Cache-Control", "no-cache")
                .header("Connection", "keep-alive")
                .build();

        currentStreamCall = activeOkHttpClient.newCall(request);
        currentStreamCall.enqueue(new Callback() {
            @Override
            public void onFailure(@NonNull Call call, @NonNull IOException e) {
                if (call.isCanceled()) return;
                Log.e(TAG, "SSE call failed: " + e.getMessage(), e);
                isStreaming = false;
                runOnMainThread(() -> {
                    btnSend.setEnabled(true);
                    updateLastBotMessage("Error contacting AI Assistant. Please ensure it is running on port 8000.");
                    scrollToBottom();
                });
            }

            @Override
            public void onResponse(@NonNull Call call, @NonNull Response response) throws IOException {
                if (call.isCanceled()) return;

                if (!response.isSuccessful()) {
                    isStreaming = false;
                    ResponseBody errBody = response.body();
                    String errMsg = errBody != null ? errBody.string() : "Unknown API error";
                    Log.e(TAG, "SSE failed with code " + response.code() + ": " + errMsg);
                    runOnMainThread(() -> {
                        btnSend.setEnabled(true);
                        updateLastBotMessage("Error from server: " + response.code() + " - " + errMsg);
                        scrollToBottom();
                    });
                    return;
                }

                ResponseBody responseBody = response.body();
                if (responseBody == null) {
                    isStreaming = false;
                    runOnMainThread(() -> {
                        btnSend.setEnabled(true);
                        updateLastBotMessage("Error: Received empty response from AI Assistant.");
                        scrollToBottom();
                    });
                    return;
                }

                BufferedSource source = responseBody.source();
                final StringBuilder fullAnswer = new StringBuilder();
                boolean firstTokenReceived = false;

                try {
                    String line;
                    while (!call.isCanceled() && (line = source.readUtf8Line()) != null) {
                        String trimmed = line.trim();
                        if (trimmed.startsWith("data:")) {
                            String token = trimmed.substring(5); // extract token string
                            
                            // sse-starlette and fastapi send data package
                            if (!TextUtils.isEmpty(token)) {
                                fullAnswer.append(token);
                                
                                final boolean isFirst = !firstTokenReceived;
                                firstTokenReceived = true;
                                final String currentText = fullAnswer.toString();
                                
                                runOnMainThread(() -> {
                                    if (isFirst) {
                                        // Replace "Thinking..." placeholder with the first token
                                        updateLastBotMessage(currentText);
                                    } else {
                                        // Stream next tokens
                                        updateLastBotMessage(currentText);
                                    }
                                    scrollToBottom();
                                });
                            }
                        }
                    }
                } catch (Exception ex) {
                    Log.e(TAG, "Exception reading SSE source: " + ex.getMessage(), ex);
                } finally {
                    isStreaming = false;
                    responseBody.close();
                    runOnMainThread(() -> {
                        btnSend.setEnabled(true);
                        // Save the final completed message in memory
                        if (chatMessagesList.size() > 0) {
                            ChatMessage lastMsg = chatMessagesList.get(chatMessagesList.size() - 1);
                            if (lastMsg.getType() == ChatMessage.TYPE_BOT) {
                                chatMessagesList.set(chatMessagesList.size() - 1, new ChatMessage(fullAnswer.toString(), ChatMessage.TYPE_BOT));
                            }
                        }
                    });
                }
            }
        });
    }

    private void addMessageToView(String message, int type) {
        ChatMessage chatMsg = new ChatMessage(message, type);
        chatMessagesList.add(chatMsg);
        chatAdapter.addMessage(chatMsg);
    }

    private void updateLastBotMessage(String message) {
        if (!chatMessagesList.isEmpty()) {
            int lastIndex = chatMessagesList.size() - 1;
            ChatMessage lastMsg = chatMessagesList.get(lastIndex);
            if (lastMsg.getType() == ChatMessage.TYPE_BOT) {
                ChatMessage updatedMsg = new ChatMessage(message, ChatMessage.TYPE_BOT);
                chatMessagesList.set(lastIndex, updatedMsg);
                chatAdapter.setMessages(chatMessagesList);
            }
        }
    }

    private void scrollToBottom() {
        if (chatAdapter.getItemCount() > 0) {
            rvChatMessages.scrollToPosition(chatAdapter.getItemCount() - 1);
        }
    }

    private void runOnMainThread(Runnable action) {
        if (isAdded() && getActivity() != null) {
            getActivity().runOnUiThread(action);
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (currentStreamCall != null) {
            currentStreamCall.cancel();
        }
    }
}

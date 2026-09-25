/**
 * NOA AI — Lecture Studio & AI Assistant Controller (Phase 2)
 * Features: Video Embed, Formatted Transcript, Summaries, Timestamps,
 * Personal Notes CRUD, Translation, SSE AI Chat, File Exports (.md, .txt, PDF),
 * Text-to-Speech Audio Reader, Lecture Analytics, and Keyboard Shortcuts.
 */

document.addEventListener("DOMContentLoaded", () => {
    
    // ============================================================
    // APP STATE & STORAGE KEYS
    // ============================================================
    const STORAGE_KEYS = {
        theme: "noa_ai_theme",
        studentId: "noa_ai_student_id",
        backendUrl: "noa_ai_backend_url",
        chatHistory: "noa_ai_chat_history"
    };

    const state = {
        theme: localStorage.getItem(STORAGE_KEYS.theme) || "dark",
        studentId: localStorage.getItem(STORAGE_KEYS.studentId) || `student_${Math.floor(1000 + Math.random() * 9000)}`,
        backendUrl: localStorage.getItem(STORAGE_KEYS.backendUrl) || "http://localhost:8000",
        flaskUrl: "http://localhost:5000",
        currentUrl: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        currentVideoId: "dQw4w9WgXcQ",
        activeTab: "summary",
        transcriptText: "",
        summaryText: "",
        timestampsData: [],
        notesData: [],
        speechUtterance: null,
        isSpeaking: false
    };

    // ============================================================
    // DOM ELEMENTS INITIALIZATION
    // ============================================================
    const themeToggleBtn = document.getElementById("theme-toggle");
    const settingsToggleBtn = document.getElementById("settings-toggle");
    const shortcutsToggleBtn = document.getElementById("shortcuts-toggle");
    const settingsDrawer = document.getElementById("settings-drawer");
    const closeDrawerBtn = document.getElementById("close-drawer");
    const shortcutsModal = document.getElementById("shortcuts-modal");
    const closeShortcutsModalBtn = document.getElementById("close-shortcuts-modal");

    const studentIdInput = document.getElementById("student-id-input");
    const backendUrlSelect = document.getElementById("backend-url-select");

    const youtubeUrlInput = document.getElementById("youtube-url-input");
    const pasteBtn = document.getElementById("paste-btn");
    const processBtn = document.getElementById("process-btn");
    const videoIframe = document.getElementById("video-iframe");
    const sampleChips = document.querySelectorAll(".sample-chip");

    // Lecture Stats Bar Elements
    const analyticsBar = document.getElementById("analytics-bar");
    const statWords = document.getElementById("stat-words");
    const statTime = document.getElementById("stat-time");
    const statConcepts = document.getElementById("stat-concepts");

    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanels = document.querySelectorAll(".tab-panel");

    // Summary Elements
    const summaryContent = document.getElementById("summary-content");
    const copySummaryBtn = document.getElementById("copy-summary-btn");
    const refreshSummaryBtn = document.getElementById("refresh-summary-btn");
    const exportSummaryMd = document.getElementById("export-summary-md");
    const exportSummaryTxt = document.getElementById("export-summary-txt");
    const printSummaryPdf = document.getElementById("print-summary-pdf");

    // TTS Reader Elements
    const ttsPlayBtn = document.getElementById("tts-play-btn");
    const ttsIcon = document.getElementById("tts-icon");
    const ttsLabel = document.getElementById("tts-label");
    const ttsStatus = document.getElementById("tts-status");
    const ttsSpeedSelect = document.getElementById("tts-speed-select");

    // Transcript Elements
    const transcriptContent = document.getElementById("transcript-content");
    const transcriptSearchInput = document.getElementById("transcript-search-input");
    const copyTranscriptBtn = document.getElementById("copy-transcript-btn");
    const fetchTranscriptBtn = document.getElementById("fetch-transcript-btn");
    const exportTranscriptMd = document.getElementById("export-transcript-md");
    const exportTranscriptTxt = document.getElementById("export-transcript-txt");
    const printTranscriptPdf = document.getElementById("print-transcript-pdf");

    // Timestamps Elements
    const timestampsContent = document.getElementById("timestamps-content");
    const refreshTimestampsBtn = document.getElementById("refresh-timestamps-btn");

    // Notes Elements
    const newNoteBtn = document.getElementById("new-note-btn");
    const noteEditorCard = document.getElementById("note-editor-card");
    const editorHeading = document.getElementById("editor-heading");
    const noteEditId = document.getElementById("note-edit-id");
    const noteTitleInput = document.getElementById("note-title-input");
    const noteContentInput = document.getElementById("note-content-input");
    const cancelNoteBtn = document.getElementById("cancel-note-btn");
    const saveNoteBtn = document.getElementById("save-note-btn");
    const notesSearchInput = document.getElementById("notes-search-input");
    const notesListContainer = document.getElementById("notes-list-container");

    // Translate Elements
    const targetLangSelect = document.getElementById("target-lang-select");
    const translateActionBtn = document.getElementById("translate-action-btn");
    const translateContent = document.getElementById("translate-content");

    // Chat Assistant Elements
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const sendChatBtn = document.getElementById("send-chat-btn");
    const clearChatBtn = document.getElementById("clear-chat-btn");
    const promptChips = document.querySelectorAll(".prompt-chip");

    // ============================================================
    // THEME & MODALS CONTROLLER
    // ============================================================
    document.documentElement.setAttribute("data-theme", state.theme);
    updateThemeIcon();

    studentIdInput.value = state.studentId;
    backendUrlSelect.value = state.backendUrl;

    themeToggleBtn.addEventListener("click", () => {
        state.theme = state.theme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", state.theme);
        localStorage.setItem(STORAGE_KEYS.theme, state.theme);
        updateThemeIcon();
        showToast(`Switched to ${state.theme} mode`, "info");
    });

    function updateThemeIcon() {
        const icon = themeToggleBtn.querySelector("span");
        icon.textContent = state.theme === "dark" ? "light_mode" : "dark_mode";
    }

    settingsToggleBtn.addEventListener("click", () => {
        settingsDrawer.classList.toggle("hidden");
    });

    closeDrawerBtn.addEventListener("click", () => {
        settingsDrawer.classList.add("hidden");
    });

    shortcutsToggleBtn.addEventListener("click", () => {
        shortcutsModal.classList.remove("hidden");
    });

    closeShortcutsModalBtn.addEventListener("click", () => {
        shortcutsModal.classList.add("hidden");
    });

    // Close Modals on Backdrop Click
    shortcutsModal.addEventListener("click", (e) => {
        if (e.target === shortcutsModal) shortcutsModal.classList.add("hidden");
    });

    studentIdInput.addEventListener("change", (e) => {
        state.studentId = e.target.value.trim() || "anonymous";
        localStorage.setItem(STORAGE_KEYS.studentId, state.studentId);
        loadNotes();
    });

    backendUrlSelect.addEventListener("change", (e) => {
        state.backendUrl = e.target.value;
        localStorage.setItem(STORAGE_KEYS.backendUrl, state.backendUrl);
    });

    // ============================================================
    // TOAST NOTIFICATIONS SYSTEM
    // ============================================================
    function showToast(message, type = "info") {
        const toastContainer = document.getElementById("toast-container");
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        const icon = type === "error" ? "error" : type === "success" ? "check_circle" : "info";
        toast.innerHTML = `<span class="material-symbols-outlined">${icon}</span><span>${message}</span>`;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = "0";
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // ============================================================
    // YOUTUBE VIDEO & LECTURE ENGINE
    // ============================================================
    function extractVideoId(url) {
        if (!url) return null;
        const trimmed = url.trim();
        if (/^[a-zA-Z0-9_-]{11}$/.test(trimmed)) return trimmed;
        const match = trimmed.match(/(?:watch\?v=|youtu\.be\/|embed\/|shorts\/)([a-zA-Z0-9_-]{11})/);
        return match ? match[1] : null;
    }

    function loadVideo(url) {
        const videoId = extractVideoId(url);
        if (!videoId) {
            showToast("Invalid YouTube URL. Please enter a valid link.", "error");
            return false;
        }
        state.currentUrl = url;
        state.currentVideoId = videoId;
        videoIframe.src = `https://www.youtube.com/embed/${videoId}?enablejsapi=1`;
        return true;
    }

    pasteBtn.addEventListener("click", async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                youtubeUrlInput.value = text;
                showToast("URL pasted from clipboard", "info");
            }
        } catch (e) {
            showToast("Clipboard access denied", "error");
        }
    });

    sampleChips.forEach(chip => {
        chip.addEventListener("click", () => {
            const sampleUrl = chip.dataset.url;
            youtubeUrlInput.value = sampleUrl;
            processLecture();
        });
    });

    processBtn.addEventListener("click", processLecture);

    function processLecture() {
        const url = youtubeUrlInput.value.trim();
        if (loadVideo(url)) {
            showToast("Processing video lecture...", "info");
            loadSummary();
            loadTranscript();
            loadTimestamps();
            loadNotes();
        }
    }

    // ============================================================
    // TAB NAVIGATION CONTROLLER
    // ============================================================
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.dataset.tab;
            switchTab(targetTab);
        });
    });

    function switchTab(tabName) {
        tabBtns.forEach(b => {
            b.classList.toggle("active", b.dataset.tab === tabName);
        });
        tabPanels.forEach(p => {
            p.classList.toggle("active", p.id === `panel-${tabName}`);
        });
        state.activeTab = tabName;
    }

    // ============================================================
    // MARKDOWN PARSER UTILITY
    // ============================================================
    function parseMarkdown(text) {
        if (!text) return "";
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        html = html.replace(/```([\s\S]*?)```/g, (m, code) => `<pre><code>${code.trim()}</code></pre>`);
        html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
        html = html.replace(/^### (.*?)$/gm, "<h3>$1</h3>");
        html = html.replace(/^## (.*?)$/gm, "<h2>$1</h2>");
        html = html.replace(/^# (.*?)$/gm, "<h1>$1</h1>");
        html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
        html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
        html = html.replace(/^\s*[-*]\s+(.*?)$/gm, "<li>$1</li>");
        html = html.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>");
        html = html.replace(/\n\n/g, "</p><p>");
        html = html.replace(/\n/g, "<br>");
        return `<p>${html}</p>`;
    }

    // ============================================================
    // LECTURE ANALYTICS CALCULATOR
    // ============================================================
    function updateAnalytics(text) {
        if (!text) {
            analyticsBar.classList.add("hidden");
            return;
        }

        analyticsBar.classList.remove("hidden");

        // Calculate Word Count
        const words = text.trim().split(/\s+/).filter(w => w.length > 0);
        const wordCount = words.length;
        statWords.textContent = wordCount.toLocaleString();

        // Calculate Est. Reading Time (200 words/min)
        const readTime = Math.max(1, Math.ceil(wordCount / 200));
        statTime.textContent = `${readTime} min`;

        // Extract Key Concepts (Capitalized words > 4 chars)
        const conceptMap = {};
        words.forEach(w => {
            const clean = w.replace(/[^a-zA-Z]/g, "");
            if (clean.length >= 5 && /^[A-Z]/.test(clean) && !["Verse", "Chorus", "Pre-Chorus", "Introduction", "Summary", "Transcript"].includes(clean)) {
                conceptMap[clean] = (conceptMap[clean] || 0) + 1;
            }
        });

        const topConcepts = Object.keys(conceptMap)
            .sort((a, b) => conceptMap[b] - conceptMap[a])
            .slice(0, 4);

        statConcepts.innerHTML = "";
        if (topConcepts.length > 0) {
            topConcepts.forEach(c => {
                const tag = document.createElement("span");
                tag.className = "concept-tag";
                tag.textContent = c;
                statConcepts.appendChild(tag);
            });
        } else {
            statConcepts.innerHTML = `<span class="concept-tag">General</span>`;
        }
    }

    // ============================================================
    // EXPORT UTILITIES (.md, .txt, PDF)
    // ============================================================
    function downloadFile(filename, content, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // Summary Exports
    exportSummaryMd.addEventListener("click", () => {
        if (!state.summaryText) return showToast("No summary to export", "error");
        downloadFile(`summary_${state.currentVideoId}.md`, state.summaryText, "text/markdown");
        showToast("Summary exported as Markdown!", "success");
    });

    exportSummaryTxt.addEventListener("click", () => {
        if (!state.summaryText) return showToast("No summary to export", "error");
        downloadFile(`summary_${state.currentVideoId}.txt`, state.summaryText, "text/plain");
        showToast("Summary exported as Text!", "success");
    });

    printSummaryPdf.addEventListener("click", () => {
        if (!state.summaryText) return showToast("No summary to print", "error");
        window.print();
    });

    // Transcript Exports
    exportTranscriptMd.addEventListener("click", () => {
        if (!state.transcriptText) return showToast("No transcript to export", "error");
        downloadFile(`transcript_${state.currentVideoId}.md`, state.transcriptText, "text/markdown");
        showToast("Transcript exported as Markdown!", "success");
    });

    exportTranscriptTxt.addEventListener("click", () => {
        if (!state.transcriptText) return showToast("No transcript to export", "error");
        downloadFile(`transcript_${state.currentVideoId}.txt`, state.transcriptText, "text/plain");
        showToast("Transcript exported as Text!", "success");
    });

    printTranscriptPdf.addEventListener("click", () => {
        if (!state.transcriptText) return showToast("No transcript to print", "error");
        window.print();
    });

    // ============================================================
    // TEXT-TO-SPEECH (TTS) AUDIO READER ENGINE
    // ============================================================
    if ('speechSynthesis' in window) {
        ttsPlayBtn.addEventListener("click", toggleSpeech);
    } else {
        ttsPlayBtn.disabled = true;
        ttsStatus.textContent = "TTS Not Supported";
    }

    function toggleSpeech() {
        if (state.isSpeaking) {
            window.speechSynthesis.cancel();
            state.isSpeaking = false;
            updateTtsUi(false);
            return;
        }

        const textToRead = state.summaryText || state.transcriptText;
        if (!textToRead) {
            showToast("No summary or transcript text available to read", "error");
            return;
        }

        const cleanText = textToRead.replace(/[*#`\-\[\]]/g, " ");
        state.speechUtterance = new SpeechSynthesisUtterance(cleanText);
        state.speechUtterance.rate = parseFloat(ttsSpeedSelect.value) || 1.0;

        state.speechUtterance.onstart = () => {
            state.isSpeaking = true;
            updateTtsUi(true);
        };

        state.speechUtterance.onend = () => {
            state.isSpeaking = false;
            updateTtsUi(false);
        };

        state.speechUtterance.onerror = () => {
            state.isSpeaking = false;
            updateTtsUi(false);
            showToast("Audio reader encountered an error", "error");
        };

        window.speechSynthesis.speak(state.speechUtterance);
    }

    function updateTtsUi(playing) {
        if (playing) {
            ttsIcon.textContent = "pause";
            ttsLabel.textContent = "Pause Audio";
            ttsStatus.textContent = "Playing Audio...";
        } else {
            ttsIcon.textContent = "play_arrow";
            ttsLabel.textContent = "Listen Aloud";
            ttsStatus.textContent = "Ready";
        }
    }

    ttsSpeedSelect.addEventListener("change", () => {
        if (state.isSpeaking && state.speechUtterance) {
            window.speechSynthesis.cancel();
            toggleSpeech();
        }
    });

    // ============================================================
    // 1. SUMMARY MODULE (POST /api/summary)
    // ============================================================
    async function loadSummary() {
        summaryContent.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon animate-spin">sync</span><p>Generating summary with Gemini 2.5 Flash...</p></div>`;
        
        try {
            let response;
            try {
                response = await fetch(`${state.flaskUrl}/api/summary`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url: state.currentUrl })
                });
            } catch (err) {
                response = await fetch(`${state.backendUrl}/api/summary`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url: state.currentUrl })
                });
            }

            const data = await response.json();
            if (data.success && data.summary) {
                state.summaryText = data.summary;
                summaryContent.innerHTML = parseMarkdown(data.summary);
                updateAnalytics(data.summary);
                showToast("Summary generated successfully!", "success");
            } else {
                summaryContent.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon" style="color:var(--error);">error</span><p>${data.message || "Failed to generate summary."}</p></div>`;
            }
        } catch (error) {
            summaryContent.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon" style="color:var(--error);">wifi_off</span><p>Error connecting to backend: ${error.message}</p></div>`;
        }
    }

    refreshSummaryBtn.addEventListener("click", loadSummary);
    copySummaryBtn.addEventListener("click", () => {
        if (state.summaryText) {
            navigator.clipboard.writeText(state.summaryText);
            showToast("Summary copied to clipboard!", "success");
        }
    });

    // ============================================================
    // 2. TRANSCRIPT MODULE (POST /api/transcript/formatted)
    // ============================================================
    async function loadTranscript() {
        transcriptContent.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon animate-spin">sync</span><p>Fetching and structuring transcript with Gemini...</p></div>`;

        try {
            const response = await fetch(`${state.backendUrl}/api/transcript/formatted`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: state.currentUrl })
            });

            const data = await response.json();
            if (data.success && data.transcript) {
                state.transcriptText = data.transcript;
                renderTranscript(data.transcript);
                if (!state.summaryText) updateAnalytics(data.transcript);
                if (data.warning) {
                    showToast(data.warning, "info");
                } else {
                    showToast("Transcript loaded!", "success");
                }
            } else {
                transcriptContent.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon" style="color:var(--error);">error</span><p>${data.message || "Transcript unavailable."}</p></div>`;
            }
        } catch (error) {
            transcriptContent.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon" style="color:var(--error);">wifi_off</span><p>Error loading transcript: ${error.message}</p></div>`;
        }
    }

    function renderTranscript(text) {
        transcriptContent.innerHTML = parseMarkdown(text);
    }

    transcriptSearchInput.addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase();
        if (!state.transcriptText) return;
        if (!query) {
            renderTranscript(state.transcriptText);
            return;
        }
        const lines = state.transcriptText.split("\n");
        const filtered = lines.filter(line => line.toLowerCase().includes(query)).join("\n");
        renderTranscript(filtered || "*No matching text found in transcript.*");
    });

    fetchTranscriptBtn.addEventListener("click", loadTranscript);
    copyTranscriptBtn.addEventListener("click", () => {
        if (state.transcriptText) {
            navigator.clipboard.writeText(state.transcriptText);
            showToast("Transcript copied to clipboard!", "success");
        }
    });

    // ============================================================
    // 3. TIMESTAMPS MODULE (POST /api/timestamps)
    // ============================================================
    async function loadTimestamps() {
        timestampsContent.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon animate-spin">sync</span><p>Extracting timestamps with Gemini...</p></div>`;

        try {
            let response;
            try {
                response = await fetch(`${state.flaskUrl}/api/timestamps`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url: state.currentUrl })
                });
            } catch (e) {
                response = await fetch(`${state.backendUrl}/api/timestamps`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ url: state.currentUrl })
                });
            }

            const data = await response.json();
            if (data.success && data.timestamps && Array.isArray(data.timestamps)) {
                state.timestampsData = data.timestamps;
                renderTimestamps(data.timestamps);
            } else {
                timestampsContent.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon">schedule</span><p>${data.message || "No timestamps returned."}</p></div>`;
            }
        } catch (error) {
            timestampsContent.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon" style="color:var(--error);">wifi_off</span><p>Error extracting timestamps: ${error.message}</p></div>`;
        }
    }

    function renderTimestamps(items) {
        if (!items || items.length === 0) {
            timestampsContent.innerHTML = `<div class="empty-state"><p>No topic timestamps available.</p></div>`;
            return;
        }

        const container = document.createElement("div");
        container.className = "timestamp-list";

        items.forEach(item => {
            const timeStr = item.time || "00:00";
            const topicStr = item.topic || "Section";

            const row = document.createElement("div");
            row.className = "timestamp-item";
            row.innerHTML = `
                <span class="time-badge">${timeStr}</span>
                <span class="topic-title">${topicStr}</span>
            `;

            row.addEventListener("click", () => {
                const parts = timeStr.split(":").map(Number);
                let seconds = 0;
                if (parts.length === 2) seconds = parts[0] * 60 + parts[1];
                else if (parts.length === 3) seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];

                videoIframe.src = `https://www.youtube.com/embed/${state.currentVideoId}?start=${seconds}&autoplay=1`;
                showToast(`Jumped video to ${timeStr}`, "info");
            });

            container.appendChild(row);
        });

        timestampsContent.innerHTML = "";
        timestampsContent.appendChild(container);
    }

    refreshTimestampsBtn.addEventListener("click", loadTimestamps);

    // ============================================================
    // 4. PERSONAL NOTES CRUD MODULE (/api/notes)
    // ============================================================
    async function loadNotes(query = "") {
        notesListContainer.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon animate-spin">sync</span><p>Loading personal notes...</p></div>`;

        try {
            const url = `${state.backendUrl}/api/notes?student_id=${encodeURIComponent(state.studentId)}${query ? `&q=${encodeURIComponent(query)}` : ''}`;
            const response = await fetch(url);
            const notes = await response.json();

            if (Array.isArray(notes)) {
                state.notesData = notes;
                renderNotes(notes);
            } else {
                notesListContainer.innerHTML = `<div class="empty-state"><p>Failed to retrieve notes.</p></div>`;
            }
        } catch (error) {
            notesListContainer.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon" style="color:var(--error);">error</span><p>Error loading notes: ${error.message}</p></div>`;
        }
    }

    function renderNotes(notes) {
        if (!notes || notes.length === 0) {
            notesListContainer.innerHTML = `
                <div class="empty-state">
                    <span class="material-symbols-outlined empty-icon">edit_note</span>
                    <h4>No Notes Found</h4>
                    <p>Click <strong>New Note</strong> above to add notes for this student.</p>
                </div>`;
            return;
        }

        notesListContainer.innerHTML = "";
        notes.forEach(note => {
            const card = document.createElement("div");
            card.className = "note-item-card";
            card.innerHTML = `
                <div class="note-item-header">
                    <span class="note-item-title">${note.title}</span>
                    <div class="note-item-actions">
                        <button class="icon-btn sm edit-note-btn" title="Edit Note"><span class="material-symbols-outlined">edit</span></button>
                        <button class="icon-btn sm delete-note-btn" title="Delete Note"><span class="material-symbols-outlined">delete</span></button>
                    </div>
                </div>
                <div class="note-item-body">${parseMarkdown(note.content)}</div>
            `;

            card.querySelector(".edit-note-btn").addEventListener("click", () => openNoteEditor(note));
            card.querySelector(".delete-note-btn").addEventListener("click", () => deleteNote(note.id));

            notesListContainer.appendChild(card);
        });
    }

    newNoteBtn.addEventListener("click", () => openNoteEditor());

    function openNoteEditor(note = null) {
        noteEditorCard.classList.remove("hidden");
        if (note) {
            editorHeading.textContent = "Edit Note";
            noteEditId.value = note.id;
            noteTitleInput.value = note.title;
            noteContentInput.value = note.content;
        } else {
            editorHeading.textContent = "Create Note";
            noteEditId.value = "";
            noteTitleInput.value = "";
            noteContentInput.value = "";
        }
        noteTitleInput.focus();
    }

    cancelNoteBtn.addEventListener("click", () => {
        noteEditorCard.classList.add("hidden");
    });

    saveNoteBtn.addEventListener("click", async () => {
        const title = noteTitleInput.value.trim();
        const content = noteContentInput.value.trim();
        const id = noteEditId.value;

        if (!title || !content) {
            showToast("Title and content cannot be empty", "error");
            return;
        }

        try {
            if (id) {
                const res = await fetch(`${state.backendUrl}/api/notes/${id}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title, content })
                });
                if (res.ok) showToast("Note updated!", "success");
            } else {
                const res = await fetch(`${state.backendUrl}/api/notes`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ student_id: state.studentId, title, content })
                });
                if (res.ok) showToast("Note created!", "success");
            }
            noteEditorCard.classList.add("hidden");
            loadNotes();
        } catch (e) {
            showToast(`Save failed: ${e.message}`, "error");
        }
    });

    async function deleteNote(id) {
        if (!confirm("Are you sure you want to delete this note?")) return;
        try {
            const res = await fetch(`${state.backendUrl}/api/notes/${id}`, { method: "DELETE" });
            if (res.ok) {
                showToast("Note deleted", "info");
                loadNotes();
            }
        } catch (e) {
            showToast(`Delete failed: ${e.message}`, "error");
        }
    }

    notesSearchInput.addEventListener("input", (e) => {
        loadNotes(e.target.value.trim());
    });

    // ============================================================
    // 5. TRANSLATION MODULE (POST /api/translate)
    // ============================================================
    translateActionBtn.addEventListener("click", async () => {
        const targetLang = targetLangSelect.value;
        const textToTranslate = state.transcriptText || state.summaryText;

        if (!textToTranslate) {
            showToast("No transcript or summary available to translate. Process a video first.", "error");
            return;
        }

        translateContent.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon animate-spin">translate</span><p>Translating to ${targetLang}...</p></div>`;

        try {
            let res;
            try {
                res = await fetch(`${state.flaskUrl}/api/translate`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        transcript: textToTranslate,
                        source_language: "English",
                        target_language: targetLang
                    })
                });
            } catch (e) {
                res = await fetch(`${state.backendUrl}/api/translate`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text: textToTranslate,
                        target_lang: targetLang
                    })
                });
            }

            const data = await res.json();
            const translatedText = data.translated_transcript || data.translated_text;

            if (data.success && translatedText) {
                translateContent.innerHTML = parseMarkdown(translatedText);
                showToast(`Translation to ${targetLang} complete!`, "success");
            } else {
                translateContent.innerHTML = `<div class="empty-state"><p>${data.message || "Translation failed."}</p></div>`;
            }
        } catch (err) {
            translateContent.innerHTML = `<div class="empty-state"><span class="material-symbols-outlined empty-icon" style="color:var(--error);">error</span><p>Translation error: ${err.message}</p></div>`;
        }
    });

    // ============================================================
    // 6. AI ASSISTANT CHAT MODULE (POST /ask/stream)
    // ============================================================
    chatInput.addEventListener("input", () => {
        chatInput.style.height = "auto";
        chatInput.style.height = `${chatInput.scrollHeight}px`;
        sendChatBtn.disabled = !chatInput.value.trim();
    });

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });

    sendChatBtn.addEventListener("click", sendChatMessage);

    promptChips.forEach(chip => {
        chip.addEventListener("click", () => {
            chatInput.value = chip.dataset.prompt;
            sendChatMessage();
        });
    });

    clearChatBtn.addEventListener("click", () => {
        chatMessages.innerHTML = "";
        localStorage.removeItem(STORAGE_KEYS.chatHistory);
        appendChatMessage("assistant", "Chat history cleared. How can I help you with this lecture?");
    });

    async function sendChatMessage() {
        const question = chatInput.value.trim();
        if (!question) return;

        chatInput.value = "";
        chatInput.style.height = "auto";
        sendChatBtn.disabled = true;

        appendChatMessage("user", question);

        try {
            const response = await fetch(`${state.backendUrl}/ask/stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    student_id: state.studentId,
                    lecture_id: state.currentVideoId,
                    question: question
                })
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const assistantRow = document.createElement("div");
            assistantRow.className = "chat-bubble-row assistant";
            const bubble = document.createElement("div");
            bubble.className = "chat-bubble";
            assistantRow.appendChild(bubble);
            chatMessages.appendChild(assistantRow);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulated = "";

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split("\n");

                for (const line of lines) {
                    if (line.trim().startsWith("data: ")) {
                        const token = line.trim().slice(6);
                        accumulated += token;
                        bubble.innerHTML = parseMarkdown(accumulated);
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    }
                }
            }

            saveChatHistory();

        } catch (error) {
            appendChatMessage("assistant", `*Connection Error*: Unable to reach AI Assistant (${error.message}). Ensure backend server is online.`);
        }
    }

    function appendChatMessage(role, content) {
        const row = document.createElement("div");
        row.className = `chat-bubble-row ${role}`;
        row.innerHTML = `<div class="chat-bubble">${parseMarkdown(content)}</div>`;
        chatMessages.appendChild(row);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function saveChatHistory() {
        const history = [];
        chatMessages.querySelectorAll(".chat-bubble-row").forEach(row => {
            const role = row.classList.contains("user") ? "user" : "assistant";
            const content = row.querySelector(".chat-bubble").innerText;
            history.push({ role, content });
        });
        localStorage.setItem(STORAGE_KEYS.chatHistory, JSON.stringify(history));
    }

    function loadChatHistory() {
        chatMessages.innerHTML = "";
        const historyJson = localStorage.getItem(STORAGE_KEYS.chatHistory);
        if (historyJson) {
            try {
                const history = JSON.parse(historyJson);
                history.forEach(item => appendChatMessage(item.role, item.content));
            } catch (e) {}
        }

        if (chatMessages.children.length === 0) {
            appendChatMessage("assistant", 
                "**Welcome to NOA AI Assistant!** 👋\n\n" +
                "I am here to help you understand your lecture, answer questions, explain concepts, and analyze topics.\n\n" +
                "Process a YouTube link above or choose a quick prompt to start!"
            );
        }
    }

    // ============================================================
    // KEYBOARD SHORTCUTS GLOBAL LISTENER
    // ============================================================
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            settingsDrawer.classList.add("hidden");
            shortcutsModal.classList.add("hidden");
            noteEditorCard.classList.add("hidden");
        }
        if (e.altKey && (e.key === "s" || e.key === "S")) {
            e.preventDefault();
            switchTab("summary");
        }
        if (e.altKey && (e.key === "t" || e.key === "T")) {
            e.preventDefault();
            switchTab("transcript");
        }
        if (e.altKey && (e.key === "n" || e.key === "N")) {
            e.preventDefault();
            switchTab("notes");
        }
    });

    // Initialize Default View
    loadVideo(state.currentUrl);
    loadChatHistory();
    loadSummary();
    loadTranscript();
    loadNotes();
});

"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import Header from "@/components/Header";
import WelcomeScreen from "@/components/WelcomeScreen";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import Sidebar from "@/components/Sidebar";
import Toast from "@/components/Toast";

const API_BASE = "";

export default function Home() {
  /* ---- state ---- */
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingText, setStreamingText] = useState("");
  const [statusMsg, setStatusMsg] = useState(null); // {text, type}
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [toast, setToast] = useState(null);

  // Model & settings
  const [models, setModels] = useState({});
  const [model, setModel] = useState("");
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1000);

  // Stats
  const [stats, setStats] = useState(null);
  const [filmTitles, setFilmTitles] = useState([]);
  const [tmdbResults, setTmdbResults] = useState([]);
  const [loadingStats, setLoadingStats] = useState(false);

  const chatEndRef = useRef(null);
  const abortRef = useRef(null);

  /* ---- scroll to bottom ---- */
  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingText, statusMsg, scrollToBottom]);

  /* ---- fetch models on mount ---- */
  useEffect(() => {
    fetch(`${API_BASE}/api/models`)
      .then((r) => r.json())
      .then((data) => {
        setModels(data.models || {});
        setModel(data.default || Object.keys(data.models || {})[0] || "");
        setTemperature(data.defaults?.temperature ?? 0.7);
        setMaxTokens(data.defaults?.max_tokens ?? 1000);
      })
      .catch(() => showToast("Tidak bisa terhubung ke server API.", "error"));
  }, []);

  /* ---- toast helper ---- */
  const showToast = useCallback((text, type = "info") => {
    setToast({ text, type });
    setTimeout(() => setToast(null), 3500);
  }, []);

  /* ---- send message ---- */
  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || isStreaming) return;

      // Handle slash commands locally
      const trimmed = text.trim();
      if (trimmed.startsWith("/")) {
        const cmd = trimmed.slice(1).split(/\s+/)[0].toLowerCase();
        if (cmd === "help" || cmd === "bantuan") {
          showToast("Gunakan panel pengaturan di kanan atas.", "info");
          return;
        }
        if (cmd === "reset" || cmd === "clear" || cmd === "bersih") {
          setMessages([]);
          setStats(null);
          setFilmTitles([]);
          setTmdbResults([]);
          showToast("Ingatan Kino dikosongkan.", "success");
          return;
        }
        if (cmd === "statistik" || cmd === "stats") {
          setSidebarOpen(true);
          fetchStats();
          return;
        }
      }

      const userMsg = { role: "user", content: trimmed };
      const updatedMessages = [...messages, userMsg];
      setMessages(updatedMessages);
      setIsStreaming(true);
      setStreamingText("");
      setStatusMsg(null);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const res = await fetch(`${API_BASE}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: updatedMessages,
            model,
            temperature,
            max_tokens: maxTokens,
          }),
          signal: controller.signal,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Server error");
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let accumulated = "";
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const payload = line.slice(6);
            if (payload === "[DONE]") continue;

            try {
              const parsed = JSON.parse(payload);
              if (parsed.type === "teks") {
                accumulated += parsed.content;
                setStreamingText(accumulated);
              } else if (parsed.type === "status") {
                setStatusMsg({ text: parsed.content, type: "status" });
              } else if (parsed.type === "error") {
                setStatusMsg({ text: parsed.content, type: "error" });
              }
            } catch {
              // skip malformed SSE lines
            }
          }
        }

        // Finalize
        if (accumulated) {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: accumulated },
          ]);
        }
      } catch (err) {
        if (err.name !== "AbortError") {
          setStatusMsg({
            text: err.message || "Gagal menghubungi server.",
            type: "error",
          });
          // Remove the user message if no response was generated
          setMessages((prev) => prev.slice(0, -1));
          return false; // Mengembalikan false agar ChatInput tahu pesan gagal dikirim
        }
      } finally {
        setIsStreaming(false);
        setStreamingText("");
        abortRef.current = null;
      }
    },
    [messages, model, temperature, maxTokens, isStreaming, showToast]
  );

  /* ---- stop streaming ---- */
  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  /* ---- fetch stats ---- */
  const fetchStats = useCallback(async () => {
    if (messages.length === 0) return;
    setLoadingStats(true);
    try {
      const res = await fetch(`${API_BASE}/api/stats`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages,
          model,
          extract_titles: true,
        }),
      });
      const data = await res.json();
      setStats(data.stats);
      setFilmTitles(data.titles || []);

      // Verify with TMDB if titles found
      if (data.titles?.length) {
        const verifyRes = await fetch(`${API_BASE}/api/verify`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ titles: data.titles }),
        });
        const verifyData = await verifyRes.json();
        setTmdbResults(verifyData.results || []);
      }
    } catch {
      showToast("Gagal mengambil statistik.", "error");
    } finally {
      setLoadingStats(false);
    }
  }, [messages, model, showToast]);

  /* ---- export chat ---- */
  const exportChat = useCallback(() => {
    if (messages.length === 0) {
      showToast("Belum ada percakapan untuk diunduh.", "info");
      return;
    }
    const data = JSON.stringify(messages, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const now = new Date();
    const ts = now.toISOString().replace(/[:.]/g, "-").slice(0, 19);
    a.href = url;
    a.download = `chat_kino_${ts}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Riwayat berhasil diunduh.", "success");
  }, [messages, showToast]);

  /* ---- import chat ---- */
  const importChat = useCallback(
    (file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const parsed = JSON.parse(e.target.result);
          if (!Array.isArray(parsed)) throw new Error("Format tidak valid");
          const clean = parsed.filter(
            (m) =>
              m.role &&
              m.content &&
              ["user", "assistant"].includes(m.role)
          );
          if (clean.length === 0) throw new Error("Tidak ada pesan");
          setMessages(clean);
          setStats(null);
          setFilmTitles([]);
          setTmdbResults([]);
          showToast(`${clean.length} pesan berhasil dimuat.`, "success");
        } catch (err) {
          showToast(`Gagal memuat: ${err.message}`, "error");
        }
      };
      reader.readAsText(file);
    },
    [showToast]
  );

  /* ---- new chat ---- */
  const newChat = useCallback(() => {
    setMessages([]);
    setStats(null);
    setFilmTitles([]);
    setTmdbResults([]);
    setStreamingText("");
    setStatusMsg(null);
    setIsStreaming(false);
    abortRef.current?.abort();
  }, []);

  /* ---- render ---- */
  const hasMessages = messages.length > 0 || isStreaming;

  return (
    <div className="app-layout">
      <Header
        onToggleSidebar={() => setSidebarOpen((o) => !o)}
        sidebarOpen={sidebarOpen}
        onNewChat={newChat}
        onExport={exportChat}
        hasMessages={messages.length > 0}
      />

      <div className="main-content">
        <div className="ambient-bg">
          <div className="ambient-blob blob-1"></div>
          <div className="ambient-blob blob-2"></div>
          <div className="ambient-blob blob-3"></div>
        </div>
        <div className="chat-column">
          <div className="chat-area">
            <div className="chat-container">
              {!hasMessages && (
                <WelcomeScreen onSend={sendMessage} />
              )}

              {messages.map((msg, i) => (
                <ChatMessage key={i} message={msg} />
              ))}

              {isStreaming && streamingText && (
                <ChatMessage
                  message={{ role: "assistant", content: streamingText }}
                  isStreaming
                />
              )}

              {isStreaming && !streamingText && !statusMsg && (
                <div className="message assistant">
                  <div className="message-avatar">🍅</div>
                  <div className="message-body">
                    <div className="message-name">Kino</div>
                    <div className="message-bubble">
                      <div className="loading-dots">
                        <span></span><span></span><span></span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {statusMsg && (
                <div className="message-status">
                  <div className={`message-status-pill ${statusMsg.type === "error" ? "error" : ""}`}>
                    {statusMsg.type !== "error" && <div className="spinner" />}
                    {statusMsg.text}
                  </div>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>
          </div>

          <ChatInput
            onSend={sendMessage}
            onStop={stopStreaming}
            isStreaming={isStreaming}
            disabled={!model}
          />
        </div>
      </div>

      <Sidebar
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        models={models}
        model={model}
        onModelChange={setModel}
        temperature={temperature}
        onTemperatureChange={setTemperature}
        maxTokens={maxTokens}
        onMaxTokensChange={setMaxTokens}
        stats={stats}
        filmTitles={filmTitles}
        tmdbResults={tmdbResults}
        loadingStats={loadingStats}
        onFetchStats={fetchStats}
        onExport={exportChat}
        onImport={importChat}
        onNewChat={newChat}
        hasMessages={messages.length > 0}
      />

      <Toast toast={toast} />
    </div>
  );
}

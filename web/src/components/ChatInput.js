import { useState, useRef, useEffect } from "react";

export default function ChatInput({ onSend, onStop, isStreaming, disabled }) {
  const [text, setText] = useState("");
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 150) + "px";
  }, [text]);

  // Focus on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // Re-focus after streaming ends
  useEffect(() => {
    if (!isStreaming) {
      textareaRef.current?.focus();
    }
  }, [isStreaming]);

  const handleSubmit = async () => {
    if (!text.trim() || disabled) return;
    const success = await onSend(text.trim());
    
    // Hanya hapus input jika onSend berhasil (tidak return false)
    if (success !== false) {
      setText("");
      // Reset height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (isStreaming) return;
      handleSubmit();
    }
  };

  return (
    <div className="input-area">
      <div className="input-container">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            className="input-field"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Sebut satu film yang kamu suka, atau ketik /help"
            rows={1}
            maxLength={2000}
            disabled={isStreaming || disabled}
          />
        </div>

        {isStreaming ? (
          <button className="send-btn" onClick={onStop} title="Hentikan">
            ■
          </button>
        ) : (
          <button
            className="send-btn"
            onClick={handleSubmit}
            disabled={!text.trim() || disabled}
            title="Kirim"
          >
            ➤
          </button>
        )}
      </div>
      <div className="input-hint">
        <kbd>Enter</kbd> kirim · <kbd>Shift+Enter</kbd> baris baru
      </div>
    </div>
  );
}

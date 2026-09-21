export default function Header({
  onToggleSidebar,
  sidebarOpen,
  onNewChat,
  onExport,
  hasMessages,
}) {
  return (
    <header className="header">
      <div className="header-brand">
        <span className="header-logo">🍅</span>
        <span className="header-title">Kino</span>
        <span className="header-subtitle">Kurator Rute Sinema</span>
      </div>

      <div className="header-actions">
        <button
          className="header-btn"
          onClick={onExport}
          disabled={!hasMessages}
          title="Unduh riwayat"
        >
          <span className="header-btn-icon">↓</span>
          <span className="label">Unduh</span>
        </button>

        <button
          className="header-btn accent"
          onClick={onNewChat}
          title="Percakapan baru"
        >
          <span className="header-btn-icon">+</span>
          <span className="label">Baru</span>
        </button>

        <button
          className={`header-btn ${sidebarOpen ? "active" : ""}`}
          onClick={onToggleSidebar}
          title="Pengaturan"
        >
          <span className="header-btn-icon">☰</span>
        </button>
      </div>
    </header>
  );
}

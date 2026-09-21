import { useRef } from "react";

export default function Sidebar({
  open,
  onClose,
  models,
  model,
  onModelChange,
  temperature,
  onTemperatureChange,
  maxTokens,
  onMaxTokensChange,
  stats,
  filmTitles,
  tmdbResults,
  loadingStats,
  onFetchStats,
  onExport,
  onImport,
  onNewChat,
  hasMessages,
}) {
  const fileInputRef = useRef(null);

  const tmdbMap = {};
  (tmdbResults || []).forEach((r) => {
    tmdbMap[r.judul?.toLowerCase()] = r;
  });

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onImport(file);
      e.target.value = "";
    }
  };

  return (
    <>
      {/* Overlay */}
      <div
        className={`sidebar-overlay ${open ? "open" : ""}`}
        onClick={onClose}
      />

      {/* Panel */}
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="sidebar-header">
          <h2 className="sidebar-title">Ruang Proyeksi</h2>
          <button className="sidebar-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="sidebar-body">
          {/* Model Selection */}
          <div className="sidebar-section">
            <h3 className="sidebar-section-title">Model AI</h3>
            <div className="model-list">
              {Object.entries(models).map(([id, desc]) => (
                <div
                  key={id}
                  className={`model-option ${id === model ? "active" : ""}`}
                  onClick={() => onModelChange(id)}
                >
                  <span className="model-option-name">{id}</span>
                  <span className="model-option-desc">{desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Sliders */}
          <div className="sidebar-section">
            <h3 className="sidebar-section-title">Parameter</h3>

            <div className="slider-group">
              <div className="slider-label">
                <span className="slider-label-text">Kreativitas</span>
                <span className="slider-value">{temperature.toFixed(1)}</span>
              </div>
              <input
                type="range"
                className="slider-input"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => onTemperatureChange(parseFloat(e.target.value))}
              />
            </div>

            <div className="slider-group">
              <div className="slider-label">
                <span className="slider-label-text">Panjang maks jawaban</span>
                <span className="slider-value">{maxTokens}</span>
              </div>
              <input
                type="range"
                className="slider-input"
                min="200"
                max="1200"
                step="50"
                value={maxTokens}
                onChange={(e) => onMaxTokensChange(parseInt(e.target.value, 10))}
              />
            </div>
          </div>

          {/* Statistics */}
          <div className="sidebar-section">
            <h3 className="sidebar-section-title">Statistik Sesi</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px', lineHeight: 1.4 }}>
              *Kino mengingat 24 interaksi terakhir untuk menghemat memori.
            </p>

            {stats ? (
              <>
                <div className="stats-grid">
                  <div className="stat-card">
                    <div className="stat-value">{stats.pesan_kamu}</div>
                    <div className="stat-label">Pesanmu</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{stats.balasan_kino}</div>
                    <div className="stat-label">Balasan Kino</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">{stats.rata_kata_balasan}</div>
                    <div className="stat-label">Rata-rata kata</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-value">~{stats.perkiraan_token}</div>
                    <div className="stat-label">Token</div>
                  </div>
                </div>

                {/* Film titles */}
                {filmTitles.length > 0 && (
                  <>
                    <h3 className="sidebar-section-title" style={{ marginTop: 20 }}>
                      Film yang Dibahas ({filmTitles.length})
                    </h3>
                    <div className="film-list">
                      {filmTitles.map((title, i) => {
                        const tmdb = tmdbMap[title.toLowerCase()];
                        return (
                          <div key={i} className="film-item">
                            <div className="film-dot" />
                            <span className="film-title">{title}</span>
                            {tmdb && (
                              <span className="film-year">{tmdb.tahun}</span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                    {tmdbResults.length > 0 && (
                      <div className="tmdb-badge">
                        ✓ Terverifikasi TMDB
                      </div>
                    )}
                  </>
                )}

                {filmTitles.length === 0 && !loadingStats && (
                  <p className="stat-detail">Belum ada judul film terdeteksi.</p>
                )}
              </>
            ) : (
              <button
                className="extract-btn"
                onClick={onFetchStats}
                disabled={!hasMessages || loadingStats}
              >
                {loadingStats ? "Menganalisis..." : "Tampilkan statistik sesi"}
              </button>
            )}

            {loadingStats && (
              <div style={{ textAlign: "center", marginTop: 12 }}>
                <div className="loading-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="sidebar-section">
            <h3 className="sidebar-section-title">Riwayat</h3>

            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <button
                className="extract-btn"
                onClick={onExport}
                disabled={!hasMessages}
              >
                ↓ Unduh percakapan
              </button>
              <button
                className="extract-btn"
                onClick={() => fileInputRef.current?.click()}
              >
                ↑ Muat percakapan lama
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".json"
                style={{ display: "none" }}
                onChange={handleFileChange}
              />
              <button
                className="extract-btn"
                onClick={onNewChat}
                style={{ color: "var(--accent-red)", borderColor: "var(--accent-red)" }}
              >
                ✕ Kosongkan percakapan
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

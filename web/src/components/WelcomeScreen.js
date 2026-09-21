export default function WelcomeScreen({ onSend }) {
  const suggestions = [
    "Aku suka Interstellar",
    "Rekomendasi film thriller psikologis",
    "Film Asia yang wajib ditonton",
    "Habis nonton Parasite, ke mana lagi?",
  ];

  return (
    <div className="welcome">
      <div className="welcome-icon">🍅</div>
      <h1 className="welcome-title">KINO</h1>
      <p className="welcome-tagline">Kurator Rute Sinema</p>
      <p className="welcome-description">
        Sebut satu film yang kamu suka, dan aku akan menebak{" "}
        <em>apa yang sebenarnya kamu nikmati</em> dari film itu — lalu
        menunjukkan rute ke film berikutnya.
      </p>
      <div className="welcome-chips">
        {suggestions.map((s) => (
          <button
            key={s}
            className="welcome-chip"
            onClick={() => onSend(s)}
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

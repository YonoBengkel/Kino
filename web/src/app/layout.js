import "./globals.css";

export const metadata = {
  title: "Kino — Kurator Rute Sinema",
  description:
    "Chatbot AI yang menunjukkan rute tontonan bertahap, bukan sekadar daftar film.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="id">
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}

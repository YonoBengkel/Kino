import { useMemo } from "react";

/**
 * Render markdown sederhana ke HTML.
 * Tidak memakai library eksternal supaya bundle tetap kecil.
 * Mendukung heading, bold/italic, list, blockquote, code, dan tabel GFM.
 */
function simpleMarkdown(text) {
  // Step 1: split into lines and process block-level elements
  const lines = text.split("\n");
  const blocks = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Detect table: current line has pipes AND next line is separator (|---|)
    if (
      line.trim().startsWith("|") &&
      i + 1 < lines.length &&
      /^\|[\s:]*-+/.test(lines[i + 1].trim())
    ) {
      // Parse table header
      const headerCells = line
        .split("|")
        .map((c) => c.trim())
        .filter(Boolean);
      i += 2; // skip header + separator

      const bodyRows = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const cells = lines[i]
          .split("|")
          .map((c) => c.trim())
          .filter(Boolean);
        bodyRows.push(cells);
        i++;
      }

      let tableHTML = '<table class="md-table"><thead><tr>';
      headerCells.forEach((c) => {
        tableHTML += `<th>${inlineMarkdown(c)}</th>`;
      });
      tableHTML += "</tr></thead><tbody>";
      bodyRows.forEach((row) => {
        tableHTML += "<tr>";
        row.forEach((c) => {
          tableHTML += `<td>${inlineMarkdown(c)}</td>`;
        });
        tableHTML += "</tr>";
      });
      tableHTML += "</tbody></table>";
      blocks.push(tableHTML);
      continue;
    }

    // Empty line = block separator
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Heading
    const h3 = line.match(/^### (.+)$/);
    if (h3) { blocks.push(`<h3>${inlineMarkdown(h3[1])}</h3>`); i++; continue; }
    const h2 = line.match(/^## (.+)$/);
    if (h2) { blocks.push(`<h2>${inlineMarkdown(h2[1])}</h2>`); i++; continue; }
    const h1 = line.match(/^# (.+)$/);
    if (h1) { blocks.push(`<h1>${inlineMarkdown(h1[1])}</h1>`); i++; continue; }

    // Horizontal rule
    if (/^---+$/.test(line.trim())) { blocks.push("<hr>"); i++; continue; }

    // Blockquote
    const bq = line.match(/^> (.+)$/);
    if (bq) { blocks.push(`<blockquote>${inlineMarkdown(bq[1])}</blockquote>`); i++; continue; }

    // Unordered list
    if (/^[-*] /.test(line.trim())) {
      let listHTML = "<ul>";
      while (i < lines.length && /^[-*] /.test(lines[i].trim())) {
        const content = lines[i].trim().replace(/^[-*] /, "");
        listHTML += `<li>${inlineMarkdown(content)}</li>`;
        i++;
      }
      listHTML += "</ul>";
      blocks.push(listHTML);
      continue;
    }

    // Ordered list
    if (/^\d+\. /.test(line.trim())) {
      let listHTML = "<ol>";
      while (i < lines.length && /^\d+\. /.test(lines[i].trim())) {
        const content = lines[i].trim().replace(/^\d+\. /, "");
        listHTML += `<li>${inlineMarkdown(content)}</li>`;
        i++;
      }
      listHTML += "</ol>";
      blocks.push(listHTML);
      continue;
    }

    // Paragraph: collect consecutive non-special lines
    let para = "";
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !/^#{1,3} /.test(lines[i]) &&
      !/^[-*] /.test(lines[i].trim()) &&
      !/^\d+\. /.test(lines[i].trim()) &&
      !/^> /.test(lines[i]) &&
      !/^---+$/.test(lines[i].trim()) &&
      !(lines[i].trim().startsWith("|") && i + 1 < lines.length && /^\|[\s:]*-+/.test((lines[i+1] || "").trim()))
    ) {
      if (para) para += "<br>";
      para += inlineMarkdown(lines[i]);
      i++;
    }
    if (para) blocks.push(`<p>${para}</p>`);
  }

  return blocks.join("");
}

/** Handle inline markdown: bold, italic, code, escape */
function inlineMarkdown(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
}

export default function ChatMessage({ message, isStreaming }) {
  const { role, content } = message;
  const isAssistant = role === "assistant";

  const renderedHTML = useMemo(() => simpleMarkdown(content), [content]);

  return (
    <div className={`message ${role}`}>
      <div className="message-avatar">
        {isAssistant ? "🍅" : "🍿"}
      </div>
      <div className="message-body">
        <div className="message-name">
          {isAssistant ? "Kino" : "Kamu"}
        </div>
        <div className="message-bubble">
          <div dangerouslySetInnerHTML={{ __html: renderedHTML }} />
          {isStreaming && <span className="typing-cursor" />}
        </div>
      </div>
    </div>
  );
}

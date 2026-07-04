import type { ReactNode } from "react";

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Backend highlight is untrusted HTML-ish text. We never parse it as markup —
// we only recognize the literal `<mark>…</mark>` marker and render everything
// else as plain text nodes, so injected tags show up as inert characters.
export function renderServerHighlight(highlight: string): ReactNode[] {
  return highlight
    .split(/(<mark>[\s\S]*?<\/mark>)/)
    .filter((part) => part.length > 0)
    .map((part, i) => {
      const match = /^<mark>([\s\S]*)<\/mark>$/.exec(part);
      return match ? <mark key={i}>{match[1]}</mark> : part;
    });
}

// Fallback when the backend sends no `highlight`: match query words client-side.
export function renderClientHighlight(text: string, query: string): ReactNode[] {
  const words = [...new Set(query.trim().split(/\s+/).filter(Boolean))].map(escapeRegExp);
  if (words.length === 0) return [text];

  const re = new RegExp(words.join("|"), "giu");
  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let key = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    if (m.index > lastIndex) nodes.push(text.slice(lastIndex, m.index));
    nodes.push(<mark key={key++}>{m[0]}</mark>);
    lastIndex = m.index + m[0].length;
  }
  if (lastIndex < text.length) nodes.push(text.slice(lastIndex));
  return nodes;
}

export function renderSnippet(text: string, highlight: string | null, query: string): ReactNode[] {
  return highlight ? renderServerHighlight(highlight) : renderClientHighlight(text, query);
}

/** Keep short replies intact; split longer ones at sentence or paragraph boundaries. */
export function splitSpeechText(text: string, maxChars = 220): string[] {
  const clean = text.trim();
  if (!clean || clean.length <= maxChars) return clean ? [clean] : [];

  const sentences = clean.match(/[^。！？!?；;\n]+[。！？!?；;\n]*|\n+/g) ?? [clean];
  const chunks: string[] = [];
  let current = "";
  for (const sentence of sentences) {
    const part = sentence;
    if (!part.trim()) continue;
    if (current && current.length + part.length > maxChars) {
      chunks.push(current);
      current = "";
    }
    // A single long sentence still has to stay below the provider's limit.
    for (let offset = 0; offset < part.length; offset += maxChars) {
      const slice = part.slice(offset, offset + maxChars);
      if (current && current.length + slice.length > maxChars) {
        chunks.push(current);
        current = "";
      }
      current += slice;
    }
  }
  if (current) chunks.push(current);
  return chunks;
}

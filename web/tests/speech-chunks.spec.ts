import { describe, expect, it } from "vitest";
import { splitSpeechText } from "../lib/speech-chunks";

describe("splitSpeechText", () => {
  it("keeps short replies in one request", () => {
    expect(splitSpeechText("你好，今天学习历史。")).toEqual(["你好，今天学习历史。"]);
  });

  it("starts long replies with a short segment without losing text", () => {
    const text = "秦朝统一六国。".repeat(100);
    const chunks = splitSpeechText(text);
    expect(chunks.length).toBeGreaterThan(1);
    expect(chunks[0].length).toBeLessThanOrEqual(220);
    expect(chunks.every((chunk) => chunk.length <= 220)).toBe(true);
    expect(chunks.join("")).toBe(text);
  });

  it("splits a sentence longer than one segment", () => {
    const text = "长".repeat(500);
    expect(splitSpeechText(text).map((chunk) => chunk.length)).toEqual([220, 220, 60]);
  });

  it("preserves spaces within English text", () => {
    const text = "Hello world. This is a long English sentence. ".repeat(20).trim();
    expect(splitSpeechText(text).join("")).toBe(text);
  });
});

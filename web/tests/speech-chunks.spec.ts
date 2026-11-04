import { describe, expect, it } from "vitest";
import { splitSpeechText } from "../lib/speech-chunks";

describe("splitSpeechText", () => {
  it("keeps short replies in one request", () => {
    expect(splitSpeechText("你好，今天学习历史。", 220)).toEqual(["你好，今天学习历史。"]);
  });

  it("starts long replies with a short segment without losing text", () => {
    const text = "秦朝统一六国。".repeat(100);
    const chunks = splitSpeechText(text, 220);
    expect(chunks.length).toBeGreaterThan(1);
    expect(chunks[0].length).toBeLessThanOrEqual(220);
    expect(chunks.every((chunk) => chunk.length <= 220)).toBe(true);
    expect(chunks.join("")).toBe(text);
  });

  it("splits a sentence longer than one segment", () => {
    const text = "长".repeat(500);
    expect(splitSpeechText(text, 220).map((chunk) => chunk.length)).toEqual([220, 220, 60]);
  });

  it("preserves spaces within English text", () => {
    const text = "Hello world. This is a long English sentence. ".repeat(20).trim();
    expect(splitSpeechText(text, 220).join("")).toBe(text);
  });

  it("honors the active model's smaller input limit", () => {
    const text = "短模型必须完整朗读。".repeat(80);
    const chunks = splitSpeechText(text, 200);
    expect(chunks.every((chunk) => chunk.length <= 200)).toBe(true);
    expect(chunks.join("")).toBe(text);
  });
});

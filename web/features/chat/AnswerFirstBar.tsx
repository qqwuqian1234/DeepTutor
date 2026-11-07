"use client";

import { useTranslation } from "react-i18next";

/** Optional “write your answer, then compare” step. Off unless the student turns it on. */
export function AnswerFirstBar({
  enabled,
  holdingQuestion,
  draft,
  onDraftChange,
  onToggle,
  onCompare,
  onSkip,
  onCancel,
}: {
  enabled: boolean;
  holdingQuestion: string | null;
  draft: string;
  onDraftChange: (value: string) => void;
  onToggle: () => void;
  onCompare: () => void;
  onSkip: () => void;
  onCancel: () => void;
}) {
  const { t } = useTranslation();
  if (holdingQuestion) {
    return (
      <div className="px-4 pt-3" data-answer-first="holding">
        <div className="text-[12px] font-medium text-[var(--foreground)]">
          {t("Write your own answer before the explanation")}
        </div>
        <p className="mt-1 line-clamp-2 text-[12px] text-[var(--muted-foreground)]">{holdingQuestion}</p>
        <textarea
          value={draft}
          onChange={(event) => onDraftChange(event.target.value)}
          rows={3}
          placeholder={t("Phenomenon, reason, or equations")}
          className="mt-2 w-full resize-none rounded-lg border border-[var(--border)] bg-[var(--background)] px-2 py-1.5 text-[13px] leading-relaxed text-[var(--foreground)] outline-none"
        />
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={!draft.trim()}
            onClick={onCompare}
            className="rounded-md bg-[var(--foreground)] px-2.5 py-1 text-[12px] font-medium text-[var(--background)] disabled:opacity-40"
          >
            {t("Compare with the explanation")}
          </button>
          <button
            type="button"
            onClick={onSkip}
            className="rounded-md px-2.5 py-1 text-[12px] font-medium text-[var(--foreground)] hover:bg-[var(--muted)]"
          >
            {t("Skip and explain")}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md px-2.5 py-1 text-[12px] text-[var(--muted-foreground)] hover:bg-[var(--muted)]"
          >
            {t("Cancel")}
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2 px-4 pt-3">
      <button
        type="button"
        aria-pressed={enabled}
        onClick={onToggle}
        className={`rounded-full border px-2.5 py-0.5 text-[11.5px] font-medium ${
          enabled
            ? "border-[var(--foreground)] bg-[var(--foreground)] text-[var(--background)]"
            : "border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
        }`}
      >
        {t("Answer first")}
      </button>
      <span className="min-w-0 truncate text-[11.5px] text-[var(--muted-foreground)]">
        {t("Off by default. Use it when you want to try before reading the explanation.")}
      </span>
    </div>
  );
}

import clsx from "clsx";

import type { KnowledgeDocument } from "../hooks/useKnowledgeDocuments";
import { KNOWLEDGE_DOCUMENT_FILE_URL } from "../lib/config";

type DocumentPreviewModalProps = {
  document: KnowledgeDocument | null;
  onClose: () => void;
};

export function DocumentPreviewModal({ document, onClose }: DocumentPreviewModalProps) {
  if (!document) {
    return null;
  }

  const previewUrl = KNOWLEDGE_DOCUMENT_FILE_URL(document.id);
  const fileType = inferFileType(document.filename);

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center bg-[#0a1726]/80 px-4 py-10 backdrop-blur-sm">
      <div className="relative flex h-full w-full max-w-5xl flex-col overflow-hidden rounded-[12px] border border-brand-primary/30 bg-white shadow-[0_35px_90px_rgba(29,52,94,0.25)] ring-1 ring-brand-primary/20 dark:border-brand-primary/40 dark:bg-[#101c2f] dark:ring-brand-primary/30">
        <header className="flex items-start justify-between gap-4 border-b border-brand-primary/20 bg-white/95 px-6 py-4 dark:border-brand-primary/30 dark:bg-[#14243b]/90">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand-link/80 dark:text-brand-primary/70">
              {fileType === "pdf"
                ? "PDF document"
                : fileType === "html"
                  ? "HTML document"
                  : "File preview"}
            </p>
            <h3 className="mt-1 font-heading text-xl font-semibold text-brand-text dark:text-white">
              {document.title}
            </h3>
            {document.description ? (
              <p className="mt-2 max-w-3xl text-base text-brand-text/70 dark:text-brand-primary/70">
                {document.description}
              </p>
            ) : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full border border-brand-primary/40 bg-brand-primary/30 px-4 py-1 text-sm font-semibold text-brand-link shadow-sm transition hover:-translate-y-0.5 hover:bg-brand-primary/50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-link dark:border-brand-primary/50 dark:bg-[#1a3356] dark:text-white dark:hover:bg-brand-primary/40"
          >
            Close
          </button>
        </header>

        <div className="flex-1 bg-brand-primary/10 dark:bg-[#0f1b2a]">
          <iframe
            key={document.id}
            title={document.title}
            src={previewUrl}
            className={clsx(
              "h-full w-full border-0",
              fileType === "pdf" ? "bg-brand-primary/20" : "bg-white",
            )}
            allow="fullscreen"
          />
        </div>
      </div>
    </div>
  );
}

function inferFileType(filename: string) {
  const lower = filename.toLowerCase();
  if (lower.endsWith(".pdf")) return "pdf" as const;
  if (lower.endsWith(".html")) return "html" as const;
  return "file" as const;
}

import clsx from "clsx";

import type { KnowledgeDocument } from "../hooks/useKnowledgeDocuments";
import type { CitationRecord } from "../hooks/useThreadCitations";

type KnowledgeDocumentsPanelProps = {
  documents: KnowledgeDocument[];
  activeDocumentIds: Set<string>;
  citations: CitationRecord[];
  loadingDocuments: boolean;
  loadingCitations: boolean;
  documentsError: string | null;
  citationsError: string | null;
  onSelectDocument: (document: KnowledgeDocument) => void;
};

export function KnowledgeDocumentsPanel({
  documents,
  activeDocumentIds,
  citations,
  loadingDocuments,
  loadingCitations,
  documentsError,
  citationsError,
  onSelectDocument,
}: KnowledgeDocumentsPanelProps) {
  const statusMessage = getStatusMessage({
    loadingCitations,
    citationsError,
    activeCount: activeDocumentIds.size,
  });

  return (
    <div className="flex h-full flex-col rounded-[12px] border border-brand-primary/30 bg-white shadow-[0_30px_70px_rgba(29,52,94,0.12)] backdrop-blur-sm dark:border-brand-primary/40 dark:bg-[#14243b] dark:shadow-[0_30px_90px_rgba(0,0,0,0.45)]">
      <div className="border-b border-brand-primary/20 bg-white/90 px-6 py-5 dark:border-brand-primary/30 dark:bg-[#14243b]/80">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="font-heading text-[28px] font-semibold leading-snug text-brand-text dark:text-white">
              Knowledge library
            </h2>
            <p className="mt-2 max-w-2xl text-base text-brand-text/70 dark:text-[#e3ecfa]">
              Browse the September 2025 FOMC source set. Documents cited in the latest assistant response are highlighted.
            </p>
          </div>
          <span className="rounded-full bg-brand-primary/20 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand-link dark:bg-brand-primary/30 dark:text-white/80">
            {loadingDocuments ? "Loading…" : `${documents.length} files`}
          </span>
        </div>
        <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-brand-link/70 dark:text-brand-primary/70">
          {statusMessage}
        </p>
      </div>

      <div className="relative flex-1 overflow-hidden">
        {documentsError ? (
          <ErrorState message={documentsError} />
        ) : (
          <DocumentGrid
            documents={documents}
            loading={loadingDocuments}
            activeDocumentIds={activeDocumentIds}
            onSelectDocument={onSelectDocument}
          />
        )}
      </div>

      {citations.length > 0 ? (
        <aside className="border-t border-brand-primary/20 bg-brand-primary/10 px-6 py-4 text-sm text-brand-link dark:border-brand-primary/30 dark:bg-[#102037] dark:text-brand-primary/80">
          <p className="font-heading text-sm font-semibold uppercase tracking-wide text-brand-link dark:text-brand-primary/70">
            Latest sources
          </p>
          <ul className="mt-2 space-y-1">
            {citations.map((citation) => (
              <li
                key={`${citation.document_id}-${citation.annotation_index ?? "na"}`}
                className="flex flex-wrap items-baseline gap-2"
              >
                <span className="font-medium text-brand-text dark:text-white">
                  {citation.title}
                </span>
                <span className="text-xs uppercase tracking-wide text-brand-link/70 dark:text-brand-primary/60">
                  {citation.filename}
                </span>
              </li>
            ))}
          </ul>
        </aside>
      ) : null}
    </div>
  );
}

function getStatusMessage({
  loadingCitations,
  citationsError,
  activeCount,
}: {
  loadingCitations: boolean;
  citationsError: string | null;
  activeCount: number;
}) {
  if (loadingCitations) {
    return "Updating citations…";
  }
  if (citationsError) {
    return citationsError;
  }
  if (activeCount > 0) {
    return `${activeCount} source${activeCount === 1 ? "" : "s"} cited in the latest response.`;
  }
  return "No sources cited yet.";
}

function DocumentGrid({
  documents,
  loading,
  activeDocumentIds,
  onSelectDocument,
}: {
  documents: KnowledgeDocument[];
  loading: boolean;
  activeDocumentIds: Set<string>;
  onSelectDocument: (document: KnowledgeDocument) => void;
}) {
  if (loading) {
    return (
      <div className="grid h-full place-items-center bg-brand-primary/10 text-brand-link">
        <span className="text-sm font-medium">Loading documents…</span>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="grid h-full place-items-center bg-brand-primary/5 text-sm text-brand-link/70 dark:bg-[#14243b]/50 dark:text-brand-primary/70">
        No documents available.
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-6">
      <div
        className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3"
        style={{ gridAutoRows: "1fr" }}
      >
        {documents.map((document) => {
          const active = activeDocumentIds.has(document.id);
          const fileVariant = getFileVariant(document.filename);
          return (
            <button
              type="button"
              key={document.id}
              className={clsx(
                "group flex h-full min-h-[260px] flex-col justify-between overflow-hidden rounded-[12px] border border-brand-primary/20 bg-white p-4 text-left shadow-sm transition-all duration-200 hover:-translate-y-1 hover:border-brand-link hover:shadow-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-link dark:border-brand-primary/30 dark:bg-[#14243b]/90",
                active
                  ? "border-brand-link ring-2 ring-brand-link/40"
                  : "dark:ring-0",
              )}
              onClick={() => onSelectDocument(document)}
            >
              <div className="flex flex-col gap-4">
                <div className="space-y-1">
                  <span
                    className={clsx(
                      "inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
                      fileVariant.badge,
                    )}
                  >
                    {fileVariant.label}
                  </span>
                  <p
                    className="break-words text-xs font-medium text-brand-link/70 dark:text-brand-primary/60"
                  >
                    {document.filename}
                  </p>
                </div>
                <div className="flex flex-1 flex-col space-y-2">
                  <h3 className="break-words text-base font-semibold leading-snug text-brand-link transition-colors group-hover:text-brand-link/80 dark:text-white dark:group-hover:text-brand-primary">
                    {document.title}
                  </h3>
                  {document.description ? (
                    <p
                      className="line-clamp-3 break-words text-sm leading-snug text-brand-text/70 dark:text-brand-primary/70"
                      style={{
                        display: "-webkit-box",
                        WebkitBoxOrient: "vertical",
                        WebkitLineClamp: 3,
                        overflow: "hidden",
                      }}
                    >
                      {document.description}
                    </p>
                  ) : null}
                </div>
              </div>
              <span
                className={clsx(
                  "mt-6 inline-flex w-fit items-center self-start rounded-full px-3 py-1 text-xs font-medium",
                  active
                    ? "bg-brand-primary/30 text-brand-link dark:bg-brand-primary/40 dark:text-white"
                    : "bg-brand-primary/15 text-brand-link/80 dark:bg-[#1a3356] dark:text-brand-primary/70",
                )}
              >
                {active ? "Cited in latest response" : "Not yet cited"}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 bg-[#fbeae7] px-6 text-center text-sm text-[#8f2f23] dark:bg-[#3a1410] dark:text-[#f6c4bc]">
      <span className="font-semibold">Unable to load documents</span>
      <span>{message}</span>
    </div>
  );
}

type FileVariant = "pdf" | "html" | "default";

function getFileVariant(filename: string): {
  variant: FileVariant;
  label: string;
  badge: string;
} {
  const lower = filename.toLowerCase();
  let variant: FileVariant = "default";
  if (lower.endsWith(".pdf")) variant = "pdf";
  else if (lower.endsWith(".html")) variant = "html";

  const styles: Record<FileVariant, { label: string; badge: string }> = {
    pdf: {
      label: "PDF",
      badge: "bg-[#f6d5d0] text-[#8f2f23] dark:bg-[#3a1410] dark:text-[#f6c4bc]",
    },
    html: {
      label: "HTML",
      badge: "bg-brand-primary/25 text-brand-link dark:bg-brand-primary/30 dark:text-white",
    },
    default: {
      label: "FILE",
      badge: "bg-brand-primary/15 text-brand-link/80 dark:bg-[#1a3356] dark:text-brand-primary/70",
    },
  };

  const style = styles[variant];
  return { variant, ...style };
}

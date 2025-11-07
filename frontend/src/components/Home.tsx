import { useCallback, useState } from "react";
import clsx from "clsx";

import { ChatKitPanel } from "./ChatKitPanel";
import { DocumentPreviewModal } from "./DocumentPreviewModal";
import { KnowledgeDocumentsPanel } from "./KnowledgeDocumentsPanel";
import { ThemeToggle } from "./ThemeToggle";
import type { KnowledgeDocument } from "../hooks/useKnowledgeDocuments";
import { useKnowledgeDocuments } from "../hooks/useKnowledgeDocuments";
import { useThreadCitations } from "../hooks/useThreadCitations";
import type { ColorScheme } from "../hooks/useColorScheme";

type HomeProps = {
  scheme: ColorScheme;
  onThemeChange: (scheme: ColorScheme) => void;
};

export default function Home({ scheme, onThemeChange }: HomeProps) {
  const [selectedDocument, setSelectedDocument] = useState<KnowledgeDocument | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);

  const {
    documents,
    loading: loadingDocuments,
    error: documentsError,
  } = useKnowledgeDocuments();

  const {
    citations,
    activeDocumentIds,
    loading: loadingCitations,
    error: citationsError,
    refresh: refreshCitations,
  } = useThreadCitations(threadId);

  const isDark = scheme === "dark";

  const containerClass = clsx(
    "min-h-screen transition-colors duration-300",
    isDark ? "bg-[#0d1b2a] text-white" : "bg-brand-background text-brand-text",
  );

  const handleDocumentSelect = useCallback((document: KnowledgeDocument) => {
    setSelectedDocument(document);
  }, []);

  const handleClosePreview = useCallback(() => {
    setSelectedDocument(null);
  }, []);

  const handleThreadChange = useCallback((nextThreadId: string | null) => {
    setThreadId(nextThreadId);
  }, []);

  const handleResponseCompleted = useCallback(() => {
    void refreshCitations();
  }, [refreshCitations]);

  return (
    <div className={containerClass}>
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-8 px-6 py-8 lg:h-screen lg:max-h-screen lg:py-10">
        <header className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-brand-link/70 dark:text-brand-primary/80">
              Holson Desk AI Assistant
            </p>
            <h1 className="font-heading text-[30px] font-semibold leading-tight text-brand-text dark:text-white sm:text-[32px]">
              Explore your knowledge base and get help with your tickets.
            </h1>
            <p className="max-w-3xl text-base text-brand-text/80 dark:text-[#d7e4f6]">
              Ask questions about last open ticket and get help from your database to answer it.
            </p>
          </div>
          <ThemeToggle value={scheme} onChange={onThemeChange} />
        </header>

        <div className="flex flex-1 flex-col gap-8">
          <section className="flex flex-1 flex-col overflow-hidden rounded-3xl bg-white/80 shadow-[0_45px_90px_-45px_rgba(15,23,42,0.6)] ring-1 ring-slate-200/60 backdrop-blur dark:bg-slate-900/70 dark:shadow-[0_45px_90px_-45px_rgba(15,23,42,0.85)] dark:ring-slate-800/60">
            <div className="flex flex-1" style={{ height: "800px" }}>
              <ChatKitPanel
                theme={scheme}
                onThreadChange={handleThreadChange}
                onResponseCompleted={handleResponseCompleted}
              />
            </div>
          </section>

          <section className="flex flex-col overflow-hidden rounded-[12px]">
            <KnowledgeDocumentsPanel
              documents={documents}
              activeDocumentIds={activeDocumentIds}
              citations={citations}
              loadingDocuments={loadingDocuments}
              loadingCitations={loadingCitations}
              documentsError={documentsError}
              citationsError={citationsError}
              onSelectDocument={handleDocumentSelect}
            />
          </section>
        </div>
      </div>

      <DocumentPreviewModal document={selectedDocument} onClose={handleClosePreview} />
    </div>
  );
}

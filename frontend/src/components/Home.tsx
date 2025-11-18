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
    isDark ? "bg-[#fff9f6] text-white" : "bg-brand-background text-brand-text",
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
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-8 px-4 py-8 pt-24 lg:h-screen lg:max-h-screen lg:py-10">
        <header className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-brand-link/70 dark:text-brand-primary/80">
              Holson Zoho Desk IA Assistant
            </p>
            <h1 className="font-heading text-[30px] font-semibold leading-tight text-brand-text dark:text-white sm:text-[32px]">
              Obtenez de l'assistance pour vos tickets Zoho Desk
            </h1>
            <p className="max-w-3xl text-base text-brand-text/80 dark:text-[#d7e4f6]">
              Posez des questions sur vos tickets Zoho Desk et obtenez de l'assistance.
            </p>
          </div>
          <ThemeToggle value={scheme} onChange={onThemeChange} />
        </header>

        <div className="grid flex-1 grid-cols-1 gap-8 lg:h-[calc(100vh-260px)] lg:items-stretch">
          <section className="flex flex-1 min-h-[50vh] flex-col overflow-hidden rounded-[12px] border border-brand-primary/30 bg-white shadow-[0_40px_70px_rgba(29,52,94,0.12)] backdrop-blur-sm dark:border-brand-primary/40 dark:bg-[#14243b] dark:shadow-[0_40px_90px_rgba(2,12,29,0.55)]">
            <div className="flex flex-1">
              <ChatKitPanel
                theme={scheme}
                onThreadChange={handleThreadChange}
                onResponseCompleted={handleResponseCompleted}
              />
            </div>
          </section>

          {/* <section className="flex flex-1 flex-col overflow-hidden">
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
          </section> */}
        </div>
      </div>

      <DocumentPreviewModal document={selectedDocument} onClose={handleClosePreview} />
    </div>
  );
}

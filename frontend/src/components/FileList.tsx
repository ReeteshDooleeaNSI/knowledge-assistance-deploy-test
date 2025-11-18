import { useCallback, useState } from "react";
import clsx from "clsx";

import type { VectorStoreFile } from "../hooks/useVectorStoreFiles";

type FileListProps = {
  files: VectorStoreFile[];
  loading: boolean;
  onDelete: (fileId: string) => Promise<void>;
};

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

function formatDate(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getStatusColor(status: string): string {
  switch (status) {
    case "completed":
      return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400";
    case "in_progress":
      return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400";
    case "failed":
      return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400";
    default:
      return "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300";
  }
}

export function FileList({ files, loading, onDelete }: FileListProps) {
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const handleDeleteClick = useCallback(
    (fileId: string, e: React.MouseEvent) => {
      e.stopPropagation();
      setDeleteConfirmId(fileId);
    },
    []
  );

  const handleConfirmDelete = useCallback(
    async (fileId: string) => {
      setDeleteConfirmId(null);
      setDeletingIds((prev) => new Set(prev).add(fileId));
      try {
        await onDelete(fileId);
      } catch (err) {
        console.error("Failed to delete file:", err);
      } finally {
        setDeletingIds((prev) => {
          const next = new Set(prev);
          next.delete(fileId);
          return next;
        });
      }
    },
    [onDelete]
  );

  const handleCancelDelete = useCallback(() => {
    setDeleteConfirmId(null);
  }, []);

  if (loading) {
    return (
      <div className="grid h-full place-items-center bg-brand-primary/10 text-brand-link">
        <span className="text-sm font-medium">Loading files…</span>
      </div>
    );
  }

  if (files.length === 0) {
    return (
      <div className="grid h-full place-items-center bg-brand-primary/5 text-sm text-brand-link/70 dark:bg-[#14243b]/50 dark:text-brand-primary/70">
        No files in vector store.
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto px-6 py-6">
      <div className="space-y-3">
        {files.map((file) => {
          const isDeleting = deletingIds.has(file.id);
          const showConfirm = deleteConfirmId === file.id;

          return (
            <div
              key={file.id}
              className={clsx(
                "group flex items-center gap-4 rounded-[12px] border border-brand-primary/20 bg-white p-4 shadow-sm transition-all duration-200 hover:border-brand-link hover:shadow-lg dark:border-brand-primary/30 dark:bg-[#14243b]/90",
                isDeleting && "opacity-50"
              )}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-primary/10 dark:bg-brand-primary/20">
                      <svg
                        className="h-6 w-6 text-brand-link dark:text-brand-primary"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-base font-semibold text-brand-link dark:text-white">
                      {file.filename}
                    </p>
                    <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-brand-text/70 dark:text-brand-primary/70">
                      <span>{formatFileSize(file.bytes)}</span>
                      <span>•</span>
                      <span>{formatDate(file.created_at)}</span>
                      <span>•</span>
                      <span
                        className={clsx(
                          "rounded-full px-2 py-0.5 text-xs font-medium",
                          getStatusColor(file.status)
                        )}
                      >
                        {file.status}
                      </span>
                    </div>
                    {(file.immatriculation || file.client) && (
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        {file.immatriculation && (
                          <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                            🚗 {file.immatriculation}
                          </span>
                        )}
                        {file.client && (
                          <span className="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800 dark:bg-purple-900/30 dark:text-purple-400">
                            👤 {file.client}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex-shrink-0">
                {showConfirm ? (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleConfirmDelete(file.id);
                      }}
                      disabled={isDeleting}
                      className="rounded-md bg-red-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-50"
                    >
                      Confirm
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCancelDelete();
                      }}
                      disabled={isDeleting}
                      className="rounded-md border border-brand-primary/30 bg-white px-3 py-1.5 text-xs font-medium text-brand-text transition-colors hover:bg-brand-primary/5 dark:border-brand-primary/40 dark:bg-[#14243b] dark:text-white dark:hover:bg-brand-primary/10"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={(e) => handleDeleteClick(file.id, e)}
                    disabled={isDeleting}
                    className="rounded-md border border-red-300 bg-white px-3 py-1.5 text-xs font-medium text-red-600 transition-colors hover:bg-red-50 disabled:opacity-50 dark:border-red-800 dark:bg-[#14243b] dark:text-red-400 dark:hover:bg-red-900/20"
                  >
                    {isDeleting ? "Deleting..." : "Delete"}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


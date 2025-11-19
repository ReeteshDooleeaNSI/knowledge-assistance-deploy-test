import { useCallback, useRef, useState } from "react";
import clsx from "clsx";

type FileUploadAreaProps = {
  onFilesSelected: (files: File[], folderName?: string) => void;
  uploading?: boolean;
};

async function getAllFilesFromDataTransfer(
  dataTransfer: DataTransfer
): Promise<{ files: File[]; folderName?: string }> {
  const files: File[] = [];
  let folderName: string | undefined;
  const items = Array.from(dataTransfer.items);

  async function processEntry(entry: FileSystemEntry | null): Promise<void> {
    if (!entry) return;

    if (entry.isFile) {
      const file = await new Promise<File>((resolve, reject) => {
        (entry as FileSystemFileEntry).file(resolve, reject);
      });
      files.push(file);
    } else if (entry.isDirectory) {
      if (!folderName) {
        folderName = entry.name;
      }
      const dirReader = (entry as FileSystemDirectoryEntry).createReader();
      const entries = await new Promise<FileSystemEntry[]>((resolve, reject) => {
        const entries: FileSystemEntry[] = [];
        const readEntries = () => {
          dirReader.readEntries((batch) => {
            if (batch.length === 0) {
              resolve(entries);
            } else {
              entries.push(...batch);
              readEntries();
            }
          }, reject);
        };
        readEntries();
      });

      await Promise.all(entries.map(processEntry));
    }
  }

  for (const item of items) {
    if (item.kind === "file") {
      const entry = item.webkitGetAsEntry();
      if (entry) {
        await processEntry(entry as FileSystemEntry);
      } else {
        const file = item.getAsFile();
        if (file) {
          files.push(file);
        }
      }
    }
  }

  return { files, folderName };
}

export function FileUploadArea({
  onFilesSelected,
  uploading = false,
}: FileUploadAreaProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget === e.target) {
      setIsDragging(false);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (uploading) return;

      try {
        const { files, folderName } = await getAllFilesFromDataTransfer(
          e.dataTransfer
        );
        if (files.length > 0) {
          onFilesSelected(files, folderName);
        }
      } catch (err) {
        console.error("Error processing dropped files:", err);
        const fileList = e.dataTransfer.files;
        if (fileList.length > 0) {
          onFilesSelected(Array.from(fileList));
        }
      }
    },
    [onFilesSelected, uploading]
  );

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFiles = e.target.files;
      if (selectedFiles && selectedFiles.length > 0) {
        onFilesSelected(Array.from(selectedFiles));
      }
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    },
    [onFilesSelected]
  );

  const handleClick = useCallback(() => {
    if (!uploading && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [uploading]);

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={clsx(
        "relative flex cursor-pointer flex-col items-center justify-center rounded-[12px] border-2 border-dashed p-8 transition-all duration-200",
        isDragging
          ? "border-brand-link bg-brand-primary/10 dark:border-brand-primary dark:bg-brand-primary/20"
          : "border-brand-primary/30 bg-white/50 hover:border-brand-link/50 hover:bg-brand-primary/5 dark:border-brand-primary/40 dark:bg-[#14243b]/50 dark:hover:border-brand-primary/60 dark:hover:bg-brand-primary/10",
        uploading && "cursor-not-allowed opacity-50"
      )}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileInputChange}
        className="hidden"
        disabled={uploading}
      />
      <div className="flex flex-col items-center gap-4 text-center">
        {uploading ? (
          <>
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-brand-primary/20 border-t-brand-link dark:border-brand-primary/30 dark:border-t-brand-primary" />
            <p className="text-sm font-medium text-brand-text dark:text-white">
              Uploading files...
            </p>
          </>
        ) : (
          <>
            <svg
              className="h-12 w-12 text-brand-link/70 dark:text-brand-primary/70"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <div className="space-y-2">
              <p className="text-base font-semibold text-brand-text dark:text-white">
                Déposez des fichiers ou des dossiers ici
              </p>
              <p className="text-sm text-brand-text/70 dark:text-brand-primary/70">
                ou cliquez pour parcourir
              </p>
              <p className="text-xs text-brand-text/50 dark:text-brand-primary/50">
                Supports tous les types de fichiers
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}


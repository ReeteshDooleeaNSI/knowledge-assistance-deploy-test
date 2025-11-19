import { useCallback, useEffect, useState } from "react";
import clsx from "clsx";

import { FileList } from "./FileList";
import { FileUploadArea } from "./FileUploadArea";
import { useVectorStoreFiles } from "../hooks/useVectorStoreFiles";
import type { ColorScheme } from "../hooks/useColorScheme";

type FileManagementPageProps = {
  scheme: ColorScheme;
};

const IMMATRICULATION_REGEX = /^[A-Z]{2}-[A-Z0-9]{3}-[A-Z0-9]{2}$/;

function extractImmatriculation(folderName: string): string | null {
  if (IMMATRICULATION_REGEX.test(folderName)) {
    return folderName;
  }
  const parts = folderName.split("-");
  if (parts.length >= 3) {
    const candidate = parts.slice(0, 3).join("-");
    if (IMMATRICULATION_REGEX.test(candidate)) {
      return candidate;
    }
  }
  return null;
}

export function FileManagementPage({ scheme }: FileManagementPageProps) {
  const {
    files,
    loading,
    uploading,
    error,
    listFiles,
    uploadFiles,
    deleteFile,
  } = useVectorStoreFiles();

  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<number>(0);
  const [showMetadataForm, setShowMetadataForm] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [pendingFolderName, setPendingFolderName] = useState<string | undefined>();
  const [immatriculation, setImmatriculation] = useState("");
  const [client, setClient] = useState("");
  const [searchImmatriculation, setSearchImmatriculation] = useState("");
  const [searchClient, setSearchClient] = useState("");

  useEffect(() => {
    void listFiles();
  }, [listFiles]);

  const handleFilesSelected = useCallback(
    (selectedFiles: File[], folderName?: string) => {
      if (selectedFiles.length > 100) {
        setUploadError(`Too many files. Maximum is 100, received ${selectedFiles.length}.`);
        return;
      }

      setUploadError(null);
      setUploadSuccess(0);
      setPendingFiles(selectedFiles);
      setPendingFolderName(folderName);

      const extractedImmat = folderName ? extractImmatriculation(folderName) : null;
      if (extractedImmat) {
        setImmatriculation(extractedImmat);
      } else {
        setImmatriculation("");
      }

      setShowMetadataForm(true);
    },
    []
  );

  const handleMetadataSubmit = useCallback(
    async () => {
      if (!pendingFiles.length) return;

      setUploadError(null);
      setUploadSuccess(0);
      setShowMetadataForm(false);

      try {
        const result = await uploadFiles(pendingFiles, {
          immatriculation: immatriculation || undefined,
          client: client || undefined,
          folderName: pendingFolderName,
        });
        setUploadSuccess(result.success_count);
        if (result.error_count > 0) {
          const errorDetails = result.errors
            .map((e) => `${e.file}: ${e.error}`)
            .join("; ");
          setUploadError(
            `${result.error_count} file(s) failed to upload. ${errorDetails}`
          );
        }
        setPendingFiles([]);
        setPendingFolderName(undefined);
        setImmatriculation("");
        setClient("");
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setUploadError(message);
      }
    },
    [pendingFiles, immatriculation, client, pendingFolderName, uploadFiles]
  );

  const handleCancelMetadata = useCallback(() => {
    setShowMetadataForm(false);
    setPendingFiles([]);
    setPendingFolderName(undefined);
    setImmatriculation("");
    setClient("");
  }, []);

  const handleSearch = useCallback(() => {
    void listFiles({
      immatriculation: searchImmatriculation || undefined,
      client: searchClient || undefined,
    });
  }, [searchImmatriculation, searchClient, listFiles]);

  const handleResetSearch = useCallback(() => {
    setSearchImmatriculation("");
    setSearchClient("");
    void listFiles();
  }, [listFiles]);

  const handleDelete = useCallback(
    async (fileId: string) => {
      try {
        await deleteFile(fileId);
      } catch (err) {
        console.error("Failed to delete file:", err);
      }
    },
    [deleteFile]
  );

  const isDark = scheme === "dark";

  const containerClass = clsx(
    "min-h-screen transition-colors duration-300",
    isDark ? "bg-[#fff9f6] text-white" : "bg-brand-background text-brand-text"
  );

  return (
    <div className={containerClass}>
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-8 px-4 py-8 pt-28 lg:py-10 lg:pt-16">
        <header className="flex flex-col gap-6">
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-brand-link/70 dark:text-brand-primary/80">
              Gestion de la base de données vectorielle
            </p>
            <h1 className="font-heading text-[30px] font-semibold leading-tight text-brand-text dark:text-white sm:text-[32px]">
              Gestion des fichiers
            </h1>
            <p className="max-w-3xl text-base text-brand-text/80 dark:text-[#d7e4f6]">
              Uploadez des fichiers dans votre base de données vectorielle ou supprimez des fichiers existants. Glissez-déposez des dossiers pour uploader tous les fichiers à l'intérieur.
            </p>
          </div>
        </header>

        <div className="flex flex-col gap-8">
          <section className="flex flex-col gap-4 overflow-hidden rounded-[12px] border border-brand-primary/30 bg-white shadow-[0_40px_70px_rgba(29,52,94,0.12)] backdrop-blur-sm dark:border-brand-primary/40 dark:bg-[#14243b] dark:shadow-[0_40px_90px_rgba(2,12,29,0.55)]">
            <div className="border-b border-brand-primary/20 bg-white/90 px-6 py-5 dark:border-brand-primary/30 dark:bg-[#14243b]/80">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-heading text-[28px] font-semibold leading-snug text-brand-text dark:text-white">
                    Uploader des fichiers
                  </h2>
                  <p className="mt-2 max-w-2xl text-base text-brand-text/70 dark:text-[#e3ecfa]">
                    Glissez-déposez des fichiers ou des dossiers ici, ou cliquez pour parcourir.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="rounded-full bg-brand-primary/20 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand-link dark:bg-brand-primary/30 dark:text-white/80">
                    {files.length} fichier{files.length !== 1 ? "s" : ""}
                  </span>
                  {pendingFiles.length > 0 && (
                    <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                      {pendingFiles.length}/100 fichiers
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="p-6">
              {!showMetadataForm ? (
                <FileUploadArea
                  onFilesSelected={handleFilesSelected}
                  uploading={uploading}
                />
              ) : (
                <div className="space-y-4 rounded-lg border border-brand-primary/20 bg-white/50 p-6 dark:border-brand-primary/30 dark:bg-[#14243b]/50">
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-brand-text dark:text-white">
                      Immatriculation (format: XX-XXX-XX)
                    </label>
                    <input
                      type="text"
                      value={immatriculation}
                      onChange={(e) => setImmatriculation(e.target.value)}
                      placeholder="GH-XXX-XX"
                      pattern="[A-Z]{2}-[A-Z0-9]{3}-[A-Z0-9]{2}"
                      className="w-full rounded-md border border-brand-primary/30 bg-white px-3 py-2 text-sm text-brand-text focus:border-brand-link focus:outline-none dark:border-brand-primary/40 dark:bg-[#14243b] dark:text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-brand-text dark:text-white">
                      Client
                    </label>
                    <select
                      value={client}
                      onChange={(e) => setClient(e.target.value)}
                      className="w-full rounded-md border border-brand-primary/30 bg-white px-3 py-2 text-sm text-brand-text focus:border-brand-link focus:outline-none dark:border-brand-primary/40 dark:bg-[#14243b] dark:text-white"
                    >
                      <option value="">Sélectionner un client</option>
                      <option value="GROUPE BEL">GROUPE BEL</option>
                      <option value="HOMECARE">HOMECARE</option>
                    </select>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={handleMetadataSubmit}
                      disabled={uploading || pendingFiles.length === 0}
                      className="flex-1 rounded-md bg-brand-link px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-link/90 disabled:opacity-50 dark:bg-brand-primary dark:hover:bg-brand-primary/90"
                    >
                      Continuer l'upload ({pendingFiles.length} fichiers)
                    </button>
                    <button
                      onClick={handleCancelMetadata}
                      disabled={uploading}
                      className="rounded-md border border-brand-primary/30 bg-white px-4 py-2 text-sm font-medium text-brand-text transition-colors hover:bg-brand-primary/5 disabled:opacity-50 dark:border-brand-primary/40 dark:bg-[#14243b] dark:text-white dark:hover:bg-brand-primary/10"
                    >
                      Annuler
                    </button>
                  </div>
                </div>
              )}
              {uploadSuccess > 0 && (
                <div className="mt-4 rounded-md bg-green-50 p-3 text-sm text-green-800 dark:bg-green-900/30 dark:text-green-400">
                  Téléchargement réussi de {uploadSuccess} fichier{uploadSuccess !== 1 ? "s" : ""}.
                </div>
              )}
              {uploadError && (
                <div className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-900/30 dark:text-red-400">
                  {uploadError}
                </div>
              )}
            </div>
          </section>

          <section className="flex flex-1 flex-col overflow-hidden rounded-[12px] border border-brand-primary/30 bg-white shadow-[0_30px_70px_rgba(29,52,94,0.12)] backdrop-blur-sm dark:border-brand-primary/40 dark:bg-[#14243b] dark:shadow-[0_30px_90px_rgba(0,0,0,0.45)]">
            <div className="border-b border-brand-primary/20 bg-white/90 px-6 py-5 dark:border-brand-primary/30 dark:bg-[#14243b]/80">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-heading text-[28px] font-semibold leading-snug text-brand-text dark:text-white">
                    Fichiers dans la base de données vectorielle
                  </h2>
                  <p className="mt-2 max-w-2xl text-base text-brand-text/70 dark:text-[#e3ecfa]">
                    Tous les fichiers actuellement dans votre base de données vectorielle. Cliquez sur supprimer pour supprimer un fichier.
                  </p>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap items-end gap-3">
                <div className="flex-1 min-w-[200px]">
                  <label className="block text-xs font-medium text-brand-text/70 dark:text-brand-primary/70 mb-1">
                    Rechercher par immatriculation
                  </label>
                  <input
                    type="text"
                    value={searchImmatriculation}
                    onChange={(e) => setSearchImmatriculation(e.target.value)}
                    placeholder="XX-XXX-XX"
                    className="w-full rounded-md border border-brand-primary/30 bg-white px-3 py-1.5 text-sm text-brand-text focus:border-brand-link focus:outline-none dark:border-brand-primary/40 dark:bg-[#14243b] dark:text-white"
                  />
                </div>
                <div className="flex-1 min-w-[200px]">
                  <label className="block text-xs font-medium text-brand-text/70 dark:text-brand-primary/70 mb-1">
                    Filtrer par client
                  </label>
                  <select
                    value={searchClient}
                    onChange={(e) => setSearchClient(e.target.value)}
                    className="w-full rounded-md border border-brand-primary/30 bg-white px-3 py-1.5 text-sm text-brand-text focus:border-brand-link focus:outline-none dark:border-brand-primary/40 dark:bg-[#14243b] dark:text-white"
                  >
                    <option value="">Tous les clients</option>
                    <option value="GROUPE BEL">GROUPE BEL</option>
                    <option value="HOMECARE">HOMECARE</option>
                  </select>
                </div>
                <button
                  onClick={handleSearch}
                  className="rounded-md bg-brand-link px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-brand-link/90 dark:bg-brand-primary dark:hover:bg-brand-primary/90"
                >
                  Filtrer
                </button>
                <button
                  onClick={handleResetSearch}
                  className="rounded-md border border-brand-primary/30 bg-white px-4 py-1.5 text-sm font-medium text-brand-text transition-colors hover:bg-brand-primary/5 dark:border-brand-primary/40 dark:bg-[#14243b] dark:text-white dark:hover:bg-brand-primary/10"
                >
                  Réinitialiser
                </button>
              </div>
            </div>
            <div className="relative flex-1 overflow-hidden">
              {error ? (
                <div className="flex h-full flex-col items-center justify-center gap-3 bg-[#fbeae7] px-6 text-center text-sm text-[#8f2f23] dark:bg-[#3a1410] dark:text-[#f6c4bc]">
                  <span className="font-semibold">Impossible de charger les fichiers</span>
                  <span>{error}</span>
                </div>
              ) : (
                <FileList files={files} loading={loading} onDelete={handleDelete} />
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}


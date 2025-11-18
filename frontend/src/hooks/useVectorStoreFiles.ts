import { useCallback, useState } from "react";

import {
  VECTOR_STORE_FILES_BATCH_URL,
  VECTOR_STORE_FILES_URL,
  VECTOR_STORE_FILE_DELETE_URL,
} from "../lib/config";

export type VectorStoreFile = {
  id: string;
  filename: string;
  status: string;
  created_at: number;
  bytes: number;
  purpose: string;
  immatriculation?: string;
  client?: string;
};

type FilesResponse = {
  files: VectorStoreFile[];
};

type UploadResponse = {
  file: VectorStoreFile;
};

type BatchUploadResponse = {
  files: VectorStoreFile[];
  errors: Array<{ file: string; error: string }>;
  success_count: number;
  error_count: number;
};

type DeleteResponse = {
  success: boolean;
  file_id: string;
  message: string;
};

export function useVectorStoreFiles() {
  const [files, setFiles] = useState<VectorStoreFile[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const listFiles = useCallback(
    async (filters?: { immatriculation?: string; client?: string }) => {
      setLoading(true);
      setError(null);

      try {
        const url = new URL(VECTOR_STORE_FILES_URL, window.location.origin);
        if (filters?.immatriculation) {
          url.searchParams.append("immatriculation", filters.immatriculation);
        }
        if (filters?.client) {
          url.searchParams.append("client", filters.client);
        }

        const response = await fetch(url.toString(), {
          headers: { Accept: "application/json" },
        });

        if (!response.ok) {
          throw new Error(`Failed to load files (${response.status})`);
        }

        const payload = (await response.json()) as FilesResponse;
        setFiles(payload.files ?? []);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message);
        setFiles([]);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const uploadFile = useCallback(async (file: File): Promise<VectorStoreFile> => {
    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(VECTOR_STORE_FILES_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to upload file (${response.status})`
        );
      }

      const payload = (await response.json()) as UploadResponse;
      await listFiles();
      return payload.file;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setError(message);
      throw err;
    } finally {
      setUploading(false);
    }
  }, [listFiles]);

  const uploadFiles = useCallback(
    async (
      filesToUpload: File[],
      options?: {
        immatriculation?: string;
        client?: string;
        folderName?: string;
      }
    ): Promise<BatchUploadResponse> => {
      setUploading(true);
      setError(null);

      if (filesToUpload.length > 100) {
        const error = new Error(
          `Too many files. Maximum is 100, received ${filesToUpload.length}.`
        );
        setError(error.message);
        throw error;
      }

      try {
        const formData = new FormData();
        filesToUpload.forEach((file) => {
          formData.append("files", file);
        });

        if (options?.immatriculation) {
          formData.append("immatriculation", options.immatriculation);
        }
        if (options?.client) {
          formData.append("client", options.client);
        }
        if (options?.folderName) {
          formData.append("folder_name", options.folderName);
        }

        const response = await fetch(VECTOR_STORE_FILES_BATCH_URL, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.detail || `Failed to upload files (${response.status})`
          );
        }

        const payload = (await response.json()) as BatchUploadResponse;
        await listFiles();
        return payload;
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message);
        throw err;
      } finally {
        setUploading(false);
      }
    },
    [listFiles]
  );

  const deleteFile = useCallback(
    async (fileId: string): Promise<void> => {
      setError(null);

      try {
        const response = await fetch(VECTOR_STORE_FILE_DELETE_URL(fileId), {
          method: "DELETE",
          headers: { Accept: "application/json" },
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.detail || `Failed to delete file (${response.status})`
          );
        }

        await listFiles();
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        setError(message);
        throw err;
      }
    },
    [listFiles]
  );

  return {
    files,
    loading,
    uploading,
    error,
    listFiles,
    uploadFile,
    uploadFiles,
    deleteFile,
  };
}


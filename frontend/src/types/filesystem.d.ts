interface FileSystemEntry {
  readonly isFile: boolean;
  readonly isDirectory: boolean;
  readonly name: string;
  readonly fullPath: string;
  readonly filesystem: FileSystem;
}

interface FileSystemFileEntry extends FileSystemEntry {
  file(
    successCallback: (file: File) => void,
    errorCallback?: (error: Error) => void
  ): void;
}

interface FileSystemDirectoryEntry extends FileSystemEntry {
  createReader(): FileSystemDirectoryReader;
}

interface FileSystemDirectoryReader {
  readEntries(
    successCallback: (entries: FileSystemEntry[]) => void,
    errorCallback?: (error: Error) => void
  ): void;
}

interface FileSystem {
  readonly name: string;
  readonly root: FileSystemDirectoryEntry;
}

declare global {
  interface DataTransferItem {
    webkitGetAsEntry(): FileSystemEntry | null;
  }
}

export {};


import { StartScreenPrompt } from "@openai/chatkit";

export const THEME_STORAGE_KEY = "knowledge-assistant-theme";

const KNOWLEDGE_API_BASE =
  import.meta.env.VITE_KNOWLEDGE_API_BASE ?? "/knowledge";

export const KNOWLEDGE_CHATKIT_API_URL =
  import.meta.env.VITE_KNOWLEDGE_CHATKIT_API_URL ??
  `${KNOWLEDGE_API_BASE}/chatkit`;

/**
 * ChatKit still expects a domain key at runtime. Use any placeholder locally,
 * but register your production domain at
 * https://platform.openai.com/settings/organization/security/domain-allowlist
 * and deploy the real key.
 */
export const KNOWLEDGE_CHATKIT_API_DOMAIN_KEY =
  import.meta.env.VITE_KNOWLEDGE_CHATKIT_API_DOMAIN_KEY ?? "domain_pk_localhost_dev";

export const KNOWLEDGE_DOCUMENTS_URL =
  import.meta.env.VITE_KNOWLEDGE_DOCUMENTS_URL ??
  `${KNOWLEDGE_API_BASE}/documents`;

export const KNOWLEDGE_DOCUMENT_FILE_URL = (documentId: string): string =>
  `${
    import.meta.env.VITE_KNOWLEDGE_DOCUMENT_FILE_BASE_URL ??
    `${KNOWLEDGE_API_BASE}/documents`
  }/${documentId}/file`;

export const getKnowledgeThreadCitationsUrl = (threadId: string): string =>
  `${
    import.meta.env.VITE_KNOWLEDGE_THREADS_BASE_URL ??
    `${KNOWLEDGE_API_BASE}/threads`
  }/${threadId}/citations`;

export const KNOWLEDGE_GREETING =
  import.meta.env.VITE_KNOWLEDGE_GREETING ??
  "Bienvenue dans l'assistant de support Holson Desk AI";

export const KNOWLEDGE_STARTER_PROMPTS: StartScreenPrompt[] = [
  {
    label: "Comment traiter un problème de pneumatique pour le GROUPE BEL?",
    prompt: "Comment traiter un problème de pneumatique pour le GROUPE BEL en te basant sur les informations disponibles dans Zoho Learn.",
    icon: "sparkle",
  },
  {
    label: "Donne moi les informations sur la voiture immatriculée GH-728-KS",
    prompt: "Donne moi les informations sur la voiture immatriculée GH-728-KS",
    icon: "chart",
  },
  {
    label: "Aide moi à répondre au dernier ticket du GROUPE BEL",
    prompt: "Aide moi à répondre au dernier ticket du GROUPE BEL en te basant sur les informations disponibles dans Zoho Desk",
    icon: "notebook",
  },
];

export const KNOWLEDGE_COMPOSER_PLACEHOLDER =
  import.meta.env.VITE_KNOWLEDGE_COMPOSER_PLACEHOLDER ??
  "Demande des informations sur des tickets Zoho Desk ou sur la base de connaissances Carfleet";

export const VECTOR_STORE_FILES_URL =
  import.meta.env.VITE_VECTOR_STORE_FILES_URL ??
  `${KNOWLEDGE_API_BASE}/vector-store/files`;

export const VECTOR_STORE_FILES_BATCH_URL =
  import.meta.env.VITE_VECTOR_STORE_FILES_BATCH_URL ??
  `${KNOWLEDGE_API_BASE}/vector-store/files/batch`;

export const VECTOR_STORE_FILE_DELETE_URL = (fileId: string): string =>
  `${VECTOR_STORE_FILES_URL}/${fileId}`;

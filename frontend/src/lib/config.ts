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
    label: "Combien de tickets le GROUPE BEL a en ce moment et quels sont leurs statuts ?",
    prompt: "Combien de tickets le GROUPE BEL a en ce moment et quels sont leurs statuts en utilisant Zoho Desk ?",
    icon: "chart",
  },
  {
    label: "Aide moi à répondre au dernier ticket du GROUP BEL",
    prompt: "Aide moi à répondre au dernier ticket du GROUP BEL en te basant sur les informations disponibles dans Zoho Desk et dans la base de connaissances Carfleet",
    icon: "notebook",
  },
];

export const KNOWLEDGE_COMPOSER_PLACEHOLDER =
  import.meta.env.VITE_KNOWLEDGE_COMPOSER_PLACEHOLDER ??
  "Ask about the last ticket status";

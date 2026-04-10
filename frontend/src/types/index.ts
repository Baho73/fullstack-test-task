// FILE: frontend/src/types/index.ts
// VERSION: 1.0.0
// START_MODULE_CONTRACT
//   PURPOSE: TypeScript types shared across frontend: FileItem, AlertItem, PaginatedResponse.
//   SCOPE: Type definitions only, no runtime code.
//   DEPENDS: none
//   LINKS: M-FE-TYPES, V-M-FE-TYPES
// END_MODULE_CONTRACT

// START_BLOCK_FILE_TYPES
export type FileItem = {
  id: string;
  title: string;
  original_name: string;
  stored_name: string;
  mime_type: string;
  size: number;
  processing_status: string;
  scan_status: string | null;
  scan_details: string | null;
  metadata_json: Record<string, unknown> | null;
  requires_attention: boolean;
  created_at: string;
  updated_at: string;
};
// END_BLOCK_FILE_TYPES

// START_BLOCK_ALERT_TYPES
export type AlertItem = {
  id: number;
  file_id: string;
  level: string;
  message: string;
  created_at: string;
};
// END_BLOCK_ALERT_TYPES

// START_BLOCK_PAGINATED_RESPONSE
export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};
// END_BLOCK_PAGINATED_RESPONSE

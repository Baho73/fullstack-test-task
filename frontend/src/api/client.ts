// FILE: frontend/src/api/client.ts
// VERSION: 1.0.0
// START_MODULE_CONTRACT
//   PURPOSE: API client: typed fetch functions for backend endpoints. Base URL from env.
//   SCOPE: fetchFiles, fetchAlerts, uploadFile
//   DEPENDS: M-FE-TYPES
//   LINKS: M-FE-API, V-M-FE-API
// END_MODULE_CONTRACT

import type { AlertItem, FileItem, PaginatedResponse } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// START_BLOCK_FETCH_FILES
export async function fetchFiles(
  limit: number = 20,
  offset: number = 0,
): Promise<PaginatedResponse<FileItem>> {
  const resp = await fetch(
    `${API_BASE}/files?limit=${limit}&offset=${offset}`,
    { cache: "no-store" },
  );
  if (!resp.ok) throw new Error("Failed to fetch files");
  return resp.json();
}
// END_BLOCK_FETCH_FILES

// START_BLOCK_FETCH_ALERTS
export async function fetchAlerts(
  limit: number = 20,
  offset: number = 0,
): Promise<PaginatedResponse<AlertItem>> {
  const resp = await fetch(
    `${API_BASE}/alerts?limit=${limit}&offset=${offset}`,
    { cache: "no-store" },
  );
  if (!resp.ok) throw new Error("Failed to fetch alerts");
  return resp.json();
}
// END_BLOCK_FETCH_ALERTS

// START_BLOCK_UPLOAD_FILE
export async function uploadFile(
  title: string,
  file: File,
): Promise<FileItem> {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);

  const resp = await fetch(`${API_BASE}/files`, {
    method: "POST",
    body: formData,
  });
  if (!resp.ok) throw new Error("Failed to upload file");
  return resp.json();
}
// END_BLOCK_UPLOAD_FILE

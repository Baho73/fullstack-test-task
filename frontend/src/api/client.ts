import type { AlertItem, FileItem, PaginatedResponse } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

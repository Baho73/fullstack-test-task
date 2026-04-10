// FILE: frontend/src/components/FilesTable.tsx
// VERSION: 1.0.0
// START_MODULE_CONTRACT
//   PURPOSE: Files table component with pagination.
//   SCOPE: FilesTable component
//   DEPENDS: M-FE-TYPES, M-FE-PAGINATION
//   LINKS: M-FE-FILES-TABLE, V-M-FE-FILES-TABLE
// END_MODULE_CONTRACT

"use client";

import { Badge, Button, Spinner, Table } from "react-bootstrap";
import type { FileItem, PaginatedResponse } from "@/types";
import { PaginationControl } from "./Pagination";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function formatSize(size: number) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function getProcessingVariant(status: string) {
  if (status === "failed") return "danger";
  if (status === "processing") return "warning";
  if (status === "processed") return "success";
  return "secondary";
}

type Props = {
  data: PaginatedResponse<FileItem> | null;
  isLoading: boolean;
  onPageChange: (newOffset: number) => void;
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// START_BLOCK_FILES_TABLE
export function FilesTable({ data, isLoading, onPageChange }: Props) {
  if (isLoading) {
    return (
      <div className="d-flex justify-content-center py-5">
        <Spinner animation="border" />
      </div>
    );
  }

  const files = data?.items ?? [];

  return (
    <>
      <div className="table-responsive">
        <Table hover bordered className="align-middle mb-0">
          <thead className="table-light">
            <tr>
              <th>Название</th>
              <th>Файл</th>
              <th>MIME</th>
              <th>Размер</th>
              <th>Статус</th>
              <th>Проверка</th>
              <th>Создан</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {files.length === 0 ? (
              <tr>
                <td colSpan={8} className="text-center py-4 text-secondary">
                  Файлы пока не загружены
                </td>
              </tr>
            ) : (
              files.map((file) => (
                <tr key={file.id}>
                  <td>
                    <div className="fw-semibold">{file.title}</div>
                    <div className="small text-secondary">{file.id}</div>
                  </td>
                  <td>{file.original_name}</td>
                  <td>{file.mime_type}</td>
                  <td>{formatSize(file.size)}</td>
                  <td>
                    <Badge bg={getProcessingVariant(file.processing_status)}>
                      {file.processing_status}
                    </Badge>
                  </td>
                  <td>
                    <div className="d-flex flex-column gap-1">
                      <Badge bg={file.requires_attention ? "warning" : "success"}>
                        {file.scan_status ?? "pending"}
                      </Badge>
                      <span className="small text-secondary">
                        {file.scan_details ?? "Ожидает обработки"}
                      </span>
                    </div>
                  </td>
                  <td>{formatDate(file.created_at)}</td>
                  <td className="text-nowrap">
                    <Button
                      as="a"
                      href={`${API_BASE}/files/${file.id}/download`}
                      variant="outline-primary"
                      size="sm"
                    >
                      Скачать
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </Table>
      </div>
      {data && (
        <PaginationControl
          total={data.total}
          limit={data.limit}
          offset={data.offset}
          onPageChange={onPageChange}
        />
      )}
    </>
  );
}
// END_BLOCK_FILES_TABLE

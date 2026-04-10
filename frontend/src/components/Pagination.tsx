// FILE: frontend/src/components/Pagination.tsx
// VERSION: 1.0.0
// START_MODULE_CONTRACT
//   PURPOSE: Reusable pagination control component with page numbers.
//   SCOPE: PaginationControl component
//   DEPENDS: none
//   LINKS: M-FE-PAGINATION, V-M-FE-PAGINATION
// END_MODULE_CONTRACT

"use client";

import { Pagination } from "react-bootstrap";

type Props = {
  total: number;
  limit: number;
  offset: number;
  onPageChange: (newOffset: number) => void;
};

// START_BLOCK_PAGINATION_CONTROL
export function PaginationControl({ total, limit, offset, onPageChange }: Props) {
  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  if (totalPages <= 1) return null;

  const pages: number[] = [];
  const startPage = Math.max(1, currentPage - 2);
  const endPage = Math.min(totalPages, currentPage + 2);

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }

  return (
    <div className="d-flex justify-content-between align-items-center mt-3">
      <small className="text-secondary">
        Показано {Math.min(offset + 1, total)}–{Math.min(offset + limit, total)} из {total}
      </small>
      <Pagination className="mb-0" size="sm">
        <Pagination.First
          disabled={currentPage === 1}
          onClick={() => onPageChange(0)}
        />
        <Pagination.Prev
          disabled={currentPage === 1}
          onClick={() => onPageChange(Math.max(0, offset - limit))}
        />
        {startPage > 1 && <Pagination.Ellipsis disabled />}
        {pages.map((page) => (
          <Pagination.Item
            key={page}
            active={page === currentPage}
            onClick={() => onPageChange((page - 1) * limit)}
          >
            {page}
          </Pagination.Item>
        ))}
        {endPage < totalPages && <Pagination.Ellipsis disabled />}
        <Pagination.Next
          disabled={currentPage === totalPages}
          onClick={() => onPageChange(offset + limit)}
        />
        <Pagination.Last
          disabled={currentPage === totalPages}
          onClick={() => onPageChange((totalPages - 1) * limit)}
        />
      </Pagination>
    </div>
  );
}
// END_BLOCK_PAGINATION_CONTROL

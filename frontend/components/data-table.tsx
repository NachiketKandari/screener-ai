"use client";

import { memo } from "react";
import { SkeletonTable } from "./skeleton-table";
import { ChevronLeft, ChevronRight, ArrowUp, ArrowDown } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export interface Column {
  key: string;
  label: string;
  sortable?: boolean;
  linkable?: boolean;
}

interface Props {
  columns: Column[];
  rows: Record<string, any>[];
  loading: boolean;
  emptyMessage?: string;
  emptyDetail?: string;
  sortBy?: string;
  sortDir?: string;
  onSort?: (column: string) => void;
  limit?: number;
  offset?: number;
  totalCount?: number;
  onPageChange?: (offset: number) => void;
  formatCell?: (columnKey: string, value: any) => string;
  onRowClick?: (row: Record<string, any>) => void;
  getRowHref?: (row: Record<string, any>) => string;
}

function defaultFormatCell(_key: string, value: any): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    if (Number.isInteger(value)) return value.toLocaleString();
    return value.toFixed(2);
  }
  return String(value);
}

export const DataTable = memo(function DataTable({
  columns,
  rows,
  loading,
  emptyMessage = "No results found.",
  emptyDetail,
  sortBy,
  sortDir,
  onSort,
  limit,
  offset,
  totalCount,
  onPageChange,
  formatCell = defaultFormatCell,
  onRowClick,
  getRowHref,
}: Props) {
  const router = useRouter();
  const fmt = formatCell;

  const hasPagination =
    limit != null && offset != null && totalCount != null && onPageChange != null;
  const totalPages = hasPagination ? Math.ceil(totalCount! / limit!) : 0;
  const currentPage = hasPagination ? Math.floor(offset! / limit!) + 1 : 0;

  if (rows.length === 0 && !loading) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <p className="text-lg font-medium">{emptyMessage}</p>
        {emptyDetail && <p className="text-sm mt-1">{emptyDetail}</p>}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto border rounded-lg">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-muted/50 border-b">
              {columns.map((col) => {
                const isSortable = col.sortable && onSort;
                const isActive = sortBy === col.key;

                return (
                  <th
                    key={col.key}
                    className={`text-left px-4 py-2.5 font-medium text-muted-foreground whitespace-nowrap ${
                      isSortable
                        ? "cursor-pointer select-none hover:text-foreground hover:bg-muted transition-colors"
                        : ""
                    } ${isActive ? "text-foreground" : ""}`}
                    onClick={() => {
                      if (isSortable) onSort(col.key);
                    }}
                  >
                    <span className="inline-flex items-center gap-1">
                      {col.label}
                      {isActive && sortDir === "asc" && (
                        <ArrowUp className="h-3 w-3" />
                      )}
                      {isActive && sortDir === "desc" && (
                        <ArrowDown className="h-3 w-3" />
                      )}
                    </span>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <SkeletonTable rows={Math.min(limit || 10, 10)} cols={columns.length} />
            ) : (
              rows.map((row, i) => {
                const href = getRowHref ? getRowHref(row) : undefined;
                const clickable = !!(onRowClick || href);

                return (
                  <tr
                    key={i}
                    className={`border-b last:border-0 hover:bg-muted/30 transition-colors ${
                      clickable ? "cursor-pointer" : ""
                    }`}
                    onClick={() => {
                      if (onRowClick) {
                        onRowClick(row);
                      } else if (href) {
                        router.push(href);
                      }
                    }}
                  >
                    {columns.map((col) => {
                      const value = row[col.key];
                      const isLinkable = col.linkable && href;

                      return (
                        <td
                          key={col.key}
                          className={`px-4 py-2.5 whitespace-nowrap ${
                            isLinkable ? "text-primary" : ""
                          }`}
                        >
                          {isLinkable ? (
                            <Link
                              href={href}
                              className="hover:underline"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {fmt(col.key, value)}
                            </Link>
                          ) : (
                            fmt(col.key, value)
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {hasPagination && totalCount! > limit! && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Showing {offset! + 1}–{Math.min(offset! + limit!, totalCount!)} of{" "}
            {totalCount!.toLocaleString()}
          </span>
          <div className="flex gap-1">
            <Button
              variant="outline"
              size="sm"
              disabled={offset === 0}
              onClick={() => onPageChange!(Math.max(0, offset! - limit!))}
            >
              <ChevronLeft className="h-4 w-4" /> Prev
            </Button>
            <span className="px-3 py-1.5 tabular-nums">
              {currentPage} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={offset! + limit! >= totalCount!}
              onClick={() => onPageChange!(offset! + limit!)}
            >
              Next <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
});

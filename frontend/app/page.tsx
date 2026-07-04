"use client";

import { useReducer, useCallback, useEffect, useRef } from "react";
import { FilterSpec, ScreenResponse, FilterOptions, HealthResponse } from "@/lib/types";
import { screenStocks, screenNaturalLanguage, fetchFilterOptions, fetchHealth } from "@/lib/api";
import { logger } from "@/lib/logger";
import { FilterBar } from "@/components/filter-bar";
import { NaturalLanguageInput } from "@/components/natural-language";
import { ResultsTable } from "@/components/results-table";
import { SummaryBar } from "@/components/summary-bar";
import { SkeletonTable } from "@/components/skeleton-table";
import { DataFreshnessFooter } from "@/components/data-freshness-footer";

type State = {
  filters: FilterSpec;
  options: FilterOptions | null;
  results: ScreenResponse | null;
  loading: boolean;
  error: string | null;
  health: HealthResponse | null;
};

type Action =
  | { type: "SET_FILTERS"; filters: Partial<FilterSpec> }
  | { type: "SET_OPTIONS"; options: FilterOptions }
  | { type: "SET_RESULTS"; results: ScreenResponse }
  | { type: "SET_LOADING"; loading: boolean }
  | { type: "SET_ERROR"; error: string | null }
  | { type: "SET_HEALTH"; health: HealthResponse }
  | { type: "RESET_FILTERS" };

const DEFAULT_FILTERS: FilterSpec = {
  sort_by: "market_cap_crore",
  sort_dir: "desc",
  limit: 50,
  offset: 0,
};

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "SET_FILTERS":
      return { ...state, filters: { ...state.filters, ...action.filters, offset: 0 } };
    case "SET_OPTIONS":
      return { ...state, options: action.options };
    case "SET_RESULTS":
      return { ...state, results: action.results, loading: false, error: null };
    case "SET_LOADING":
      return { ...state, loading: action.loading, error: null };
    case "SET_ERROR":
      return { ...state, error: action.error, loading: false };
    case "SET_HEALTH":
      return { ...state, health: action.health };
    case "RESET_FILTERS":
      return { ...state, filters: { ...DEFAULT_FILTERS } };
    default:
      return state;
  }
}

export default function ScreenerPage() {
  const [state, dispatch] = useReducer(reducer, {
    filters: { ...DEFAULT_FILTERS },
    options: null,
    results: null,
    loading: true,
    error: null,
    health: null,
  });

  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const fetchResults = useCallback(async (filters: FilterSpec) => {
    dispatch({ type: "SET_LOADING", loading: true });
    const start = Date.now();
    try {
      const params: Record<string, string | string[] | undefined> = {};
      for (const [key, value] of Object.entries(filters)) {
        if (value !== undefined && value !== null && value !== "" && value !== false) {
          params[key] = Array.isArray(value) ? value : String(value);
        }
      }
      logger.info("API call: GET /api/screen", { filters: Object.keys(params) });
      const results = await screenStocks(params);
      logger.info("API response", { duration_ms: Date.now() - start, row_count: results.total_count });
      dispatch({ type: "SET_RESULTS", results });
    } catch (err) {
      logger.error("API call failed", err instanceof Error ? err : new Error(String(err)));
      dispatch({ type: "SET_ERROR", error: err instanceof Error ? err.message : "Unknown error" });
    }
  }, []);

  // Initial load
  useEffect(() => {
    Promise.all([
      fetchFilterOptions().then(opts => dispatch({ type: "SET_OPTIONS", options: opts })),
      fetchHealth().then(h => dispatch({ type: "SET_HEALTH", health: h })),
      fetchResults(DEFAULT_FILTERS),
    ]);
  }, [fetchResults]);

  // Debounced filter changes
  const updateFilters = useCallback((partial: Partial<FilterSpec>) => {
    dispatch({ type: "SET_FILTERS", filters: partial });
    const newFilters = { ...state.filters, ...partial, offset: 0 };
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => fetchResults(newFilters), 400);
  }, [state.filters, fetchResults]);

  // Pagination (no debounce)
  const setPage = useCallback((newOffset: number) => {
    const newFilters = { ...state.filters, offset: newOffset };
    dispatch({ type: "SET_FILTERS", filters: { offset: newOffset } });
    fetchResults(newFilters);
  }, [state.filters, fetchResults]);

  const handleNLQuery = useCallback(async (query: string) => {
    dispatch({ type: "SET_LOADING", loading: true });
    try {
      const results = await screenNaturalLanguage(query);
      dispatch({ type: "SET_RESULTS", results });
    } catch (err) {
      dispatch({ type: "SET_ERROR", error: err instanceof Error ? err.message : "Unknown error" });
    }
  }, []);

  const clearAll = useCallback(() => {
    dispatch({ type: "RESET_FILTERS" });
    fetchResults(DEFAULT_FILTERS);
  }, [fetchResults]);

  const handleColumnSort = useCallback(
    (column: string) => {
      const currentSortBy = state.filters.sort_by || "market_cap_crore";
      const currentSortDir = state.filters.sort_dir || "desc";

      if (column === currentSortBy) {
        updateFilters({ sort_by: column, sort_dir: currentSortDir === "asc" ? "desc" : "asc" });
      } else {
        updateFilters({ sort_by: column, sort_dir: "asc" });
      }
    },
    [state.filters.sort_by, state.filters.sort_dir, updateFilters],
  );

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Strattest Screener</h1>

      <NaturalLanguageInput onSubmit={handleNLQuery} loading={state.loading} />

      {state.options && (
        <FilterBar
          options={state.options}
          filters={state.filters}
          onChange={updateFilters}
          onClear={clearAll}
        />
      )}

      {state.loading && !state.results && (
        <div className="overflow-x-auto border rounded-lg">
          <table className="w-full text-sm">
            <tbody>
              <SkeletonTable />
            </tbody>
          </table>
        </div>
      )}

      {state.error && (
        <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-lg text-sm">
          {state.error}
        </div>
      )}

      {state.results && (
        <>
          <SummaryBar
            totalCount={state.results.total_count}
            queryTimeMs={state.results.query_time_ms}
            sortBy={state.filters.sort_by || "market_cap_crore"}
            sortDir={state.filters.sort_dir || "desc"}
            warnings={state.results.warnings}
            onSortChange={(sort_by, sort_dir) => updateFilters({ sort_by, sort_dir })}
            sortColumns={state.options?.sort_columns}
          />
          <ResultsTable
            columns={state.results.columns}
            rows={state.results.rows}
            loading={state.loading}
            limit={state.filters.limit || 50}
            offset={state.filters.offset || 0}
            totalCount={state.results.total_count}
            onPageChange={setPage}
            sortBy={state.filters.sort_by}
            sortDir={state.filters.sort_dir}
            onSort={handleColumnSort}
          />
        </>
      )}

      {state.health && <DataFreshnessFooter health={state.health} />}
    </div>
  );
}

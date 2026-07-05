import { useState, useEffect, useCallback, useRef } from "react";
import { logger } from "@/lib/logger";

export interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useAsyncData<T>(
  fetcher: () => Promise<T>,
  deps: any[] = [],
): AsyncState<T> & { refetch: () => void } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: true,
    error: null,
  });
  const mountedRef = useRef(true);
  const fetcherRef = useRef(fetcher);
  const inFlightRef = useRef<Promise<T> | null>(null);
  fetcherRef.current = fetcher;

  const execute = useCallback(async () => {
    // Deduplicate: if a fetch is already in-flight, reuse its promise.
    // This prevents double-fetches caused by React Strict Mode double-mounting.
    if (inFlightRef.current) return inFlightRef.current;

    setState((prev) => ({ ...prev, loading: true, error: null }));
    const start = Date.now();
    const promise = fetcherRef.current();
    inFlightRef.current = promise;
    try {
      logger.info("useAsyncData fetch started");
      const data = await promise;
      if (!mountedRef.current) return;
      setState({ data, loading: false, error: null });
      logger.info("useAsyncData fetch succeeded", { duration_ms: Date.now() - start });
    } catch (err) {
      if (!mountedRef.current) return;
      const msg = err instanceof Error ? err.message : "Unknown error";
      setState((prev) => ({ ...prev, loading: false, error: msg }));
      logger.error(
        "useAsyncData fetch failed",
        err instanceof Error ? err : new Error(String(err)),
      );
    } finally {
      inFlightRef.current = null;
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    execute();
    return () => {
      mountedRef.current = false;
    };
    // execute is stable (useCallback with [] deps, fetcher accessed via ref).
    // User-provided deps trigger re-fetch when they change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [execute, ...deps]);

  const refetch = useCallback(() => {
    execute();
  }, [execute]);

  return { ...state, refetch };
}

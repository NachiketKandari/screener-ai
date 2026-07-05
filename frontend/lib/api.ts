import { ScreenResponse, FilterOptions, HealthResponse, CompanyResponse, ChartResponse, PeerResponse } from "@/lib/types";
import { dedupeFetch } from "@/lib/cache";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function cacheKey(prefix: string, params: Record<string, string> = {}): string {
  const sorted = Object.entries(params)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${v}`)
    .join("&");
  return sorted ? `${prefix}?${sorted}` : prefix;
}

// ── Screen APIs ───────────────────────────────────────────────────────────

export async function screenStocks(
  filters: Record<string, string | string[] | undefined>,
): Promise<ScreenResponse> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      value.forEach((v) => params.append(key, v));
    } else {
      params.set(key, String(value));
    }
  }
  const queryString = params.toString();
  const key = cacheKey("screen", { q: queryString });

  return dedupeFetch(key, 30_000, async () => {
    const res = await fetch(`${API_URL}/api/screen?${queryString}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "API error");
    }
    return res.json();
  });
}

export async function screenNaturalLanguage(query: string): Promise<ScreenResponse> {
  const res = await fetch(`${API_URL}/api/screen/nl`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

// ── Filter options (long TTL — rarely changes) ────────────────────────────

export async function fetchFilterOptions(): Promise<FilterOptions> {
  return dedupeFetch("filterOptions", 5 * 60_000, async () => {
    const res = await fetch(`${API_URL}/api/filters/options`);
    if (!res.ok) throw new Error("Failed to fetch filter options");
    return res.json();
  });
}

// ── Health (moderate TTL) ─────────────────────────────────────────────────

export async function fetchHealth(): Promise<HealthResponse> {
  return dedupeFetch("health", 2 * 60_000, async () => {
    const res = await fetch(`${API_URL}/api/health`);
    if (!res.ok) throw new Error("Health check failed");
    return res.json();
  });
}

// ── Company detail (short TTL — prices change) ────────────────────────────

export async function fetchCompany(ticker: string): Promise<CompanyResponse> {
  const key = cacheKey("company", { ticker: ticker.toUpperCase() });
  return dedupeFetch(key, 60_000, async () => {
    const res = await fetch(`${API_URL}/api/company/${encodeURIComponent(ticker)}`);
    if (!res.ok) {
      if (res.status === 404) throw new Error("NOT_FOUND");
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "API error");
    }
    return res.json();
  });
}

// ── Chart (long TTL — historical data doesn't change) ─────────────────────

export async function fetchChart(
  ticker: string,
  range: string = "1y",
): Promise<ChartResponse> {
  const key = cacheKey("chart", { ticker: ticker.toUpperCase(), range });
  return dedupeFetch(key, 5 * 60_000, async () => {
    const res = await fetch(
      `${API_URL}/api/company/${encodeURIComponent(ticker)}/chart?range=${range}`,
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "API error");
    }
    return res.json();
  });
}

// ── Peers (long TTL) ──────────────────────────────────────────────────────

export async function fetchPeers(
  ticker: string,
  limit: number = 10,
): Promise<PeerResponse> {
  const key = cacheKey("peers", { ticker: ticker.toUpperCase(), limit: String(limit) });
  return dedupeFetch(key, 5 * 60_000, async () => {
    const res = await fetch(
      `${API_URL}/api/company/${encodeURIComponent(ticker)}/peers?limit=${limit}`,
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "API error");
    }
    return res.json();
  });
}

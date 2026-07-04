import { ScreenResponse, FilterOptions, HealthResponse, CompanyResponse, ChartResponse, PeerResponse } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function screenStocks(filters: Record<string, string | string[] | undefined>): Promise<ScreenResponse> {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value)) {
      value.forEach(v => params.append(key, v));
    } else {
      params.set(key, String(value));
    }
  }
  const res = await fetch(`${API_URL}/api/screen?${params.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
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

export async function fetchFilterOptions(): Promise<FilterOptions> {
  const res = await fetch(`${API_URL}/api/filters/options`);
  if (!res.ok) throw new Error("Failed to fetch filter options");
  return res.json();
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_URL}/api/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function fetchCompany(ticker: string): Promise<CompanyResponse> {
  const res = await fetch(`${API_URL}/api/company/${encodeURIComponent(ticker)}`);
  if (!res.ok) {
    if (res.status === 404) throw new Error("NOT_FOUND");
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

export async function fetchChart(ticker: string, range: string = "1y"): Promise<ChartResponse> {
  const res = await fetch(`${API_URL}/api/company/${encodeURIComponent(ticker)}/chart?range=${range}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

export async function fetchPeers(ticker: string, limit: number = 10): Promise<PeerResponse> {
  const res = await fetch(`${API_URL}/api/company/${encodeURIComponent(ticker)}/peers?limit=${limit}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "API error");
  }
  return res.json();
}

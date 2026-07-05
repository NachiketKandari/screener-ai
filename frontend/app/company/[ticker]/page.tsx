"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { CompanyResponse, ChartResponse, PeerResponse } from "@/lib/types";
import { fetchCompany, fetchChart, fetchPeers } from "@/lib/api";
import { logger } from "@/lib/logger";
import { useAsyncData } from "@/lib/hooks";
import { CompanyHeader } from "@/components/company/company-header";
import { CompanyNavTabs } from "@/components/company/company-nav-tabs";
import { CompanyChart } from "@/components/company/company-chart";
import { MetricsDashboard } from "@/components/company/metrics-dashboard";
import { PeerComparison } from "@/components/company/peer-comparison";
import { AnalystCoverage } from "@/components/company/analyst-coverage";
import { CompanySkeleton } from "@/components/company/skeleton";
import { CompanyErrorState } from "@/components/company/error-state";
import { DataFreshnessFooter } from "@/components/data-freshness-footer";
import { ArrowLeft } from "lucide-react";

type Tab = "overview" | "chart" | "metrics" | "peers" | "analysts";

export default function CompanyDetailPage() {
  const params = useParams();
  const ticker = typeof params.ticker === "string" ? params.ticker.toUpperCase() : "";

  // ── Company data via shared hook ─────────────────────────────────────
  const { data: company, loading, error } = useAsyncData(
    async () => {
      if (!ticker) throw new Error("No ticker provided");
      logger.info("Fetching company data", { ticker });
      const data = await fetchCompany(ticker);
      logger.info("Company data loaded", { ticker, company_name: data.company_name });
      return data;
    },
    [ticker],
  );

  // ── Chart & peers (lazy-loaded on tab change, event-driven) ──────────
  const [chart, setChart] = useState<ChartResponse | null>(null);
  const [peers, setPeers] = useState<PeerResponse | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("overview");

  const loadChart = useCallback(
    async (range: string) => {
      if (!ticker) return;
      try {
        logger.info("Fetching chart data", { ticker, range });
        const data = await fetchChart(ticker, range);
        setChart(data);
      } catch (err) {
        logger.error("Chart fetch failed", err instanceof Error ? err : new Error(String(err)), {
          ticker,
        });
      }
    },
    [ticker],
  );

  const loadPeers = useCallback(async () => {
    if (!ticker) return;
    try {
      logger.info("Fetching peers", { ticker });
      const data = await fetchPeers(ticker);
      setPeers(data);
    } catch (err) {
      logger.error("Peers fetch failed", err instanceof Error ? err : new Error(String(err)), {
        ticker,
      });
    }
  }, [ticker]);

  // Preload chart + peers in background once company data arrives.
  // By the time the user clicks the tab the data is already cached.
  const preloadedRef = useRef(false);
  useEffect(() => {
    if (company && !preloadedRef.current) {
      preloadedRef.current = true;
      if (!chart) loadChart("1y");
      if (!peers) loadPeers();
    }
  }, [company, chart, peers, loadChart, loadPeers]);

  const handleTabChange = useCallback(
    (tab: Tab) => {
      setActiveTab(tab);
      if (tab === "chart" && !chart) loadChart("1y");
      if (tab === "peers" && !peers) loadPeers();
    },
    [chart, peers, loadChart, loadPeers],
  );

  if (loading) return <CompanySkeleton />;
  if (error || !company) return <CompanyErrorState ticker={ticker} error={error} />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" /> Back to screener
      </Link>

      <CompanyHeader company={company} />

      <CompanyNavTabs activeTab={activeTab} onTabChange={handleTabChange} />

      {activeTab === "overview" && (
        <div className="space-y-6">
          <CompanyChart
            chart={chart}
            ticker={ticker}
            onRangeChange={loadChart}
            onLoad={() => {
              if (!chart) loadChart("1y");
            }}
          />
          <MetricsDashboard company={company} />
        </div>
      )}

      {activeTab === "chart" && (
        <CompanyChart
          chart={chart}
          ticker={ticker}
          onRangeChange={loadChart}
          onLoad={() => {
            if (!chart) loadChart("1y");
          }}
          expanded
        />
      )}

      {activeTab === "metrics" && <MetricsDashboard company={company} expanded />}

      {activeTab === "peers" && (
        <PeerComparison
          peers={peers}
          ticker={ticker}
          sector={company.sector}
          onLoad={loadPeers}
        />
      )}

      {activeTab === "analysts" && (
        <AnalystCoverage analyst={company.analyst_coverage} price={company.price} />
      )}

      <DataFreshnessFooter
        health={{
          status: "ok",
          latest_data_date: company.as_of_date,
          stock_count: null,
          db_size_mb: null,
          stale: false,
        }}
      />
    </div>
  );
}

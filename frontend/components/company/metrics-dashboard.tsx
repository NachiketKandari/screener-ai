import { CompanyResponse } from "@/lib/types";
import { fmtLargeNumber, fmtPercent, fmtMarketCap, fmtPrice, colorSignal } from "@/lib/format";
import { METRIC_GLOSSARY } from "@/lib/glossary";
import { MetricCard } from "./metric-card";

interface Props {
  company: CompanyResponse;
  expanded?: boolean;
}

export function MetricsDashboard({ company }: Props) {
  const v = company.valuation;
  const p = company.profitability;
  const g = company.growth;
  const f = company.financial_health;

  const sections = [
    {
      title: "Valuation",
      cards: [
        { metricId: "market_cap_crore", label: "Market Cap", value: fmtMarketCap(v.market_cap_crore) },
        { metricId: "pe_ratio", label: "P/E Ratio", value: fmtLargeNumber(v.pe_ratio) },
        { metricId: "forward_pe", label: "Forward P/E", value: fmtLargeNumber(v.forward_pe) },
        { metricId: "pb_ratio", label: "P/B Ratio", value: fmtLargeNumber(v.pb_ratio) },
        { metricId: "peg_ratio", label: "PEG Ratio", value: fmtLargeNumber(v.peg_ratio) },
        { metricId: "eps_ttm", label: "EPS (TTM)", value: fmtPrice(v.eps_ttm) },
        { metricId: "book_value_per_share", label: "Book Value/Share", value: fmtPrice(v.book_value_per_share) },
        { metricId: "price_to_sales", label: "Price to Sales", value: fmtLargeNumber(v.price_to_sales) },
      ],
    },
    {
      title: "Profitability",
      cards: [
        { metricId: "roe_pct", label: "ROE", value: fmtPercent(p.roe_pct), signal: colorSignal(p.roe_pct, { green: 15, red: 5 }) },
        { metricId: "roa_pct", label: "ROA", value: fmtPercent(p.roa_pct) },
        { metricId: "profit_margins_pct", label: "Net Margin", value: fmtPercent(p.profit_margins_pct) },
        { metricId: "operating_margins_pct", label: "Op Margin", value: fmtPercent(p.operating_margins_pct) },
        { metricId: "gross_margins_pct", label: "Gross Margin", value: fmtPercent(p.gross_margins_pct) },
        { metricId: "ebitda_margins_pct", label: "EBITDA Margin", value: fmtPercent(p.ebitda_margins_pct) },
      ],
    },
    {
      title: "Growth & Cash Flow",
      cards: [
        { metricId: "revenue_growth_pct", label: "Revenue Growth", value: fmtPercent(g.revenue_growth_pct), signal: colorSignal(g.revenue_growth_pct, { green: 10, red: 0 }) },
        { metricId: "earnings_growth_pct", label: "Earnings Growth", value: fmtPercent(g.earnings_growth_pct), signal: colorSignal(g.earnings_growth_pct, { green: 10, red: 0 }) },
        { metricId: "free_cashflow", label: "Free Cash Flow", value: fmtLargeNumber(f.free_cashflow) + " Cr" },
        { metricId: "operating_cashflow", label: "Operating CF", value: fmtLargeNumber(f.operating_cashflow) + " Cr" },
        { metricId: "ebitda", label: "EBITDA", value: fmtLargeNumber(f.ebitda) + " Cr" },
        { metricId: "total_cash_per_share", label: "Cash Per Share", value: fmtPrice(f.total_cash_per_share) },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      {sections.map((section) => (
        <div key={section.title}>
          <h3 className="text-sm font-semibold text-muted-foreground mb-3">{section.title}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {section.cards.map((card) => (
              <MetricCard
                key={card.metricId}
                label={card.label}
                value={card.value}
                signal={card.signal}
                description={METRIC_GLOSSARY[card.metricId]}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

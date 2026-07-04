import { CompanyResponse } from "@/lib/types";
import { fmtLargeNumber, fmtPercent, fmtMarketCap, fmtPrice, colorSignal } from "@/lib/format";
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
        { label: "Market Cap", value: fmtMarketCap(v.market_cap_crore) },
        { label: "P/E Ratio", value: fmtLargeNumber(v.pe_ratio) },
        { label: "Forward P/E", value: fmtLargeNumber(v.forward_pe) },
        { label: "P/B Ratio", value: fmtLargeNumber(v.pb_ratio) },
        { label: "PEG Ratio", value: fmtLargeNumber(v.peg_ratio) },
        { label: "EPS (TTM)", value: fmtPrice(v.eps_ttm) },
        { label: "Book Value/Share", value: fmtPrice(v.book_value_per_share) },
        { label: "Price to Sales", value: fmtLargeNumber(v.price_to_sales) },
      ],
    },
    {
      title: "Profitability",
      cards: [
        { label: "ROE", value: fmtPercent(p.roe_pct), signal: colorSignal(p.roe_pct, { green: 15, red: 5 }) },
        { label: "ROA", value: fmtPercent(p.roa_pct) },
        { label: "Net Margin", value: fmtPercent(p.profit_margins_pct) },
        { label: "Op Margin", value: fmtPercent(p.operating_margins_pct) },
        { label: "Gross Margin", value: fmtPercent(p.gross_margins_pct) },
        { label: "EBITDA Margin", value: fmtPercent(p.ebitda_margins_pct) },
      ],
    },
    {
      title: "Growth & Cash Flow",
      cards: [
        { label: "Revenue Growth", value: fmtPercent(g.revenue_growth_pct), signal: colorSignal(g.revenue_growth_pct, { green: 10, red: 0 }) },
        { label: "Earnings Growth", value: fmtPercent(g.earnings_growth_pct), signal: colorSignal(g.earnings_growth_pct, { green: 10, red: 0 }) },
        { label: "Free Cash Flow", value: fmtLargeNumber(f.free_cashflow) + " Cr" },
        { label: "Operating CF", value: fmtLargeNumber(f.operating_cashflow) + " Cr" },
        { label: "EBITDA", value: fmtLargeNumber(f.ebitda) + " Cr" },
        { label: "Cash Per Share", value: fmtPrice(f.total_cash_per_share) },
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
              <MetricCard key={card.label} label={card.label} value={card.value} signal={card.signal} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

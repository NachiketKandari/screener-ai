export const METRIC_GLOSSARY: Record<string, string> = {
  market_cap_crore:
    "Market capitalization in ₹ crore. Large cap > 20,000 Cr, mid cap 5,000–20,000 Cr, small cap < 5,000 Cr.",
  pe_ratio:
    "Trailing P/E ratio — how much investors pay per rupee of earnings. < 15 is considered value, 15–25 fair, > 50 growth premium. Missing for unprofitable companies.",
  forward_pe:
    "Forward P/E based on analyst earnings estimates. A lower forward P/E compared to trailing P/E suggests expected earnings growth.",
  pb_ratio:
    "Price to Book ratio — market value vs accounting book value. < 1 may signal undervaluation or distress. Most useful for banking and financial stocks.",
  peg_ratio:
    "P/E divided by earnings growth rate. < 1 suggests the stock may be undervalued relative to its growth. Missing if P/E or growth rate is unavailable.",
  eps_ttm:
    "Trailing twelve-month earnings per share in rupees. Price divided by EPS gives the P/E ratio. Missing for unprofitable companies.",
  book_value_per_share:
    "Book value per share in rupees — the accounting value of net assets divided by shares outstanding. Used to calculate P/B ratio.",
  price_to_sales:
    "Price to Sales ratio — useful when earnings are negative. Lower means cheaper relative to revenue generated.",
  roe_pct:
    "Return on Equity — how much profit is generated per rupee of shareholder equity. Above 15% is good, above 20% is excellent. Negative means the company is losing shareholder value.",
  roa_pct:
    "Return on Assets — how efficiently the company uses its assets to generate profit. Higher is better. Compare within the same sector since asset-heavy industries naturally have lower ROA.",
  profit_margins_pct:
    "Net profit margin — what percentage of revenue becomes bottom-line profit after all expenses. Higher margins mean more of each rupee earned is kept as profit.",
  operating_margins_pct:
    "Operating profit margin — excludes interest and taxes for a cleaner view of operational efficiency. Compare across companies to see who runs a tighter operation.",
  gross_margins_pct:
    "Gross profit margin — revenue minus direct costs of goods sold. Higher margins indicate stronger pricing power. Compare within the same industry.",
  ebitda_margins_pct:
    "EBITDA margin — earnings before interest, taxes, depreciation, and amortization as a percentage of revenue. Useful for comparing capital-intensive industries.",
  revenue_growth_pct:
    "Year-over-year revenue growth. Above 20% is high growth, above 50% is exceptional. Negative means declining revenue — warrants investigation.",
  earnings_growth_pct:
    "Year-over-year earnings growth. Compare with revenue growth — earnings growing slower than revenue suggests profit margins are compressing.",
  free_cashflow:
    "Free cash flow in rupees — cash generated after capital expenditures. Positive FCF means the company funds its own growth; negative means it may need external financing.",
  operating_cashflow:
    "Operating cash flow in rupees — cash from core business operations. Should exceed net income for a healthy company, since earnings can include non-cash items.",
  ebitda:
    "EBITDA in rupees — a proxy for operating cash generation before capex and working capital. Often used with total debt to assess leverage (Debt/EBITDA).",
  total_cash_per_share:
    "Cash and equivalents per share in rupees. High cash reserves suggest capacity for acquisitions, buybacks, or weathering downturns.",
};

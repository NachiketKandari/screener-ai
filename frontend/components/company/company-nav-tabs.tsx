type Tab = "overview" | "chart" | "metrics" | "peers" | "analysts";

const TABS: { id: Tab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "chart", label: "Chart" },
  { id: "metrics", label: "Metrics" },
  { id: "peers", label: "Peers" },
  { id: "analysts", label: "Analysts" },
];

interface Props {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}

export function CompanyNavTabs({ activeTab, onTabChange }: Props) {
  return (
    <div className="sticky top-0 z-10 bg-background border-b overflow-x-auto">
      <nav className="flex gap-0 min-w-max" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-[1px] whitespace-nowrap ${
              activeTab === tab.id
                ? "border-primary text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>
    </div>
  );
}

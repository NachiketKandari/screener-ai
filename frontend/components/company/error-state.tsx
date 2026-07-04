import Link from "next/link";
import { AlertCircle } from "lucide-react";

interface Props {
  ticker: string;
  error: string | null;
}

export function CompanyErrorState({ ticker, error }: Props) {
  const is404 = error === "NOT_FOUND";

  return (
    <div className="max-w-7xl mx-auto px-4 py-16 text-center">
      <AlertCircle className="h-10 w-10 mx-auto mb-4 text-muted-foreground" />
      {is404 ? (
        <>
          <p className="text-lg font-medium">{ticker} not found.</p>
          <p className="text-sm text-muted-foreground mt-1">
            This ticker may be delisted or incorrectly typed.
          </p>
        </>
      ) : (
        <>
          <p className="text-lg font-medium">Something went wrong.</p>
          <p className="text-sm text-muted-foreground mt-1">{error || "Failed to load company data."}</p>
        </>
      )}
      <Link href="/" className="inline-block mt-4 text-sm text-primary hover:underline">
        Back to screener
      </Link>
    </div>
  );
}

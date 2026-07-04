"use client";

import { useReducer, useCallback, useRef, useEffect } from "react";
import { FilterSpec, FilterOptions, FilterChipState } from "@/lib/types";
import {
  DEFAULT_METRIC_IDS,
  createEmptyChip,
  serializeChipsToFilterSpec,
} from "@/lib/filter-registry";
import { FilterChip } from "@/components/filter-chip";
import { AddFilterDropdown } from "@/components/add-filter-dropdown";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface Props {
  options: FilterOptions;
  filters: FilterSpec;
  onChange: (partial: Partial<FilterSpec>) => void;
  onClear: () => void;
}

// ── Chip reducer ──────────────────────────────────────────────────────

type ChipAction =
  | { type: "UPDATE_CHIP"; id: string; updates: Partial<FilterChipState> }
  | { type: "REMOVE_CHIP"; id: string }
  | { type: "ADD_CHIP"; metricId: string }
  | { type: "RESET" };

function initChips(): FilterChipState[] {
  return DEFAULT_METRIC_IDS
    .map((id) => createEmptyChip(id))
    .filter((c): c is FilterChipState => c !== null);
}

function chipsReducer(
  state: FilterChipState[],
  action: ChipAction,
): FilterChipState[] {
  switch (action.type) {
    case "UPDATE_CHIP":
      return state.map((c) =>
        c.id === action.id ? { ...c, ...action.updates } : c,
      );
    case "REMOVE_CHIP":
      return state.filter((c) => c.id !== action.id);
    case "ADD_CHIP": {
      const chip = createEmptyChip(action.metricId);
      return chip ? [...state, chip] : state;
    }
    case "RESET":
      return initChips();
  }
}

export function FilterBar({ options, filters, onChange, onClear }: Props) {
  const [chips, dispatch] = useReducer(chipsReducer, null, initChips);
  const chipsRef = useRef(chips);
  chipsRef.current = chips;

  const hasFilters = chips.some((c) => {
    if (c.value.trim()) return true;
    if (c.valueEnd?.trim()) return true;
    return false;
  });

  // Sync chips → parent FilterSpec
  const syncToParent = useCallback(
    (nextChips: FilterChipState[]) => {
      const partial = serializeChipsToFilterSpec(nextChips);
      onChange(partial);
    },
    [onChange],
  );

  // Wrap dispatch to auto-sync
  const dispatchAndSync = useCallback(
    (action: ChipAction) => {
      dispatch(action);

      // Compute next state manually since dispatch is async
      const next = (() => {
        switch (action.type) {
          case "UPDATE_CHIP":
            return chipsRef.current.map((c) =>
              c.id === action.id ? { ...c, ...action.updates } : c,
            );
          case "REMOVE_CHIP":
            return chipsRef.current.filter((c) => c.id !== action.id);
          case "ADD_CHIP": {
            const chip = createEmptyChip(action.metricId);
            return chip ? [...chipsRef.current, chip] : chipsRef.current;
          }
          case "RESET":
            return initChips();
        }
      })();

      chipsRef.current = next;
      syncToParent(next);
    },
    [syncToParent],
  );

  // Initial sync on mount
  useEffect(() => {
    syncToParent(chips);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleClearAll = useCallback(() => {
    dispatchAndSync({ type: "RESET" });
    onClear();
  }, [dispatchAndSync, onClear]);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 items-center">
        {chips.map((chip) => (
          <FilterChip
            key={chip.id}
            chip={chip}
            options={options}
            onChange={(id, updates) =>
              dispatchAndSync({ type: "UPDATE_CHIP", id, updates })
            }
            onRemove={(id) => dispatchAndSync({ type: "REMOVE_CHIP", id })}
          />
        ))}

        <AddFilterDropdown
          activeChips={chips}
          onAdd={(metricId) =>
            dispatchAndSync({ type: "ADD_CHIP", metricId })
          }
        />

        {hasFilters && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearAll}
            className="gap-1 h-8"
          >
            <X className="h-3 w-3" /> Clear All
          </Button>
        )}
      </div>
    </div>
  );
}

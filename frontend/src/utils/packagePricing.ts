import type { ChildPricingRule, ProductVariation } from "../types/finance";

export interface ChildSelectionMap {
  [key: string]: number;
}

export interface ChildBreakdownResult {
  key: string;
  label: string;
  quantity: number;
  unitAmountCents: number;
  totalAmountCents: number;
  countsTowardsCapacity: boolean;
  countsAsPassenger: boolean;
}

export interface PackageComposition {
  basePriceCents: number;
  childExtraCents: number;
  totalPriceCents: number;
  basePassengers: number;
  childPassengers: number;
  totalPassengers: number;
  baseCapacity: number;
  childCapacity: number;
  totalCapacity: number;
  childBreakdown: ChildBreakdownResult[];
}

const clampToInt = (value: number) => Math.max(0, Math.floor(Number.isFinite(value) ? value : 0));

const ruleMaxAllowed = (rule: ChildPricingRule, quantity: number): number => {
  if (!rule.enabled) {
    return 0;
  }
  if (rule.max_quantity === null || typeof rule.max_quantity === "undefined") {
    return Number.POSITIVE_INFINITY;
  }
  return Math.max(0, rule.max_quantity) * Math.max(0, quantity);
};

export const emptyChildSelection = (variation: ProductVariation): ChildSelectionMap => {
  const selection: ChildSelectionMap = {};
  (variation.child_pricing_rules || []).forEach(rule => {
    selection[rule.key] = 0;
  });
  return selection;
};

export const sanitizeChildSelection = (
  variation: ProductVariation,
  quantity: number,
  input: ChildSelectionMap,
): ChildSelectionMap => {
  const next: ChildSelectionMap = {};
  (variation.child_pricing_rules || []).forEach(rule => {
    const raw = input?.[rule.key] ?? 0;
    const limit = ruleMaxAllowed(rule, quantity);
    const value = clampToInt(raw);
    if (!Number.isFinite(limit)) {
      next[rule.key] = value;
    } else {
      next[rule.key] = Math.min(value, limit);
    }
  });
  return next;
};

export const calculatePackageComposition = (
  variation: ProductVariation,
  quantity: number,
  children: ChildSelectionMap = {},
): PackageComposition => {
    const safeQuantity = Math.max(0, Math.floor(quantity));
    const basePrice = (variation.price_cents || 0) * safeQuantity;
    const basePassengers = Math.max(variation.people_included || 0, 0) * safeQuantity;
    const slotsPerUnit = Math.max(Math.floor(variation.slots_per_unit || 0), 0) || Math.max(variation.people_included || 1, 1);
    const baseCapacity = Math.max(slotsPerUnit * safeQuantity, basePassengers, 1);
    let childExtra = 0;
    let childPassengers = 0;
    let childCapacity = 0;
    const breakdown: ChildBreakdownResult[] = [];

    (variation.child_pricing_rules || []).forEach(rule => {
      const max = ruleMaxAllowed(rule, safeQuantity);
      if (max <= 0) {
        return;
      }
      const desired = clampToInt(children[rule.key] ?? 0);
      const quantityForRule = Number.isFinite(max) ? Math.min(desired, max) : desired;
      if (quantityForRule <= 0) {
        return;
      }
      const unitAmount = rule.pricing_mode === "extra" ? Math.max(0, rule.extra_amount_cents || 0) : 0;
      const totalAmount = unitAmount * quantityForRule;
      childExtra += totalAmount;
      if (rule.counts_as_passenger) {
        childPassengers += quantityForRule;
      }
      if (rule.counts_towards_capacity) {
        childCapacity += quantityForRule;
      }
      breakdown.push({
        key: rule.key,
        label: rule.label,
        quantity: quantityForRule,
        unitAmountCents: unitAmount,
        totalAmountCents: totalAmount,
        countsTowardsCapacity: rule.counts_towards_capacity,
        countsAsPassenger: rule.counts_as_passenger,
      });
    });

    return {
      basePriceCents: basePrice,
      childExtraCents: childExtra,
      totalPriceCents: basePrice + childExtra,
      basePassengers,
      childPassengers,
      totalPassengers: basePassengers + childPassengers,
      baseCapacity,
      childCapacity,
      totalCapacity: baseCapacity + childCapacity,
      childBreakdown: breakdown,
    };
};

export const ruleChargeLabel = (rule: ChildPricingRule): string => {
  if (rule.pricing_mode === "free") {
    return "Gratuito";
  }
  const amount = (rule.extra_amount_cents || 0) / 100;
  return amount > 0 ? `+${amount.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}` : "Sem adicional";
};

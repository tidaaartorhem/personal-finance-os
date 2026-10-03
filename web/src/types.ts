export interface MonthPoint {
  month: string;
  income: number;
  expenses: number;
  net: number;
}

export interface CategoryTotal {
  category: string;
  total: number;
  count: number;
}

export interface Subscription {
  merchant: string;
  display_name: string;
  monthly_amount: number;
  annualized_cost: number;
  occurrences: number;
  last_charge: string;
  median_interval_days: number;
  confidence: number;
}

export interface Cashflow {
  months_covered: number;
  avg_monthly_income: number;
  avg_monthly_expenses: number;
  avg_essential_spend: number;
  tax_setaside_monthly: number;
  safe_spend: number;
  runway_months: number | null;
  liquid_cash_assumed: number;
  essential_categories: string[];
  forecast: MonthPoint[];
}

export interface TaxEstimate {
  net_business_income: number;
  federal_tax: number;
  ontario_tax: number;
  cpp_self_employed: number;
  total_estimated: number;
  effective_rate: number;
  monthly_set_aside: number;
  bracket_breakdown: {
    level: string;
    lower: number;
    upper: number | null;
    rate: number;
    taxable_amount: number;
    tax: number;
  }[];
  disclaimer: string;
}

export interface Anomaly {
  date: string;
  description: string;
  category: string;
  amount: number;
  category_monthly_avg: number;
  multiple: number;
}

export interface Brief {
  markdown: string;
  bullets: string[];
  anomalies: Anomaly[];
  subscription_monthly_total: number;
  subscription_annual_total: number;
}

export interface FinanceData {
  generated_at: string;
  period: { start: string; end: string };
  summary: {
    transactions: number;
    skipped_rows: number;
    total_income: number;
    total_expenses: number;
    business_expenses: number;
    annualized_net_business_income: number;
    warnings: string[];
  };
  monthly_series: MonthPoint[];
  categories: CategoryTotal[];
  subscriptions: Subscription[];
  cashflow: Cashflow;
  tax: TaxEstimate;
  brief: Brief;
}

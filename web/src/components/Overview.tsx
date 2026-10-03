import { currency, currency0 } from '../lib/format';
import type { FinanceData } from '../types';
import { CategoryBars, Legend, MonthlyChart } from './Charts';

export default function Overview({ data }: { data: FinanceData }) {
  const f = data.cashflow;
  const s = data.summary;
  const last = data.monthly_series[data.monthly_series.length - 1];

  return (
    <>
      <div className="grid">
        <div className="card hero">
          <h3>Safe monthly spend</h3>
          <div className="big">{currency(f.safe_spend)}</div>
          <div className="sub">
            Average income of {currency(f.avg_monthly_income)}, minus essentials of{' '}
            {currency(f.avg_essential_spend)} and a tax set-aside of{' '}
            {currency(f.tax_setaside_monthly)}. Computed from your last {f.months_covered}{' '}
            months of actual cash flow.
          </div>
        </div>
      </div>

      <div className="grid grid-3" style={{ marginTop: 16 }}>
        <div className="card">
          <h3>Avg monthly income</h3>
          <div className="big accent">{currency(f.avg_monthly_income)}</div>
          <div className="sub">Across {f.months_covered} months</div>
        </div>
        <div className="card">
          <h3>Avg monthly expenses</h3>
          <div className="big">{currency(f.avg_monthly_expenses)}</div>
          <div className="sub">Last month: {currency(last.expenses)}</div>
        </div>
        <div className="card">
          <h3>Runway</h3>
          <div className="big">{f.runway_months ?? 'n/a'} <span style={{ fontSize: 18 }}>months</span></div>
          <div className="sub">On {currency(f.liquid_cash_assumed)} of liquid cash at current burn</div>
        </div>
      </div>

      <h2 className="section-title">Monthly cash flow</h2>
      <p className="section-sub">Income versus expenses, per month.</p>
      <div className="card">
        <Legend />
        <MonthlyChart series={data.monthly_series} />
      </div>

      <h2 className="section-title">Where the money goes</h2>
      <p className="section-sub">Total outflow by category over the full period.</p>
      <div className="card">
        <CategoryBars categories={data.categories} />
      </div>

      <h2 className="section-title">Next 3 months</h2>
      <p className="section-sub">Forecast from your averages: income in, spend out.</p>
      <div className="grid grid-3">
        {f.forecast.map((fc) => (
          <div className="card" key={fc.month}>
            <h3>{fc.month}</h3>
            <div style={{ fontSize: 22, fontWeight: 700, margin: '8px 0' }}>
              {currency0(fc.net)}
            </div>
            <div className="sub">
              {currency0(fc.income)} in, {currency0(fc.expenses)} out
            </div>
          </div>
        ))}
      </div>

      <div className="footer" style={{ border: 'none', paddingTop: 0, marginTop: 28 }}>
        <div className="sub">
          {s.transactions} transactions analyzed, {s.skipped_rows} rows skipped.
          {s.warnings.length > 0 && ` First warning: ${s.warnings[0]}`}
        </div>
      </div>
    </>
  );
}

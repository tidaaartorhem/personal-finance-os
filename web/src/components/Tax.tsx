import { currency, pct } from '../lib/format';
import type { FinanceData } from '../types';

function bracketLabel(lower: number, upper: number | null): string {
  const up = upper === null ? 'and up' : `to ${currency(Math.round(upper))}`;
  return `${currency(Math.round(lower))} ${up}`;
}

export default function Tax({ data }: { data: FinanceData }) {
  const t = data.tax;
  const federal = t.bracket_breakdown.filter((b) => b.level === 'Federal');
  const ontario = t.bracket_breakdown.filter((b) => b.level === 'Ontario');

  return (
    <>
      <h2 className="section-title">Ontario self-employed tax plan</h2>
      <p className="section-sub">
        Estimated 2026 tax on your annualized net business income of{' '}
        {currency(t.net_business_income)}. Brackets are planning approximations.
      </p>

      <div className="grid grid-3">
        <div className="card hero">
          <h3>Monthly set-aside target</h3>
          <div className="big">{currency(t.monthly_set_aside)}</div>
          <div className="sub">Move this to a separate account each month.</div>
        </div>
        <div className="card">
          <h3>Estimated total tax</h3>
          <div className="big">{currency(t.total_estimated)}</div>
          <div className="sub">for the year, at current run rate</div>
        </div>
        <div className="card">
          <h3>Effective rate</h3>
          <div className="big">{pct(t.effective_rate)}</div>
          <div className="sub">total estimate divided by net business income</div>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginTop: 16 }}>
        <div className="card">
          <h3>Federal</h3>
          <div className="big">{currency(t.federal_tax)}</div>
          <div className="sub">marginal brackets applied to net income</div>
        </div>
        <div className="card">
          <h3>Ontario + CPP</h3>
          <div className="big">{currency(t.ontario_tax + t.cpp_self_employed)}</div>
          <div className="sub">
            {currency(t.ontario_tax)} provincial, {currency(t.cpp_self_employed)} CPP (both halves)
          </div>
        </div>
      </div>

      <h2 className="section-title">Bracket breakdown</h2>
      <p className="section-sub">How the estimate was built, bracket by bracket.</p>
      {(
        [
          ['Federal brackets', federal],
          ['Ontario brackets', ontario],
        ] as [string, typeof federal][]
      ).map(([title, rows]) => (
        <div className="card" style={{ padding: 0, marginBottom: 16 }} key={title}>
          <table>
            <thead>
              <tr>
                <th>{title}</th>
                <th className="num">Rate</th>
                <th className="num">Taxable in bracket</th>
                <th className="num">Tax</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((b) => (
                <tr key={`${b.level}-${b.lower}`}>
                  <td>{bracketLabel(b.lower, b.upper)}</td>
                  <td className="num">{pct(b.rate)}</td>
                  <td className="num">{currency(b.taxable_amount)}</td>
                  <td className="num">{currency(b.tax)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}

      <div className="disclaimer">{t.disclaimer}</div>
    </>
  );
}

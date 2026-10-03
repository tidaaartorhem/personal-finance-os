import { useEffect, useState } from 'react';
import { confidenceLabel, currency } from '../lib/format';
import type { FinanceData } from '../types';

const STORAGE_KEY = 'pfos-cancelled-subscriptions';

export default function Subscriptions({ data }: { data: FinanceData }) {
  const [cancelled, setCancelled] = useState<string[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) ?? '[]');
    } catch {
      return [];
    }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cancelled));
  }, [cancelled]);

  const toggle = (merchant: string) =>
    setCancelled((prev) =>
      prev.includes(merchant) ? prev.filter((m) => m !== merchant) : [...prev, merchant]
    );

  const recoverableMonthly = data.subscriptions
    .filter((s) => cancelled.includes(s.merchant))
    .reduce((sum, s) => sum + s.monthly_amount, 0);

  return (
    <>
      <h2 className="section-title">Recurring charges</h2>
      <p className="section-sub">
        Detected from your history: 3 or more monthly charges, billed within a 28
        to 32 day rhythm, amounts within 15 percent. Tick the ones you cancel and
        watch the recoverable total grow.
      </p>

      {recoverableMonthly > 0 && (
        <div className="recoverable">
          Cancelling the ticked charges recovers {currency(recoverableMonthly)} a
          month, or {currency(recoverableMonthly * 12)} a year.
        </div>
      )}

      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Cancel</th>
              <th>Charge</th>
              <th className="num">Monthly</th>
              <th className="num">Annualized</th>
              <th>Last charged</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {data.subscriptions.map((s) => {
              const isCancelled = cancelled.includes(s.merchant);
              return (
                <tr key={s.merchant} className={isCancelled ? 'cancelled' : ''}>
                  <td className="checkbox-cell">
                    <input
                      type="checkbox"
                      checked={isCancelled}
                      onChange={() => toggle(s.merchant)}
                      aria-label={`Mark ${s.display_name} as cancelled`}
                    />
                  </td>
                  <td>{s.display_name}</td>
                  <td className="num">{currency(s.monthly_amount)}</td>
                  <td className="num">{currency(s.annualized_cost)}</td>
                  <td>{s.last_charge}</td>
                  <td>
                    <span className={s.confidence < 0.7 ? 'badge low' : 'badge'}>
                      {confidenceLabel(s.confidence)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="grid grid-3" style={{ marginTop: 16 }}>
        <div className="card">
          <h3>Total recurring</h3>
          <div className="big">{currency(data.brief.subscription_monthly_total)}</div>
          <div className="sub">per month across {data.subscriptions.length} charges</div>
        </div>
        <div className="card">
          <h3>Annualized</h3>
          <div className="big">{currency(data.brief.subscription_annual_total)}</div>
          <div className="sub">what a year of these costs</div>
        </div>
        <div className="card">
          <h3>Recovered so far</h3>
          <div className="big accent">{currency(recoverableMonthly)}</div>
          <div className="sub">per month, from cancelled charges</div>
        </div>
      </div>
    </>
  );
}

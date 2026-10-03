import { currency } from '../lib/format';
import type { FinanceData } from '../types';

export default function Brief({ data }: { data: FinanceData }) {
  const b = data.brief;
  return (
    <>
      <h2 className="section-title">Monthly money brief</h2>
      <p className="section-sub">
        Deterministic summary generated from your actual data. No model, no
        guesses, every number traces back to the pipeline.
      </p>
      <div className="card">
        <ul className="brief-list">
          {b.bullets.map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      </div>

      {b.anomalies.length > 0 && (
        <>
          <h2 className="section-title">Worth a second look</h2>
          <p className="section-sub">
            Transactions over 2.5x their category's monthly average.
          </p>
          <div className="card" style={{ padding: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Description</th>
                  <th>Category</th>
                  <th className="num">Amount</th>
                  <th className="num">Multiple</th>
                </tr>
              </thead>
              <tbody>
                {b.anomalies.map((a) => (
                  <tr key={`${a.date}-${a.description}`}>
                    <td>{a.date}</td>
                    <td>{a.description}</td>
                    <td>{a.category}</td>
                    <td className="num">{currency(a.amount)}</td>
                    <td className="num">{a.multiple}x</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}

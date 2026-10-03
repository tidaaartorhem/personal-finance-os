import { currency0, monthLabel } from '../lib/format';
import type { CategoryTotal, MonthPoint } from '../types';

/** Grouped monthly income vs expense bar chart, hand-rolled SVG. */
export function MonthlyChart({ series }: { series: MonthPoint[] }) {
  const W = 640;
  const H = 260;
  const PAD = { top: 16, right: 8, bottom: 34, left: 56 };
  const iw = W - PAD.left - PAD.right;
  const ih = H - PAD.top - PAD.bottom;
  const max = Math.max(...series.map((s) => Math.max(s.income, s.expenses))) * 1.1;
  const n = series.length;
  const groupW = iw / n;
  const barW = Math.min(26, groupW * 0.32);
  const y = (v: number) => PAD.top + ih - (v / max) * ih;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height: 'auto' }} role="img" aria-label="Monthly income versus expenses">
      {[0.25, 0.5, 0.75, 1].map((f) => (
        <g key={f}>
          <line x1={PAD.left} x2={W - PAD.right} y1={y(max * f)} y2={y(max * f)} stroke="#eef2f0" />
          <text x={PAD.left - 8} y={y(max * f) + 4} textAnchor="end" fontSize={11} fill="#64716d">
            {currency0(max * f)}
          </text>
        </g>
      ))}
      {series.map((s, i) => {
        const cx = PAD.left + groupW * i + groupW / 2;
        return (
          <g key={s.month}>
            <rect x={cx - barW - 3} y={y(s.income)} width={barW} height={Math.max(1, PAD.top + ih - y(s.income))} rx={3} fill="#0e6f5c" />
            <rect x={cx + 3} y={y(s.expenses)} width={barW} height={Math.max(1, PAD.top + ih - y(s.expenses))} rx={3} fill="#c0564f" />
            <text x={cx} y={H - 10} textAnchor="middle" fontSize={12} fill="#64716d">
              {monthLabel(s.month)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export function Legend() {
  return (
    <div style={{ display: 'flex', gap: 20, marginBottom: 8, fontSize: 13, color: '#64716d' }}>
      <span>
        <span style={{ display: 'inline-block', width: 12, height: 12, background: '#0e6f5c', borderRadius: 3, marginRight: 6 }} />
        Income
      </span>
      <span>
        <span style={{ display: 'inline-block', width: 12, height: 12, background: '#c0564f', borderRadius: 3, marginRight: 6 }} />
        Expenses
      </span>
    </div>
  );
}

/** Horizontal category breakdown bars. */
export function CategoryBars({ categories }: { categories: CategoryTotal[] }) {
  const top = categories.slice(0, 10);
  const max = Math.max(...top.map((c) => c.total));
  return (
    <div>
      {top.map((c) => (
        <div className="bar-row" key={c.category}>
          <div className="bar-label">{c.category}</div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: `${(c.total / max) * 100}%` }} />
          </div>
          <div className="bar-value">{currency0(c.total)}</div>
        </div>
      ))}
    </div>
  );
}

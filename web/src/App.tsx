import { useEffect, useState } from 'react';
import Brief from './components/Brief';
import Overview from './components/Overview';
import Subscriptions from './components/Subscriptions';
import Tax from './components/Tax';
import './styles.css';
import type { FinanceData } from './types';

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'subscriptions', label: 'Subscriptions' },
  { id: 'tax', label: 'Tax' },
  { id: 'brief', label: 'Brief' },
] as const;

type TabId = (typeof TABS)[number]['id'];

export default function App() {
  const [data, setData] = useState<FinanceData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>('overview');

  useEffect(() => {
    fetch('finance.json')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) return <div className="app"><div className="error">Could not load finance.json: {error}</div></div>;
  if (!data) return <div className="app"><div className="loading">Crunching the numbers...</div></div>;

  return (
    <div className="app">
      <header className="header">
        <h1>
          <span className="brand">personal-finance-os</span>
        </h1>
        <p>The cash-flow operating system for independent earners.</p>
        <div className="period">
          Data: {data.period.start} to {data.period.end} · generated{' '}
          {new Date(data.generated_at).toLocaleDateString('en-CA', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </div>
      </header>

      <nav className="tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            className={tab === t.id ? 'active' : ''}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main>
        {tab === 'overview' && <Overview data={data} />}
        {tab === 'subscriptions' && <Subscriptions data={data} />}
        {tab === 'tax' && <Tax data={data} />}
        {tab === 'brief' && <Brief data={data} />}
      </main>

      <footer className="footer">
        Built from your bank CSVs by deterministic rules: no API keys, no model
        calls, every number auditable. Tax figures are planning estimates, not
        tax advice. Sample data is synthetic and clearly labeled.
      </footer>
    </div>
  );
}

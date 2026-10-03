import { describe, expect, it } from 'vitest';
import { confidenceLabel, currency, monthLabel, pct } from './format';

describe('formatting helpers', () => {
  it('formats currency in CAD', () => {
    expect(currency(7652.53)).toContain('7,652.53');
  });

  it('formats rates as percentages', () => {
    expect(pct(0.348)).toBe('34.8%');
  });

  it('labels YYYY-MM months', () => {
    expect(monthLabel('2026-01')).toBe('Jan 2026');
    expect(monthLabel('2026-12')).toBe('Dec 2026');
  });

  it('labels subscription confidence', () => {
    expect(confidenceLabel(0.94)).toBe('High');
    expect(confidenceLabel(0.8)).toBe('Medium');
    expect(confidenceLabel(0.5)).toBe('Low');
  });
});

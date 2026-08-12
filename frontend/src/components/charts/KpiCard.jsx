import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const KpiCard = ({ title, value, unit, change, trend, loading }) => {
  if (loading) {
    return (
      <div className="glass-panel" style={{ height: '140px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div style={{ width: '60%', height: '16px', background: 'var(--border-glass)', borderRadius: '4px', marginBottom: '16px', animation: 'pulse 2s infinite' }}></div>
        <div style={{ width: '80%', height: '32px', background: 'var(--border-glass)', borderRadius: '4px', animation: 'pulse 2s infinite' }}></div>
      </div>
    );
  }

  const isPositive = trend === 'up';
  const isNeutral = trend === 'neutral';
  
  const TrendIcon = isPositive ? TrendingUp : isNeutral ? Minus : TrendingDown;
  const trendColor = isPositive ? 'var(--success)' : isNeutral ? 'var(--text-secondary)' : 'var(--danger)';

  // Format value beautifully
  let displayValue = value;
  if (typeof value === 'number') {
    if (unit === 'USD' || unit === '$') {
      displayValue = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
      unit = '';
    } else {
      displayValue = new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value);
    }
  }

  return (
    <div className="glass-panel" style={{ padding: '20px', transition: 'transform 0.2s', cursor: 'default' }}
      onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'}
      onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}
    >
      <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', fontWeight: 500, marginBottom: '8px' }}>
        {title}
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '12px' }}>
        <span style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-display)' }}>
          {displayValue}
        </span>
        {unit && <span style={{ color: 'var(--text-secondary)', fontSize: '1rem', fontWeight: 500 }}>{unit}</span>}
      </div>
      
      {change !== undefined && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
          <div style={{ 
            display: 'flex', alignItems: 'center', gap: '4px', 
            background: `rgba(${isPositive ? '5, 205, 153' : isNeutral ? '163, 174, 208' : '238, 93, 80'}, 0.1)`, 
            color: trendColor, 
            padding: '4px 8px', borderRadius: '20px', fontWeight: 600 
          }}>
            <TrendIcon size={14} />
            {change > 0 ? '+' : ''}{change}%
          </div>
          <span style={{ color: 'var(--text-secondary)' }}>vs last month</span>
        </div>
      )}
    </div>
  );
};

export default KpiCard;

import React, { useState, useEffect } from 'react';
import { Lightbulb, TrendingUp, AlertTriangle, Link as LinkIcon, PieChart, CheckCircle } from 'lucide-react';
import api from '../api/axios';

const AIInsightsPage = () => {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    try {
      const res = await api.get('/insights');
      setInsights(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      await api.post(`/insights/${id}/read`);
      setInsights(insights.map(i => i.id === id ? { ...i, is_read: true } : i));
    } catch (e) {
      console.error(e);
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'trend': return <TrendingUp size={24} color="var(--primary)" />;
      case 'anomaly': return <AlertTriangle size={24} color="var(--danger)" />;
      case 'correlation': return <LinkIcon size={24} color="var(--secondary)" />;
      case 'segment': return <PieChart size={24} color="var(--accent)" />;
      default: return <Lightbulb size={24} color="var(--primary)" />;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>AI Data Insights</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Automated discoveries and anomalies found in your datasets.</p>
        </div>
      </div>

      {loading ? (
        <p>Loading insights...</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {insights.map(insight => (
            <div key={insight.id} className="glass-panel animate-fade-in" style={{ 
              display: 'flex', gap: '20px', 
              opacity: insight.is_read ? 0.7 : 1,
              borderLeft: insight.is_read ? '1px solid var(--border-glass)' : `4px solid ${insight.impact_level === 'high' ? 'var(--danger)' : 'var(--primary)'}`
            }}>
              <div style={{ 
                width: 50, height: 50, borderRadius: '50%', 
                background: 'var(--bg-main)', display: 'flex', alignItems: 'center', justifyContent: 'center' 
              }}>
                {getIcon(insight.type)}
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{insight.title}</h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{new Date(insight.created_at).toLocaleDateString()}</span>
                    <span style={{ 
                      fontSize: '0.75rem', 
                      background: insight.impact_level === 'high' ? 'rgba(238, 93, 80, 0.1)' : 'rgba(108, 99, 255, 0.1)', 
                      color: insight.impact_level === 'high' ? 'var(--danger)' : 'var(--primary)',
                      padding: '4px 10px', borderRadius: '12px', fontWeight: 600, textTransform: 'capitalize'
                    }}>
                      {insight.impact_level} Impact
                    </span>
                  </div>
                </div>
                
                <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '16px', fontSize: '0.95rem' }}>
                  {insight.description.split('**').map((part, i) => i % 2 === 1 ? <strong key={i} style={{ color: 'var(--text-primary)' }}>{part}</strong> : part)}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <div style={{ fontSize: '0.8rem', background: 'var(--bg-main)', padding: '6px 12px', borderRadius: '6px', border: '1px solid var(--border-glass)' }}>
                      Confidence: <strong>{Math.round(insight.confidence_score * 100)}%</strong>
                    </div>
                  </div>
                  
                  {!insight.is_read && (
                    <button 
                      onClick={() => markAsRead(insight.id)}
                      style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}
                      onMouseOver={(e) => e.currentTarget.style.color = 'var(--primary)'}
                      onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
                    >
                      <CheckCircle size={16} /> Mark Read
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AIInsightsPage;

import React, { useState, useEffect } from 'react';
import { Target, CheckCircle2, ChevronRight, AlertCircle, ArrowRight } from 'lucide-react';
import api from '../api/axios';

const RecommendationCenterPage = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecs = async () => {
      try {
        const res = await api.get('/insights/recommendations');
        setRecommendations(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchRecs();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Recommendation Center</h2>
          <p style={{ color: 'var(--text-secondary)' }}>AI-driven business strategies based on your data.</p>
        </div>
      </div>

      {loading ? (
        <p>Generating recommendations...</p>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '24px' }}>
          {recommendations.map(rec => (
            <div key={rec.id} className="glass-panel animate-fade-in" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ 
                    width: 36, height: 36, borderRadius: '8px', 
                    background: rec.priority === 1 ? 'rgba(238, 93, 80, 0.1)' : rec.priority === 2 ? 'rgba(255, 206, 32, 0.1)' : 'rgba(108, 99, 255, 0.1)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center' 
                  }}>
                    <Target size={20} color={rec.priority === 1 ? 'var(--danger)' : rec.priority === 2 ? 'var(--warning)' : 'var(--primary)'} />
                  </div>
                  <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{rec.title}</h3>
                </div>
              </div>
              
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.5, marginBottom: '20px' }}>
                {rec.description}
              </p>

              <div style={{ background: 'var(--bg-main)', padding: '16px', borderRadius: '8px', marginBottom: '20px', flex: 1, border: '1px solid var(--border-glass)' }}>
                <h4 style={{ fontSize: '0.85rem', color: 'var(--text-primary)', marginBottom: '12px', textTransform: 'uppercase' }}>Action Plan</h4>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {rec.action_items.map((item, idx) => (
                    <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                      <ChevronRight size={16} color="var(--primary)" style={{ marginTop: '2px', flexShrink: 0 }} />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', background: 'rgba(5, 205, 153, 0.05)', border: '1px solid rgba(5, 205, 153, 0.2)', padding: '12px', borderRadius: '8px', marginBottom: '20px' }}>
                <CheckCircle2 size={16} color="var(--success)" />
                <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', fontWeight: 500 }}>Impact: {rec.expected_impact}</span>
              </div>
              
              <button className="btn btn-primary" style={{ width: '100%' }}>
                Create Task <ArrowRight size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecommendationCenterPage;

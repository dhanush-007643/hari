import React, { useState, useEffect } from 'react';
import { Calendar, Download, RefreshCw, ArrowUpRight } from 'lucide-react';
import KpiCard from '../components/charts/KpiCard';
import BaseChart from '../components/charts/BaseChart';
import api from '../api/axios';
import { useNavigate } from 'react-router-dom';

const DashboardPage = () => {
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState([]);
  const [revenueData, setRevenueData] = useState(null);
  const [ordersData, setOrdersData] = useState(null);
  const [topProducts, setTopProducts] = useState(null);
  const [insights, setInsights] = useState([]);
  const navigate = useNavigate();

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [kpiRes, revRes, ordRes, prodRes, insRes] = await Promise.all([
        api.get('/analytics/kpis'),
        api.get('/analytics/charts/monthly-revenue'),
        api.get('/analytics/charts/orders-by-status'),
        api.get('/analytics/charts/top-products?limit=5'),
        api.get('/insights?limit=3')
      ]);

      setKpis(kpiRes.data);
      setRevenueData(revRes.data);
      
      // Transform order data for chart.js
      setOrdersData({
        labels: ordRes.data.labels,
        datasets: [{
          data: ordRes.data.data,
          backgroundColor: ordRes.data.backgroundColor,
          borderWidth: 0,
          hoverOffset: 4
        }]
      });

      setTopProducts(prodRes.data);
      setInsights(insRes.data);
    } catch (e) {
      console.error('Failed to load dashboard data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Executive Dashboard</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Welcome back. Here's what's happening with your business today.</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <div className="glass-panel" style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <Calendar size={18} color="var(--primary)" />
            <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>Last 30 Days</span>
          </div>
          <button className="btn btn-outline" onClick={fetchDashboardData} disabled={loading} style={{ padding: '8px' }}>
            <RefreshCw size={18} className={loading ? 'spin' : ''} />
          </button>
          <button className="btn btn-primary" onClick={() => navigate('/reports')}>
            <Download size={18} /> Export
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
        {loading ? (
          Array(4).fill(0).map((_, i) => <KpiCard key={i} loading={true} />)
        ) : (
          kpis.slice(0, 4).map((kpi, i) => (
            <KpiCard 
              key={i}
              title={kpi.name}
              value={kpi.value}
              unit={kpi.unit}
              change={kpi.change_percent}
              trend={kpi.trend}
            />
          ))
        )}
      </div>

      {/* Main Charts Area */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        
        {/* Left Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0 }}>Revenue Overview</h3>
              <button className="btn btn-outline" style={{ padding: '4px 12px', fontSize: '0.85rem' }} onClick={() => navigate('/analytics')}>View Details</button>
            </div>
            <BaseChart type="line" data={revenueData} height={320} />
          </div>

          <div className="glass-panel">
            <h3 style={{ margin: 0, marginBottom: '20px' }}>Top Products by Revenue</h3>
            {topProducts ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {topProducts.labels.map((label, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <div style={{ width: '30px', fontWeight: 600, color: 'var(--text-secondary)' }}>#{idx + 1}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <span style={{ fontWeight: 500 }}>{label}</span>
                        <span style={{ fontWeight: 600, color: 'var(--primary)' }}>${(topProducts.data[idx]/1000).toFixed(1)}k</span>
                      </div>
                      <div style={{ width: '100%', height: '8px', background: 'var(--border-glass)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ width: `${(topProducts.data[idx] / Math.max(...topProducts.data)) * 100}%`, height: '100%', background: 'var(--primary)', borderRadius: '4px' }}></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading...</div>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <div className="glass-panel">
            <h3 style={{ margin: 0, marginBottom: '20px' }}>Order Status</h3>
            <BaseChart type="doughnut" data={ordersData} height={250} />
          </div>

          <div className="glass-panel" style={{ flex: 1 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0 }}>AI Insights</h3>
              <ArrowUpRight size={20} color="var(--primary)" style={{ cursor: 'pointer' }} onClick={() => navigate('/insights')} />
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {insights.map(insight => (
                <div key={insight.id} style={{ 
                  padding: '16px', borderRadius: '12px', 
                  background: 'var(--bg-main)', border: '1px solid var(--border-glass)'
                }}>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ 
                      width: 8, height: 8, borderRadius: '50%', 
                      background: insight.impact_level === 'high' ? 'var(--danger)' : 'var(--warning)' 
                    }}></div>
                    <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>{insight.title}</span>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                    {insight.description}
                  </p>
                </div>
              ))}
            </div>
            <button className="btn btn-outline" style={{ width: '100%', marginTop: '16px' }} onClick={() => navigate('/insights')}>
              View All Insights
            </button>
          </div>

        </div>
      </div>
    </div>
  );
};

export default DashboardPage;

import React, { useState, useEffect } from 'react';
import { Filter, Download } from 'lucide-react';
import BaseChart from '../components/charts/BaseChart';
import api from '../api/axios';

const AnalyticsPage = () => {
  const [loading, setLoading] = useState(true);
  const [revenueRegionData, setRevenueRegionData] = useState(null);
  const [customerSegmentsData, setCustomerSegmentsData] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [regRes, segRes, heatRes] = await Promise.all([
          api.get('/analytics/charts/revenue-by-region'),
          api.get('/analytics/charts/customer-segments'),
          api.get('/analytics/charts/revenue-heatmap')
        ]);

        // Transform region data
        setRevenueRegionData({
          labels: regRes.data.labels,
          datasets: regRes.data.datasets.map(ds => ({
            ...ds,
            borderRadius: 6
          }))
        });

        // Transform scatter data
        const datasets = Object.keys(segRes.data.segments).map(segName => ({
          label: segName,
          data: segRes.data.data.filter(d => d.segment === segName),
          backgroundColor: segRes.data.segments[segName],
        }));
        setCustomerSegmentsData({ datasets });

        // Heatmap custom rendering is complex with chart.js, we will use a grid layout instead for simplicity
        setHeatmapData(heatRes.data);

      } catch (e) {
        console.error("Failed to load analytics");
      } finally {
        setLoading(false);
      }
    };
    fetchAnalytics();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>Deep Analytics</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Explore your data dimensions in detail.</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-outline">
            <Filter size={18} /> Add Filter
          </button>
          <button className="btn btn-outline">
            <Download size={18} /> Export
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="glass-panel">
          <h3 style={{ marginBottom: '20px' }}>Revenue by Region (YoY)</h3>
          <BaseChart type="bar" data={revenueRegionData} height={350} />
        </div>

        <div className="glass-panel">
          <h3 style={{ marginBottom: '20px' }}>Customer Segmentation</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '-10px', marginBottom: '20px' }}>
            X-Axis: Order Frequency | Y-Axis: Customer Lifetime Value
          </p>
          <BaseChart type="scatter" data={customerSegmentsData} height={350} />
        </div>
      </div>

      <div className="glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ margin: 0 }}>Revenue Heatmap (Day vs Hour)</h3>
        </div>
        
        {loading || !heatmapData ? (
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading...</div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ padding: '8px', color: 'var(--text-secondary)' }}></th>
                  {heatmapData.hours.map(h => (
                    <th key={h} style={{ padding: '8px', fontSize: '0.8rem', color: 'var(--text-secondary)', fontWeight: 500 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {heatmapData.days.map(day => (
                  <tr key={day}>
                    <td style={{ padding: '8px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{day}</td>
                    {heatmapData.hours.map(hour => {
                      const point = heatmapData.data.find(d => d.day === day && d.hour === hour);
                      const val = point ? point.value : 0;
                      // Calculate opacity based on max value (~25000)
                      const intensity = Math.min(1, val / 25000);
                      return (
                        <td key={`${day}-${hour}`} style={{ padding: '2px' }}>
                          <div 
                            title={`$${val.toLocaleString()}`}
                            style={{ 
                              height: '30px', 
                              background: `rgba(108, 99, 255, ${intensity})`,
                              borderRadius: '4px',
                              border: '1px solid rgba(255,255,255,0.1)'
                            }}
                          ></div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalyticsPage;

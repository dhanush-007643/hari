import React, { useState, useEffect } from 'react';
import { FileText, Download, Plus, FileSpreadsheet, Trash2 } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';

const ReportsPage = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  
  // Form state
  const [reportName, setReportName] = useState('');
  const [reportFormat, setReportFormat] = useState('pdf');
  const [reportType, setReportType] = useState('business_summary');

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const res = await api.get('/reports');
      setReports(res.data);
    } catch (e) {
      toast.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!reportName) {
      toast.error('Please enter a report name');
      return;
    }
    setGenerating(true);
    try {
      await api.post('/reports/generate', {
        name: reportName,
        format: reportFormat,
        report_type: reportType
      });
      toast.success('Report generated successfully!');
      fetchReports();
      setReportName('');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/reports/${id}`);
      toast.success('Report deleted');
      fetchReports();
    } catch (e) {
      toast.error('Failed to delete report');
    }
  };

  const getFormatIcon = (format) => {
    if (format === 'excel' || format === 'csv') return <FileSpreadsheet size={20} color="var(--success)" />;
    return <FileText size={20} color="var(--danger)" />;
  };

  return (
    <div style={{ display: 'flex', gap: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* Left: Report List */}
      <div style={{ flex: 2, display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2>Report Archive</h2>
            <p style={{ color: 'var(--text-secondary)' }}>Download generated business reports.</p>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead style={{ background: 'var(--bg-main)' }}>
              <tr>
                <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Report Name</th>
                <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Type</th>
                <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>Date</th>
                <th style={{ padding: '16px', fontWeight: 600, color: 'var(--text-secondary)', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={4} style={{ padding: '24px', textAlign: 'center' }}>Loading...</td></tr>
              ) : reports.length === 0 ? (
                <tr><td colSpan={4} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>No reports generated yet.</td></tr>
              ) : reports.map(r => (
                <tr key={r.id} style={{ borderTop: '1px solid var(--border-glass)' }}>
                  <td style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {getFormatIcon(r.format)}
                    <span style={{ fontWeight: 500 }}>{r.name}</span>
                  </td>
                  <td style={{ padding: '16px', color: 'var(--text-secondary)' }}>{r.report_type.replace('_', ' ')}</td>
                  <td style={{ padding: '16px', color: 'var(--text-secondary)' }}>{new Date(r.created_at).toLocaleDateString()}</td>
                  <td style={{ padding: '16px', textAlign: 'right' }}>
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                      {r.has_file && (
                        <a 
                          href={`/api/v1/reports/${r.id}/download`} 
                          download
                          className="btn btn-outline" 
                          style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                        >
                          <Download size={14} /> Download
                        </a>
                      )}
                      <button 
                        onClick={() => handleDelete(r.id)}
                        className="btn btn-outline" 
                        style={{ padding: '6px', color: 'var(--danger)', borderColor: 'transparent' }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Right: Generate Form */}
      <div style={{ flex: 1 }}>
        <div className="glass-panel" style={{ position: 'sticky', top: '100px' }}>
          <h3 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Plus size={20} color="var(--primary)" /> New Report
          </h3>
          
          <form onSubmit={handleGenerate} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', fontWeight: 500 }}>Report Name</label>
              <input 
                type="text" value={reportName} onChange={e => setReportName(e.target.value)}
                placeholder="e.g. Q4 Executive Summary" required
                style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-glass)', background: 'var(--bg-main)', color: 'var(--text-primary)' }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', fontWeight: 500 }}>Report Type</label>
              <select 
                value={reportType} onChange={e => setReportType(e.target.value)}
                style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-glass)', background: 'var(--bg-main)', color: 'var(--text-primary)' }}
              >
                <option value="business_summary">Complete Business Summary</option>
                <option value="kpi">KPI & Metrics Only</option>
                <option value="prediction">Predictions & Models</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', fontWeight: 500 }}>Export Format</label>
              <div style={{ display: 'flex', gap: '12px' }}>
                {['pdf', 'excel', 'csv'].map(fmt => (
                  <label key={fmt} style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '10px', border: `1px solid ${reportFormat === fmt ? 'var(--primary)' : 'var(--border-glass)'}`, borderRadius: '8px', cursor: 'pointer', background: reportFormat === fmt ? 'rgba(108, 99, 255, 0.1)' : 'var(--bg-main)' }}>
                    <input type="radio" name="format" value={fmt} checked={reportFormat === fmt} onChange={() => setReportFormat(fmt)} style={{ display: 'none' }} />
                    <span style={{ textTransform: 'uppercase', fontWeight: 500, color: reportFormat === fmt ? 'var(--primary)' : 'var(--text-secondary)', fontSize: '0.85rem' }}>{fmt}</span>
                  </label>
                ))}
              </div>
            </div>

            <button type="submit" className="btn btn-primary" disabled={generating} style={{ marginTop: '10px', padding: '12px' }}>
              {generating ? 'Generating...' : 'Generate Report'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;

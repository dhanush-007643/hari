import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Table as TableIcon, Clock, Save, Star, ChevronDown, CheckCircle2, AlertCircle } from 'lucide-react';
import NLQInput from '../components/NLQInput';
import SQLEditor from '../components/SQLEditor';
import api from '../api/axios';
import toast from 'react-hot-toast';

const SQLPlaygroundPage = () => {
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [activeTab, setActiveTab] = useState('results'); // results, explanation, nlp

  // Check if passed a query from Navbar search
  useEffect(() => {
    if (location.state?.query) {
      handleNLQSubmit(location.state.query);
    }
    fetchHistory();
  }, [location.state]);

  const fetchHistory = async () => {
    try {
      const res = await api.get('/queries/history');
      setHistory(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleNLQSubmit = async (query) => {
    setLoading(true);
    setResult(null);
    try {
      const res = await api.post('/queries/nlq', { query });
      setResult(res.data);
      toast.success('Query processed successfully');
      fetchHistory(); // refresh history
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to process query');
    } finally {
      setLoading(false);
    }
  };

  const handleSQLExecute = async (sql) => {
    setLoading(true);
    try {
      const res = await api.post('/queries/execute', { sql });
      setResult(prev => ({
        ...prev,
        generated_sql: sql,
        results: res.data,
        explanation: 'Custom SQL execution.',
        intent: 'CUSTOM_SQL',
        error: null
      }));
      toast.success('Query executed');
    } catch (e) {
      setResult(prev => ({
        ...prev,
        generated_sql: sql,
        error: e.response?.data?.detail || 'SQL Execution failed'
      }));
      toast.error('SQL Execution failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveQuery = async () => {
    if (!result?.query_id) return;
    try {
      await api.post('/queries/save', {
        query_id: result.query_id,
        name: `Query ${new Date().toLocaleDateString()}`,
        is_favorite: true
      });
      toast.success('Query saved to favorites');
    } catch (e) {
      toast.error('Failed to save query');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2>SQL Playground</h2>
          <p style={{ color: 'var(--text-secondary)' }}>Convert natural language to SQL and explore your data</p>
        </div>
        <button 
          className="btn btn-outline" 
          onClick={() => setShowHistory(!showHistory)}
        >
          <Clock size={18} /> {showHistory ? 'Hide History' : 'Query History'}
        </button>
      </div>

      {showHistory && (
        <div className="glass-panel animate-fade-in" style={{ padding: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '12px' }}>Recent Queries</h3>
          <div style={{ display: 'flex', gap: '12px', overflowX: 'auto', paddingBottom: '8px' }}>
            {history.length === 0 ? <p style={{ color: 'var(--text-secondary)' }}>No recent queries.</p> : history.map(h => (
              <div 
                key={h.id} 
                onClick={() => handleNLQSubmit(h.natural_language_query)}
                style={{ 
                  background: 'var(--bg-main)', padding: '12px', borderRadius: '8px', 
                  minWidth: '250px', cursor: 'pointer', border: '1px solid var(--border-glass)'
                }}
              >
                <div style={{ fontSize: '0.9rem', fontWeight: 500, marginBottom: '8px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  "{h.natural_language_query}"
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  <span>{h.status === 'success' ? <CheckCircle2 size={12} color="var(--success)"/> : <AlertCircle size={12} color="var(--danger)"/>} {h.row_count_returned} rows</span>
                  <span>{new Date(h.created_at).toLocaleTimeString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input Section */}
      <div style={{ padding: '20px 0' }}>
        <NLQInput 
          onQuerySubmit={handleNLQSubmit} 
          disabled={loading} 
          initialQuery={location.state?.query || ''} 
        />
      </div>

      {/* Editor & Results Section */}
      <div style={{ display: 'flex', gap: '24px', flex: 1, minHeight: '500px' }}>
        
        {/* Left Side - Editor & Details */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
            <SQLEditor 
              initialSql={result?.generated_sql || ''} 
              onExecute={handleSQLExecute}
              disabled={loading}
            />
          </div>

          {result && !result.error && (
            <div className="glass-panel animate-fade-in" style={{ flex: 1 }}>
              <div style={{ display: 'flex', gap: '16px', borderBottom: '1px solid var(--border-glass)', marginBottom: '16px' }}>
                <button 
                  style={{ background: 'transparent', border: 'none', borderBottom: activeTab === 'explanation' ? '2px solid var(--primary)' : '2px solid transparent', padding: '8px 16px', color: activeTab === 'explanation' ? 'var(--primary)' : 'var(--text-secondary)', fontWeight: 500, cursor: 'pointer' }}
                  onClick={() => setActiveTab('explanation')}
                >
                  AI Explanation
                </button>
                <button 
                  style={{ background: 'transparent', border: 'none', borderBottom: activeTab === 'nlp' ? '2px solid var(--primary)' : '2px solid transparent', padding: '8px 16px', color: activeTab === 'nlp' ? 'var(--primary)' : 'var(--text-secondary)', fontWeight: 500, cursor: 'pointer' }}
                  onClick={() => setActiveTab('nlp')}
                >
                  NLP Analysis
                </button>
              </div>

              {activeTab === 'explanation' && (
                <div style={{ lineHeight: 1.6 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <div style={{ background: 'rgba(108, 99, 255, 0.1)', color: 'var(--primary)', padding: '4px 12px', borderRadius: '12px', fontSize: '0.85rem', fontWeight: 600 }}>
                      Intent: {result.intent}
                    </div>
                    <div style={{ background: result.confidence > 0.8 ? 'rgba(5, 205, 153, 0.1)' : 'rgba(255, 206, 32, 0.1)', color: result.confidence > 0.8 ? 'var(--success)' : 'var(--warning)', padding: '4px 12px', borderRadius: '12px', fontSize: '0.85rem', fontWeight: 600 }}>
                      Confidence: {Math.round(result.confidence * 100)}%
                    </div>
                  </div>
                  <p>{result.explanation}</p>
                </div>
              )}

              {activeTab === 'nlp' && result.nlp_analysis && (
                <div>
                  <pre style={{ background: 'var(--bg-main)', padding: '16px', borderRadius: '8px', fontSize: '0.9rem', overflowX: 'auto', border: '1px solid var(--border-glass)' }}>
                    {JSON.stringify(result.nlp_analysis, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Side - Results Table */}
        <div className="glass-panel" style={{ flex: 1.5, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontSize: '1.1rem', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <TableIcon size={20} color="var(--primary)" /> Query Results
            </h3>
            {result && !result.error && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {result.results?.row_count || 0} rows in {result.results?.execution_time_ms || 0}ms
                </span>
                <button onClick={handleSaveQuery} className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '0.85rem' }}>
                  <Save size={14} /> Save
                </button>
              </div>
            )}
          </div>

          {loading ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
              Executing query...
            </div>
          ) : result?.error ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--danger)', background: 'rgba(238, 93, 80, 0.05)', borderRadius: '12px', border: '1px solid rgba(238, 93, 80, 0.2)', padding: '24px', textAlign: 'center' }}>
              <AlertCircle size={48} style={{ marginBottom: '16px' }} />
              <h4 style={{ margin: 0, marginBottom: '8px' }}>Execution Failed</h4>
              <p style={{ fontSize: '0.9rem' }}>{result.error}</p>
            </div>
          ) : result?.results?.rows?.length > 0 ? (
            <div style={{ flex: 1, overflow: 'auto', borderRadius: '8px', border: '1px solid var(--border-glass)' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', backdropFilter: 'blur(10px)', zIndex: 10 }}>
                  <tr>
                    {result.results.columns.map(col => (
                      <th key={col} style={{ padding: '12px 16px', borderBottom: '2px solid var(--border-glass)', fontWeight: 600, fontSize: '0.9rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                        {col.replace(/_/g, ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.results.rows.map((row, r_idx) => (
                    <tr key={r_idx} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                      {result.results.columns.map(col => (
                        <td key={col} style={{ padding: '10px 16px', fontSize: '0.9rem' }}>
                          {row[col] !== null ? row[col].toString() : <span style={{ color: 'var(--text-secondary)', fontStyle: 'italic' }}>null</span>}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : result ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
              No data returned.
            </div>
          ) : (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
              <Database size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
              <p>Enter a natural language query or SQL to view results.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SQLPlaygroundPage;

import React, { useState, useEffect } from 'react';
import { Play, Copy, CheckCircle2 } from 'lucide-react';

const SQLEditor = ({ initialSql, onExecute, disabled }) => {
  const [sql, setSql] = useState(initialSql || '');
  const [copied, setCopied] = useState(false);

  // Update internal state when initialSql prop changes
  useEffect(() => {
    setSql(initialSql || '');
  }, [initialSql]);

  const handleCopy = () => {
    if (!sql) return;
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleKeyDown = (e) => {
    // Ctrl + Enter / Cmd + Enter to execute query
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (sql.trim() && !disabled) {
        onExecute(sql);
      }
    }
  };

  return (
    <div style={{
      borderRadius: '12px',
      overflow: 'hidden',
      border: '1px solid var(--border-glass)',
      background: '#181A20',
      display: 'flex',
      flexDirection: 'column',
      boxShadow: '0 8px 24px rgba(0, 0, 0, 0.2)'
    }}>
      {/* Editor Header Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '10px 16px',
        background: '#222630',
        borderBottom: '1px solid #2E3440'
      }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div style={{ width: 11, height: 11, borderRadius: '50%', background: '#FF5F56' }}></div>
          <div style={{ width: 11, height: 11, borderRadius: '50%', background: '#FFBD2E' }}></div>
          <div style={{ width: 11, height: 11, borderRadius: '50%', background: '#27C93F' }}></div>
          <span style={{ marginLeft: '12px', color: '#A0AEC0', fontSize: '0.85rem', fontFamily: 'monospace' }}>
            SQL Query Editor <span style={{ fontSize: '0.75rem', opacity: 0.7 }}>(Ctrl+Enter to run)</span>
          </span>
        </div>
        
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button 
            type="button"
            onClick={handleCopy}
            title="Copy SQL to clipboard"
            style={{
              background: 'transparent',
              border: '1px solid #3A3F4D',
              color: '#CBD5E0',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '6px',
              fontSize: '0.82rem',
              transition: 'background 0.2s'
            }}
            onMouseOver={(e) => e.currentTarget.style.background = '#2E3440'}
            onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
          >
            {copied ? <CheckCircle2 size={14} color="#27C93F" /> : <Copy size={14} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
          
          <button 
            type="button"
            onClick={() => onExecute(sql)}
            disabled={disabled || !sql.trim()}
            style={{
              background: 'var(--primary)',
              border: 'none',
              color: 'white',
              cursor: disabled || !sql.trim() ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 16px',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '0.85rem',
              opacity: disabled || !sql.trim() ? 0.6 : 1,
              transition: 'opacity 0.2s'
            }}
          >
            <Play size={15} fill="currentColor" /> {disabled ? 'Running...' : 'Execute'}
          </button>
        </div>
      </div>

      {/* Code Textarea */}
      <div style={{ padding: '16px', position: 'relative' }}>
        <textarea
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="-- Enter SQL query here (e.g. SELECT * FROM sales_orders LIMIT 10;)"
          spellCheck="false"
          rows={6}
          style={{
            width: '100%',
            fontFamily: '"Fira Code", Consolas, Monaco, "Courier New", monospace',
            fontSize: '14px',
            lineHeight: '1.6',
            color: '#E2E8F0',
            background: 'transparent',
            border: 'none',
            outline: 'none',
            resize: 'vertical',
            minHeight: '140px',
            boxSizing: 'border-box'
          }}
        />
      </div>
    </div>
  );
};

export default SQLEditor;

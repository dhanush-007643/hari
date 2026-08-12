import React, { useState } from 'react';
import { Play, Copy, CheckCircle2 } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const SQLEditor = ({ initialSql, onExecute, disabled }) => {
  const [sql, setSql] = useState(initialSql || '');
  const [copied, setCopied] = useState(false);

  // Update internal state when props change
  React.useEffect(() => {
    setSql(initialSql || '');
  }, [initialSql]);

  const handleCopy = () => {
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{
      borderRadius: '12px',
      overflow: 'hidden',
      border: '1px solid var(--border-glass)',
      background: '#1E1E1E',
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 16px',
        background: '#2D2D2D',
        borderBottom: '1px solid #404040'
      }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#FF5F56' }}></div>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#FFBD2E' }}></div>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#27C93F' }}></div>
          <span style={{ marginLeft: '12px', color: '#A0A0A0', fontSize: '0.85rem', fontFamily: 'monospace' }}>Generated SQL</span>
        </div>
        
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={handleCopy}
            title="Copy SQL"
            style={{
              background: 'transparent', border: 'none', color: '#A0A0A0', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '4px', padding: '4px 8px', borderRadius: '4px'
            }}
            onMouseOver={(e) => e.currentTarget.style.background = '#404040'}
            onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
          >
            {copied ? <CheckCircle2 size={16} color="#27C93F" /> : <Copy size={16} />}
          </button>
          <button 
            onClick={() => onExecute(sql)}
            disabled={disabled || !sql.trim()}
            style={{
              background: 'var(--primary)', border: 'none', color: 'white', cursor: disabled ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 16px', borderRadius: '6px',
              fontWeight: 500, opacity: disabled ? 0.7 : 1
            }}
          >
            <Play size={16} /> Execute
          </button>
        </div>
      </div>

      <div style={{ position: 'relative' }}>
        <textarea
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          spellCheck="false"
          style={{
            position: 'absolute',
            top: 0, left: 0, right: 0, bottom: 0,
            width: '100%', height: '100%',
            padding: '16px', margin: 0,
            fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
            fontSize: '14px', lineHeight: '1.5',
            color: 'transparent', background: 'transparent',
            caretColor: 'white', border: 'none', outline: 'none', resize: 'none',
            zIndex: 1
          }}
        />
        <SyntaxHighlighter 
          language="sql" 
          style={vscDarkPlus}
          customStyle={{
            margin: 0, padding: '16px',
            background: 'transparent', border: 'none',
            fontFamily: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", monospace',
            fontSize: '14px', lineHeight: '1.5',
            minHeight: '150px'
          }}
        >
          {sql || '-- Enter SQL query here'}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};

export default SQLEditor;

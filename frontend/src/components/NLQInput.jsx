import React, { useState, useEffect } from 'react';
import { Search, Sparkles, X, ChevronDown } from 'lucide-react';
import api from '../api/axios';

const NLQInput = ({ onQuerySubmit, disabled, initialQuery = '' }) => {
  const [query, setQuery] = useState(initialQuery);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery);
    }
  }, [initialQuery]);

  const fetchSuggestions = async (input) => {
    try {
      const res = await api.get('/queries/suggestions', { params: { q: input } });
      setSuggestions(res.data);
    } catch (e) {
      console.error('Failed to fetch suggestions');
    }
  };

  const handleInputChange = (e) => {
    const val = e.target.value;
    setQuery(val);
    if (val.length > 2) {
      fetchSuggestions(val);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim().length > 2 && !disabled) {
      setShowSuggestions(false);
      onQuerySubmit(query);
    }
  };

  const selectSuggestion = (suggestion) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    onQuerySubmit(suggestion);
  };

  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: '800px', margin: '0 auto' }}>
      <form onSubmit={handleSubmit} style={{
        display: 'flex',
        alignItems: 'center',
        background: 'var(--bg-card)',
        border: '2px solid var(--primary)',
        borderRadius: '16px',
        padding: '8px 16px',
        boxShadow: '0 8px 32px rgba(108, 99, 255, 0.15)',
        transition: 'all 0.3s ease'
      }}>
        <Sparkles size={24} color="var(--primary)" style={{ marginRight: '12px' }} />
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          disabled={disabled}
          placeholder="Ask a question about your data (e.g. 'Show total revenue by region')"
          style={{
            flex: 1,
            border: 'none',
            background: 'transparent',
            outline: 'none',
            fontSize: '1.1rem',
            color: 'var(--text-primary)',
            padding: '8px 0',
            fontFamily: 'var(--font-sans)'
          }}
          onFocus={() => {
            if (query.length > 2) setShowSuggestions(true);
            else {
              fetchSuggestions('');
              setShowSuggestions(true);
            }
          }}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
        />
        {query && (
          <button 
            type="button"
            onClick={() => setQuery('')}
            style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '4px', marginRight: '8px', color: 'var(--text-secondary)' }}
          >
            <X size={18} />
          </button>
        )}
        <button 
          type="submit" 
          disabled={disabled || query.length < 3}
          className="btn btn-primary"
          style={{ borderRadius: '12px', padding: '8px 24px' }}
        >
          {disabled ? 'Processing...' : 'Ask AI'}
        </button>
      </form>

      {showSuggestions && suggestions.length > 0 && (
        <div className="glass-panel animate-fade-in" style={{
          position: 'absolute',
          top: '110%',
          left: 0,
          right: 0,
          zIndex: 50,
          padding: '8px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px'
        }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', padding: '4px 12px', fontWeight: 600, textTransform: 'uppercase' }}>
            Suggested Queries
          </div>
          {suggestions.map((s, idx) => (
            <button
              key={idx}
              onClick={() => selectSuggestion(s)}
              style={{
                textAlign: 'left',
                padding: '10px 12px',
                background: 'transparent',
                border: 'none',
                borderRadius: '8px',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'background 0.2s',
                fontSize: '0.95rem'
              }}
              onMouseOver={(e) => e.currentTarget.style.background = 'var(--bg-main)'}
              onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
            >
              <Search size={14} color="var(--text-secondary)" />
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default NLQInput;

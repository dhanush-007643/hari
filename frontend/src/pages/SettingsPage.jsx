import React from 'react';
import { Settings as SettingsIcon, Bell, Shield, Database, Layout } from 'lucide-react';
import useAuthStore from '../store/authStore';

const SettingsPage = () => {
  const { user } = useAuthStore();

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2>Settings</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Manage your account and preferences.</p>
      </div>

      <div className="glass-panel">
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
          <Layout size={20} color="var(--primary)" /> Appearance
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 0', borderBottom: '1px solid var(--border-glass)' }}>
          <div>
            <div style={{ fontWeight: 500, marginBottom: '4px' }}>Theme</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Toggle light and dark mode in the navigation bar.</div>
          </div>
        </div>
      </div>

      <div className="glass-panel">
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
          <Bell size={20} color="var(--primary)" /> Notifications
        </h3>
        {['Email alerts for anomalies', 'Weekly summary reports', 'Dataset analysis completion', 'New insight generation'].map((item, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 0', borderBottom: '1px solid var(--border-glass)' }}>
            <div>
              <div style={{ fontWeight: 500, marginBottom: '4px' }}>{item}</div>
            </div>
            <label style={{ position: 'relative', display: 'inline-block', width: '44px', height: '24px' }}>
              <input type="checkbox" defaultChecked={i !== 1} style={{ opacity: 0, width: 0, height: 0 }} />
              <span style={{ 
                position: 'absolute', cursor: 'pointer', top: 0, left: 0, right: 0, bottom: 0, 
                backgroundColor: i !== 1 ? 'var(--primary)' : 'var(--bg-main)', 
                borderRadius: '24px', border: '1px solid var(--border-glass)', transition: '.4s' 
              }}>
                <span style={{
                  position: 'absolute', height: '16px', width: '16px', left: i !== 1 ? '24px' : '4px', bottom: '3px',
                  backgroundColor: 'white', borderRadius: '50%', transition: '.4s'
                }}></span>
              </span>
            </label>
          </div>
        ))}
      </div>

      {user?.is_superuser && (
        <div className="glass-panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <Database size={20} color="var(--primary)" /> System Configuration (Admin)
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 0', borderBottom: '1px solid var(--border-glass)' }}>
            <div>
              <div style={{ fontWeight: 500, marginBottom: '4px' }}>LLM Provider</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Select the backing LLM for text-to-SQL conversions.</div>
            </div>
            <select style={{ padding: '8px', borderRadius: '8px', border: '1px solid var(--border-glass)', background: 'var(--bg-main)', color: 'var(--text-primary)' }}>
              <option>Gemini 1.5 Pro</option>
              <option>Claude 3.5 Sonnet</option>
              <option>GPT-4o</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsPage;

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Database, BrainCircuit, BarChart2 } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-main)' }}>
      {/* Nav */}
      <nav style={{ padding: '20px 40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: '2rem', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
          <span style={{ color: 'var(--primary)' }}>Data</span>Vista<span style={{ color: 'var(--accent)' }}>+</span>
        </h1>
        <div style={{ display: 'flex', gap: '16px' }}>
          <button className="btn btn-outline" onClick={() => navigate('/login')}>Login</button>
          <button className="btn btn-primary" onClick={() => navigate('/register')}>Get Started</button>
        </div>
      </nav>

      {/* Hero */}
      <main style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px', textAlign: 'center' }}>
        <div style={{ maxWidth: '800px' }} className="animate-fade-in">
          <div style={{ display: 'inline-block', padding: '8px 16px', background: 'rgba(108, 99, 255, 0.1)', color: 'var(--primary)', borderRadius: '20px', fontWeight: 600, marginBottom: '24px' }}>
            Enterprise Decision Intelligence
          </div>
          <h1 style={{ fontSize: '4rem', lineHeight: 1.1, marginBottom: '24px', color: 'var(--text-primary)' }}>
            Talk to your data.<br />Make better decisions.
          </h1>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-secondary)', marginBottom: '40px', lineHeight: 1.6 }}>
            DataVista+ transforms natural language into powerful SQL, generates automated insights, 
            and predicts future trends with explainable AI. No coding required.
          </p>
          <div style={{ display: 'flex', gap: '20px', justifyContent: 'center' }}>
            <button className="btn btn-primary" style={{ padding: '16px 32px', fontSize: '1.1rem' }} onClick={() => navigate('/register')}>
              Start Free Trial <ArrowRight size={20} />
            </button>
            <button className="btn btn-outline" style={{ padding: '16px 32px', fontSize: '1.1rem' }} onClick={() => navigate('/login')}>
              Live Demo
            </button>
          </div>

          {/* Features */}
          <div style={{ display: 'flex', gap: '24px', marginTop: '80px', justifyContent: 'center' }}>
            {[
              { icon: <MessageSquare size={32} color="var(--primary)" />, title: 'Natural Language SQL' },
              { icon: <BarChart2 size={32} color="var(--secondary)" />, title: 'Interactive Dashboards' },
              { icon: <BrainCircuit size={32} color="var(--accent)" />, title: 'Explainable ML' },
            ].map((f, i) => (
              <div key={i} className="glass-panel" style={{ flex: 1, padding: '24px', textAlign: 'center' }}>
                <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'center' }}>{f.icon}</div>
                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{f.title}</h3>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};

import { MessageSquare } from 'lucide-react';

export default LandingPage;

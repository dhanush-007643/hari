import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  BarChart2, 
  Database, 
  MessageSquare, 
  BrainCircuit, 
  Lightbulb, 
  CheckCircle,
  FileText,
  Settings,
  Shield,
  Menu,
  ChevronLeft
} from 'lucide-react';
import useAuthStore from '../store/authStore';

const Sidebar = ({ collapsed, setCollapsed }) => {
  const { user } = useAuthStore();

  const navItems = [
    { label: 'Dashboard', icon: <LayoutDashboard size={20} />, path: '/dashboard' },
    { label: 'Analytics', icon: <BarChart2 size={20} />, path: '/analytics' },
    { label: 'SQL Playground', icon: <MessageSquare size={20} />, path: '/sql-playground' },
    { label: 'Datasets', icon: <Database size={20} />, path: '/datasets/upload' },
    { label: 'Predictive Models', icon: <BrainCircuit size={20} />, path: '/predictions' },
    { label: 'AI Insights', icon: <Lightbulb size={20} />, path: '/insights' },
    { label: 'Recommendations', icon: <CheckCircle size={20} />, path: '/recommendations' },
    { label: 'Reports', icon: <FileText size={20} />, path: '/reports' },
  ];

  return (
    <aside 
      className="glass-panel"
      style={{
        position: 'fixed',
        top: '20px',
        bottom: '20px',
        left: '20px',
        width: collapsed ? '80px' : '260px',
        transition: 'width 0.3s ease',
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        padding: collapsed ? '24px 12px' : '24px'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'space-between', marginBottom: '40px' }}>
        {!collapsed && (
          <h2 style={{ margin: 0, fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'var(--primary)' }}>Data</span>Vista<span style={{ color: 'var(--accent)' }}>+</span>
          </h2>
        )}
        <button 
          onClick={() => setCollapsed(!collapsed)}
          style={{ 
            background: 'transparent', 
            border: 'none', 
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            padding: '4px'
          }}
        >
          {collapsed ? <Menu size={24} /> : <ChevronLeft size={24} />}
        </button>
      </div>

      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              justifyContent: collapsed ? 'center' : 'flex-start',
              gap: '12px',
              padding: '12px',
              borderRadius: '12px',
              color: isActive ? 'white' : 'var(--text-secondary)',
              background: isActive ? 'var(--primary)' : 'transparent',
              textDecoration: 'none',
              fontWeight: 500,
              transition: 'all 0.2s ease',
            })}
          >
            {item.icon}
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
        
        {user?.is_superuser && (
          <>
            <div style={{ 
              margin: '20px 0 10px 0', 
              borderBottom: '1px solid var(--border-glass)',
              display: collapsed ? 'none' : 'block' 
            }} />
            <NavLink
              to="/admin"
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                justifyContent: collapsed ? 'center' : 'flex-start',
                gap: '12px',
                padding: '12px',
                borderRadius: '12px',
                color: isActive ? 'white' : 'var(--warning)',
                background: isActive ? 'var(--warning)' : 'transparent',
                textDecoration: 'none',
                fontWeight: 500,
              })}
            >
              <Shield size={20} color={window.location.pathname === '/admin' ? 'white' : 'var(--warning)'} />
              {!collapsed && <span>Admin Panel</span>}
            </NavLink>
          </>
        )}
      </nav>

      <div style={{ marginTop: 'auto' }}>
        <NavLink
          to="/settings"
          style={({ isActive }) => ({
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: '12px',
            padding: '12px',
            borderRadius: '12px',
            color: isActive ? 'white' : 'var(--text-secondary)',
            background: isActive ? 'var(--primary)' : 'transparent',
            textDecoration: 'none',
            fontWeight: 500,
          })}
        >
          <Settings size={20} />
          {!collapsed && <span>Settings</span>}
        </NavLink>
      </div>
    </aside>
  );
};

export default Sidebar;

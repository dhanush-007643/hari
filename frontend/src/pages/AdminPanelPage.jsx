import React, { useState, useEffect } from 'react';
import { Users, Database, ShieldAlert, Activity, FileText } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';
import KpiCard from '../components/charts/KpiCard';

const AdminPanelPage = () => {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      const [statRes, userRes, logRes] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/users'),
        api.get('/admin/audit-logs?limit=10')
      ]);
      setStats(statRes.data);
      setUsers(userRes.data);
      setLogs(logRes.data);
    } catch (e) {
      toast.error('Failed to load admin dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (id) => {
    if (!window.confirm('Are you sure you want to deactivate this user?')) return;
    try {
      await api.delete(`/admin/users/${id}`);
      toast.success('User deactivated');
      fetchAdminData();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to deactivate user');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2>Admin Panel</h2>
        <p style={{ color: 'var(--text-secondary)' }}>System overview, user management, and audit logs.</p>
      </div>

      {loading ? (
        <p>Loading admin panel...</p>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
            <KpiCard title="Total Users" value={stats.total_users} trend="up" change={5} />
            <KpiCard title="Total Queries" value={stats.total_queries} trend="up" change={12} />
            <KpiCard title="Total Datasets" value={stats.total_datasets} trend="neutral" />
            <KpiCard title="API Uptime" value={stats.api_uptime} trend="up" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
            {/* User Management */}
            <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
              <div style={{ padding: '20px', borderBottom: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Users size={20} color="var(--primary)" /> User Management
                </h3>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead style={{ background: 'var(--bg-main)' }}>
                  <tr>
                    <th style={{ padding: '12px 20px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>USERNAME</th>
                    <th style={{ padding: '12px 20px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>EMAIL</th>
                    <th style={{ padding: '12px 20px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>ROLE</th>
                    <th style={{ padding: '12px 20px', fontSize: '0.85rem', color: 'var(--text-secondary)', textAlign: 'right' }}>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => (
                    <tr key={u.id} style={{ borderTop: '1px solid var(--border-glass)', opacity: u.is_active ? 1 : 0.5 }}>
                      <td style={{ padding: '16px 20px', fontWeight: 500 }}>{u.username}</td>
                      <td style={{ padding: '16px 20px', color: 'var(--text-secondary)' }}>{u.email}</td>
                      <td style={{ padding: '16px 20px' }}>
                        <span style={{ 
                          fontSize: '0.75rem', padding: '4px 8px', borderRadius: '12px', fontWeight: 600,
                          background: u.is_superuser ? 'rgba(238, 93, 80, 0.1)' : 'rgba(108, 99, 255, 0.1)',
                          color: u.is_superuser ? 'var(--danger)' : 'var(--primary)'
                        }}>
                          {u.is_superuser ? 'Admin' : u.role || 'User'}
                        </span>
                      </td>
                      <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                        {u.is_active ? (
                          <button onClick={() => handleDeleteUser(u.id)} style={{ background: 'transparent', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}>Deactivate</button>
                        ) : (
                          <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Inactive</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Audit Logs */}
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
              <h3 style={{ margin: 0, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldAlert size={20} color="var(--primary)" /> Recent Audit Logs
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flex: 1, overflowY: 'auto' }}>
                {logs.map(log => (
                  <div key={log.id} style={{ borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{log.action}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{new Date(log.created_at).toLocaleString()}</span>
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      User: <span style={{ color: 'var(--text-primary)' }}>{log.user}</span> | Target: {log.resource_type} {log.resource_id}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AdminPanelPage;

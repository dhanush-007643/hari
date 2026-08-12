import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileSpreadsheet, FileText, CheckCircle2, AlertCircle, Database, BarChart2 } from 'lucide-react';
import api from '../api/axios';
import toast from 'react-hot-toast';
import { useNavigate } from 'react-router-dom';

const DatasetUploadPage = () => {
  const [file, setFile] = useState(null);
  const [datasetName, setDatasetName] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const navigate = useNavigate();

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      const f = acceptedFiles[0];
      setFile(f);
      if (!datasetName) {
        setDatasetName(f.name.replace(/\.[^/.]+$/, ""));
      }
    }
  }, [datasetName]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  const handleUpload = async () => {
    if (!file || !datasetName) {
      toast.error('Please provide a file and a dataset name');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', datasetName);
    formData.append('description', description);

    setUploading(true);
    try {
      const res = await api.post('/ml/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setResult(res.data);
      toast.success('Dataset uploaded & analyzed successfully!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h2>Dataset Management</h2>
        <p style={{ color: 'var(--text-secondary)' }}>Upload tabular data (CSV/Excel) for SQL analysis and Machine Learning.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: result ? '1fr 1fr' : '1fr', gap: '24px' }}>
        
        {/* Upload Form */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Dataset Name *</label>
            <input 
              type="text" 
              value={datasetName}
              onChange={(e) => setDatasetName(e.target.value)}
              placeholder="e.g. Q4 Sales Data"
              style={{
                width: '100%', padding: '12px', borderRadius: '8px',
                border: '1px solid var(--border-glass)', background: 'var(--bg-main)',
                color: 'var(--text-primary)', outline: 'none'
              }}
            />
          </div>
          
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Description</label>
            <textarea 
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of this dataset..."
              rows={3}
              style={{
                width: '100%', padding: '12px', borderRadius: '8px',
                border: '1px solid var(--border-glass)', background: 'var(--bg-main)',
                color: 'var(--text-primary)', outline: 'none', resize: 'vertical'
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Data File (CSV, Excel) *</label>
            <div 
              {...getRootProps()} 
              style={{
                border: `2px dashed ${isDragActive ? 'var(--primary)' : 'var(--border-glass)'}`,
                borderRadius: '12px',
                padding: '40px 20px',
                textAlign: 'center',
                background: isDragActive ? 'rgba(108, 99, 255, 0.05)' : 'var(--bg-main)',
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              <input {...getInputProps()} />
              
              {file ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                  {file.name.endsWith('.csv') ? <FileText size={48} color="var(--primary)" /> : <FileSpreadsheet size={48} color="var(--success)" />}
                  <div style={{ fontWeight: 600 }}>{file.name}</div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </div>
                  <button 
                    onClick={(e) => { e.stopPropagation(); setFile(null); }}
                    className="btn btn-outline"
                    style={{ padding: '4px 12px', fontSize: '0.85rem', marginTop: '8px' }}
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', color: 'var(--text-secondary)' }}>
                  <UploadCloud size={48} color="var(--primary)" style={{ opacity: 0.8 }} />
                  <div>
                    <span style={{ color: 'var(--primary)', fontWeight: 600 }}>Click to upload</span> or drag and drop
                  </div>
                  <div style={{ fontSize: '0.85rem' }}>CSV, XLS, XLSX up to 50MB</div>
                </div>
              )}
            </div>
          </div>

          <button 
            className="btn btn-primary" 
            onClick={handleUpload}
            disabled={uploading || !file || !datasetName}
            style={{ padding: '14px', fontSize: '1rem', marginTop: '10px' }}
          >
            {uploading ? 'Uploading & Analyzing...' : 'Upload Dataset'}
          </button>
        </div>

        {/* Results / Analysis Panel */}
        {result && (
          <div className="glass-panel animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxHeight: '600px', overflowY: 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--success)', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
              <CheckCircle2 size={24} />
              <h3 style={{ margin: 0 }}>Analysis Complete</h3>
            </div>

            <div style={{ display: 'flex', gap: '16px' }}>
              <div style={{ flex: 1, background: 'var(--bg-main)', padding: '16px', borderRadius: '12px', textAlign: 'center', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--primary)' }}>{result.rows.toLocaleString()}</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Rows</div>
              </div>
              <div style={{ flex: 1, background: 'var(--bg-main)', padding: '16px', borderRadius: '12px', textAlign: 'center', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--secondary)' }}>{result.columns}</div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Columns</div>
              </div>
              <div style={{ flex: 1, background: 'var(--bg-main)', padding: '16px', borderRadius: '12px', textAlign: 'center', border: '1px solid var(--border-glass)' }}>
                <div style={{ fontSize: '2rem', fontWeight: 700, color: result.quality_score > 90 ? 'var(--success)' : 'var(--warning)' }}>
                  {result.quality_score}%
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Quality Score</div>
              </div>
            </div>

            <div>
              <h4 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Database size={18} color="var(--primary)" /> Data Dictionary
              </h4>
              <div style={{ background: 'var(--bg-main)', borderRadius: '12px', border: '1px solid var(--border-glass)', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead style={{ background: 'rgba(0,0,0,0.02)' }}>
                    <tr>
                      <th style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>COLUMN</th>
                      <th style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>TYPE</th>
                      <th style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 600 }}>MISSING</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.column_profile.map((col, i) => (
                      <tr key={i} style={{ borderTop: '1px solid var(--border-glass)' }}>
                        <td style={{ padding: '10px 16px', fontSize: '0.9rem', fontWeight: 500 }}>{col.name}</td>
                        <td style={{ padding: '10px 16px', fontSize: '0.85rem', color: 'var(--primary)' }}>
                          <span style={{ background: 'rgba(108, 99, 255, 0.1)', padding: '2px 8px', borderRadius: '12px' }}>{col.dtype}</span>
                        </td>
                        <td style={{ padding: '10px 16px', fontSize: '0.9rem' }}>
                          {col.null_count > 0 ? (
                            <span style={{ color: 'var(--danger)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <AlertCircle size={14} /> {col.null_count}
                            </span>
                          ) : (
                            <span style={{ color: 'var(--success)' }}>0</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '16px', marginTop: '10px' }}>
              <button className="btn btn-outline" style={{ flex: 1 }} onClick={() => navigate('/sql-playground')}>
                <Database size={18} /> Query Data
              </button>
              <button className="btn btn-primary" style={{ flex: 1 }} onClick={() => navigate('/predictions')}>
                <BarChart2 size={18} /> Train ML Model
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DatasetUploadPage;

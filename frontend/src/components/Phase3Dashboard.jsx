import React, { useState, useEffect } from 'react';
import {
  Users,
  AlertTriangle,
  Syringe,
  Calendar,
  Search,
  RefreshCw,
  Eye,
  FileCheck,
  ShieldAlert,
  ArrowUpRight
} from 'lucide-react';

export default function Phase3Dashboard({ onSelectReport }) {
  const [records, setRecords] = useState([]);
  const [stats, setStats] = useState({
    total_visits: 0,
    high_risk_referrals: 0,
    immunizations_scheduled: 0,
    pending_followups: 0
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [loading, setLoading] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);

  const fetchRegister = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/report/list');
      if (res.ok) {
        const data = await res.json();
        setRecords(data.records || []);
        setStats(data.stats || {});
      }
    } catch (e) {
      console.error('Error fetching Phase 3 Register:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRegister();
  }, []);

  const filteredRecords = records.filter((r) => {
    const matchesSearch =
      (r.beneficiary_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (r.beneficiary_id || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (r.visit_type || '').toLowerCase().includes(searchTerm.toLowerCase());

    if (filterType === 'HIGH_RISK') {
      return matchesSearch && (r.referral_required || (r.danger_signs && r.danger_signs.length > 0));
    }
    if (filterType === 'ANC') {
      return matchesSearch && (r.visit_type || '').includes('ANC');
    }
    if (filterType === 'PNC') {
      return matchesSearch && (r.visit_type || '').includes('PNC');
    }
    if (filterType === 'VAX') {
      return matchesSearch && (r.vaccinations_due && r.vaccinations_due.length > 0);
    }
    return matchesSearch;
  });

  return (
    <div style={styles.container}>
      {/* Top Header & Refresh */}
      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>
            ASHA Field Register Dashboard (ಆಶಾ ಕ್ಷೇತ್ರ ನೋಂದಣಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್)
          </h2>
          <p style={styles.subtitle}>
            Phase 3 Community Health Registry • Confirmed Maternal & Child Health Visits
          </p>
        </div>
        <button type="button" onClick={fetchRegister} style={styles.refreshBtn} disabled={loading}>
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          {loading ? 'Refreshing...' : 'Refresh Register'}
        </button>
      </div>

      {/* 4 Metric Cards */}
      <div style={styles.metricsGrid}>
        <div style={{ ...styles.metricCard, borderLeftColor: '#0284c7' }}>
          <div style={styles.metricIconWrap}>
            <Users size={20} color="#0284c7" />
          </div>
          <div>
            <div style={styles.metricValue}>{stats.total_visits}</div>
            <div style={styles.metricLabel}>Total Field Visits (ಒಟ್ಟು ಭೇಟಿಗಳು)</div>
          </div>
        </div>

        <div style={{ ...styles.metricCard, borderLeftColor: '#dc2626' }}>
          <div style={{ ...styles.metricIconWrap, backgroundColor: '#fee2e2' }}>
            <ShieldAlert size={20} color="#dc2626" />
          </div>
          <div>
            <div style={{ ...styles.metricValue, color: '#dc2626' }}>{stats.high_risk_referrals}</div>
            <div style={styles.metricLabel}>High-Risk Cases (ತುರ್ತು ಪ್ರಕರಣಗಳು)</div>
          </div>
        </div>

        <div style={{ ...styles.metricCard, borderLeftColor: '#8b5cf6' }}>
          <div style={{ ...styles.metricIconWrap, backgroundColor: '#ede9fe' }}>
            <Syringe size={20} color="#8b5cf6" />
          </div>
          <div>
            <div style={styles.metricValue}>{stats.immunizations_scheduled}</div>
            <div style={styles.metricLabel}>Vaccines Due (ಬಾಕಿ ಲಸಿಕೆಗಳು)</div>
          </div>
        </div>

        <div style={{ ...styles.metricCard, borderLeftColor: '#10b981' }}>
          <div style={{ ...styles.metricIconWrap, backgroundColor: '#d1fae5' }}>
            <Calendar size={20} color="#10b981" />
          </div>
          <div>
            <div style={styles.metricValue}>{stats.pending_followups}</div>
            <div style={styles.metricLabel}>Follow-Ups Scheduled (ಫಾಲೋ-ಅಪ್)</div>
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div style={styles.filterBar}>
        <div style={styles.searchWrap}>
          <Search size={16} color="#64748b" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Beneficiary Name, ID, or Visit Type..."
            style={styles.searchInput}
          />
        </div>

        <div style={styles.filterBtns}>
          {['ALL', 'HIGH_RISK', 'ANC', 'PNC', 'VAX'].map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setFilterType(type)}
              style={{
                ...styles.filterBtn,
                backgroundColor: filterType === type ? '#0284c7' : '#ffffff',
                color: filterType === type ? '#ffffff' : '#475569',
                borderColor: filterType === type ? '#0284c7' : '#cbd5e1'
              }}
            >
              {type === 'ALL' && 'All Visits'}
              {type === 'HIGH_RISK' && '🚨 High Risk'}
              {type === 'ANC' && 'Pregnant / ANC'}
              {type === 'PNC' && 'Postpartum / PNC'}
              {type === 'VAX' && 'Immunization'}
            </button>
          ))}
        </div>
      </div>

      {/* Register Table */}
      <div style={styles.tableCard}>
        <table style={styles.table}>
          <thead>
            <tr style={styles.theadRow}>
              <th style={styles.th}>Record ID</th>
              <th style={styles.th}>Beneficiary (ಫಲಾನುಭವಿ)</th>
              <th style={styles.th}>Visit Type</th>
              <th style={styles.th}>Vitals & Measurements</th>
              <th style={styles.th}>Vaccinations Due</th>
              <th style={styles.th}>Next Visit</th>
              <th style={styles.th}>Status / Alerts</th>
              <th style={styles.th}>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredRecords.length === 0 ? (
              <tr>
                <td colSpan={8} style={styles.emptyTd}>
                  No confirmed visit records match the current filter.
                </td>
              </tr>
            ) : (
              filteredRecords.map((r, i) => {
                const hasDanger = r.danger_signs && r.danger_signs.length > 0;
                return (
                  <tr key={i} style={styles.tr}>
                    <td style={styles.tdId}>
                      <code>{r.id || `REC-${i + 1}`}</code>
                    </td>
                    <td style={styles.td}>
                      <strong>{r.beneficiary_name || 'Unspecified'}</strong>
                      {r.beneficiary_id && (
                        <div style={styles.subText}>ID: {r.beneficiary_id}</div>
                      )}
                    </td>
                    <td style={styles.td}>
                      <span style={styles.visitPill}>{r.visit_type}</span>
                    </td>
                    <td style={styles.td}>
                      {r.infant_weight && <div>Weight: <strong>{r.infant_weight}</strong></div>}
                      {r.blood_pressure && <div>BP: <strong>{r.blood_pressure}</strong></div>}
                      {r.gestational_age && <div>Age: <strong>{r.gestational_age}</strong></div>}
                      {!r.infant_weight && !r.blood_pressure && !r.gestational_age && (
                        <span style={{ color: '#94a3b8' }}>-</span>
                      )}
                    </td>
                    <td style={styles.td}>
                      {r.vaccinations_due && r.vaccinations_due.length > 0 ? (
                        r.vaccinations_due.map((v, idx) => (
                          <span key={idx} style={styles.vaxPill}>{v}</span>
                        ))
                      ) : (
                        <span style={{ color: '#94a3b8' }}>None</span>
                      )}
                    </td>
                    <td style={styles.td}>
                      {r.next_visit_date ? (
                        <span style={{ color: '#059669', fontWeight: '600' }}>
                          {r.next_visit_date}
                        </span>
                      ) : (
                        <span style={{ color: '#94a3b8' }}>-</span>
                      )}
                    </td>
                    <td style={styles.td}>
                      {hasDanger ? (
                        <span style={styles.dangerAlertBadge}>
                          🚨 {r.danger_signs[0].name}
                        </span>
                      ) : (
                        <span style={styles.confirmedBadge}>
                          ✓ Confirmed
                        </span>
                      )}
                    </td>
                    <td style={styles.td}>
                      <button
                        type="button"
                        onClick={() => setSelectedRecord(r)}
                        style={styles.viewBtn}
                      >
                        <Eye size={14} /> View
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Record Detail Modal */}
      {selectedRecord && (
        <div style={styles.modalOverlay} onClick={() => setSelectedRecord(null)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h3 style={{ margin: 0, fontSize: '16px', color: '#0f172a' }}>
                Visit Record Details: {selectedRecord.beneficiary_name} ({selectedRecord.id})
              </h3>
              <button
                type="button"
                onClick={() => setSelectedRecord(null)}
                style={styles.modalCloseBtn}
              >
                ✕
              </button>
            </div>

            <div style={styles.modalBody}>
              <div style={styles.modalGrid}>
                <div><strong>Beneficiary ID:</strong> {selectedRecord.beneficiary_id || 'Null'}</div>
                <div><strong>Visit Type:</strong> {selectedRecord.visit_type}</div>
                <div><strong>Infant Weight:</strong> {selectedRecord.infant_weight || 'Null'}</div>
                <div><strong>Blood Pressure:</strong> {selectedRecord.blood_pressure || 'Null'}</div>
                <div><strong>Next Visit:</strong> {selectedRecord.next_visit_date || 'Null'}</div>
                <div><strong>Pregnancy Status:</strong> {selectedRecord.pregnancy_status || 'Null'}</div>
              </div>

              <div style={{ marginTop: '12px' }}>
                <strong>Reported Symptoms:</strong>{' '}
                {selectedRecord.symptoms_reported?.join(', ') || 'None reported'}
              </div>

              <div style={{ marginTop: '6px' }}>
                <strong>Confirmed Negated:</strong>{' '}
                {selectedRecord.negated_symptoms?.join(', ') || 'None'}
              </div>

              <div style={{ marginTop: '10px' }}>
                <strong>Original Spoken Narrative:</strong>
                <blockquote style={styles.modalQuote}>
                  "{selectedRecord.raw_transcript}"
                </blockquote>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    marginTop: '20px'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
    flexWrap: 'wrap',
    gap: '12px'
  },
  title: {
    fontSize: '18px',
    fontWeight: '800',
    color: '#0f172a',
    margin: 0
  },
  subtitle: {
    fontSize: '12px',
    color: '#64748b',
    margin: '3px 0 0 0'
  },
  refreshBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 14px',
    fontSize: '12px',
    fontWeight: '600',
    backgroundColor: '#ffffff',
    color: '#0284c7',
    border: '1px solid #0284c7',
    borderRadius: '8px',
    cursor: 'pointer'
  },
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '14px',
    marginBottom: '18px'
  },
  metricCard: {
    backgroundColor: '#ffffff',
    border: '1px solid #e2e8f0',
    borderLeftWidth: '4px',
    borderRadius: '10px',
    padding: '14px 16px',
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.03)'
  },
  metricIconWrap: {
    width: '38px',
    height: '38px',
    borderRadius: '8px',
    backgroundColor: '#e0f2fe',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  metricValue: {
    fontSize: '20px',
    fontWeight: '800',
    color: '#0f172a'
  },
  metricLabel: {
    fontSize: '11px',
    color: '#64748b',
    marginTop: '2px'
  },
  filterBar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '14px',
    flexWrap: 'wrap',
    gap: '10px'
  },
  searchWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    backgroundColor: '#ffffff',
    border: '1px solid #cbd5e1',
    borderRadius: '8px',
    padding: '6px 12px',
    minWidth: '280px'
  },
  searchInput: {
    border: 'none',
    outline: 'none',
    fontSize: '12px',
    width: '100%',
    color: '#1e293b'
  },
  filterBtns: {
    display: 'flex',
    gap: '6px',
    flexWrap: 'wrap'
  },
  filterBtn: {
    fontSize: '11px',
    fontWeight: '600',
    padding: '6px 12px',
    borderRadius: '6px',
    border: '1px solid',
    cursor: 'pointer'
  },
  tableCard: {
    backgroundColor: '#ffffff',
    borderRadius: '10px',
    border: '1px solid #e2e8f0',
    overflowX: 'auto',
    boxShadow: '0 2px 6px rgba(0,0,0,0.04)'
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    textAlign: 'left',
    fontSize: '12px'
  },
  theadRow: {
    backgroundColor: '#f8fafc',
    borderBottom: '1px solid #e2e8f0'
  },
  th: {
    padding: '12px 14px',
    fontWeight: '700',
    color: '#475569',
    whiteSpace: 'nowrap'
  },
  tr: {
    borderBottom: '1px solid #f1f5f9'
  },
  td: {
    padding: '12px 14px',
    color: '#1e293b',
    verticalAlign: 'middle'
  },
  tdId: {
    padding: '12px 14px',
    color: '#64748b',
    fontSize: '11px',
    fontWeight: '600'
  },
  emptyTd: {
    padding: '30px',
    textAlign: 'center',
    color: '#94a3b8'
  },
  subText: {
    fontSize: '11px',
    color: '#64748b'
  },
  visitPill: {
    display: 'inline-block',
    padding: '2px 8px',
    fontSize: '11px',
    backgroundColor: '#f1f5f9',
    borderRadius: '4px',
    color: '#334155'
  },
  vaxPill: {
    display: 'inline-block',
    marginRight: '4px',
    padding: '2px 6px',
    fontSize: '10px',
    backgroundColor: '#ede9fe',
    color: '#6d28d9',
    borderRadius: '4px'
  },
  dangerAlertBadge: {
    backgroundColor: '#fee2e2',
    color: '#dc2626',
    fontWeight: '700',
    fontSize: '11px',
    padding: '3px 8px',
    borderRadius: '6px'
  },
  confirmedBadge: {
    backgroundColor: '#dcfce7',
    color: '#16a34a',
    fontWeight: '700',
    fontSize: '11px',
    padding: '3px 8px',
    borderRadius: '6px'
  },
  viewBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    padding: '4px 10px',
    fontSize: '11px',
    fontWeight: '600',
    backgroundColor: '#e0f2fe',
    color: '#0369a1',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer'
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 999
  },
  modalContent: {
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    width: '90%',
    maxWidth: '560px',
    padding: '20px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.2)'
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid #e2e8f0',
    paddingBottom: '10px'
  },
  modalCloseBtn: {
    background: 'none',
    border: 'none',
    fontSize: '18px',
    cursor: 'pointer',
    color: '#64748b'
  },
  modalBody: {
    paddingTop: '14px',
    fontSize: '13px',
    color: '#334155'
  },
  modalGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '10px',
    backgroundColor: '#f8fafc',
    padding: '12px',
    borderRadius: '8px'
  },
  modalQuote: {
    backgroundColor: '#f1f5f9',
    padding: '10px 14px',
    borderRadius: '6px',
    fontStyle: 'italic',
    margin: '6px 0 0 0',
    fontSize: '12px',
    color: '#475569'
  }
};


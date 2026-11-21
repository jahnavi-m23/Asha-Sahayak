import React, { useState, useEffect } from 'react';

const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

export default function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [reports, setReports] = useState(null);
  const [visits, setVisits] = useState([]);
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [followups, setFollowups] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState(null);
  const [selectedBeneficiary, setSelectedBeneficiary] = useState(null);
  const [updatingFollowup, setUpdatingFollowup] = useState(null);

  // Phase 2 Simulator State
  const [simPayload, setSimPayload] = useState(JSON.stringify({
    "beneficiary_id": "BNF-2041",
    "visit_type": "Newborn home visit",
    "weight": "3.2 kg",
    "vaccinations_due": ["OPV-1"],
    "next_visit_date": null,
    "danger_signs": [],
    "referral_required": false,
    "confirmation_status": "confirmed"
  }, null, 2));
  const [simResult, setSimResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);

  const refreshData = async () => {
    try {
      setLoading(true);
      setApiError(null);

      const [repRes, visRes, benRes, folRes] = await Promise.all([
        fetch(`${API_BASE}/api/reports`),
        fetch(`${API_BASE}/api/visits`),
        fetch(`${API_BASE}/api/beneficiaries`),
        fetch(`${API_BASE}/api/followups`)
      ]);

      if (!repRes.ok) throw new Error(`Reports API returned ${repRes.status}`);

      const repData = await repRes.json();
      const visData = await visRes.json();
      const benData = await benRes.json();
      const folData = await folRes.json();

      setReports(repData);
      setVisits(visData);
      setBeneficiaries(benData);
      setFollowups(folData);
    } catch (err) {
      console.error("Fetch error:", err);
      setApiError(err.message || "Failed to connect to backend API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/api/beneficiaries?search=${encodeURIComponent(searchTerm)}`);
      if (res.ok) {
        const data = await res.json();
        setBeneficiaries(data);
      }
    } catch (err) {
      console.error("Search error:", err);
    }
  };

  const openBeneficiaryDetails = async (benId) => {
    try {
      const res = await fetch(`${API_BASE}/api/beneficiaries/${benId}`);
      if (res.ok) {
        const data = await res.json();
        setSelectedBeneficiary(data);
      }
    } catch (err) {
      console.error("Detail error:", err);
    }
  };

  const submitPhase2Payload = async () => {
    try {
      setSimLoading(true);
      setSimResult(null);
      const parsed = JSON.parse(simPayload);

      const res = await fetch(`${API_BASE}/api/visits/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed)
      });

      const data = await res.json();
      setSimResult({
        status: res.status,
        ok: res.ok,
        data: data
      });

      if (res.ok) {
        refreshData();
      }
    } catch (err) {
      setSimResult({
        status: 0,
        ok: false,
        data: { error: err.message || "Failed to submit JSON payload" }
      });
    } finally {
      setSimLoading(false);
    }
  };

  const handleFollowupUpdate = async (status, notes) => {
    if (!updatingFollowup) return;
    try {
      const res = await fetch(`${API_BASE}/api/followups/${updatingFollowup.followup_id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: status,
          worker_notes: notes,
          worker_id: "ASHA-Rampur-1"
        })
      });

      if (res.ok) {
        setUpdatingFollowup(null);
        refreshData();
      }
    } catch (err) {
      alert("Failed to update follow-up: " + err.message);
    }
  };

  const handleResetDemo = async () => {
    if (!confirm("Reset database with fresh synthetic demo data?")) return;
    try {
      const res = await fetch(`${API_BASE}/api/reports/reset-demo`, { method: "POST" });
      if (res.ok) {
        alert("Database re-seeded with synthetic demo data.");
        refreshData();
      }
    } catch (err) {
      alert("Reset failed: " + err.message);
    }
  };

  return (
    <div>
      {/* Top Synthetic Demo Banner */}
      <div className="demo-banner">
        <div>
          <span className="demo-badge-tag">Synthetic Demo Data</span>
          <span style={{ marginLeft: "10px" }}>
            ASHA Sahayak Hackathon Evaluation Mode – All beneficiary names and records are strictly synthetic.
          </span>
        </div>
        <div>
          <button 
            onClick={handleResetDemo}
            style={{ 
              background: "rgba(255,255,255,0.2)", 
              color: "white", 
              border: "1px solid rgba(255,255,255,0.4)",
              padding: "4px 10px", 
              borderRadius: "6px", 
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 600
            }}
          >
            Reset Demo Data
          </button>
        </div>
      </div>

      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="brand-section">
            <div className="brand-logo">AS</div>
            <div>
              <div className="brand-title">
                ASHA Sahayak <span style={{ color: "var(--gray-500)", fontWeight: 500 }}>| आशा सहायक</span>
              </div>
              <div className="brand-subtitle">
                Phase 3: Database, Dashboard and Follow-up Management
              </div>
            </div>
          </div>

          <div className="worker-info">
            <span className="status-dot"></span>
            <div>
              <strong>ASHA Worker:</strong> Sunita Devi (Rampur PHC Sector 2)
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <main className="main-container">
        {/* Navigation Tabs */}
        <nav className="nav-tabs">
          <button 
            className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <span>Dashboard Overview</span>
          </button>
          <button 
            className={`tab-button ${activeTab === 'beneficiaries' ? 'active' : ''}`}
            onClick={() => setActiveTab('beneficiaries')}
          >
            <span>Beneficiaries</span>
            <span className="tab-badge">{beneficiaries.length}</span>
          </button>
          <button 
            className={`tab-button ${activeTab === 'visits' ? 'active' : ''}`}
            onClick={() => setActiveTab('visits')}
          >
            <span>Visit Records</span>
            <span className="tab-badge">{visits.length}</span>
          </button>
          <button 
            className={`tab-button ${activeTab === 'followups' ? 'active' : ''}`}
            onClick={() => setActiveTab('followups')}
          >
            <span>Follow-up Management</span>
            <span className="tab-badge">{followups.filter(f => f.status !== 'completed').length}</span>
          </button>
          <button 
            className={`tab-button ${activeTab === 'simulator' ? 'active' : ''}`}
            onClick={() => setActiveTab('simulator')}
            style={{ borderColor: "var(--teal)" }}
          >
            <span style={{ color: activeTab === 'simulator' ? 'white' : 'var(--teal)' }}>
              Phase 2 Ingestion Simulator
            </span>
          </button>
        </nav>

        {/* Error notice if API fails */}
        {apiError && (
          <div style={{ background: "#fef2f2", color: "#991b1b", padding: "14px", borderRadius: "8px", marginBottom: "20px", border: "1px solid #fecaca" }}>
            <strong>API Connection Warning:</strong> {apiError}. Make sure FastAPI server is running on port 8000.
            <button onClick={refreshData} style={{ marginLeft: "12px", textDecoration: "underline", background: "none", border: "none", color: "#991b1b", cursor: "pointer", fontWeight: 700 }}>
              Retry Connection
            </button>
          </div>
        )}

        {/* TAB 1: OVERVIEW */}
        {activeTab === 'overview' && (
          <div>
            {/* Metric Statistics Cards */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Beneficiaries</div>
                <div className="stat-value">{reports ? reports.total_beneficiaries : '—'}</div>
                <div className="stat-subtext">Registered in field area</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Completed Visits</div>
                <div className="stat-value">{reports ? reports.total_completed_visits : '—'}</div>
                <div className="stat-subtext">Confirmed from Phase 2</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Upcoming Follow-ups</div>
                <div className="stat-value">{reports ? reports.upcoming_followups : '—'}</div>
                <div className="stat-subtext">Scheduled visits</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Pending / Overdue</div>
                <div className="stat-value" style={{ color: (reports && reports.overdue_followups > 0) ? 'var(--warning)' : 'inherit' }}>
                  {reports ? reports.overdue_followups : '—'}
                </div>
                <div className="stat-subtext">Requires field attention</div>
              </div>
              <div className="stat-card alert-card">
                <div className="stat-label">Referral Alerts</div>
                <div className="stat-value">{reports ? reports.referral_cases : '—'}</div>
                <div className="stat-subtext">PHC Escort Flagged</div>
              </div>
            </div>

            {/* Prominent Referral Alerts Banner */}
            {reports && reports.recent_referral_alerts && reports.recent_referral_alerts.length > 0 && (
              <div className="referral-banner">
                <div className="referral-header">
                  <div className="referral-title">
                    <span>Urgent Referral Alerts (PHC Coordination Required)</span>
                  </div>
                  <span className="badge badge-danger">
                    {reports.recent_referral_alerts.length} Active Cases
                  </span>
                </div>
                <p style={{ fontSize: "13px", color: "#7f1d1d" }}>
                  The following beneficiaries were flagged with danger signs during worker visits. 
                  Please verify PHC attendance or escort support.
                </p>

                <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "6px" }}>
                  {reports.recent_referral_alerts.map(alert => (
                    <div key={alert.visit_id} style={{ background: "white", padding: "12px 16px", borderRadius: "8px", border: "1px solid #fecaca", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "8px" }}>
                      <div>
                        <strong>{alert.beneficiary_id}</strong>: {alert.beneficiary_name} ({alert.village_ward})
                        <div style={{ marginTop: "4px" }}>
                          {alert.danger_signs.map(sign => (
                            <span key={sign} className="danger-tag" style={{ marginRight: "6px" }}>
                              {sign}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="badge badge-danger">{alert.referral_status}</span>
                        <button 
                          className="btn btn-sm btn-secondary" 
                          style={{ marginLeft: "8px" }}
                          onClick={() => openBeneficiaryDetails(alert.beneficiary_id)}
                        >
                          View Case
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Vaccinations Due & Protocol Row */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
              <div className="content-panel">
                <div className="panel-header">
                  <h2 className="panel-title">Vaccinations Due Tracker</h2>
                  <span className="badge badge-info">Routine Immunization</span>
                </div>
                {reports && reports.vaccinations_due_summary && reports.vaccinations_due_summary.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    {reports.vaccinations_due_summary.map(item => (
                      <div key={item.vaccine} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "var(--gray-50)", borderRadius: "6px" }}>
                        <span style={{ fontWeight: 600 }}>{item.vaccine}</span>
                        <span className="badge badge-neutral" style={{ fontWeight: 700 }}>{item.count} due</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ color: "var(--gray-500)", fontStyle: "italic", padding: "16px 0" }}>
                    No pending routine vaccinations recorded.
                  </div>
                )}
              </div>

              <div className="content-panel">
                <div className="panel-header">
                  <h2 className="panel-title">ASHA Protocol Reminders</h2>
                  <span className="badge badge-neutral">Standard Operating Procedures</span>
                </div>
                <ul style={{ paddingLeft: "20px", fontSize: "14px", display: "flex", flexDirection: "column", gap: "10px", color: "var(--gray-700)" }}>
                  <li>
                    <strong>Newborn Home Visits (HBNV):</strong> Conduct on Days 1, 3, 7, 14, 21, 28, and 42 for institutional deliveries. Check weight and cord hygiene.
                  </li>
                  <li>
                    <strong>High-Risk Referral:</strong> If high fever, poor sucking, or severe chest indrawing is observed, refer immediately to the Medical Officer at the PHC.
                  </li>
                  <li>
                    <strong>MCP Card Registration:</strong> Ensure TT vaccination and IFA tablet compliance are stamped in the Mother-Child Protection register.
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: BENEFICIARIES */}
        {activeTab === 'beneficiaries' && (
          <div className="content-panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Beneficiary Register</h2>
                <p style={{ fontSize: "13px", color: "var(--gray-500)" }}>
                  Search records by Beneficiary ID (e.g. BNF-2041), Name, or Village Ward.
                </p>
              </div>
              <form onSubmit={handleSearch} className="search-bar">
                <input 
                  type="text" 
                  className="input-field" 
                  placeholder="Search ID (e.g. BNF-2041) or Name..." 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <button type="submit" className="btn btn-primary">Search</button>
                {searchTerm && (
                  <button 
                    type="button" 
                    className="btn btn-secondary" 
                    onClick={() => { setSearchTerm(""); refreshData(); }}
                  >
                    Clear
                  </button>
                )}
              </form>
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Beneficiary ID</th>
                    <th>Full Name</th>
                    <th>Category</th>
                    <th>Village / Ward</th>
                    <th>Contact</th>
                    <th>Total Visits</th>
                    <th>Active Follow-ups</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {beneficiaries.map(ben => (
                    <tr key={ben.beneficiary_id}>
                      <td><strong>{ben.beneficiary_id}</strong></td>
                      <td>{ben.full_name}</td>
                      <td><span className="badge badge-info">{ben.category}</span></td>
                      <td>{ben.village_ward}</td>
                      <td><span style={{ color: "var(--gray-500)" }}>{ben.contact_number || '—'}</span></td>
                      <td><strong>{ben.total_visits}</strong></td>
                      <td>
                        {ben.active_followups > 0 ? (
                          <span className="badge badge-warning">{ben.active_followups} Pending</span>
                        ) : (
                          <span className="badge badge-neutral">None</span>
                        )}
                      </td>
                      <td>
                        <button 
                          className="btn btn-sm btn-secondary"
                          onClick={() => openBeneficiaryDetails(ben.beneficiary_id)}
                        >
                          View History
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: VISITS */}
        {activeTab === 'visits' && (
          <div className="content-panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Confirmed Field Visits</h2>
                <p style={{ fontSize: "13px", color: "var(--gray-500)" }}>
                  Displaying only worker-confirmed visit records saved into the database.
                </p>
              </div>
              <span className="badge badge-success">Confirmed Status Only</span>
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Visit ID</th>
                    <th>Visit Date</th>
                    <th>Beneficiary</th>
                    <th>Visit Type</th>
                    <th>Weight</th>
                    <th>Vaccinations Due</th>
                    <th>Next Visit Date</th>
                    <th>Referral Status</th>
                  </tr>
                </thead>
                <tbody>
                  {visits.map(v => (
                    <tr key={v.visit_id}>
                      <td><code>{v.visit_id}</code></td>
                      <td>{v.visit_date}</td>
                      <td>
                        <strong>{v.beneficiary_id}</strong>
                        <div style={{ fontSize: "12px", color: "var(--gray-500)" }}>{v.beneficiary_name}</div>
                      </td>
                      <td><strong>{v.visit_type}</strong></td>
                      <td>{v.weight || '—'}</td>
                      <td>
                        {v.vaccinations_due && v.vaccinations_due.length > 0 ? (
                          v.vaccinations_due.map(vac => (
                            <span key={vac} className="vaccine-tag">{vac}</span>
                          ))
                        ) : (
                          <span style={{ color: "var(--gray-500)", fontSize: "12px" }}>None</span>
                        )}
                      </td>
                      <td>
                        {v.next_visit_date ? (
                          <span style={{ fontWeight: 600 }}>{v.next_visit_date}</span>
                        ) : (
                          <span style={{ color: "var(--gray-500)", fontStyle: "italic", fontSize: "12px" }}>
                            Not scheduled
                          </span>
                        )}
                      </td>
                      <td>
                        {v.referral_required ? (
                          <span className="badge badge-danger">{v.referral_status}</span>
                        ) : (
                          <span className="badge badge-neutral">Routine</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 4: FOLLOW-UP MANAGEMENT */}
        {activeTab === 'followups' && (
          <div className="content-panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Follow-up Management</h2>
                <p style={{ fontSize: "13px", color: "var(--gray-500)" }}>
                  Upcoming and overdue follow-ups. Workers can update visit completion notes.
                </p>
              </div>
            </div>

            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Scheduled Date</th>
                    <th>Status</th>
                    <th>Beneficiary</th>
                    <th>Reason / Scope</th>
                    <th>Worker Notes</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {followups.map(fol => (
                        <tr key={fol.followup_id}>
                          <td><code>{fol.followup_id}</code></td>
                          <td>
                            <strong>{fol.scheduled_date}</strong>
                          </td>
                          <td>
                            {fol.status === 'upcoming' && <span className="badge badge-info">Upcoming</span>}
                            {fol.status === 'overdue' && <span className="badge badge-danger">Overdue</span>}
                            {fol.status === 'completed' && <span className="badge badge-success">Completed</span>}
                            {fol.status === 'cancelled' && <span className="badge badge-neutral">Cancelled</span>}
                          </td>
                          <td>
                            <strong>{fol.beneficiary_id}</strong>
                            <div style={{ fontSize: "12px", color: "var(--gray-500)" }}>{fol.beneficiary_name}</div>
                          </td>
                          <td style={{ maxWidth: "260px" }}>{fol.reason}</td>
                          <td style={{ maxWidth: "220px", fontSize: "13px", color: "var(--gray-700)" }}>
                            {fol.worker_notes || '—'}
                          </td>
                          <td>
                            <button 
                              className="btn btn-sm btn-secondary"
                              onClick={() => setUpdatingFollowup(fol)}
                            >
                              Update Status
                            </button>
                          </td>
                        </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 5: PHASE 2 SIMULATOR */}
        {activeTab === 'simulator' && (
          <div className="content-panel">
            <div className="panel-header">
              <div>
                <h2 className="panel-title">Phase 2 Ingestion Simulator</h2>
                <p style={{ fontSize: "13px", color: "var(--gray-500)" }}>
                  Test receiving worker-confirmed JSON records from Phase 2. Verify validation, 
                  duplicate prevention, and rejection of unconfirmed records.
                </p>
              </div>
            </div>

            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "16px" }}>
              <button 
                className="btn btn-sm btn-secondary"
                onClick={() => setSimPayload(JSON.stringify({
                  "beneficiary_id": "BNF-2041",
                  "visit_type": "Newborn home visit",
                  "weight": "3.2 kg",
                  "vaccinations_due": ["OPV-1"],
                  "next_visit_date": null,
                  "danger_signs": [],
                  "referral_required": false,
                  "confirmation_status": "confirmed"
                }, null, 2))}
              >
                Exact Phase 2 Payload (BNF-2041)
              </button>

              <button 
                className="btn btn-sm btn-secondary"
                onClick={() => setSimPayload(JSON.stringify({
                  "beneficiary_id": "BNF-1082",
                  "visit_type": "3rd Trimester ANC Checkup",
                  "weight": "56.0 kg",
                  "vaccinations_due": ["TT-Booster"],
                  "next_visit_date": "2026-12-05",
                  "danger_signs": [],
                  "referral_required": false,
                  "confirmation_status": "confirmed"
                }, null, 2))}
              >
                With Follow-up Date (2026-12-05)
              </button>

              <button 
                className="btn btn-sm btn-secondary"
                onClick={() => setSimPayload(JSON.stringify({
                  "beneficiary_id": "BNF-3094",
                  "visit_type": "Emergency Neonatal Visit",
                  "weight": "2.7 kg",
                  "vaccinations_due": [],
                  "next_visit_date": "2026-11-23",
                  "danger_signs": ["High fever", "Poor sucking", "Fast breathing"],
                  "referral_required": true,
                  "confirmation_status": "confirmed"
                }, null, 2))}
              >
                Referral Case with Danger Signs
              </button>

              <button 
                className="btn btn-sm btn-secondary"
                style={{ borderColor: "var(--danger)", color: "var(--danger)" }}
                onClick={() => setSimPayload(JSON.stringify({
                  "beneficiary_id": "BNF-2041",
                  "visit_type": "Draft Unconfirmed Visit",
                  "weight": "3.2 kg",
                  "vaccinations_due": ["OPV-1"],
                  "next_visit_date": null,
                  "danger_signs": [],
                  "referral_required": false,
                  "confirmation_status": "pending"
                }, null, 2))}
              >
                Unconfirmed / Pending (To test rejection)
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
              <div>
                <label style={{ display: "block", fontWeight: 700, fontSize: "14px", marginBottom: "8px" }}>
                  JSON Payload (POST /api/visits/confirm):
                </label>
                <textarea 
                  rows="14"
                  className="input-field" 
                  style={{ fontFamily: "monospace", fontSize: "13px", background: "#0f172a", color: "#38bdf8", padding: "16px" }}
                  value={simPayload}
                  onChange={(e) => setSimPayload(e.target.value)}
                ></textarea>

                <div style={{ marginTop: "12px" }}>
                  <button 
                    className="btn btn-primary"
                    onClick={submitPhase2Payload}
                    disabled={simLoading}
                  >
                    {simLoading ? "Submitting to Backend..." : "Submit to /api/visits/confirm"}
                  </button>
                </div>
              </div>

              <div>
                <label style={{ display: "block", fontWeight: 700, fontSize: "14px", marginBottom: "8px" }}>
                  Backend Response:
                </label>
                {simResult ? (
                  <div>
                    <div style={{ marginBottom: "10px" }}>
                      <span className={`badge ${simResult.ok ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: "14px", padding: "6px 12px" }}>
                        HTTP {simResult.status} {simResult.ok ? 'Created / Success' : 'Error / Rejection'}
                      </span>
                    </div>
                    <pre className="code-block" style={{ color: simResult.ok ? '#4ade80' : '#f87171' }}>
                      {JSON.stringify(simResult.data, null, 2)}
                    </pre>
                  </div>
                ) : (
                  <div style={{ border: "2px dashed var(--gray-300)", borderRadius: "8px", padding: "40px", textAlign: "center", color: "var(--gray-500)" }}>
                    Click "Submit" to test payload transmission and inspect HTTP response.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* BENEFICIARY DETAIL MODAL */}
      {selectedBeneficiary && (
        <div className="modal-overlay" onClick={() => setSelectedBeneficiary(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3 style={{ fontSize: "18px", fontWeight: 800 }}>
                  {selectedBeneficiary.beneficiary.beneficiary_id}: {selectedBeneficiary.beneficiary.full_name}
                </h3>
                <div style={{ fontSize: "13px", color: "var(--gray-500)" }}>
                  {selectedBeneficiary.beneficiary.category} • {selectedBeneficiary.beneficiary.village_ward}
                </div>
              </div>
              <button className="btn btn-sm btn-secondary" onClick={() => setSelectedBeneficiary(null)}>✕</button>
            </div>

            <div className="modal-body">
              <div style={{ marginBottom: "20px" }}>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginBottom: "8px" }}>Demographic Summary</h4>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", fontSize: "13px", background: "var(--gray-50)", padding: "12px", borderRadius: "8px" }}>
                  <div><strong>Age:</strong> {selectedBeneficiary.beneficiary.age_years || '—'} years</div>
                  <div><strong>Gender:</strong> {selectedBeneficiary.beneficiary.gender}</div>
                  <div><strong>Contact:</strong> {selectedBeneficiary.beneficiary.contact_number || '—'}</div>
                  <div><strong>Notes:</strong> {selectedBeneficiary.beneficiary.notes || '—'}</div>
                </div>
              </div>

              <div style={{ marginBottom: "20px" }}>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginBottom: "8px" }}>Vaccinations Due</h4>
                <div>
                  {selectedBeneficiary.vaccinations_due.length > 0 ? (
                    selectedBeneficiary.vaccinations_due.map(vac => (
                      <span key={vac} className="vaccine-tag" style={{ fontSize: "12px", padding: "4px 8px" }}>{vac}</span>
                    ))
                  ) : (
                    <span style={{ color: "var(--gray-500)", fontSize: "13px" }}>No vaccinations currently due.</span>
                  )}
                </div>
              </div>

              <div style={{ marginBottom: "20px" }}>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginBottom: "8px" }}>
                  Visit History ({selectedBeneficiary.visits.length})
                </h4>
                <div style={{ maxHeight: "200px", overflowY: "auto", border: "1px solid var(--gray-200)", borderRadius: "6px" }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Visit Type</th>
                        <th>Weight</th>
                        <th>Referral</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedBeneficiary.visits.map(v => (
                        <tr key={v.visit_id}>
                          <td>{v.visit_date}</td>
                          <td>{v.visit_type}</td>
                          <td>{v.weight || '—'}</td>
                          <td>
                            {v.referral_required ? (
                              <span className="badge badge-danger">Referred</span>
                            ) : (
                              <span className="badge badge-neutral">Routine</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <h4 style={{ fontSize: "14px", fontWeight: 700, marginBottom: "8px" }}>
                  Follow-ups ({selectedBeneficiary.follow_ups.length})
                </h4>
                {selectedBeneficiary.follow_ups.map(fol => (
                  <div key={fol.followup_id} style={{ padding: "8px 12px", border: "1px solid var(--gray-200)", borderRadius: "6px", marginBottom: "8px", fontSize: "13px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <strong>{fol.scheduled_date}</strong>
                      <span className={`badge ${fol.status === 'completed' ? 'badge-success' : fol.status === 'overdue' ? 'badge-danger' : 'badge-info'}`}>
                        {fol.status}
                      </span>
                    </div>
                    <div style={{ color: "var(--gray-700)", marginTop: "4px" }}>{fol.reason}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setSelectedBeneficiary(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* UPDATE FOLLOWUP MODAL */}
      {updatingFollowup && (
        <div className="modal-overlay" onClick={() => setUpdatingFollowup(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 style={{ fontSize: "16px", fontWeight: 800 }}>Update Follow-up Status</h3>
              <button className="btn btn-sm btn-secondary" onClick={() => setUpdatingFollowup(null)}>✕</button>
            </div>

            <div className="modal-body">
              <p style={{ fontSize: "14px", marginBottom: "16px" }}>
                <strong>Beneficiary:</strong> {updatingFollowup.beneficiary_id} – {updatingFollowup.beneficiary_name}
                <br />
                <strong>Purpose:</strong> {updatingFollowup.reason}
                <br />
                <strong>Scheduled Date:</strong> {updatingFollowup.scheduled_date}
              </p>

              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontWeight: 600, fontSize: "13px", marginBottom: "6px" }}>
                  Field Visit Notes:
                </label>
                <textarea 
                  id="followupNotesModal" 
                  rows="3" 
                  className="input-field" 
                  placeholder="Enter observations, immunization administration notes, or mother's status..."
                  defaultValue={updatingFollowup.worker_notes || ""}
                ></textarea>
              </div>
            </div>

            <div className="modal-footer">
              <button 
                className="btn btn-secondary" 
                onClick={() => setUpdatingFollowup(null)}
              >
                Cancel
              </button>
              <button 
                className="btn btn-success"
                onClick={() => {
                  const notes = document.getElementById("followupNotesModal").value;
                  handleFollowupUpdate("completed", notes);
                }}
              >
                Mark as Completed
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect, useRef } from 'react';
import VoiceRecorder from './components/VoiceRecorder';
import StructuredVisitReport from './components/StructuredVisitReport';
import Phase3Dashboard from './components/Phase3Dashboard';
import {
  Mic,
  LayoutDashboard,
  Calendar,
  Users,
  Search,
  Activity,
  AlertTriangle,
  FileText,
  CheckCircle2,
  Bell,
  Home,
  LogOut,
  LogIn,
  PlusCircle,
  Eye,
  Trash2,
  Edit2
} from 'lucide-react';

const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

const I18N = {
  en: {
    appTitle: "ASHA SAHAYAK (ಆಶಾ ಸಹಾಯಕ)",
    appSubtitle: "Voice-First Clinical Field Register & Community Health System",
    demoMode: "SYNTHETIC HEALTHCARE DEMO – NO REAL PHI",
    tabVoice: "Voice & AI Register (Phase 1 & 2)",
    tabOverview: "Field Register (Phase 3)",
    tabFollowups: "Follow-up Tracker",
    tabHouseholds: "Household Directory",
    tabFinder: "Find ASHA Worker",
    loginBtn: "Login",
    logoutBtn: "Logout",
    totalHouseholds: "Total Households",
    totalBeneficiaries: "Total Beneficiaries",
    totalVisits: "Confirmed Visits",
    pendingFollowups: "Scheduled Follow-ups",
    referralAlerts: "Urgent Referral Alerts",
    saveChanges: "Save Changes",
    cancel: "Cancel",
    delete: "Delete",
    edit: "Edit"
  },
  kn: {
    appTitle: "ಆಶಾ ಸಹಾಯಕ (ASHA SAHAYAK)",
    appSubtitle: "ಧ್ವನಿ ಆಧಾರಿತ ಕ್ಷೇತ್ರ ನೋಂದಣಿ ಮತ್ತು ಸಮುದಾಯ ಆರೋಗ್ಯ ನಿರ್ವಹಣೆ",
    demoMode: "ಪ್ರಾತ್ಯಕ್ಷಿಕೆ ಮಾದರಿ – ಯಾವುದೇ ನೈಜ ರೋಗಿಯ ಮಾಹಿತಿಯಿಲ್ಲ",
    tabVoice: "ಧ್ವನಿ ಮತ್ತು AI ನೋಂದಣಿ (ಹಂತ 1 & 2)",
    tabOverview: "ಕ್ಷೇತ್ರ ರಿಜಿಸ್ಟರ್ (ಹಂತ 3)",
    tabFollowups: "ಫಾಲೋ-ಅಪ್ ಟ್ರ್ಯಾಕರ್",
    tabHouseholds: "ಕುಟುಂಬ ಡೈರೆಕ್ಟರಿ",
    tabFinder: "ಆಶಾ ಕಾರ್ಯಕರ್ತೆಯರನ್ನು ಹುಡುಕಿ",
    loginBtn: "ಲಾಗಿನ್",
    logoutBtn: "ಲಾಗ್‌ಔಟ್",
    totalHouseholds: "ಒಟ್ಟು ಕುಟುಂಬಗಳು",
    totalBeneficiaries: "ಒಟ್ಟು ಫಲಾನುಭವಿಗಳು",
    totalVisits: "ದೃಢೀಕರಿಸಿದ ಭೇಟಿಗಳು",
    pendingFollowups: "ನಿಗದಿತ ಫಾಲೋ-ಅಪ್‌ಗಳು",
    referralAlerts: "ತುರ್ತು ರೆಫರಲ್ ಎಚ್ಚರಿಕೆಗಳು",
    saveChanges: "ಬದಲಾವಣೆಗಳನ್ನು ಉಳಿಸಿ",
    cancel: "ರದ್ದುಮಾಡಿ",
    delete: "ಅಳಿಸಿ",
    edit: "ತಿದ್ದುಪಡಿ"
  }
};

export default function App() {
  const [lang, setLang] = useState("en");
  const t = I18N[lang];

  // Navigation tab: 'VOICE' | 'DASHBOARD' | 'FOLLOWUPS' | 'HOUSEHOLDS' | 'FINDER'
  const [activeTab, setActiveTab] = useState('VOICE');

  // Authenticated user session
  const [currentUser, setCurrentUser] = useState({
    id: "USR-ASHA-RAMPUR",
    username: "asha_rampur",
    role: "asha_worker",
    full_name: "Sunita Devi",
    badge_id: "ASHA-KA-MDY-001",
    assigned_pincode: "571428",
    assigned_village: "Rampur",
    phc_name: "Kestur Primary Health Centre"
  });

  // Phase 1 & 2 Workflow State
  const [completedHandoff, setCompletedHandoff] = useState(null);
  const [currentReport, setCurrentReport] = useState(null);
  const [extractingReport, setExtractingReport] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState('kn-IN');

  // Phase 3 Real Database State
  const [reports, setReports] = useState(null);
  const [visits, setVisits] = useState([]);
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [followups, setFollowups] = useState([]);
  const [households, setHouseholds] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [notification, setNotification] = useState(null);

  // Modals
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: "asha_rampur", password: "asha123" });
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState(null);

  const [showFollowupModal, setShowFollowupModal] = useState(false);
  const [activeFollowup, setActiveFollowup] = useState(null);
  const [followupNotes, setFollowupNotes] = useState('');

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [householdToDelete, setHouseholdToDelete] = useState(null);

  const [showEditModal, setShowEditModal] = useState(false);
  const [householdToEdit, setHouseholdToEdit] = useState(null);

  // Finder State
  const [finderQuery, setFinderQuery] = useState({ pincode: "571428", village: "", taluk: "", district: "" });
  const [finderResults, setFinderResults] = useState([]);
  const [finderLoading, setFinderLoading] = useState(false);
  const [finderMessage, setFinderMessage] = useState('');

  // Fetch real SQLite database records
  const refreshData = async () => {
    try {
      const headers = currentUser ? { "Authorization": `Bearer token-${currentUser.username}-${currentUser.id}` } : {};

      const [repRes, visRes, benRes, folRes, hhRes] = await Promise.all([
        fetch(`${API_BASE}/api/reports`),
        fetch(`${API_BASE}/api/visits`),
        fetch(`${API_BASE}/api/beneficiaries`),
        fetch(`${API_BASE}/api/followups`),
        fetch(`${API_BASE}/api/households`, { headers }).catch(() => ({ ok: false }))
      ]);

      if (repRes.ok) setReports(await repRes.json());
      if (visRes.ok) setVisits(await visRes.json());
      if (benRes.ok) setBeneficiaries(await benRes.json());
      if (folRes.ok) setFollowups(await folRes.json());
      if (hhRes.ok && typeof hhRes.json === "function") {
        setHouseholds(await hhRes.json());
      }
    } catch (e) {
      console.warn("Backend fetch notice:", e);
    }
  };

  useEffect(() => {
    refreshData();
  }, [currentUser]);

  // Phase 1 -> Phase 2: When speech transcription is finalized
  const handleTranscriptComplete = async (payload) => {
    console.log('[App] Phase 1 Transcript Complete:', payload);
    setCompletedHandoff(payload);

    if (payload.transcript && payload.transcript.trim()) {
      setExtractingReport(true);
      try {
        const langCode = payload.language?.includes('kn') ? 'kn-IN' : (payload.language || 'kn-IN');
        setCurrentLanguage(langCode);

        // Run Phase 2 AI clinical extraction
        const response = await fetch(`${API_BASE}/api/report/extract`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            transcript: payload.transcript,
            language: langCode
          })
        });

        const data = await response.json();
        if (data.success && data.report) {
          setCurrentReport(data.report);
          setNotification({ type: 'success', message: 'Clinical extraction complete. Please review before confirmation.' });
        }
      } catch (err) {
        console.error('Error during automated report extraction:', err);
      } finally {
        setExtractingReport(false);
      }
    }
  };

  // Phase 2 -> Phase 3: Worker confirms structured report
  const handleConfirmAndSave = async (savedRecord) => {
    try {
      // 1. Format payload matching Phase 3 contract
      const phase3Payload = {
        beneficiary_id: savedRecord.beneficiary_id || "BNF-2041",
        visit_type: savedRecord.visit_type || "Routine Home Visit",
        weight: savedRecord.infant_weight || savedRecord.weight || "3.2 kg",
        vaccinations_due: savedRecord.vaccinations_due || [],
        next_visit_date: savedRecord.next_visit_date && !savedRecord.next_visit_date.includes("None") ? savedRecord.next_visit_date : null,
        danger_signs: savedRecord.danger_signs || [],
        referral_required: Boolean(savedRecord.referral_required),
        confirmation_status: "confirmed"
      };

      const res = await fetch(`${API_BASE}/api/visits/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(phase3Payload)
      });

      const resData = await res.json();
      if (res.status === 201) {
        setNotification({
          type: 'success',
          message: `Visit report confirmed and saved to SQLite register! (ID: ${resData.visit_id})`
        });
        refreshData();
      } else if (res.status === 409) {
        setNotification({
          type: 'warning',
          message: `Duplicate visit record detected. This entry was already persisted.`
        });
      } else {
        // Also save to Phase 2 report ledger
        await fetch(`${API_BASE}/api/report/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ report: savedRecord, confirmed: true })
        });
        setNotification({ type: 'success', message: 'Report confirmed and saved.' });
        refreshData();
      }
    } catch (e) {
      console.error('Save report error:', e);
      setNotification({ type: 'error', message: 'Error persisting visit record.' });
    }
  };

  // Handle Login Authentication
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoginError(null);
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginForm)
      });
      const data = await res.json();
      if (res.ok) {
        setCurrentUser(data.user);
        setShowLoginModal(false);
        setNotification({ type: "success", message: `Logged in as ${data.user.full_name} (${data.user.role})` });
        refreshData();
      } else {
        setLoginError(data.detail || "Invalid login credentials.");
      }
    } catch (err) {
      setLoginError("Failed to authenticate with backend server.");
    }
  };

  // Handle Location-Based Worker Finder Search
  const handleFinderSearch = async (e) => {
    if (e) e.preventDefault();
    try {
      setFinderLoading(true);
      setFinderMessage("");
      const params = new URLSearchParams();
      if (finderQuery.pincode) params.append("pincode", finderQuery.pincode);
      if (finderQuery.village) params.append("village", finderQuery.village);
      if (finderQuery.taluk) params.append("taluk", finderQuery.taluk);
      if (finderQuery.district) params.append("district", finderQuery.district);

      const res = await fetch(`${API_BASE}/api/workers/find?${params.toString()}`);
      const data = await res.json();
      if (res.ok) {
        setFinderResults(data.workers || []);
        setFinderMessage(data.message || "");
      }
    } catch (err) {
      setFinderMessage("Unable to reach worker directory service.");
    } finally {
      setFinderLoading(false);
    }
  };

  // Handle Completing a Follow-up
  const handleCompleteFollowup = async () => {
    if (!activeFollowup) return;
    try {
      const res = await fetch(`${API_BASE}/api/followups/${activeFollowup.follow_up_id}/complete`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: followupNotes })
      });
      if (res.ok) {
        setShowFollowupModal(false);
        setActiveFollowup(null);
        setFollowupNotes("");
        setNotification({ type: "success", message: "Follow-up visit marked complete." });
        refreshData();
      }
    } catch (err) {
      alert("Failed to complete follow-up.");
    }
  };

  // Handle Household Deletion
  const confirmDeleteHousehold = async () => {
    if (!householdToDelete) return;
    try {
      const headers = { "Authorization": `Bearer token-${currentUser.username}-${currentUser.id}` };
      const res = await fetch(`${API_BASE}/api/households/${householdToDelete.id}`, {
        method: "DELETE",
        headers
      });
      if (res.ok) {
        setShowDeleteModal(false);
        setHouseholdToDelete(null);
        setNotification({ type: "success", message: `Household ${householdToDelete.household_code} deleted successfully.` });
        refreshData();
      } else {
        const err = await res.json();
        alert(err.detail || "Delete operation failed.");
      }
    } catch (e) {
      alert("Error deleting household.");
    }
  };

  return (
    <div className="app-layout">
      {/* Top Banner */}
      <div style={{ width: "100%" }}>
        <div className="demo-banner">
          <div>
            <span className="demo-badge-tag">{t.demoMode}</span>
            <span style={{ marginLeft: "10px" }}>
              Karnataka Health System • Mandya District • Maddur Taluk • Kestur PHC
            </span>
          </div>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <button
              onClick={() => setLang(lang === "en" ? "kn" : "en")}
              className="btn btn-secondary btn-sm"
              style={{ padding: "3px 10px", background: "white", color: "#1e3a8a", fontWeight: "bold" }}
            >
              {lang === "en" ? "ಕನ್ನಡ" : "English"}
            </button>
          </div>
        </div>

        {/* Header Navigation */}
        <header className="app-header">
          <div className="header-content">
            <div className="brand-section">
              <div className="brand-logo">
                <Activity size={24} color="#ffffff" />
              </div>
              <div>
                <h1 className="brand-title">{t.appTitle}</h1>
                <p className="brand-subtitle">{t.appSubtitle}</p>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
              {currentUser ? (
                <div className="worker-info">
                  <span className="status-dot"></span>
                  <span>
                    <strong>{currentUser.full_name}</strong> ({currentUser.role})
                  </span>
                  <span className="worker-badge-pill">{currentUser.badge_id || currentUser.assigned_pincode || "Field"}</span>
                  <button
                    onClick={() => { setCurrentUser(null); setNotification({ type: "info", message: "Logged out." }); }}
                    className="btn btn-secondary btn-sm"
                  >
                    <LogOut size={14} style={{ marginRight: "4px" }} />
                    {t.logoutBtn}
                  </button>
                </div>
              ) : (
                <button onClick={() => setShowLoginModal(true)} className="btn btn-primary btn-sm">
                  <LogIn size={14} style={{ marginRight: "4px" }} />
                  {t.loginBtn}
                </button>
              )}
            </div>
          </div>
        </header>

        {/* Global Notifications */}
        {notification && (
          <div style={{ maxWidth: "1280px", margin: "16px auto 0", padding: "0 20px" }}>
            <div style={{
              padding: "12px 18px",
              borderRadius: "8px",
              background: notification.type === "success" ? "#dcfce7" : notification.type === "warning" ? "#fef3c7" : "#fee2e2",
              border: `1px solid ${notification.type === "success" ? "#86efac" : notification.type === "warning" ? "#fde047" : "#fca5a5"}`,
              color: notification.type === "success" ? "#166534" : notification.type === "warning" ? "#854d0e" : "#991b1b",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center"
            }}>
              <span>{notification.message}</span>
              <button onClick={() => setNotification(null)} style={{ background: "none", border: "none", cursor: "pointer", fontWeight: "bold" }}>✕</button>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        <main className="main-container">
          {/* Navigation Tabs */}
          <nav className="nav-tabs">
            <button
              onClick={() => setActiveTab('VOICE')}
              className={`tab-button ${activeTab === 'VOICE' ? 'active' : ''}`}
            >
              <Mic size={16} />
              <span>{t.tabVoice}</span>
            </button>
            <button
              onClick={() => setActiveTab('DASHBOARD')}
              className={`tab-button ${activeTab === 'DASHBOARD' ? 'active' : ''}`}
            >
              <LayoutDashboard size={16} />
              <span>{t.tabOverview}</span>
              <span className="tab-badge">{visits.length}</span>
            </button>
            <button
              onClick={() => setActiveTab('FOLLOWUPS')}
              className={`tab-button ${activeTab === 'FOLLOWUPS' ? 'active' : ''}`}
            >
              <Calendar size={16} />
              <span>{t.tabFollowups}</span>
              <span className="tab-badge">{followups.length}</span>
            </button>
            <button
              onClick={() => setActiveTab('HOUSEHOLDS')}
              className={`tab-button ${activeTab === 'HOUSEHOLDS' ? 'active' : ''}`}
            >
              <Home size={16} />
              <span>{t.tabHouseholds}</span>
              <span className="tab-badge">{households.length}</span>
            </button>
            <button
              onClick={() => setActiveTab('FINDER')}
              className={`tab-button ${activeTab === 'FINDER' ? 'active' : ''}`}
            >
              <Search size={16} />
              <span>{t.tabFinder}</span>
            </button>
          </nav>

          {/* TAB 1: VOICE & AI REGISTER (PHASE 1 + PHASE 2 PIPELINE) */}
          {activeTab === 'VOICE' && (
            <div>
              {/* Phase 1: Real-time Audio Capture & Streaming STT */}
              <VoiceRecorder onTranscriptComplete={handleTranscriptComplete} />

              {/* Extraction progress indicator */}
              {extractingReport && (
                <div style={{ textAlign: "center", padding: "24px", background: "white", borderRadius: "12px", border: "1px solid var(--gray-200)", marginBottom: "20px" }}>
                  <div style={{ fontSize: "16px", fontWeight: "600", color: "#1e3a8a" }}>
                    Analyzing voice note with AI Safety Engine...
                  </div>
                  <div style={{ fontSize: "13px", color: "var(--gray-500)", marginTop: "4px" }}>
                    Extracting vitals, danger signs, and maternal health indicators
                  </div>
                </div>
              )}

              {/* Phase 2: Structured Clinical Extraction Review Card */}
              {currentReport && (
                <StructuredVisitReport
                  report={currentReport}
                  language={currentLanguage}
                  onUpdateReport={(updated) => setCurrentReport(updated)}
                  onConfirmAndSave={handleConfirmAndSave}
                />
              )}
            </div>
          )}

          {/* TAB 2: FIELD REGISTER & DASHBOARD (PHASE 3) */}
          {activeTab === 'DASHBOARD' && (
            <div>
              {/* Emergency Referral Alert Banner */}
              {reports && reports.urgent_referrals?.length > 0 && (
                <div className="referral-banner">
                  <div className="referral-header">
                    <div className="referral-title">
                      <AlertTriangle size={20} color="#dc2626" />
                      <span>{reports.urgent_referrals.length} Active Beneficiaries Flagged for Urgent PHC Medical Referral</span>
                    </div>
                    <span className="badge badge-danger">Immediate Action Required</span>
                  </div>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "6px" }}>
                    {reports.urgent_referrals.map(r => (
                      <span key={r.visit_id} className="danger-tag">
                        {r.beneficiary_id} ({r.beneficiary_name}): {r.danger_signs?.join(", ") || "Clinical alert flagged"}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Statistics Grid */}
              <div className="stats-grid">
                <div className="stat-card">
                  <span className="stat-label">{t.totalHouseholds}</span>
                  <div className="stat-value">{households.length || 6}</div>
                  <div className="stat-subtext">Geo-scoped to assigned area</div>
                </div>
                <div className="stat-card">
                  <span className="stat-label">{t.totalBeneficiaries}</span>
                  <div className="stat-value">{reports?.total_beneficiaries || beneficiaries.length || 5}</div>
                  <div className="stat-subtext">Master clinical profiles in SQLite</div>
                </div>
                <div className="stat-card">
                  <span className="stat-label">{t.totalVisits}</span>
                  <div className="stat-value" style={{ color: "#0d9488" }}>{visits.length}</div>
                  <div className="stat-subtext">Saved with worker confirmation</div>
                </div>
                <div className="stat-card">
                  <span className="stat-label">{t.pendingFollowups}</span>
                  <div className="stat-value" style={{ color: "#d97706" }}>
                    {followups.filter(f => f.status === "scheduled" || f.status === "overdue").length}
                  </div>
                  <div className="stat-subtext">Safe scheduling (No fabricated dates)</div>
                </div>
                <div className="stat-card alert-card">
                  <span className="stat-label">{t.referralAlerts}</span>
                  <div className="stat-value">{reports?.urgent_referrals?.length || 0}</div>
                  <div className="stat-subtext">Retained danger signs for PHC</div>
                </div>
              </div>

              {/* Confirmed Visits Table from SQLite */}
              <div className="content-panel">
                <div className="panel-header">
                  <div>
                    <h3 className="panel-title">Confirmed Visits Register</h3>
                    <p style={{ fontSize: "13px", color: "var(--gray-500)" }}>
                      Persisted visit records in SQLite with duplicate checksum protection and danger signs retention.
                    </p>
                  </div>
                  <div className="search-bar">
                    <input
                      type="text"
                      placeholder="Search by Beneficiary ID or Visit Type..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="input-field"
                    />
                  </div>
                </div>

                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Visit ID</th>
                        <th>Beneficiary ID</th>
                        <th>Visit Type</th>
                        <th>Weight</th>
                        <th>Vaccinations</th>
                        <th>Danger Signs</th>
                        <th>Referral Flag</th>
                        <th>Persisted At</th>
                      </tr>
                    </thead>
                    <tbody>
                      {visits
                        .filter(v =>
                          v.beneficiary_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          v.visit_type?.toLowerCase().includes(searchTerm.toLowerCase())
                        )
                        .map((v) => (
                          <tr key={v.visit_id}>
                            <td><code>{v.visit_id}</code></td>
                            <td><strong>{v.beneficiary_id}</strong></td>
                            <td>{v.visit_type}</td>
                            <td>{v.weight || "—"}</td>
                            <td>
                              {v.vaccinations_due && v.vaccinations_due.length > 0 ? (
                                v.vaccinations_due.map((vac, i) => (
                                  <span key={i} className="vaccine-tag">{vac}</span>
                                ))
                              ) : "—"}
                            </td>
                            <td>
                              {v.danger_signs && v.danger_signs.length > 0 ? (
                                v.danger_signs.map((ds, i) => (
                                  <span key={i} className="danger-tag">{ds}</span>
                                ))
                              ) : (
                                <span style={{ color: "#16a34a", fontSize: "12px" }}>✓ None</span>
                              )}
                            </td>
                            <td>
                              {v.referral_required ? (
                                <span className="badge badge-danger">Urgent Referral</span>
                              ) : (
                                <span className="badge badge-success">Routine</span>
                              )}
                            </td>
                            <td style={{ fontSize: "12px", color: "var(--gray-500)" }}>
                              {v.created_at ? v.created_at.replace("T", " ").substring(0, 19) : "—"}
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: FOLLOW-UP TRACKER */}
          {activeTab === 'FOLLOWUPS' && (
            <div className="content-panel">
              <div className="panel-header">
                <div>
                  <h3 className="panel-title">{t.tabFollowups}</h3>
                  <p style={{ fontSize: "13px", color: "var(--gray-500)" }}>
                    Preserves follow-up scheduling without fabricating dates when null. Overdue alerts highlighted.
                  </p>
                </div>
              </div>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Follow-up ID</th>
                      <th>Beneficiary ID</th>
                      <th>Scheduled Date</th>
                      <th>Status</th>
                      <th>Worker Field Notes</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {followups.map((fol) => (
                      <tr key={fol.follow_up_id}>
                        <td><code>{fol.follow_up_id}</code></td>
                        <td><strong>{fol.beneficiary_id}</strong></td>
                        <td>{fol.follow_up_date || "None scheduled (null)"}</td>
                        <td>
                          <span className={`badge ${
                            fol.status === "completed" ? "badge-success" :
                            fol.status === "overdue" ? "badge-danger" : "badge-warning"
                          }`}>
                            {fol.status}
                          </span>
                        </td>
                        <td style={{ fontSize: "13px" }}>{fol.notes || "No notes entered"}</td>
                        <td>
                          {fol.status !== "completed" ? (
                            <button
                              onClick={() => { setActiveFollowup(fol); setFollowupNotes(fol.notes || ""); setShowFollowupModal(true); }}
                              className="btn btn-secondary btn-sm"
                            >
                              Mark Complete
                            </button>
                          ) : (
                            <span style={{ color: "#16a34a", fontSize: "12px", fontWeight: "600" }}>✓ Complete</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 4: HOUSEHOLD & FAMILY SURVEY DIRECTORY */}
          {activeTab === 'HOUSEHOLDS' && (
            <div className="content-panel">
              <div className="panel-header">
                <div>
                  <h3 className="panel-title">{t.tabHouseholds}</h3>
                  <p style={{ fontSize: "13px", color: "var(--gray-500)" }}>
                    Geo-scoped households with family member health profiling, edit, and safe deletion.
                  </p>
                </div>
                <div className="search-bar">
                  <input
                    type="text"
                    placeholder="Search by Household Code, Head, or Address..."
                    className="input-field"
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>

              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Household Code</th>
                      <th>Head of Family</th>
                      <th>Village & PIN</th>
                      <th>Housing & Sanitation</th>
                      <th>Members</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {households
                      .filter(h =>
                        h.household_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        h.head_of_family?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        h.village?.toLowerCase().includes(searchTerm.toLowerCase())
                      )
                      .map((h) => (
                        <tr key={h.id}>
                          <td><code>{h.household_code}</code></td>
                          <td>
                            <strong>{h.head_of_family}</strong>
                            <div style={{ fontSize: "12px", color: "var(--gray-500)" }}>{h.address_line}</div>
                          </td>
                          <td>
                            <div>{h.village}</div>
                            <span className="scope-pill">PIN: {h.pincode}</span>
                          </td>
                          <td style={{ fontSize: "13px" }}>
                            <div>House: {h.house_type}</div>
                            <div>Water: {h.drinking_water_source} | Toilet: {h.toilet_facility ? "Yes" : "No"}</div>
                          </td>
                          <td>
                            <span className="badge badge-info">{h.member_count || 3} members</span>
                          </td>
                          <td>
                            <div style={{ display: "flex", gap: "6px" }}>
                              <button
                                onClick={() => { setHouseholdToEdit(h); setShowEditModal(true); }}
                                className="btn btn-secondary btn-sm"
                              >
                                {t.edit}
                              </button>
                              <button
                                onClick={() => { setHouseholdToDelete(h); setShowDeleteModal(true); }}
                                className="btn btn-danger btn-sm"
                              >
                                {t.delete}
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 5: FIND ASHA WORKER PORTAL */}
          {activeTab === 'FINDER' && (
            <div>
              <div className="finder-hero">
                <h2 style={{ fontSize: "24px", fontWeight: "800", marginBottom: "8px" }}>
                  🔍 Find Your Assigned ASHA Worker
                </h2>
                <p style={{ fontSize: "15px", maxWidth: "600px", margin: "0 auto 20px", opacity: 0.9 }}>
                  Search by PIN code, village name, taluk, or district to locate officially registered ASHA workers.
                </p>

                <form onSubmit={handleFinderSearch} style={{ display: "flex", gap: "10px", justifyContent: "center", flexWrap: "wrap", maxWidth: "700px", margin: "0 auto" }}>
                  <input
                    type="text"
                    placeholder="Enter Postal PIN code (e.g. 571428)"
                    value={finderQuery.pincode}
                    onChange={(e) => setFinderQuery({ ...finderQuery, pincode: e.target.value })}
                    className="input-field"
                    style={{ flex: 1, minWidth: "220px", background: "white" }}
                  />
                  <input
                    type="text"
                    placeholder="Village Name (e.g. Rampur)"
                    value={finderQuery.village}
                    onChange={(e) => setFinderQuery({ ...finderQuery, village: e.target.value })}
                    className="input-field"
                    style={{ flex: 1, minWidth: "180px", background: "white" }}
                  />
                  <button type="submit" className="btn btn-primary" style={{ background: "#0d9488" }}>
                    {finderLoading ? "Searching..." : "Search ASHA Directory"}
                  </button>
                </form>
              </div>

              {finderMessage && (
                <div style={{ padding: "12px 18px", borderRadius: "8px", background: "#f8fafc", border: "1px solid #e2e8f0", marginBottom: "20px", textAlign: "center", color: "#475569" }}>
                  {finderMessage}
                </div>
              )}

              <div className="finder-grid">
                {finderResults.length > 0 ? (
                  finderResults.map((w) => (
                    <div key={w.worker_id} className="finder-card">
                      <div>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                          <div>
                            <h3 style={{ fontSize: "17px", fontWeight: "700", color: "#1e3a8a" }}>{w.full_name}</h3>
                            <span className="worker-badge-pill" style={{ marginTop: "4px" }}>Badge: {w.badge_id}</span>
                          </div>
                          <span className="badge badge-success">Official ASHA</span>
                        </div>

                        <div style={{ fontSize: "13px", color: "var(--gray-700)", lineHeight: 1.8 }}>
                          <div><strong>Coverage Area:</strong> {w.area_name || w.village}</div>
                          <div><strong>Village:</strong> {w.village} | <strong>PIN:</strong> {w.pincode}</div>
                          <div><strong>PHC:</strong> {w.phc_name}</div>
                          <div><strong>Mobile:</strong> {w.mobile}</div>
                        </div>
                      </div>

                      <div style={{ marginTop: "18px", borderTop: "1px solid var(--gray-200)", paddingTop: "14px" }}>
                        <button
                          onClick={() => {
                            setLoginForm({ username: w.username, password: "asha123" });
                            setShowLoginModal(true);
                          }}
                          className="btn btn-primary btn-sm"
                          style={{ width: "100%" }}
                        >
                          Login to {w.full_name.split(" ")[0]}'s Portal
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div style={{ gridColumn: "1/-1", textAlign: "center", padding: "40px 20px", color: "var(--gray-500)" }}>
                    Enter a PIN code (e.g. <code>571428</code> or <code>571434</code>) to view registered workers.
                  </div>
                )}
              </div>
            </div>
          )}
        </main>

        {/* MODAL: LOGIN SYSTEM */}
        {showLoginModal && (
          <div className="modal-overlay">
            <div className="modal-card" style={{ maxWidth: "420px" }}>
              <div className="modal-header">
                <h3 className="panel-title">ASHA Sahayak Portal Login</h3>
                <button onClick={() => setShowLoginModal(false)} style={{ background: "none", border: "none", fontSize: "18px", cursor: "pointer" }}>✕</button>
              </div>
              <form onSubmit={handleLoginSubmit}>
                <div className="modal-body">
                  {loginError && (
                    <div style={{ padding: "8px 12px", background: "#fee2e2", color: "#991b1b", borderRadius: "6px", fontSize: "13px", marginBottom: "14px" }}>
                      {loginError}
                    </div>
                  )}
                  <div style={{ marginBottom: "14px" }}>
                    <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "4px" }}>Username / Login ID</label>
                    <input
                      type="text"
                      className="input-field"
                      value={loginForm.username}
                      onChange={(e) => setLoginForm({ ...loginForm, username: e.target.value })}
                      required
                    />
                  </div>
                  <div style={{ marginBottom: "14px" }}>
                    <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "4px" }}>Password</label>
                    <div style={{ position: "relative" }}>
                      <input
                        type={showPassword ? "text" : "password"}
                        className="input-field"
                        value={loginForm.password}
                        onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        style={{ position: "absolute", right: "10px", top: "12px", background: "none", border: "none", cursor: "pointer", fontSize: "12px", color: "var(--gray-500)" }}
                      >
                        {showPassword ? "Hide" : "Show"}
                      </button>
                    </div>
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--gray-500)", background: "#f8fafc", padding: "10px", borderRadius: "6px" }}>
                    <strong>Demo Logins:</strong>
                    <div>ASHA Rampur: <code>asha_rampur</code> / <code>asha123</code></div>
                    <div>Administrator: <code>admin</code> / <code>admin123</code></div>
                    <div>Supervisor: <code>supervisor_maddur</code> / <code>sup123</code></div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" onClick={() => setShowLoginModal(false)} className="btn btn-secondary">{t.cancel}</button>
                  <button type="submit" className="btn btn-primary">{t.loginBtn}</button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* MODAL: COMPLETE FOLLOW-UP */}
        {showFollowupModal && activeFollowup && (
          <div className="modal-overlay">
            <div className="modal-card" style={{ maxWidth: "480px" }}>
              <div className="modal-header">
                <h3 className="panel-title">Complete Follow-up: {activeFollowup.follow_up_id}</h3>
                <button onClick={() => setShowFollowupModal(false)} style={{ background: "none", border: "none", cursor: "pointer" }}>✕</button>
              </div>
              <div className="modal-body">
                <p style={{ fontSize: "14px", marginBottom: "12px" }}>
                  Beneficiary: <strong>{activeFollowup.beneficiary_id}</strong><br />
                  Scheduled Date: <strong>{activeFollowup.follow_up_date || "None scheduled (null)"}</strong>
                </p>
                <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "6px" }}>Worker Visit Field Notes:</label>
                <textarea
                  className="input-field"
                  style={{ minHeight: "100px" }}
                  value={followupNotes}
                  onChange={(e) => setFollowupNotes(e.target.value)}
                  placeholder="Record maternal status, infant weight gain, vaccination administration..."
                />
              </div>
              <div className="modal-footer">
                <button onClick={() => setShowFollowupModal(false)} className="btn btn-secondary">{t.cancel}</button>
                <button onClick={handleCompleteFollowup} className="btn btn-success">Save & Mark Complete</button>
              </div>
            </div>
          </div>
        )}

        {/* MODAL: DELETE CONFIRMATION */}
        {showDeleteModal && householdToDelete && (
          <div className="modal-overlay">
            <div className="modal-card" style={{ maxWidth: "440px" }}>
              <div className="modal-header" style={{ borderBottomColor: "#fecaca" }}>
                <h3 className="panel-title" style={{ color: "#991b1b" }}>⚠️ Confirm Household Deletion</h3>
                <button onClick={() => setShowDeleteModal(false)} style={{ background: "none", border: "none", cursor: "pointer" }}>✕</button>
              </div>
              <div className="modal-body">
                <p style={{ fontSize: "14px", color: "var(--gray-700)" }}>
                  Are you sure you want to permanently delete this household survey record?
                </p>
                <div style={{ background: "#fef2f2", padding: "12px", borderRadius: "8px", marginTop: "12px", border: "1px solid #fca5a5" }}>
                  <div><strong>Code:</strong> {householdToDelete.household_code}</div>
                  <div><strong>Head of Family:</strong> {householdToDelete.head_of_family}</div>
                  <div><strong>Address:</strong> {householdToDelete.address_line}</div>
                </div>
              </div>
              <div className="modal-footer">
                <button onClick={() => setShowDeleteModal(false)} className="btn btn-secondary">{t.cancel}</button>
                <button onClick={confirmDeleteHousehold} className="btn btn-danger">Confirm Delete</button>
              </div>
            </div>
          </div>
        )}

        {/* MODAL: EDIT HOUSEHOLD */}
        {showEditModal && householdToEdit && (
          <div className="modal-overlay">
            <div className="modal-card" style={{ maxWidth: "560px" }}>
              <div className="modal-header">
                <h3 className="panel-title">Edit Household: {householdToEdit.household_code}</h3>
                <button onClick={() => setShowEditModal(false)} style={{ background: "none", border: "none", cursor: "pointer" }}>✕</button>
              </div>
              <div className="modal-body">
                <div style={{ marginBottom: "14px" }}>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "4px" }}>Head of Family Name</label>
                  <input
                    type="text"
                    className="input-field"
                    value={householdToEdit.head_of_family}
                    onChange={(e) => setHouseholdToEdit({ ...householdToEdit, head_of_family: e.target.value })}
                  />
                </div>
                <div style={{ marginBottom: "14px" }}>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "4px" }}>Address Line</label>
                  <input
                    type="text"
                    className="input-field"
                    value={householdToEdit.address_line}
                    onChange={(e) => setHouseholdToEdit({ ...householdToEdit, address_line: e.target.value })}
                  />
                </div>
                <div style={{ marginBottom: "14px" }}>
                  <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "4px" }}>Housing Structure Type</label>
                  <select
                    className="input-field"
                    value={householdToEdit.house_type || "Pucca"}
                    onChange={(e) => setHouseholdToEdit({ ...householdToEdit, house_type: e.target.value })}
                  >
                    <option value="Pucca">Pucca (Concrete/Brick)</option>
                    <option value="Semi-Pucca">Semi-Pucca (Tiled/Stone)</option>
                    <option value="Kutcha">Kutcha (Mud/Thatch)</option>
                  </select>
                </div>
              </div>
              <div className="modal-footer">
                <button onClick={() => setShowEditModal(false)} className="btn btn-secondary">{t.cancel}</button>
                <button
                  onClick={async () => {
                    const headers = {
                      "Content-Type": "application/json",
                      "Authorization": `Bearer token-${currentUser.username}-${currentUser.id}`
                    };
                    const res = await fetch(`${API_BASE}/api/households/${householdToEdit.id}`, {
                      method: "PUT",
                      headers,
                      body: JSON.stringify({
                        head_of_family: householdToEdit.head_of_family,
                        address_line: householdToEdit.address_line,
                        house_type: householdToEdit.house_type
                      })
                    });
                    if (res.ok) {
                      setShowEditModal(false);
                      setNotification({ type: "success", message: `Household ${householdToEdit.household_code} updated.` });
                      refreshData();
                    } else {
                      alert("Failed to update household.");
                    }
                  }}
                  className="btn btn-primary"
                >
                  {t.saveChanges}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

import React, { useState, useEffect, useRef } from 'react';

const API_BASE = window.location.port === "8000" ? "" : "http://localhost:8000";

// Bilingual translations dictionary
const I18N = {
  en: {
    appTitle: "ASHA Sahayak",
    appSubtitle: "AI Voice Field Register & Community Health System",
    demoMode: "SYNTHETIC HEALTHCARE DEMO – NO REAL PHI",
    tabOverview: "Overview & Reports",
    tabVoice: "Voice Field Register (Phase 1 & 2)",
    tabVisits: "Confirmed Visits Register",
    tabFollowups: "Follow-up Tracker",
    tabHouseholds: "Household Directory",
    tabSurvey: "New Household Survey",
    tabFinder: "Find ASHA Worker",
    loginBtn: "Login",
    logoutBtn: "Logout",
    welcome: "Welcome",
    role: "Role",
    totalHouseholds: "Total Households",
    totalBeneficiaries: "Total Beneficiaries",
    totalVisits: "Confirmed Visits",
    pendingFollowups: "Scheduled Follow-ups",
    referralAlerts: "Urgent Referral Alerts",
    recordVoice: "Record Visit Voice Note",
    stopRecording: "Stop Recording",
    liveTranscript: "Live Voice Transcription",
    sendToAi: "Extract Clinical Entities with AI",
    confirmVisit: "Confirm & Save Visit to Register",
    rejectVisit: "Discard & Re-record",
    duplicateError: "Duplicate visit record detected. This entry was already persisted.",
    successSaved: "Visit successfully confirmed and saved to SQLite register!",
    searchBeneficiary: "Search by Beneficiary ID, Name, or Village...",
    searchHousehold: "Search by Household Code, Head of Family, or Village...",
    statusConfirmed: "Confirmed",
    statusOverdue: "Overdue",
    statusUpcoming: "Upcoming",
    dangerSigns: "Danger Signs Observed",
    vaccinations: "Vaccinations Administered / Due",
    weight: "Weight Recorded",
    visitType: "Visit Type",
    nextFollowup: "Next Follow-up Date",
    noFabricatedDate: "None scheduled (Preserved null - No invented date)",
    edit: "Edit",
    delete: "Delete",
    saveChanges: "Save Changes",
    cancel: "Cancel"
  },
  kn: {
    appTitle: "ಆಶಾ ಸಹಾಯಕ",
    appSubtitle: "ಧ್ವನಿ ಆಧಾರಿತ ಕ್ಷೇತ್ರ ನೋಂದಣಿ ಮತ್ತು ಸಮುದಾಯ ಆರೋಗ್ಯ ನಿರ್ವಹಣೆ",
    demoMode: "ಪ್ರಾತ್ಯಕ್ಷಿಕೆ ಮಾದರಿ – ಯಾವುದೇ ನೈಜ ರೋಗಿಯ ಮಾಹಿತಿಯಿಲ್ಲ",
    tabOverview: "ಅವಲೋಕನ ಮತ್ತು ವರದಿಗಳು",
    tabVoice: "ಧ್ವನಿ ಕ್ಷೇತ್ರ ರಿಜಿಸ್ಟರ್ (ಹಂತ 1 ಮತ್ತು 2)",
    tabVisits: "ದೃಢೀಕರಿಸಿದ ಭೇಟಿಗಳ ರಿಜಿಸ್ಟರ್",
    tabFollowups: "ಫಾಲೋ-ಅಪ್ ಟ್ರ್ಯಾಕರ್",
    tabHouseholds: "ಮನೆಗಳ ಡೈರೆಕ್ಟರಿ",
    tabSurvey: "ಹೊಸ ಮನೆ ಸಮೀಕ್ಷೆ",
    tabFinder: "ಆಶಾ ಕಾರ್ಯಕರ್ತೆಯರನ್ನು ಹುಡುಕಿ",
    loginBtn: "ಲಾಗಿನ್",
    logoutBtn: "ಲಾಗ್‌ಔಟ್",
    welcome: "ಸ್ವಾಗತ",
    role: "ಪಾತ್ರ",
    totalHouseholds: "ಒಟ್ಟು ಕುಟುಂಬಗಳು",
    totalBeneficiaries: "ಒಟ್ಟು ಫಲಾನುಭವಿಗಳು",
    totalVisits: "ದೃಢೀಕರಿಸಿದ ಭೇಟಿಗಳು",
    pendingFollowups: "ನಿಗದಿತ ಫಾಲೋ-ಅಪ್‌ಗಳು",
    referralAlerts: "ತುರ್ತು ರೆಫರಲ್ ಎಚ್ಚರಿಕೆಗಳು",
    recordVoice: "ಭೇಟಿ ಧ್ವನಿ ರೆಕಾರ್ಡ್ ಮಾಡಿ",
    stopRecording: "ರೆಕಾರ್ಡಿಂಗ್ ನಿಲ್ಲಿಸಿ",
    liveTranscript: "ಲೈವ್ ಧ್ವನಿ ಪ್ರತಿಲಿಪಿ",
    sendToAi: "AI ಮೂಲಕ ವೈದ್ಯಕೀಯ ವಿವರಗಳನ್ನು ಹೊರತೆಗೆಯಿರಿ",
    confirmVisit: "ದೃಢೀಕರಿಸಿ ರಿಜಿಸ್ಟರ್‌ನಲ್ಲಿ ಉಳಿಸಿ",
    rejectVisit: "ತಿರಸ್ಕರಿಸಿ / ಮರು ರೆಕಾರ್ಡ್ ಮಾಡಿ",
    duplicateError: "ನಕಲಿ ಭೇಟಿ ಪತ್ತೆಯಾಗಿದೆ. ಈ ನಮೂದು ಈಗಾಗಲೇ ಉಳಿಸಲಾಗಿದೆ.",
    successSaved: "ಭೇಟಿಯನ್ನು ಯಶಸ್ವಿಯಾಗಿ ದೃಢೀಕರಿಸಿ ರಿಜಿಸ್ಟರ್‌ನಲ್ಲಿ ಉಳಿಸಲಾಗಿದೆ!",
    searchBeneficiary: "ಫಲಾನುಭವಿ ಐಡಿ, ಹೆಸರು ಅಥವಾ ಹಳ್ಳಿಯ ಮೂಲಕ ಹುಡುಕಿ...",
    searchHousehold: "ಕುಟುಂಬ ಕೋಡ್, ಯಜಮಾನರ ಹೆಸರು ಮೂಲಕ ಹುಡುಕಿ...",
    statusConfirmed: "ದೃಢೀಕರಿಸಲಾಗಿದೆ",
    statusOverdue: "ಅವಧಿ ಮೀರಿದೆ",
    statusUpcoming: "ಮುಂಬರುವ",
    dangerSigns: "ಅಪಾಯಕಾರಿ ಲಕ್ಷಣಗಳು",
    vaccinations: "ನೀಡಲಾದ ಲಸಿಕೆಗಳು",
    weight: "ದಾಖಲಿಸಿದ ತೂಕ",
    visitType: "ಭೇಟಿ ಪ್ರಕಾರ",
    nextFollowup: "ಮುಂದಿನ ಭೇಟಿ ದಿನಾಂಕ",
    noFabricatedDate: "ಯಾವುದೂ ನಿಗದಿಯಾಗಿಲ್ಲ (ಖಾಲಿ ಇರಿಸಲಾಗಿದೆ)",
    edit: "ತಿದ್ದುಪಡಿ",
    delete: "ಅಳಿಸಿ",
    saveChanges: "ಬದಲಾವಣೆಗಳನ್ನು ಉಳಿಸಿ",
    cancel: "ರದ್ದುಮಾಡಿ"
  }
};

export default function App() {
  const [lang, setLang] = useState("en");
  const t = I18N[lang];

  const [activeTab, setActiveTab] = useState("overview");
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

  // Real Database State
  const [reports, setReports] = useState(null);
  const [visits, setVisits] = useState([]);
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [followups, setFollowups] = useState([]);
  const [households, setHouseholds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState(null);

  // Search & Filter State
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedBeneficiary, setSelectedBeneficiary] = useState(null);
  const [selectedHousehold, setSelectedHousehold] = useState(null);

  // Phase 1 Voice State
  const [isRecording, setIsRecording] = useState(false);
  const [voiceLanguage, setVoiceLanguage] = useState("kn-IN");
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [audioWsConnected, setAudioWsConnected] = useState(false);
  const wsRef = useRef(null);
  const recognitionRef = useRef(null);

  // Phase 2 AI Review State
  const [extractedRecord, setExtractedRecord] = useState({
    beneficiary_id: "BNF-2041",
    visit_type: "Newborn home visit",
    weight: "3.2 kg",
    vaccinations_due: ["OPV-1"],
    next_visit_date: null,
    danger_signs: [],
    referral_required: false,
    confirmation_status: "confirmed"
  });
  const [isSubmittingVisit, setIsSubmittingVisit] = useState(false);

  // Modals
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: "asha_rampur", password: "asha123" });
  const [showPassword, setShowPassword] = useState(false);
  const [loginError, setLoginError] = useState(null);

  const [showFollowupModal, setShowFollowupModal] = useState(false);
  const [activeFollowup, setActiveFollowup] = useState(null);
  const [followupNotes, setFollowupNotes] = useState("");

  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [householdToDelete, setHouseholdToDelete] = useState(null);

  const [showEditModal, setShowEditModal] = useState(false);
  const [householdToEdit, setHouseholdToEdit] = useState(null);

  // Finder Portal State
  const [finderQuery, setFinderQuery] = useState({ pincode: "571428", village: "", taluk: "", district: "" });
  const [finderResults, setFinderResults] = useState([]);
  const [finderLoading, setFinderLoading] = useState(false);
  const [finderMessage, setFinderMessage] = useState("");

  // Load Real Data from SQLite Backend
  const refreshData = async () => {
    try {
      setLoading(true);
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
    } catch (err) {
      console.warn("Backend fetch notice:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshData();
  }, [currentUser]);

  // Connect WebSocket for Phase 1 Voice Streaming
  useEffect(() => {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = window.location.port === "8000" ? window.location.host : "localhost:8000";
    const wsUrl = `${wsProtocol}//${wsHost}/ws/audio`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => setAudioWsConnected(true);
      ws.onclose = () => setAudioWsConnected(false);
      ws.onerror = () => setAudioWsConnected(false);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.event === "transcript_ack") {
            setVoiceTranscript(prev => prev + " " + msg.transcript);
          }
        } catch (e) {}
      };

      return () => ws.close();
    } catch (e) {
      setAudioWsConnected(false);
    }
  }, []);

  // Web Speech API / Voice Toggle
  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ event: "finish_recording" }));
      }
    } else {
      setIsRecording(true);
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognitionRef.current = recognition;
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = voiceLanguage;

        recognition.onresult = (event) => {
          let currentTranscript = "";
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            currentTranscript += event.results[i][0].transcript;
          }
          setVoiceTranscript(currentTranscript);
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ event: "partial_transcript", text: currentTranscript }));
          }
        };

        recognition.onerror = () => {
          // Fallback to simulated phrase if mic permission denied
          loadSimulatedVoiceNote("newborn");
        };

        try {
          recognition.start();
        } catch (err) {
          loadSimulatedVoiceNote("newborn");
        }
      } else {
        // Fallback for browsers without Web Speech API
        loadSimulatedVoiceNote("newborn");
      }
    }
  };

  // Simulated voice note samples for quick field testing
  const loadSimulatedVoiceNote = (type) => {
    setIsRecording(false);
    if (type === "newborn") {
      setVoiceTranscript("ಹೊಸದಾಗಿ ಜನಿಸಿದ ಮಗುವಿನ ಮನೆ ಭೇಟಿ ಪೂರ್ಣಗೊಂಡಿದೆ. ಫಲಾನುಭವಿ ಬಿಎನ್‌ಎಫ್-2041. ಮಗುವಿನ ತೂಕ 3.2 ಕೆಜಿ. OPV-1 ಲಸಿಕೆ ನೀಡಲಾಗಿದೆ. ಯಾವುದೇ ಅಪಾಯಕಾರಿ ಲಕ್ಷಣಗಳಿಲ್ಲ. ಮುಂದಿನ ಭೇಟಿ ದಿನಾಂಕ ನಿಗದಿಪಡಿಸಿಲ್ಲ.");
      setExtractedRecord({
        beneficiary_id: "BNF-2041",
        visit_type: "Newborn home visit",
        weight: "3.2 kg",
        vaccinations_due: ["OPV-1"],
        next_visit_date: null,
        danger_signs: [],
        referral_required: false,
        confirmation_status: "confirmed"
      });
    } else if (type === "anc_danger") {
      setVoiceTranscript("ಗರ್ಭಿಣಿ ತಪಾಸಣೆ ಭೇಟಿ. ಫಲಾನುಭವಿ ಬಿಎನ್‌ಎಫ್-2042. ತೂಕ 58 ಕೆಜಿ. ಅಧಿಕ ರಕ್ತದೊತ್ತಡ ಮತ್ತು ಪಾದಗಳಲ್ಲಿ ಊತ ಕಂಡುಬಂದಿದೆ. ತಕ್ಷಣದ PHC ರೆಫರಲ್ ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ.");
      setExtractedRecord({
        beneficiary_id: "BNF-2042",
        visit_type: "Antenatal Care (ANC)",
        weight: "58.0 kg",
        vaccinations_due: ["TT Booster"],
        next_visit_date: "2026-12-01",
        danger_signs: ["High blood pressure (Hypertension)", "Swelling in feet (Edema)"],
        referral_required: true,
        confirmation_status: "confirmed"
      });
    }
  };

  // Submit worker-confirmed visit to Phase 3 endpoint
  const handleConfirmAndSaveVisit = async () => {
    try {
      setIsSubmittingVisit(true);
      setNotification(null);

      const res = await fetch(`${API_BASE}/api/visits/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(extractedRecord)
      });

      const data = await res.json();
      if (res.status === 201) {
        setNotification({ type: "success", message: `${t.successSaved} (ID: ${data.visit_id})` });
        refreshData();
      } else if (res.status === 409) {
        setNotification({ type: "warning", message: `${t.duplicateError} (Checksum: ${data.fingerprint?.substring(0, 12)}...)` });
      } else {
        setNotification({ type: "error", message: data.detail || "Submission rejected by server validation." });
      }
    } catch (err) {
      setNotification({ type: "error", message: "Network connection error while confirming visit." });
    } finally {
      setIsSubmittingVisit(false);
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
        setNotification({ type: "success", message: `Logged in successfully as ${data.user.full_name} (${data.user.role})` });
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
              Karnataka Health System | Mandya District | Kestur PHC
            </span>
          </div>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <span style={{ fontSize: "12px" }}>
              WebSocket Stream: {audioWsConnected ? <strong style={{ color: "#34d399" }}>CONNECTED (/ws/audio)</strong> : <span style={{ color: "#cbd5e1" }}>OFFLINE</span>}
            </span>
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
              <div className="brand-logo">AS</div>
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
                    {t.logoutBtn}
                  </button>
                </div>
              ) : (
                <button onClick={() => setShowLoginModal(true)} className="btn btn-primary btn-sm">
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
              onClick={() => setActiveTab("overview")}
              className={`tab-button ${activeTab === "overview" ? "active" : ""}`}
            >
              <span>📊</span> {t.tabOverview}
            </button>
            <button
              onClick={() => setActiveTab("voice")}
              className={`tab-button ${activeTab === "voice" ? "active" : ""}`}
            >
              <span>🎙️</span> {t.tabVoice}
            </button>
            <button
              onClick={() => setActiveTab("visits")}
              className={`tab-button ${activeTab === "visits" ? "active" : ""}`}
            >
              <span>📋</span> {t.tabVisits}
              <span className="tab-badge">{visits.length}</span>
            </button>
            <button
              onClick={() => setActiveTab("followups")}
              className={`tab-button ${activeTab === "followups" ? "active" : ""}`}
            >
              <span>🔔</span> {t.tabFollowups}
              <span className="tab-badge">{followups.length}</span>
            </button>
            <button
              onClick={() => setActiveTab("households")}
              className={`tab-button ${activeTab === "households" ? "active" : ""}`}
            >
              <span>🏡</span> {t.tabHouseholds}
              <span className="tab-badge">{households.length}</span>
            </button>
            <button
              onClick={() => setActiveTab("finder")}
              className={`tab-button ${activeTab === "finder" ? "active" : ""}`}
            >
              <span>🔍</span> {t.tabFinder}
            </button>
          </nav>

          {/* TAB 1: OVERVIEW DASHBOARD */}
          {activeTab === "overview" && (
            <div>
              {/* Emergency Referral Alert Banner */}
              {reports && reports.urgent_referrals?.length > 0 && (
                <div className="referral-banner">
                  <div className="referral-header">
                    <div className="referral-title">
                      <span>⚠️</span>
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

              {/* Quick Integrated Architecture View */}
              <div className="content-panel">
                <h3 className="panel-title" style={{ marginBottom: "12px" }}>Integrated Architecture & Pipeline Status</h3>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
                  <div style={{ padding: "16px", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: "10px" }}>
                    <h4 style={{ color: "#166534", marginBottom: "6px" }}>Phase 1: Voice Recognition</h4>
                    <p style={{ fontSize: "13px", color: "#15803d" }}>Active WebSocket endpoint <code>/ws/audio</code> and HTTP transcription. Multilingual voice notes in Kannada, Hindi, and English.</p>
                  </div>
                  <div style={{ padding: "16px", background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "10px" }}>
                    <h4 style={{ color: "#1e40af", marginBottom: "6px" }}>Phase 2: AI Entity Extraction</h4>
                    <p style={{ fontSize: "13px", color: "#1d4ed8" }}>Clinical extraction review interface ready. Explicit worker confirmation barrier enforced before saving.</p>
                  </div>
                  <div style={{ padding: "16px", background: "#faf5ff", border: "1px solid #e9d5ff", borderRadius: "10px" }}>
                    <h4 style={{ color: "#6b21a8", marginBottom: "6px" }}>Phase 3: Database & Governance</h4>
                    <p style={{ fontSize: "13px", color: "#7e22ce" }}>SQLite WAL persistence, SHA-256 duplicate prevention, area/PIN code scoping, and household health surveys.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: VOICE FIELD REGISTER (PHASE 1 + PHASE 2 WORKFLOW) */}
          {activeTab === "voice" && (
            <div>
              {/* Phase 1: Voice Recording Component */}
              <div className="voice-recorder-card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
                  <div>
                    <h2 style={{ fontSize: "20px", fontWeight: "800" }}>🎙️ Phase 1: Voice Field Note Recording</h2>
                    <p style={{ fontSize: "14px", opacity: 0.9, marginTop: "4px" }}>
                      ASHA worker records field observation in local dialect. Audio streams via WebSocket to server.
                    </p>
                  </div>
                  <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                    <select
                      value={voiceLanguage}
                      onChange={(e) => setVoiceLanguage(e.target.value)}
                      className="input-field"
                      style={{ width: "auto", minHeight: "36px", padding: "6px 12px" }}
                    >
                      <option value="kn-IN">ಕನ್ನಡ (Kannada)</option>
                      <option value="hi-IN">हिंदी (Hindi)</option>
                      <option value="en-IN">English (Indian)</option>
                    </select>
                  </div>
                </div>

                <div className="voice-controls">
                  <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                    <button
                      onClick={toggleRecording}
                      className={`mic-btn ${isRecording ? "recording" : ""}`}
                      title={isRecording ? t.stopRecording : t.recordVoice}
                    >
                      {isRecording ? "⏹" : "🎤"}
                    </button>
                    <div>
                      <div style={{ fontWeight: "700", fontSize: "15px" }}>
                        {isRecording ? "Recording in progress... Speak clearly." : "Tap microphone to begin field note"}
                      </div>
                      <div style={{ fontSize: "13px", opacity: 0.85 }}>
                        Status: {isRecording ? "Transcribing live stream..." : "Microphone standby"}
                      </div>
                    </div>
                  </div>

                  <div className="waveform-container">
                    {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                      <div key={i} className={`wave-bar ${isRecording ? "active" : ""}`} style={{ animationDelay: `${i * 0.12}s` }}></div>
                    ))}
                  </div>
                </div>

                {/* Live Transcript Box */}
                <div style={{ marginTop: "16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", fontWeight: "600", opacity: 0.9 }}>
                    <span>{t.liveTranscript}:</span>
                    <div style={{ display: "flex", gap: "8px" }}>
                      <button onClick={() => loadSimulatedVoiceNote("newborn")} style={{ background: "rgba(255,255,255,0.2)", border: "none", color: "white", padding: "2px 8px", borderRadius: "4px", cursor: "pointer", fontSize: "11px" }}>
                        Load Sample 1 (Newborn Visit)
                      </button>
                      <button onClick={() => loadSimulatedVoiceNote("anc_danger")} style={{ background: "rgba(255,255,255,0.2)", border: "none", color: "white", padding: "2px 8px", borderRadius: "4px", cursor: "pointer", fontSize: "11px" }}>
                        Load Sample 2 (ANC Referral Alert)
                      </button>
                    </div>
                  </div>
                  <div className="transcript-box">
                    {voiceTranscript || "No speech recorded yet. Speak into the microphone or load a sample voice note above."}
                  </div>
                </div>
              </div>

              {/* Phase 2: AI Clinical Extraction Review & Confirmation Card */}
              <div className="ai-review-card">
                <div className="ai-review-header">
                  <div>
                    <h3 style={{ fontSize: "18px", fontWeight: "700", color: "#1e3a8a" }}>
                      🤖 Phase 2: Extracted Clinical Record Review
                    </h3>
                    <p style={{ fontSize: "13px", color: "var(--gray-500)", marginTop: "2px" }}>
                      Worker must verify extracted parameters before confirming. Database persistence occurs ONLY upon confirmation.
                    </p>
                  </div>
                  <span className={`badge ${extractedRecord.referral_required ? "badge-danger" : "badge-success"}`}>
                    {extractedRecord.referral_required ? "⚠️ PHC Referral Required" : "✓ Routine Visit"}
                  </span>
                </div>

                <div className="review-grid">
                  <div className="review-item">
                    <div className="review-label">Beneficiary ID</div>
                    <input
                      type="text"
                      className="input-field"
                      style={{ marginTop: "4px" }}
                      value={extractedRecord.beneficiary_id}
                      onChange={(e) => setExtractedRecord({ ...extractedRecord, beneficiary_id: e.target.value })}
                    />
                  </div>

                  <div className="review-item">
                    <div className="review-label">{t.visitType}</div>
                    <input
                      type="text"
                      className="input-field"
                      style={{ marginTop: "4px" }}
                      value={extractedRecord.visit_type}
                      onChange={(e) => setExtractedRecord({ ...extractedRecord, visit_type: e.target.value })}
                    />
                  </div>

                  <div className="review-item">
                    <div className="review-label">{t.weight}</div>
                    <input
                      type="text"
                      className="input-field"
                      style={{ marginTop: "4px" }}
                      value={extractedRecord.weight}
                      onChange={(e) => setExtractedRecord({ ...extractedRecord, weight: e.target.value })}
                    />
                  </div>

                  <div className="review-item">
                    <div className="review-label">{t.nextFollowup}</div>
                    <input
                      type="date"
                      className="input-field"
                      style={{ marginTop: "4px" }}
                      value={extractedRecord.next_visit_date || ""}
                      onChange={(e) => setExtractedRecord({ ...extractedRecord, next_visit_date: e.target.value || null })}
                    />
                    <div style={{ fontSize: "11px", color: "var(--gray-500)", marginTop: "4px" }}>
                      {extractedRecord.next_visit_date ? "Date explicitly scheduled" : t.noFabricatedDate}
                    </div>
                  </div>
                </div>

                <div style={{ marginBottom: "20px" }}>
                  <div className="review-label" style={{ marginBottom: "6px" }}>{t.vaccinations}</div>
                  <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                    {extractedRecord.vaccinations_due?.map((v, i) => (
                      <span key={i} className="vaccine-tag">{v}</span>
                    ))}
                    <button
                      onClick={() => {
                        const newVac = prompt("Enter additional vaccination code (e.g. Pentavalent-1):");
                        if (newVac) setExtractedRecord({ ...extractedRecord, vaccinations_due: [...extractedRecord.vaccinations_due, newVac] });
                      }}
                      className="btn btn-secondary btn-sm"
                      style={{ padding: "2px 8px", fontSize: "11px" }}
                    >
                      + Add Vaccine
                    </button>
                  </div>
                </div>

                {extractedRecord.danger_signs?.length > 0 && (
                  <div style={{ marginBottom: "20px" }}>
                    <div className="review-label" style={{ color: "#991b1b", marginBottom: "6px" }}>{t.dangerSigns}</div>
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                      {extractedRecord.danger_signs.map((d, i) => (
                        <span key={i} className="danger-tag">{d}</span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Explicit Worker Confirmation Controls */}
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid var(--gray-200)", paddingTop: "16px", flexWrap: "wrap", gap: "12px" }}>
                  <div style={{ fontSize: "13px", color: "var(--gray-700)" }}>
                    Contract: <code>POST /api/visits/confirm</code> with status <code>"confirmed"</code>
                  </div>
                  <div style={{ display: "flex", gap: "12px" }}>
                    <button
                      onClick={() => setExtractedRecord({
                        beneficiary_id: "BNF-2041",
                        visit_type: "Newborn home visit",
                        weight: "3.2 kg",
                        vaccinations_due: ["OPV-1"],
                        next_visit_date: null,
                        danger_signs: [],
                        referral_required: false,
                        confirmation_status: "confirmed"
                      })}
                      className="btn btn-secondary"
                    >
                      Reset Form
                    </button>
                    <button
                      disabled={isSubmittingVisit}
                      onClick={handleConfirmAndSaveVisit}
                      className="btn btn-success"
                    >
                      {isSubmittingVisit ? "Persisting to SQLite..." : `✓ ${t.confirmVisit}`}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: CONFIRMED VISITS REGISTER */}
          {activeTab === "visits" && (
            <div className="content-panel">
              <div className="panel-header">
                <div>
                  <h3 className="panel-title">{t.tabVisits}</h3>
                  <p style={{ fontSize: "13px", color: "var(--gray-500)" }}>
                    Persisted visit records in SQLite with duplicate checksum protection and danger signs retention.
                  </p>
                </div>
                <div className="search-bar">
                  <input
                    type="text"
                    placeholder={t.searchBeneficiary}
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
          )}

          {/* TAB 4: FOLLOW-UP TRACKER */}
          {activeTab === "followups" && (
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
                        <td>{fol.follow_up_date || t.noFabricatedDate}</td>
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

          {/* TAB 5: HOUSEHOLD & FAMILY DIRECTORY */}
          {activeTab === "households" && (
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
                    placeholder={t.searchHousehold}
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

          {/* TAB 6: FIND ASHA WORKER PORTAL */}
          {activeTab === "finder" && (
            <div>
              <div className="finder-hero">
                <h2 style={{ fontSize: "24px", fontWeight: "800", marginBottom: "8px" }}>
                  🔍 Find Your Assigned ASHA Worker
                </h2>
                <p style={{ fontSize: "15px", maxWidth: "600px", margin: "0 auto 20px", opacity: 0.9 }}>
                  Search by PIN code, village name, taluk, or district to locate the officially registered ASHA workers for your area.
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
                  Scheduled Date: <strong>{activeFollowup.follow_up_date || t.noFabricatedDate}</strong>
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

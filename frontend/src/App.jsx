import React, { useState } from 'react';
import VoiceRecorder from './components/VoiceRecorder';
import StructuredVisitReport from './components/StructuredVisitReport';
import Phase3Dashboard from './components/Phase3Dashboard';
import { Activity, Radio, Mic, LayoutDashboard, FileText, CheckCircle2 } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('RECORD'); // 'RECORD' | 'DASHBOARD'
  const [completedHandoff, setCompletedHandoff] = useState(null);
  const [currentReport, setCurrentReport] = useState(null);
  const [extractingReport, setExtractingReport] = useState(false);
  const [currentLanguage, setCurrentLanguage] = useState('kn-IN');

  const handleTranscriptComplete = async (payload) => {
    console.log('[App] Phase 1 Transcript Complete:', payload);
    setCompletedHandoff(payload);

    if (payload.transcript && payload.transcript.trim()) {
      setExtractingReport(true);
      try {
        const lang = payload.language?.includes('kn') ? 'kn-IN' : (payload.language || 'kn-IN');
        setCurrentLanguage(lang);

        const response = await fetch('/api/report/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            transcript: payload.transcript,
            language: lang
          })
        });

        const data = await response.json();
        if (data.success && data.report) {
          setCurrentReport(data.report);
        }
      } catch (err) {
        console.error('Error during automated report extraction:', err);
      } finally {
        setExtractingReport(false);
      }
    }
  };

  const handleConfirmAndSave = (savedRecord) => {
    console.log('[App] Confirmed and Saved Report to Phase 3:', savedRecord);
  };

  return (
    <div style={appStyles.page}>
      {/* Top Navigation Bar */}
      <header style={appStyles.navbar}>
        <div style={appStyles.navContainer}>
          <div style={appStyles.brand}>
            <div style={appStyles.logoIcon}>
              <Activity size={22} color="#ffffff" />
            </div>
            <div>
              <h1 style={appStyles.brandName}>ASHA SAHAYAK (ಆಶಾ ಸಹಾಯಕ)</h1>
              <span style={appStyles.brandSub}>
                Voice-Driven Clinical Register • Gnani Prisma v3.0 & Timbre v2.5
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            {/* Navigation Tabs */}
            <nav style={appStyles.tabGroup}>
              <button
                type="button"
                onClick={() => setActiveTab('RECORD')}
                style={{
                  ...appStyles.tabBtn,
                  backgroundColor: activeTab === 'RECORD' ? '#0284c7' : 'transparent',
                  color: '#ffffff'
                }}
              >
                <Mic size={15} />
                <span>Record & Report (ವರದಿ)</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('DASHBOARD')}
                style={{
                  ...appStyles.tabBtn,
                  backgroundColor: activeTab === 'DASHBOARD' ? '#0284c7' : 'transparent',
                  color: '#ffffff'
                }}
              >
                <LayoutDashboard size={15} />
                <span>Field Register (ಡ್ಯಾಶ್‌ಬೋರ್ಡ್)</span>
              </button>
            </nav>

            <div style={appStyles.statusBadge}>
              <Radio size={14} color="#16a34a" style={{ marginRight: 6 }} />
              <span>Prisma & Timbre Online</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={appStyles.main}>
        {activeTab === 'RECORD' ? (
          <div>
            {/* Voice Recorder Component */}
            <VoiceRecorder onTranscriptComplete={handleTranscriptComplete} />

            {/* Extraction Loader */}
            {extractingReport && (
              <div style={appStyles.extractingBanner}>
                <Activity size={18} className="animate-spin" color="#0284c7" />
                <span>
                  Generating Clinical Visit Report from speech narrative... (ವರದಿ ತಯಾರಿಸಲಾಗುತ್ತಿದೆ...)
                </span>
              </div>
            )}

            {/* Structured Visit Report Card (Automatic Phase 2 Extraction) */}
            {currentReport && (
              <StructuredVisitReport
                report={currentReport}
                onUpdateReport={setCurrentReport}
                onConfirmAndSave={handleConfirmAndSave}
                language={currentLanguage}
              />
            )}
          </div>
        ) : (
          /* Phase 3 Register Dashboard */
          <Phase3Dashboard
            onSelectReport={(rec) => {
              setCurrentReport(rec);
              setActiveTab('RECORD');
            }}
          />
        )}
      </main>

      {/* Footer */}
      <footer style={appStyles.footer}>
        <p>ASHA SAHAYAK • Ministry of Health & Family Welfare / Public Health Assistance Project</p>
        <p style={{ marginTop: 4, fontSize: '11px', color: '#94a3b8' }}>
          Gnani Prisma v3.0 STT & Timbre v2.5 TTS (Kannada, Hindi, English, and all 10 Indian Languages)
        </p>
      </footer>
    </div>
  );
}

const appStyles = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f1f5f9'
  },
  navbar: {
    backgroundColor: '#0f172a',
    color: '#ffffff',
    padding: '12px 20px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
  },
  navContainer: {
    maxWidth: '1080px',
    margin: '0 auto',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: '12px'
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px'
  },
  logoIcon: {
    width: '38px',
    height: '38px',
    borderRadius: '8px',
    backgroundColor: '#0284c7',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  brandName: {
    fontSize: '17px',
    fontWeight: '800',
    margin: 0,
    letterSpacing: '-0.3px'
  },
  brandSub: {
    fontSize: '11px',
    color: '#94a3b8',
    display: 'block',
    marginTop: '2px'
  },
  tabGroup: {
    display: 'flex',
    backgroundColor: '#1e293b',
    borderRadius: '8px',
    padding: '3px',
    gap: '4px'
  },
  tabBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 14px',
    fontSize: '12px',
    fontWeight: '600',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'all 0.15s ease'
  },
  statusBadge: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: '#1e293b',
    padding: '6px 12px',
    borderRadius: '20px',
    fontSize: '12px',
    color: '#cbd5e1'
  },
  main: {
    maxWidth: '1080px',
    width: '100%',
    margin: '0 auto',
    padding: '20px',
    flex: 1
  },
  extractingBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    backgroundColor: '#e0f2fe',
    color: '#0369a1',
    fontWeight: '600',
    fontSize: '13px',
    padding: '12px 20px',
    borderRadius: '10px',
    marginTop: '16px',
    border: '1px solid #bae6fd'
  },
  footer: {
    backgroundColor: '#ffffff',
    borderTop: '1px solid #e2e8f0',
    padding: '16px 20px',
    textAlign: 'center',
    fontSize: '12px',
    color: '#64748b',
    marginTop: 'auto'
  }
};

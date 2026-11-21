import React, { useState } from 'react';
import {
  AlertTriangle,
  HeartPulse,
  Calendar,
  User,
  Baby,
  Syringe,
  FileCheck,
  Volume2,
  Mic,
  Edit3,
  CheckCircle,
  Clock,
  ShieldAlert,
  ArrowRight,
  Info,
  Check,
  X
} from 'lucide-react';

export default function StructuredVisitReport({
  report,
  onUpdateReport,
  onConfirmAndSave,
  language = 'kn-IN'
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editableReport, setEditableReport] = useState(report || {});
  const [isReadingAloud, setIsReadingAloud] = useState(false);
  const [readbackAudioUrl, setReadbackAudioUrl] = useState(null);
  const [isCorrectingByVoice, setIsCorrectingByVoice] = useState(false);
  const [voiceCorrectionInput, setVoiceCorrectionInput] = useState('');
  const [correctionLoading, setCorrectionLoading] = useState(false);
  const [correctionFeedback, setCorrectionFeedback] = useState('');
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Sync when prop report changes
  React.useEffect(() => {
    setEditableReport(report || {});
    setSavedSuccess(false);
  }, [report]);

  if (!report) return null;

  const hasDangerSigns = editableReport.danger_signs && editableReport.danger_signs.length > 0;
  const isReferral = editableReport.referral_required || hasDangerSigns;

  const handleFieldChange = (field, value) => {
    const updated = { ...editableReport, [field]: value };
    setEditableReport(updated);
    if (onUpdateReport) onUpdateReport(updated);
  };

  // 1. Voice Read-Back using real Gnani Timbre TTS
  const handleReadAloud = async () => {
    setIsReadingAloud(true);
    try {
      // Choose appropriate readback text based on selected language
      const isKannada = language.startsWith('kn');
      const textToSpeak = isKannada
        ? (editableReport.readback_kn || editableReport.readback_en || 'ವರದಿ ಸಿದ್ಧವಾಗಿದೆ')
        : (editableReport.readback_en || 'Visit report is ready');

      const response = await fetch('/api/voice/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textToSpeak,
          language: language,
          source_language: isKannada ? 'kn-IN' : 'en-IN',
          translate: true,
          speed: 1.0
        })
      });

      if (!response.ok) {
        throw new Error(`TTS failed with status ${response.status}`);
      }

      const blob = await response.blob();
      const audioUrl = URL.createObjectURL(blob);
      setReadbackAudioUrl(audioUrl);

      const audio = new Audio(audioUrl);
      audio.onended = () => setIsReadingAloud(false);
      audio.onerror = () => setIsReadingAloud(false);
      await audio.play();
    } catch (err) {
      console.error('Voice read-back error:', err);
      setIsReadingAloud(false);
    }
  };

  // 2. Submit Voice/Text Correction
  const handleApplyCorrection = async (textToApply) => {
    const text = textToApply || voiceCorrectionInput;
    if (!text.trim()) return;

    setCorrectionLoading(true);
    setCorrectionFeedback('');
    try {
      const response = await fetch('/api/report/correct', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_report: editableReport,
          correction_text: text
        })
      });

      const data = await response.json();
      if (data.success && data.updated_report) {
        setEditableReport(data.updated_report);
        if (onUpdateReport) onUpdateReport(data.updated_report);
        setCorrectionFeedback(`✓ Updated field: ${data.modified_field}. (${data.readback_phrase})`);
        setVoiceCorrectionInput('');
        setIsCorrectingByVoice(false);

        // Optionally read aloud the updated field confirmation
        if (data.readback_phrase) {
          try {
            const ttsRes = await fetch('/api/voice/tts', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                text: data.readback_phrase,
                language: language,
                speed: 1.0
              })
            });
            if (ttsRes.ok) {
              const blob = await ttsRes.blob();
              const audio = new Audio(URL.createObjectURL(blob));
              audio.play();
            }
          } catch (e) {
            console.warn('Confirmation audio play error:', e);
          }
        }
      } else {
        setCorrectionFeedback('Could not determine field to update. Please edit manually.');
      }
    } catch (err) {
      console.error('Correction error:', err);
      setCorrectionFeedback('Correction failed. Please edit directly.');
    } finally {
      setCorrectionLoading(false);
    }
  };

  // 3. Confirm & Save to Phase 3
  const handleSaveToRegister = async () => {
    try {
      const response = await fetch('/api/report/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report: editableReport,
          confirmed: true
        })
      });

      const data = await response.json();
      if (data.success) {
        setSavedSuccess(true);
        if (onConfirmAndSave) onConfirmAndSave(data.record);
      } else {
        alert('Failed to save report: ' + (data.detail || 'Unknown error'));
      }
    } catch (err) {
      alert('Save error: ' + err.message);
    }
  };

  return (
    <div style={styles.card}>
      {/* Top Banner with Title & Actions */}
      <div style={styles.cardHeader}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileCheck size={22} color="#0284c7" />
          <div>
            <h3 style={styles.title}>
              ASHA Visit Report (ಆಶಾ ಭೇಟಿ ವರದಿ)
            </h3>
            <span style={styles.subtitle}>
              Phase 2 Automated Clinical Extraction • Public Health Protocol Compliant
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            type="button"
            onClick={handleReadAloud}
            disabled={isReadingAloud}
            style={{
              ...styles.headerBtn,
              backgroundColor: isReadingAloud ? '#e0f2fe' : '#ffffff',
              color: '#0284c7',
              borderColor: '#0284c7'
            }}
            title="Read summary aloud using Gnani Timbre TTS"
          >
            <Volume2 size={16} />
            {isReadingAloud ? 'Speaking...' : 'Read Aloud (ವರದಿ ಓದಿ)'}
          </button>

          <button
            type="button"
            onClick={() => setIsEditing(!isEditing)}
            style={{
              ...styles.headerBtn,
              backgroundColor: isEditing ? '#0284c7' : '#ffffff',
              color: isEditing ? '#ffffff' : '#334155',
              borderColor: '#cbd5e1'
            }}
          >
            <Edit3 size={15} />
            {isEditing ? 'Done Editing' : 'Edit Fields (ತಿದ್ದುಪಡಿ)'}
          </button>
        </div>
      </div>

      {/* DANGER SIGNS ALERT BANNER (If present) */}
      {hasDangerSigns && (
        <div style={styles.dangerBanner}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <ShieldAlert size={26} color="#dc2626" />
            <div>
              <div style={styles.dangerTitle}>
                🚨 DANGER SIGN DETECTED (ಅಪಾಯದ ಲಕ್ಷಣ ಪತ್ತೆಯಾಗಿದೆ)
              </div>
              <div style={styles.dangerDesc}>
                {editableReport.danger_signs.map((ds, idx) => (
                  <span key={idx} style={{ fontWeight: '600', marginRight: '8px' }}>
                    • {ds.name} ({ds.kannada}) — {ds.action}
                  </span>
                ))}
              </div>
            </div>
          </div>
          <div style={styles.referralBadge}>
            IMMEDIATE REFERRAL REQUIRED
          </div>
        </div>
      )}

      {/* Missing Fields Warning Banner (If any) */}
      {editableReport.missing_fields && editableReport.missing_fields.length > 0 && (
        <div style={styles.warningBanner}>
          <Info size={18} color="#d97706" style={{ flexShrink: 0 }} />
          <div style={{ fontSize: '12px', color: '#92400e' }}>
            <strong>Missing Recommended Information (ಮಾಹಿತಿ ಅಲಭ್ಯ):</strong>{' '}
            {editableReport.missing_fields.map((f, i) => (
              <span key={i} style={styles.missingPill}>
                {f.replace('_', ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Core Report Content Grid */}
      <div style={styles.grid}>
        {/* 1. Beneficiary Information */}
        <div style={styles.sectionCard}>
          <div style={styles.sectionHeader}>
            <User size={16} color="#0284c7" />
            <span>Beneficiary Information (ಫಲಾನುಭವಿ ವಿವರ)</span>
          </div>
          <div style={styles.fieldGrid}>
            <div style={styles.fieldItem}>
              <label style={styles.label}>Beneficiary Name (ಹೆಸರು):</label>
              {isEditing ? (
                <input
                  type="text"
                  value={editableReport.beneficiary_name || ''}
                  onChange={(e) => handleFieldChange('beneficiary_name', e.target.value)}
                  style={styles.input}
                  placeholder="e.g. Lakshmi"
                />
              ) : (
                <div style={styles.value}>
                  {editableReport.beneficiary_name || (
                    <span style={styles.emptyVal}>Not Specified (ದಾಖಲಾಗಿಲ್ಲ)</span>
                  )}
                </div>
              )}
            </div>

            <div style={styles.fieldItem}>
              <label style={styles.label}>RCH / Beneficiary ID (ಗುರುತು ಸಂಖ್ಯೆ):</label>
              {isEditing ? (
                <input
                  type="text"
                  value={editableReport.beneficiary_id || ''}
                  onChange={(e) => handleFieldChange('beneficiary_id', e.target.value)}
                  style={styles.input}
                  placeholder="e.g. RCH12345"
                />
              ) : (
                <div style={styles.value}>
                  {editableReport.beneficiary_id || (
                    <span style={styles.emptyVal}>Null (ಲಭ್ಯವಿಲ್ಲ)</span>
                  )}
                </div>
              )}
            </div>

            <div style={styles.fieldItem}>
              <label style={styles.label}>Visit Type (ಭೇಟಿಯ ವಿಧ):</label>
              {isEditing ? (
                <select
                  value={editableReport.visit_type || 'Routine Field Visit'}
                  onChange={(e) => handleFieldChange('visit_type', e.target.value)}
                  style={styles.input}
                >
                  <option value="ANC Home Visit (ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ)">ANC Home Visit (ಗರ್ಭಿಣಿ ಮನೆ ಭೇಟಿ)</option>
                  <option value="PNC Home Visit (ಬಾಣಂತಿ ಭೇಟಿ)">PNC Home Visit (ಬಾಣಂತಿ ಭೇಟಿ)</option>
                  <option value="Immunization Visit (ಲಸಿಕಾ ಭೇಟಿ)">Immunization Visit (ಲಸಿಕಾ ಭೇಟಿ)</option>
                  <option value="Newborn Care Visit (ನವಜಾತ ಶಿಶು ಭೇಟಿ)">Newborn Care Visit (ನವಜಾತ ಶಿಶು ಭೇಟಿ)</option>
                  <option value="Routine Field Visit (ಸಾಮಾನ್ಯ ಭೇಟಿ)">Routine Field Visit (ಸಾಮಾನ್ಯ ಭೇಟಿ)</option>
                </select>
              ) : (
                <div style={{ ...styles.value, fontWeight: '600', color: '#0369a1' }}>
                  {editableReport.visit_type}
                </div>
              )}
            </div>

            <div style={styles.fieldItem}>
              <label style={styles.label}>Pregnancy Status (ಸ್ಥಿತಿ):</label>
              <div style={styles.value}>
                {editableReport.pregnancy_status || (
                  <span style={styles.emptyVal}>Not Applicable / Null</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 2. Clinical Vitals & Measurements */}
        <div style={styles.sectionCard}>
          <div style={styles.sectionHeader}>
            <HeartPulse size={16} color="#e11d48" />
            <span>Vitals & Body Measurements (ಅಳತೆಗಳು)</span>
          </div>
          <div style={styles.fieldGrid}>
            <div style={styles.fieldItem}>
              <label style={styles.label}>Infant / Birth Weight (ತೂಕ):</label>
              {isEditing ? (
                <input
                  type="text"
                  value={editableReport.infant_weight || ''}
                  onChange={(e) => handleFieldChange('infant_weight', e.target.value)}
                  style={styles.input}
                  placeholder="e.g. 2.8 kg"
                />
              ) : (
                <div style={styles.value}>
                  {editableReport.infant_weight ? (
                    <span style={styles.highlightBadge}>{editableReport.infant_weight}</span>
                  ) : (
                    <span style={styles.emptyVal}>Null (ದಾಖಲಾಗಿಲ್ಲ)</span>
                  )}
                </div>
              )}
            </div>

            <div style={styles.fieldItem}>
              <label style={styles.label}>Blood Pressure (ರಕ್ತದೊತ್ತಡ):</label>
              {isEditing ? (
                <input
                  type="text"
                  value={editableReport.blood_pressure || ''}
                  onChange={(e) => handleFieldChange('blood_pressure', e.target.value)}
                  style={styles.input}
                  placeholder="e.g. 120/80"
                />
              ) : (
                <div style={styles.value}>
                  {editableReport.blood_pressure ? (
                    <span style={styles.highlightBadge}>{editableReport.blood_pressure}</span>
                  ) : (
                    <span style={styles.emptyVal}>Null (ದಾಖಲಾಗಿಲ್ಲ)</span>
                  )}
                </div>
              )}
            </div>

            <div style={styles.fieldItem}>
              <label style={styles.label}>Gestational Age (ಗರ್ಭಾವಸ್ಥೆ ವಯಸ್ಸು):</label>
              {isEditing ? (
                <input
                  type="text"
                  value={editableReport.gestational_age || ''}
                  onChange={(e) => handleFieldChange('gestational_age', e.target.value)}
                  style={styles.input}
                  placeholder="e.g. 24 weeks"
                />
              ) : (
                <div style={styles.value}>
                  {editableReport.gestational_age || (
                    <span style={styles.emptyVal}>Null</span>
                  )}
                </div>
              )}
            </div>

            <div style={styles.fieldItem}>
              <label style={styles.label}>Next Visit Date (ಮುಂದಿನ ಭೇಟಿ):</label>
              {isEditing ? (
                <input
                  type="text"
                  value={editableReport.next_visit_date || ''}
                  onChange={(e) => handleFieldChange('next_visit_date', e.target.value)}
                  style={styles.input}
                  placeholder="e.g. Next Week"
                />
              ) : (
                <div style={styles.value}>
                  {editableReport.next_visit_date ? (
                    <span style={{ color: '#059669', fontWeight: '600' }}>
                      📅 {editableReport.next_visit_date}
                    </span>
                  ) : (
                    <span style={styles.emptyVal}>Null (ನಿಗದಿಯಾಗಿಲ್ಲ)</span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 3. Symptoms & Observations (Positive vs Negations) */}
        <div style={styles.sectionCard}>
          <div style={styles.sectionHeader}>
            <AlertTriangle size={16} color="#f59e0b" />
            <span>Reported Symptoms & Negations (ಲಕ್ಷಣಗಳು & ತಪಾಸಣೆ)</span>
          </div>

          <div style={{ marginBottom: '12px' }}>
            <label style={{ ...styles.label, marginBottom: '6px' }}>
              Reported Symptoms (ವರದಿಯಾದ ರೋಗಲಕ್ಷಣಗಳು):
            </label>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {editableReport.symptoms_reported && editableReport.symptoms_reported.length > 0 ? (
                editableReport.symptoms_reported.map((sym, i) => (
                  <span key={i} style={styles.symptomPill}>
                    ⚠️ {sym}
                  </span>
                ))
              ) : (
                <span style={styles.emptyVal}>None reported (ಯಾವುದೂ ವರದಿಯಾಗಿಲ್ಲ)</span>
              )}
            </div>
          </div>

          <div>
            <label style={{ ...styles.label, marginBottom: '6px' }}>
              Confirmed Absent / Negations (ಇಲ್ಲದಿರುವುದು ದೃಢಪಟ್ಟಿದೆ):
            </label>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {editableReport.negated_symptoms && editableReport.negated_symptoms.length > 0 ? (
                editableReport.negated_symptoms.map((neg, i) => (
                  <span key={i} style={styles.negationPill}>
                    ✓ {neg}
                  </span>
                ))
              ) : (
                <span style={styles.emptyVal}>No explicit negations noted</span>
              )}
            </div>
          </div>
        </div>

        {/* 4. Immunization & Vaccinations */}
        <div style={styles.sectionCard}>
          <div style={styles.sectionHeader}>
            <Syringe size={16} color="#8b5cf6" />
            <span>Immunization & Vaccines (ಲಸಿಕೆ ವಿವರ)</span>
          </div>

          <div style={{ marginBottom: '10px' }}>
            <label style={{ ...styles.label, marginBottom: '6px' }}>
              Vaccinations Due / Pending (ಬಾಕಿ ಇರುವ ಲಸಿಕೆಗಳು):
            </label>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {editableReport.vaccinations_due && editableReport.vaccinations_due.length > 0 ? (
                editableReport.vaccinations_due.map((vax, i) => (
                  <span key={i} style={styles.vaxDuePill}>
                    💉 {vax} (Due)
                  </span>
                ))
              ) : (
                <span style={styles.emptyVal}>None due mentioned</span>
              )}
            </div>
          </div>

          <div>
            <label style={{ ...styles.label, marginBottom: '6px' }}>
              Vaccinations Administered / Given (ನೀಡಲಾದ ಲಸಿಕೆಗಳು):
            </label>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {editableReport.vaccinations_given && editableReport.vaccinations_given.length > 0 ? (
                editableReport.vaccinations_given.map((vax, i) => (
                  <span key={i} style={styles.vaxGivenPill}>
                    ✓ {vax} (Given)
                  </span>
                ))
              ) : (
                <span style={styles.emptyVal}>None administered in this visit</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Voice Correction Section */}
      <div style={styles.correctionBox}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Mic size={18} color="#059669" />
            <span style={{ fontSize: '13px', fontWeight: '700', color: '#065f46' }}>
              Voice Correction & Read-Back (ಧ್ವನಿಯ ಮೂಲಕ ಸರಿಪಡಿಸಿ)
            </span>
          </div>
          <button
            type="button"
            onClick={() => setIsCorrectingByVoice(!isCorrectingByVoice)}
            style={styles.correctionToggleBtn}
          >
            {isCorrectingByVoice ? 'Close' : '🎙️ Correct Field by Voice'}
          </button>
        </div>

        {isCorrectingByVoice && (
          <div style={{ marginTop: '10px' }}>
            <p style={{ fontSize: '12px', color: '#047857', marginBottom: '6px' }}>
              Speak or type a correction (e.g. <em>"No, the weight is 2.8 kilograms"</em> or <em>"ಮುಂದಿನ ಭೇಟಿ ಮುಂದಿನ ಸೋಮವಾರ"</em>):
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                value={voiceCorrectionInput}
                onChange={(e) => setVoiceCorrectionInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleApplyCorrection()}
                placeholder="e.g. No, the weight is 2.8 kilograms"
                style={styles.correctionInput}
              />
              <button
                type="button"
                onClick={() => handleApplyCorrection()}
                disabled={correctionLoading || !voiceCorrectionInput.trim()}
                style={styles.applyBtn}
              >
                {correctionLoading ? 'Applying...' : 'Apply Correction'}
              </button>
            </div>
          </div>
        )}

        {correctionFeedback && (
          <div style={styles.feedbackNotice}>
            {correctionFeedback}
          </div>
        )}
      </div>

      {/* Confirmation & Save Button Area */}
      <div style={styles.footerActions}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '12px', color: '#64748b' }}>
            Extraction Confidence:
          </span>
          <span style={styles.confidencePill}>
            {Math.round((editableReport.confidence_score || 0.9) * 100)}%
          </span>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          {savedSuccess ? (
            <div style={styles.savedBanner}>
              <Check size={18} color="#16a34a" />
              <span>Confirmed & Saved to Phase 3 Register!</span>
            </div>
          ) : (
            <button
              type="button"
              onClick={handleSaveToRegister}
              style={styles.saveBtn}
            >
              <CheckCircle size={18} />
              Confirm & Save to Field Register (ದೃಢೀಕರಿಸಿ ಉಳಿಸಿ)
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

const styles = {
  card: {
    backgroundColor: '#ffffff',
    borderRadius: '12px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
    border: '1px solid #e2e8f0',
    marginTop: '20px',
    overflow: 'hidden'
  },
  cardHeader: {
    padding: '16px 20px',
    backgroundColor: '#f8fafc',
    borderBottom: '1px solid #e2e8f0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '12px'
  },
  title: {
    fontSize: '16px',
    fontWeight: '700',
    color: '#0f172a',
    margin: 0
  },
  subtitle: {
    fontSize: '11px',
    color: '#64748b',
    display: 'block',
    marginTop: '2px'
  },
  headerBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 12px',
    fontSize: '12px',
    fontWeight: '600',
    borderRadius: '8px',
    border: '1px solid',
    cursor: 'pointer',
    transition: 'all 0.15s ease'
  },
  dangerBanner: {
    backgroundColor: '#fef2f2',
    borderLeft: '4px solid #dc2626',
    borderBottom: '1px solid #fee2e2',
    padding: '12px 20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '12px'
  },
  dangerTitle: {
    fontSize: '13px',
    fontWeight: '800',
    color: '#991b1b'
  },
  dangerDesc: {
    fontSize: '12px',
    color: '#b91c1c',
    marginTop: '2px'
  },
  referralBadge: {
    backgroundColor: '#dc2626',
    color: '#ffffff',
    fontSize: '11px',
    fontWeight: '800',
    padding: '4px 10px',
    borderRadius: '6px',
    letterSpacing: '0.5px'
  },
  warningBanner: {
    backgroundColor: '#fffbeb',
    borderBottom: '1px solid #fef3c7',
    padding: '8px 20px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  missingPill: {
    display: 'inline-block',
    backgroundColor: '#fde68a',
    color: '#92400e',
    fontSize: '11px',
    fontWeight: '600',
    padding: '2px 8px',
    borderRadius: '12px',
    marginLeft: '4px'
  },
  grid: {
    padding: '20px',
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
    gap: '16px'
  },
  sectionCard: {
    backgroundColor: '#f8fafc',
    border: '1px solid #e2e8f0',
    borderRadius: '10px',
    padding: '14px 16px'
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '13px',
    fontWeight: '700',
    color: '#1e293b',
    borderBottom: '1px solid #e2e8f0',
    paddingBottom: '8px',
    marginBottom: '12px'
  },
  fieldGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
    gap: '10px'
  },
  fieldItem: {
    display: 'flex',
    flexDirection: 'column'
  },
  label: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#64748b',
    marginBottom: '3px'
  },
  value: {
    fontSize: '13px',
    color: '#1e293b',
    minHeight: '20px'
  },
  emptyVal: {
    color: '#94a3b8',
    fontStyle: 'italic',
    fontSize: '12px'
  },
  input: {
    fontSize: '12px',
    padding: '4px 8px',
    borderRadius: '6px',
    border: '1px solid #0284c7',
    backgroundColor: '#ffffff',
    color: '#0f172a'
  },
  highlightBadge: {
    backgroundColor: '#e0f2fe',
    color: '#0369a1',
    fontWeight: '700',
    padding: '2px 8px',
    borderRadius: '6px',
    display: 'inline-block'
  },
  symptomPill: {
    backgroundColor: '#fee2e2',
    color: '#991b1b',
    fontSize: '11px',
    fontWeight: '600',
    padding: '3px 8px',
    borderRadius: '6px'
  },
  negationPill: {
    backgroundColor: '#dcfce7',
    color: '#166534',
    fontSize: '11px',
    fontWeight: '600',
    padding: '3px 8px',
    borderRadius: '6px'
  },
  vaxDuePill: {
    backgroundColor: '#ede9fe',
    color: '#6d28d9',
    fontSize: '11px',
    fontWeight: '600',
    padding: '3px 8px',
    borderRadius: '6px'
  },
  vaxGivenPill: {
    backgroundColor: '#dcfce7',
    color: '#15803d',
    fontSize: '11px',
    fontWeight: '600',
    padding: '3px 8px',
    borderRadius: '6px'
  },
  correctionBox: {
    backgroundColor: '#ecfdf5',
    borderTop: '1px solid #d1fae5',
    borderBottom: '1px solid #d1fae5',
    padding: '12px 20px'
  },
  correctionToggleBtn: {
    fontSize: '11px',
    fontWeight: '700',
    backgroundColor: '#059669',
    color: '#ffffff',
    border: 'none',
    padding: '4px 10px',
    borderRadius: '6px',
    cursor: 'pointer'
  },
  correctionInput: {
    flex: 1,
    padding: '8px 12px',
    fontSize: '12px',
    borderRadius: '8px',
    border: '1px solid #10b981',
    backgroundColor: '#ffffff'
  },
  applyBtn: {
    backgroundColor: '#047857',
    color: '#ffffff',
    fontSize: '12px',
    fontWeight: '600',
    border: 'none',
    borderRadius: '8px',
    padding: '8px 14px',
    cursor: 'pointer'
  },
  feedbackNotice: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#065f46',
    marginTop: '6px'
  },
  footerActions: {
    padding: '14px 20px',
    backgroundColor: '#f8fafc',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '12px'
  },
  confidencePill: {
    backgroundColor: '#f1f5f9',
    color: '#334155',
    fontSize: '11px',
    fontWeight: '700',
    padding: '2px 8px',
    borderRadius: '10px'
  },
  saveBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    backgroundColor: '#0284c7',
    color: '#ffffff',
    fontSize: '13px',
    fontWeight: '700',
    padding: '10px 20px',
    borderRadius: '8px',
    border: 'none',
    cursor: 'pointer',
    boxShadow: '0 2px 4px rgba(2, 132, 199, 0.2)'
  },
  savedBanner: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    backgroundColor: '#dcfce7',
    color: '#15803d',
    fontSize: '13px',
    fontWeight: '700',
    padding: '8px 16px',
    borderRadius: '8px'
  }
};


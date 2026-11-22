import React, { useState } from 'react';
import { Home, User, CheckCircle, Volume2, AlertCircle, Plus, Trash2, ArrowRight } from 'lucide-react';

const API_BASE = window.location.origin.includes(':5173') ? 'http://localhost:8000' : '';

export default function VoiceHouseholdCard({
  householdData,
  onSaveHousehold,
  onSwitchToVisit,
  language = 'kn-IN'
}) {
  const isKn = language.includes('kn');
  const [data, setData] = useState({
    head_of_family: householdData?.head_of_family || 'Ramesh',
    contact_number: householdData?.contact_number || '98765-11001',
    village: householdData?.village || 'Rampur',
    pincode: householdData?.pincode || '571428',
    address: householdData?.address || 'House # 42, Rampur',
    house_type: householdData?.house_type || 'Pucca',
    water_source: householdData?.water_source || 'Piped Water / Tap',
    toilet_available: householdData?.toilet_available || 'Individual Household Latrine (IHHL)',
    sanitation_facility: householdData?.sanitation_facility || 'Closed Drainage',
    survey_status: 'completed',
    family_members: householdData?.family_members && householdData.family_members.length > 0
      ? householdData.family_members
      : [
          { full_name: householdData?.head_of_family || 'Ramesh', age: 42, gender: 'Male', relationship: 'Self / Head' },
          { full_name: 'Lakshmi', age: 36, gender: 'Female', relationship: 'Spouse' },
          { full_name: 'Kiran', age: 10, gender: 'Male', relationship: 'Son' },
          { full_name: 'Deepa', age: 3, gender: 'Female', relationship: 'Daughter', is_child_under_5: true }
        ]
  });

  const [isPlayingReadback, setIsPlayingReadback] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Play natural voice readback
  const handlePlayReadback = async () => {
    try {
      setIsPlayingReadback(true);
      const readbackText = isKn
        ? householdData?.readback_kn || `ಕುಟುಂಬದ ಮುಖ್ಯಸ್ಥ ${data.head_of_family}, ${data.village} ಗ್ರಾಮ, ${data.family_members.length} ಸದಸ್ಯರು. ವಿವರಗಳನ್ನು ಉಳಿಸುವುದೇ?`
        : householdData?.readback_en || `Family head is ${data.head_of_family}, ${data.village} village, ${data.family_members.length} members. Confirm and save?`;

      const res = await fetch(`${API_BASE}/api/voice/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: readbackText,
          language: isKn ? 'kn-IN' : 'en-IN',
          voice: isKn ? 'Devika' : 'Kaveri',
          speed: 1.0
        })
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.onended = () => setIsPlayingReadback(false);
        audio.onerror = () => setIsPlayingReadback(false);
        audio.play();
      } else {
        setIsPlayingReadback(false);
      }
    } catch (e) {
      setIsPlayingReadback(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSaveHousehold(data);
      setSaveSuccess(true);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div style={{ marginTop: '20px', backgroundColor: '#ffffff', borderRadius: '12px', border: '1px solid #ccfbf1', boxShadow: '0 4px 12px rgba(13, 148, 136, 0.08)', overflow: 'hidden' }}>
      {/* Header with Voice Detection Badge */}
      <div style={{ backgroundColor: '#0f766e', color: '#ffffff', padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Home size={22} color="#5eead4" />
          <div>
            <h4 style={{ margin: 0, fontSize: '15px', fontWeight: '700' }}>
              {isKn ? 'ಧ್ವನಿ ಮೂಲಕ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಭರ್ತಿ ಮಾಡಲಾದ ಕುಟುಂಬ ನೋಂದಣಿ' : 'Voice-Extracted Household Registration'}
            </h4>
            <span style={{ fontSize: '12px', color: '#ccfbf1' }}>
              {isKn ? 'ಧ್ವನಿ ಇನ್‌ಪುಟ್‌ನಿಂದ ಕುಟುಂಬದ ವಿವರಗಳನ್ನು ಹೊರತೆಗೆಯಲಾಗಿದೆ' : 'Understood from voice input. Please review and confirm to persist.'}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            onClick={handlePlayReadback}
            disabled={isPlayingReadback}
            className="btn btn-secondary btn-sm"
            style={{ backgroundColor: 'rgba(255,255,255,0.15)', color: '#ffffff', border: '1px solid rgba(255,255,255,0.3)', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Volume2 size={15} />
            <span>{isPlayingReadback ? (isKn ? 'ಆಲಿಸಲಾಗುತ್ತಿದೆ...' : 'Playing...') : isKn ? 'ಧ್ವನಿ ಪರಿಶೀಲನೆ' : 'Voice Readback'}</span>
          </button>
          {onSwitchToVisit && (
            <button
              type="button"
              onClick={onSwitchToVisit}
              className="btn btn-secondary btn-sm"
              style={{ backgroundColor: 'rgba(255,255,255,0.15)', color: '#ffffff', border: '1px solid rgba(255,255,255,0.3)', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <span>{isKn ? 'ಭೇಟಿ ವರದಿ' : 'Clinical Visit'}</span>
              <ArrowRight size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Clarification prompt if any */}
      {householdData?.clarification_prompt && (
        <div style={{ backgroundColor: '#fffbeb', borderBottom: '1px solid #fef3c7', padding: '8px 16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#b45309' }}>
          <AlertCircle size={15} color="#d97706" />
          <span>{householdData.clarification_prompt}</span>
        </div>
      )}

      {/* Form Fields */}
      <div style={{ padding: '18px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '12px', marginBottom: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '4px' }}>
              {isKn ? 'ಕುಟುಂಬದ ಮುಖ್ಯಸ್ಥ' : 'Head of Family'}
            </label>
            <input
              type="text"
              className="input-field"
              value={data.head_of_family}
              onChange={(e) => setData({ ...data, head_of_family: e.target.value })}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '4px' }}>
              {isKn ? 'ಗ್ರಾಮ' : 'Village'}
            </label>
            <input
              type="text"
              className="input-field"
              value={data.village}
              onChange={(e) => setData({ ...data, village: e.target.value })}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '4px' }}>
              {isKn ? 'ಪಿನ್ ಕೋಡ್' : 'PIN Code'}
            </label>
            <input
              type="text"
              className="input-field"
              value={data.pincode}
              onChange={(e) => setData({ ...data, pincode: e.target.value })}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '4px' }}>
              {isKn ? 'ಸಂಪರ್ಕ ಸಂಖ್ಯೆ' : 'Contact Number'}
            </label>
            <input
              type="text"
              className="input-field"
              value={data.contact_number}
              onChange={(e) => setData({ ...data, contact_number: e.target.value })}
            />
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '4px' }}>
            {isKn ? 'ವಿಳಾಸ' : 'Address'}
          </label>
          <input
            type="text"
            className="input-field"
            value={data.address}
            onChange={(e) => setData({ ...data, address: e.target.value })}
          />
        </div>

        {/* Housing & Sanitation Facility Pills */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '12px', marginBottom: '16px', backgroundColor: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: '#64748b', marginBottom: '2px' }}>House Structure</label>
            <select
              className="input-field"
              value={data.house_type}
              onChange={(e) => setData({ ...data, house_type: e.target.value })}
            >
              <option value="Pucca">Pucca (Concrete/Brick)</option>
              <option value="Semi-Pucca">Semi-Pucca (Tiled/Stone)</option>
              <option value="Kutcha">Kutcha (Mud/Thatch)</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: '#64748b', marginBottom: '2px' }}>Drinking Water</label>
            <select
              className="input-field"
              value={data.water_source}
              onChange={(e) => setData({ ...data, water_source: e.target.value })}
            >
              <option value="Piped Water / Tap">Piped Water / Tap</option>
              <option value="Borewell / Handpump">Borewell / Handpump</option>
              <option value="Well">Well</option>
              <option value="Filter Plant / RO">Filter Plant / RO</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: '#64748b', marginBottom: '2px' }}>Toilet Facility</label>
            <select
              className="input-field"
              value={data.toilet_available}
              onChange={(e) => setData({ ...data, toilet_available: e.target.value })}
            >
              <option value="Individual Household Latrine (IHHL)">Individual Latrine (IHHL)</option>
              <option value="Community Toilet">Community Toilet</option>
              <option value="None / Open">None / Open</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', fontWeight: '600', color: '#64748b', marginBottom: '2px' }}>Drainage Sanitation</label>
            <select
              className="input-field"
              value={data.sanitation_facility}
              onChange={(e) => setData({ ...data, sanitation_facility: e.target.value })}
            >
              <option value="Closed Drainage">Closed Drainage</option>
              <option value="Soak Pit">Soak Pit</option>
              <option value="Open Drain">Open Drain</option>
            </select>
          </div>
        </div>

        {/* Family Members list */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: '700', color: '#1e293b' }}>
              {isKn ? 'ಕುಟುಂಬದ ಸದಸ್ಯರು' : 'Family Members'} ({data.family_members.length})
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {data.family_members.map((m, idx) => (
              <div key={idx} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1.5fr', gap: '8px', padding: '6px 10px', backgroundColor: '#f1f5f9', borderRadius: '6px', fontSize: '12px', alignItems: 'center' }}>
                <span style={{ fontWeight: '600', color: '#1e293b' }}>{m.full_name || 'Member'}</span>
                <span>Age: {m.age}</span>
                <span>{m.gender}</span>
                <span style={{ color: '#0f766e', fontWeight: '600' }}>{m.relationship}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Action Button */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', borderTop: '1px solid #f1f5f9', paddingTop: '14px' }}>
          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving || saveSuccess}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 22px', fontSize: '14px', fontWeight: '600' }}
          >
            <CheckCircle size={18} />
            {saveSuccess
              ? isKn ? '✓ ನೋಂದಾಯಿಸಲಾಗಿದೆ' : '✓ Saved to Database'
              : isSaving
              ? isKn ? 'ಉಳಿಸಲಾಗುತ್ತಿದೆ...' : 'Saving...'
              : isKn ? 'ಕುಟುಂಬವನ್ನು ಡೇಟಾಬೇಸ್‌ಗೆ ಉಳಿಸಿ' : 'Confirm & Save Household to Database'}
          </button>
        </div>
      </div>
    </div>
  );
}


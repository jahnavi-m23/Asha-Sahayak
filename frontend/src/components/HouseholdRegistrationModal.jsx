import React, { useState, useEffect } from 'react';
import { Home, User, Phone, MapPin, Droplet, ShieldCheck, Plus, Trash2, Mic, AlertCircle, CheckCircle } from 'lucide-react';

const API_BASE = window.location.origin.includes(':5173') ? 'http://localhost:8000' : '';

export default function HouseholdRegistrationModal({
  isOpen,
  onClose,
  initialData,
  currentUser,
  onSuccess,
  lang = 'en'
}) {
  const isKn = lang === 'kn';

  const [formData, setFormData] = useState({
    head_of_family: '',
    contact_number: '98765-11001',
    village: currentUser?.assigned_village || 'Rampur',
    pincode: currentUser?.assigned_pincode || '571428',
    address: 'House # 42, Near Main Road, Rampur',
    house_type: 'Pucca',
    water_source: 'Piped Water / Tap',
    toilet_available: 'Individual Household Latrine (IHHL)',
    sanitation_facility: 'Closed Drainage',
    survey_status: 'completed',
    family_members: [
      {
        full_name: '',
        age: 40,
        gender: 'Male',
        relationship: 'Self / Head',
        is_pregnant: false,
        is_child_under_5: false,
        is_elderly: false
      }
    ]
  });

  const [voiceInputText, setVoiceInputText] = useState('');
  const [isExtractingVoice, setIsExtractingVoice] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (initialData) {
      setFormData({
        head_of_family: initialData.head_of_family || '',
        contact_number: initialData.contact_number || '98765-11001',
        village: initialData.village || currentUser?.assigned_village || 'Rampur',
        pincode: initialData.pincode || currentUser?.assigned_pincode || '571428',
        address: initialData.address || `House # 42, ${initialData.village || 'Rampur'}`,
        house_type: initialData.house_type || 'Pucca',
        water_source: initialData.water_source || 'Piped Water / Tap',
        toilet_available: initialData.toilet_available || 'Individual Household Latrine (IHHL)',
        sanitation_facility: initialData.sanitation_facility || 'Closed Drainage',
        survey_status: 'completed',
        family_members: initialData.family_members && initialData.family_members.length > 0
          ? initialData.family_members
          : [
              {
                full_name: initialData.head_of_family || 'Family Head',
                age: 40,
                gender: 'Male',
                relationship: 'Self / Head',
                is_pregnant: false,
                is_child_under_5: false,
                is_elderly: false
              }
            ]
      });
    }
  }, [initialData, currentUser]);

  if (!isOpen) return null;

  // Add Family Member row
  const handleAddMember = () => {
    setFormData((prev) => ({
      ...prev,
      family_members: [
        ...prev.family_members,
        {
          full_name: '',
          age: 25,
          gender: 'Female',
          relationship: prev.family_members.length === 1 ? 'Spouse' : 'Child',
          is_pregnant: false,
          is_child_under_5: false,
          is_elderly: false
        }
      ]
    }));
  };

  // Remove Family Member row
  const handleRemoveMember = (index) => {
    if (formData.family_members.length <= 1) return;
    setFormData((prev) => ({
      ...prev,
      family_members: prev.family_members.filter((_, i) => i !== index)
    }));
  };

  // Update Family Member field
  const handleMemberChange = (index, field, value) => {
    setFormData((prev) => {
      const updated = [...prev.family_members];
      updated[index] = { ...updated[index], [field]: value };
      return { ...prev, family_members: updated };
    });
  };

  // Voice fill trigger
  const handleVoiceFill = async () => {
    if (!voiceInputText.trim()) return;
    setIsExtractingVoice(true);
    setErrorMessage('');
    try {
      const res = await fetch(`${API_BASE}/api/households/voice-extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          transcript: voiceInputText.trim(),
          language: isKn ? 'kn-IN' : 'en-IN'
        })
      });
      const data = await res.json();
      if (res.ok && data.success && data.household) {
        const hh = data.household;
        setFormData({
          head_of_family: hh.head_of_family || formData.head_of_family,
          contact_number: hh.contact_number || formData.contact_number,
          village: hh.village || formData.village,
          pincode: hh.pincode || formData.pincode,
          address: hh.address || formData.address,
          house_type: hh.house_type || formData.house_type,
          water_source: hh.water_source || formData.water_source,
          toilet_available: hh.toilet_available || formData.toilet_available,
          sanitation_facility: hh.sanitation_facility || formData.sanitation_facility,
          survey_status: 'completed',
          family_members: hh.family_members || formData.family_members
        });
      } else {
        setErrorMessage(data.detail || 'Voice extraction failed.');
      }
    } catch (e) {
      setErrorMessage('Could not connect to voice extraction endpoint.');
    } finally {
      setIsExtractingVoice(false);
    }
  };

  // Submit Household Form
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.head_of_family.trim()) {
      setErrorMessage(isKn ? 'ಕುಟುಂಬದ ಮುಖ್ಯಸ್ಥರ ಹೆಸರು ಅಗತ್ಯವಿದೆ' : 'Head of family name is required');
      return;
    }
    if (!formData.address.trim()) {
      setErrorMessage(isKn ? 'ವಿಳಾಸ ಅಗತ್ಯವಿದೆ' : 'Address is required');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const headers = {
        'Content-Type': 'application/json',
        Authorization: `Bearer token-${currentUser?.username || 'asha_rampur'}-${currentUser?.id || 'USR-ASHA-RAMPUR'}`
      };

      const res = await fetch(`${API_BASE}/api/households`, {
        method: 'POST',
        headers,
        body: JSON.stringify(formData)
      });

      const resData = await res.json();

      if (res.status === 201) {
        onSuccess(resData);
        onClose();
      } else if (res.status === 409) {
        setErrorMessage(
          isKn
            ? `ಎಚ್ಚರಿಕೆ: ಈ ಕುಟುಂಬವು ಈಗಾಗಲೇ ನೋಂದಣಿಯಾಗಿದೆ (${resData.detail || 'Duplicate'})`
            : `Duplicate: Household already registered (${resData.detail || 'Duplicate'})`
        );
      } else {
        setErrorMessage(resData.detail || 'Failed to register household.');
      }
    } catch (err) {
      setErrorMessage('Network error while saving household.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" style={{ zIndex: 1200 }}>
      <div className="modal-card" style={{ maxWidth: '780px', maxHeight: '90vh', overflowY: 'auto' }}>
        <div className="modal-header" style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '12px' }}>
          <div>
            <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
              <Home size={20} color="#0d9488" />
              {isKn ? 'ಹೊಸ ಕುಟುಂಬ ನೋಂದಣಿ ಮತ್ತು ಸಮೀಕ್ಷೆ' : 'New Household Registration & Family Survey'}
            </h3>
            <p style={{ margin: '4px 0 0', fontSize: '13px', color: '#64748b' }}>
              {isKn
                ? 'ಆಶಾ ಕುಟುಂಬ ಡೈರೆಕ್ಟರಿಗೆ ಹೊಸ ಕುಟುಂಬ ಮತ್ತು ಸದಸ್ಯರನ್ನು ಸೇರಿಸಿ'
                : 'Register a new household and family members into the ASHA Household Directory'}
            </p>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: '#64748b' }}>
            ✕
          </button>
        </div>

        {/* Quick Voice Fill Assistant */}
        <div style={{ margin: '14px 16px 0', padding: '12px', backgroundColor: '#f0fdfa', borderRadius: '8px', border: '1px solid #ccfbf1' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', fontSize: '13px', fontWeight: '600', color: '#0f766e' }}>
            <Mic size={16} />
            <span>{isKn ? 'ಧ್ವನಿ ಮೂಲಕ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಭರ್ತಿ ಮಾಡಿ' : 'Quick Voice-Based Form Fill'}</span>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              placeholder={isKn ? "ಉದಾ: ಕುಟುಂಬದ ಮುಖ್ಯಸ್ಥ ರಮೇಶ್, 4 ಸದಸ್ಯರು, ರಾಂಪುರ, ಶೌಚಾಲಯ ಇದೆ..." : "e.g. Family head Ramesh, 4 members, Rampur village, toilet available..."}
              className="input-field"
              value={voiceInputText}
              onChange={(e) => setVoiceInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleVoiceFill()}
              style={{ flex: 1, fontSize: '13px' }}
            />
            <button
              type="button"
              onClick={handleVoiceFill}
              disabled={isExtractingVoice || !voiceInputText.trim()}
              className="btn btn-secondary"
              style={{ fontSize: '13px', whiteSpace: 'nowrap' }}
            >
              {isExtractingVoice ? '...' : isKn ? 'ಭರ್ತಿ ಮಾಡಿ' : 'Auto-Fill'}
            </button>
          </div>
        </div>

        {errorMessage && (
          <div style={{ margin: '12px 16px 0', backgroundColor: '#fef2f2', border: '1px solid #fecaca', padding: '8px 12px', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={16} color="#dc2626" />
            <span style={{ fontSize: '12px', color: '#b91c1c', fontWeight: '600' }}>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ padding: '16px' }}>
          {/* Section 1: Household Head & Location */}
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#1e293b', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <User size={16} color="#0d9488" />
              {isKn ? '೧. ಕುಟುಂಬದ ಮುಖ್ಯಸ್ಥ ಮತ್ತು ಸ್ಥಳ' : '1. Family Head & Location Details'}
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px', color: '#475569' }}>
                  {isKn ? 'ಕುಟುಂಬದ ಮುಖ್ಯಸ್ಥರ ಹೆಸರು *' : 'Head of Family Name *'}
                </label>
                <input
                  type="text"
                  required
                  className="input-field"
                  placeholder="e.g. Ramesh Gowda"
                  value={formData.head_of_family}
                  onChange={(e) => setFormData({ ...formData, head_of_family: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px', color: '#475569' }}>
                  {isKn ? 'ಸಂಪರ್ಕ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ' : 'Primary Contact Mobile'}
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g. 98765-11001"
                  value={formData.contact_number}
                  onChange={(e) => setFormData({ ...formData, contact_number: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px', color: '#475569' }}>
                  {isKn ? 'ಗ್ರಾಮ / ಸ್ಥಳ *' : 'Village / Locality *'}
                </label>
                <input
                  type="text"
                  required
                  className="input-field"
                  value={formData.village}
                  onChange={(e) => setFormData({ ...formData, village: e.target.value })}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px', color: '#475569' }}>
                  {isKn ? 'ಪಿನ್ ಕೋಡ್ *' : 'PIN Code *'}
                </label>
                <input
                  type="text"
                  required
                  maxLength={6}
                  className="input-field"
                  value={formData.pincode}
                  onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
                />
              </div>
            </div>

            <div style={{ marginTop: '10px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px', color: '#475569' }}>
                {isKn ? 'ಪೂರ್ಣ ವಸತಿ ವಿಳಾಸ *' : 'Complete Residential Address *'}
              </label>
              <input
                type="text"
                required
                className="input-field"
                placeholder="House # 42, Near Maramma Temple, Rampur"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              />
            </div>
          </div>

          {/* Section 2: Housing & Sanitation Facilities */}
          <div style={{ marginBottom: '16px', borderTop: '1px solid #e2e8f0', paddingTop: '14px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#1e293b', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <ShieldCheck size={16} color="#0d9488" />
              {isKn ? '೨. ವಸತಿ ಮತ್ತು ನೈರ್ಮಲ್ಯ ಸೌಲಭ್ಯಗಳು' : '2. Housing Structure & Sanitation Facilities'}
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px', color: '#475569' }}>
                  {isKn ? 'ಮನೆ ವಿಧ' : 'House Type'}
                </label>
                <select
                  className="input-field"
                  value={formData.house_type}
                  onChange={(e) => setFormData({ ...formData, house_type: e.target.value })}
                >
                  <option value="Pucca">Pucca (Concrete / Brick)</option>
                  <option value="Semi-Pucca">Semi-Pucca (Tiled / Stone)</option>
                  <option value="Kutcha">Kutcha (Mud / Thatch)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px', color: '#475569' }}>
                  {isKn ? 'ಕುಡಿಯುವ ನೀರಿನ ಮೂಲ' : 'Drinking Water Source'}
                </label>
                <select
                  className="input-field"
                  value={formData.water_source}
                  onChange={(e) => setFormData({ ...formData, water_source: e.target.value })}
                >
                  <option value="Piped Water / Tap">Piped Water / Tap (ನಲ್ಲಿ ನೀರು)</option>
                  <option value="Borewell / Handpump">Borewell / Handpump (ಕೊಳವೆ ಬಾವಿ)</option>
                  <option value="Well">Well (ಬಾವಿ)</option>
                  <option value="Filter Plant / RO">Filter Plant / RO (ಶುದ್ಧ ಕುಡಿಯುವ ನೀರು)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px', color: '#475569' }}>
                  {isKn ? 'ಶೌಚಾಲಯ ಸೌಲಭ್ಯ' : 'Toilet Facility'}
                </label>
                <select
                  className="input-field"
                  value={formData.toilet_available}
                  onChange={(e) => setFormData({ ...formData, toilet_available: e.target.value })}
                >
                  <option value="Individual Household Latrine (IHHL)">Individual Household Latrine (IHHL - ಶೌಚಾಲಯ ಇದೆ)</option>
                  <option value="Community Toilet">Community Toilet (ಸಮುದಾಯ ಶೌಚಾಲಯ)</option>
                  <option value="None / Open">None / Open (ಶೌಚಾಲಯ ಇಲ್ಲ)</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', marginBottom: '4px', color: '#475569' }}>
                  {isKn ? 'ಚರಂಡಿ ಸೌಲಭ್ಯ' : 'Drainage Sanitation'}
                </label>
                <select
                  className="input-field"
                  value={formData.sanitation_facility}
                  onChange={(e) => setFormData({ ...formData, sanitation_facility: e.target.value })}
                >
                  <option value="Closed Drainage">Closed Drainage (ಒಳಚರಂಡಿ)</option>
                  <option value="Soak Pit">Soak Pit (ಇಂಗು ಗುಂಡಿ)</option>
                  <option value="Open Drain">Open Drain (ತೆರೆದ ಚರಂಡಿ)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Section 3: Family Members Details */}
          <div style={{ marginBottom: '16px', borderTop: '1px solid #e2e8f0', paddingTop: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#1e293b', margin: 0, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <User size={16} color="#0d9488" />
                {isKn ? '೩. ಕುಟುಂಬದ ಸದಸ್ಯರು ಮತ್ತು ಆರೋಗ್ಯ ವಿವರಗಳು' : '3. Family Members & Health Profiling'}
                <span style={{ fontSize: '12px', fontWeight: 'normal', color: '#64748b' }}>({formData.family_members.length} members)</span>
              </h4>
              <button
                type="button"
                onClick={handleAddMember}
                className="btn btn-secondary btn-sm"
                style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px' }}
              >
                <Plus size={14} />
                {isKn ? 'ಸದಸ್ಯರನ್ನು ಸೇರಿಸಿ' : 'Add Member'}
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {formData.family_members.map((member, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: idx === 0 ? '#f8fafc' : '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    padding: '10px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px'
                  }}
                >
                  <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1.2fr 1.5fr auto', gap: '8px', alignItems: 'center' }}>
                    <input
                      type="text"
                      className="input-field"
                      placeholder={idx === 0 ? "Head Name" : "Member Name"}
                      value={member.full_name}
                      onChange={(e) => handleMemberChange(idx, 'full_name', e.target.value)}
                      style={{ fontSize: '13px' }}
                    />
                    <input
                      type="number"
                      className="input-field"
                      placeholder="Age"
                      min={0}
                      max={120}
                      value={member.age}
                      onChange={(e) => handleMemberChange(idx, 'age', parseInt(e.target.value) || 0)}
                      style={{ fontSize: '13px' }}
                    />
                    <select
                      className="input-field"
                      value={member.gender}
                      onChange={(e) => handleMemberChange(idx, 'gender', e.target.value)}
                      style={{ fontSize: '13px' }}
                    >
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                    <select
                      className="input-field"
                      value={member.relationship}
                      onChange={(e) => handleMemberChange(idx, 'relationship', e.target.value)}
                      style={{ fontSize: '13px' }}
                    >
                      <option value="Self / Head">Self / Head</option>
                      <option value="Spouse">Spouse</option>
                      <option value="Son">Son</option>
                      <option value="Daughter">Daughter</option>
                      <option value="Mother">Mother</option>
                      <option value="Father">Father</option>
                      <option value="Other">Other</option>
                    </select>
                    {formData.family_members.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveMember(idx)}
                        style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px' }}
                        title="Remove member"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>

                  {/* Health Flags */}
                  <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', fontSize: '12px', color: '#475569', paddingTop: '4px' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={Boolean(member.is_pregnant)}
                        onChange={(e) => handleMemberChange(idx, 'is_pregnant', e.target.checked)}
                      />
                      <span>Pregnant (ANC)</span>
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={Boolean(member.is_child_under_5)}
                        onChange={(e) => handleMemberChange(idx, 'is_child_under_5', e.target.checked)}
                      />
                      <span>Child Under 5</span>
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={Boolean(member.is_elderly)}
                        onChange={(e) => handleMemberChange(idx, 'is_elderly', e.target.checked)}
                      />
                      <span>Elderly (60+)</span>
                    </label>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="modal-footer" style={{ borderTop: '1px solid #e2e8f0', paddingTop: '14px', marginTop: '14px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary" disabled={isSubmitting}>
              {isKn ? 'ರದ್ದುಮಾಡಿ' : 'Cancel'}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={isSubmitting}
              style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              <CheckCircle size={16} />
              {isSubmitting ? (isKn ? 'ಉಳಿಸಲಾಗುತ್ತಿದೆ...' : 'Saving...') : isKn ? 'ಕುಟುಂಬವನ್ನು ಉಳಿಸಿ' : 'Save Household'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}


import React, { useState } from 'react';
import { UserPlus, User, Lock, Phone, MapPin, Building, ShieldCheck, AlertCircle, CheckCircle, X } from 'lucide-react';

const API_BASE = window.location.origin.includes(':5173') ? 'http://localhost:8000' : '';

export default function WorkerRegistrationModal({ isOpen, onClose, onSuccess, lang = 'en' }) {
  const isKn = lang === 'kn';

  const [formData, setFormData] = useState({
    full_name: '',
    username: '',
    password: 'asha123',
    mobile: '98450-12345',
    village: 'Rampur',
    pincode: '571428',
    taluk: 'Maddur',
    district: 'Mandya',
    state: 'Karnataka',
    phc_name: 'Kestur Primary Health Centre',
    sector: 'Ward 4 - Anganwadi Sector 2'
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    if (!formData.full_name.trim()) {
      setErrorMessage(isKn ? 'ದಯವಿಟ್ಟು ಪೂರ್ಣ ಹೆಸರನ್ನು ನಮೂದಿಸಿ' : 'Please enter full name.');
      return;
    }
    if (!formData.username.trim()) {
      setErrorMessage(isKn ? 'ದಯವಿಟ್ಟು ಬಳಕೆದಾರರ ಹೆಸರನ್ನು ನಮೂದಿಸಿ' : 'Please enter a username.');
      return;
    }
    if (!formData.pincode || formData.pincode.length !== 6) {
      setErrorMessage(isKn ? 'ದಯವಿಟ್ಟು 6 ಅಂಕಿಯ ಪಿನ್ ಕೋಡ್ ನಮೂದಿಸಿ' : 'Please enter a valid 6-digit PIN code.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setSuccessMessage(isKn ? `ಆಶಾ ಕಾರ್ಯಕರ್ತೆ ${data.user.full_name} ಯಶಸ್ವಿಯಾಗಿ ನೋಂದಾಯಿಸಲಾಗಿದೆ!` : `Worker ${data.user.full_name} registered successfully!`);
        if (onSuccess) {
          onSuccess(data.user);
        }
        setTimeout(() => {
          onClose();
        }, 1200);
      } else {
        setErrorMessage(data.detail || 'Registration failed. Please check details.');
      }
    } catch (err) {
      console.error('Registration error:', err);
      setErrorMessage('Network error while connecting to server.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.modalCard}>
        {/* Modal Header */}
        <div style={styles.header}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={styles.iconCircle}>
              <UserPlus size={20} color="#0284c7" />
            </div>
            <div>
              <h2 style={styles.title}>
                {isKn ? 'ಹೊಸ ಆಶಾ ಕಾರ್ಯಕರ್ತೆ ನೋಂದಣಿ' : 'Register New ASHA Worker'}
              </h2>
              <span style={styles.subtitle}>
                {isKn ? 'ಕರ್ನಾಟಕ ಆರೋಗ್ಯ ಮತ್ತು ಕುಟುಂಬ ಕಲ್ಯಾಣ ಇಲಾಖೆ' : 'Karnataka Health Department Official Registry'}
              </span>
            </div>
          </div>
          <button onClick={onClose} style={styles.closeBtn} type="button">
            <X size={18} />
          </button>
        </div>

        {/* Content Form */}
        <form onSubmit={handleSubmit} style={styles.body}>
          {errorMessage && (
            <div style={styles.alertError}>
              <AlertCircle size={18} color="#dc2626" />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div style={styles.alertSuccess}>
              <CheckCircle size={18} color="#16a34a" />
              <span>{successMessage}</span>
            </div>
          )}

          <div style={styles.sectionHeader}>
            <User size={16} color="#0284c7" />
            <span>{isKn ? 'ಕಾರ್ಯಕರ್ತೆಯ ವೈಯಕ್ತಿಕ ವಿವರ' : 'Worker Identity & Credentials'}</span>
          </div>

          <div style={styles.grid2}>
            <div>
              <label style={styles.label}>
                {isKn ? 'ಪೂರ್ಣ ಹೆಸರು *' : 'Full Name *'}
              </label>
              <input
                type="text"
                required
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                placeholder="e.g. Radhika Gowda"
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>
                {isKn ? 'ಬಳಕೆದಾರರ ಹೆಸರು (Login ID) *' : 'Username (Login ID) *'}
              </label>
              <input
                type="text"
                required
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value.toLowerCase().trim() })}
                placeholder="e.g. asha_radhika"
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>
                {isKn ? 'ಪಾಸ್‌ವರ್ಡ್ *' : 'Initial Password *'}
              </label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                placeholder="Password"
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>
                {isKn ? 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ' : 'Mobile Number'}
              </label>
              <input
                type="text"
                value={formData.mobile}
                onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                placeholder="e.g. 98450-12345"
                style={styles.input}
              />
            </div>
          </div>

          <div style={{ ...styles.sectionHeader, marginTop: '20px' }}>
            <MapPin size={16} color="#0284c7" />
            <span>{isKn ? 'ನಿಯೋಜಿತ ಪ್ರದೇಶ ವಿವರ' : 'Assigned Jurisdiction & Health Centre'}</span>
          </div>

          <div style={styles.grid2}>
            <div>
              <label style={styles.label}>
                {isKn ? 'ಗ್ರಾಮ / ವಾರ್ಡ್ *' : 'Village / Ward *'}
              </label>
              <input
                type="text"
                required
                value={formData.village}
                onChange={(e) => setFormData({ ...formData, village: e.target.value })}
                placeholder="e.g. Rampur"
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>
                {isKn ? 'ಪಿನ್ ಕೋಡ್ (PIN Code) *' : 'PIN Code *'}
              </label>
              <input
                type="text"
                required
                maxLength={6}
                value={formData.pincode}
                onChange={(e) => setFormData({ ...formData, pincode: e.target.value })}
                placeholder="e.g. 571428"
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>
                {isKn ? 'ತಾಲ್ಲೂಕು' : 'Taluk'}
              </label>
              <input
                type="text"
                value={formData.taluk}
                onChange={(e) => setFormData({ ...formData, taluk: e.target.value })}
                placeholder="e.g. Maddur"
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>
                {isKn ? 'ಜಿಲ್ಲೆ' : 'District'}
              </label>
              <input
                type="text"
                value={formData.district}
                onChange={(e) => setFormData({ ...formData, district: e.target.value })}
                placeholder="e.g. Mandya"
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>
                {isKn ? 'ನಿಯೋಜಿತ ಪ್ರಾಥಮಿಕ ಆರೋಗ್ಯ ಕೇಂದ್ರ (PHC)' : 'Assigned Primary Health Centre (PHC)'}
              </label>
              <input
                type="text"
                value={formData.phc_name}
                onChange={(e) => setFormData({ ...formData, phc_name: e.target.value })}
                placeholder="e.g. Kestur Primary Health Centre"
                style={styles.input}
              />
            </div>

            <div>
              <label style={styles.label}>
                {isKn ? 'ಸೆಕ್ಟರ್ / ಅಂಗನವಾಡಿ ಕೇಂದ್ರ' : 'Sector / Anganwadi Locality'}
              </label>
              <input
                type="text"
                value={formData.sector}
                onChange={(e) => setFormData({ ...formData, sector: e.target.value })}
                placeholder="e.g. Ward 4 - Anganwadi Sector 2"
                style={styles.input}
              />
            </div>
          </div>

          {/* Footer buttons */}
          <div style={styles.footer}>
            <button
              type="button"
              onClick={onClose}
              style={styles.cancelBtn}
              disabled={isSubmitting}
            >
              {isKn ? 'ರದ್ದುಮಾಡಿ' : 'Cancel'}
            </button>

            <button
              type="submit"
              disabled={isSubmitting}
              style={styles.submitBtn}
            >
              {isSubmitting ? (
                <span>{isKn ? 'ನೋಂದಾಯಿಸಲಾಗುತ್ತಿದೆ...' : 'Registering...'}</span>
              ) : (
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldCheck size={16} />
                  {isKn ? 'ಖಾತೆ ತೆರೆಯಿರಿ & ಲಾಗಿನ್ ಮಾಡಿ' : 'Register & Log In'}
                </span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(15, 23, 42, 0.65)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    backdropFilter: 'blur(3px)',
    padding: '16px'
  },
  modalCard: {
    backgroundColor: '#ffffff',
    borderRadius: '16px',
    maxWidth: '680px',
    width: '100%',
    maxHeight: '92vh',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    overflow: 'hidden'
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '18px 24px',
    borderBottom: '1px solid #e2e8f0',
    backgroundColor: '#f8fafc'
  },
  iconCircle: {
    width: '38px',
    height: '38px',
    borderRadius: '10px',
    backgroundColor: '#e0f2fe',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  title: {
    fontSize: '18px',
    fontWeight: '700',
    color: '#0f172a',
    margin: 0
  },
  subtitle: {
    fontSize: '12px',
    color: '#64748b',
    marginTop: '2px',
    display: 'block'
  },
  closeBtn: {
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    color: '#64748b',
    padding: '6px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  body: {
    padding: '24px',
    overflowY: 'auto'
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '14px',
    fontWeight: '700',
    color: '#0369a1',
    marginBottom: '12px',
    paddingBottom: '6px',
    borderBottom: '1px solid #f1f5f9'
  },
  grid2: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
    gap: '14px'
  },
  label: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#334155',
    display: 'block',
    marginBottom: '5px'
  },
  input: {
    width: '100%',
    padding: '9px 12px',
    borderRadius: '8px',
    border: '1px solid #cbd5e1',
    fontSize: '13px',
    outline: 'none',
    boxSizing: 'border-box'
  },
  footer: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'flex-end',
    gap: '12px',
    marginTop: '24px',
    paddingTop: '16px',
    borderTop: '1px solid #e2e8f0'
  },
  cancelBtn: {
    padding: '10px 18px',
    borderRadius: '8px',
    border: '1px solid #cbd5e1',
    backgroundColor: '#ffffff',
    color: '#475569',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer'
  },
  submitBtn: {
    padding: '10px 22px',
    borderRadius: '8px',
    border: 'none',
    backgroundColor: '#0284c7',
    color: '#ffffff',
    fontSize: '13px',
    fontWeight: '600',
    cursor: 'pointer'
  },
  alertError: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px 16px',
    backgroundColor: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '8px',
    color: '#b91c1c',
    fontSize: '13px',
    marginBottom: '16px'
  },
  alertSuccess: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '12px 16px',
    backgroundColor: '#f0fdf4',
    border: '1px solid #bbf7d0',
    borderRadius: '8px',
    color: '#15803d',
    fontSize: '13px',
    marginBottom: '16px'
  }
};


import React, { useState, useEffect } from 'react';
import './InstallPWA.css';

function InstallPWA() {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstall, setShowInstall] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      // Prevent the mini-infobar from appearing on mobile
      e.preventDefault();
      // Save the event so it can be triggered later
      setDeferredPrompt(e);
      // Show the install button
      setShowInstall(true);
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;

    // Show the install prompt
    deferredPrompt.prompt();

    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('✅ User accepted the install prompt');
    } else {
      console.log('❌ User dismissed the install prompt');
    }

    // Clear the saved prompt since it can't be used again
    setDeferredPrompt(null);
    setShowInstall(false);
  };

  const handleDismiss = () => {
    setShowInstall(false);
  };

  if (!showInstall) return null;

  return (
    <div className="install-pwa-banner">
      <div className="install-content">
        <span className="install-icon">📱</span>
        <div className="install-text">
          <strong>Install Muse</strong>
          <span>Get the app experience!</span>
        </div>
      </div>
      <div className="install-actions">
        <button onClick={handleInstall} className="btn-install">
          Install
        </button>
        <button onClick={handleDismiss} className="btn-dismiss">
          ✕
        </button>
      </div>
    </div>
  );
}

export default InstallPWA;

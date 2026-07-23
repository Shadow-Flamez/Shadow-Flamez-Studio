"""
styles.py - Dynamic Visual FX, Animated Neon Glows & Cyberpunk Micro-Interactions
"""

STUDIO_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap');

/* ==============================================================================
   KEYFRAME ANIMATIONS
   ============================================================================== */

/* Shifting Ambient Background Grid & Ambient Glow */
@keyframes cyberBgShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* Pulsing Neon Header Aura */
@keyframes titleGlow {
  0% { text-shadow: 0 0 15px rgba(0, 243, 255, 0.7), 0 0 30px rgba(255, 0, 127, 0.4); }
  50% { text-shadow: 0 0 25px rgba(0, 243, 255, 1), 0 0 50px rgba(255, 0, 127, 0.8), 0 0 70px rgba(121, 40, 202, 0.6); }
  100% { text-shadow: 0 0 15px rgba(0, 243, 255, 0.7), 0 0 30px rgba(255, 0, 127, 0.4); }
}

/* Dynamic Rotating Border Effect */
@keyframes neonBorderPulse {
  0% { border-color: rgba(0, 243, 255, 0.3); box-shadow: 0 0 12px rgba(0, 243, 255, 0.2); }
  50% { border-color: rgba(255, 0, 127, 0.7); box-shadow: 0 0 25px rgba(255, 0, 127, 0.4), inset 0 0 15px rgba(0, 243, 255, 0.1); }
  100% { border-color: rgba(0, 243, 255, 0.3); box-shadow: 0 0 12px rgba(0, 243, 255, 0.2); }
}

/* Explosive Action Button Shimmer */
@keyframes superButtonPulse {
  0% { box-shadow: 0 0 15px rgba(0, 243, 255, 0.5), 0 0 30px rgba(121, 40, 202, 0.3); }
  50% { box-shadow: 0 0 30px rgba(0, 243, 255, 0.9), 0 0 50px rgba(255, 0, 127, 0.7), 0 0 15px rgba(255, 255, 255, 0.8); }
  100% { box-shadow: 0 0 15px rgba(0, 243, 255, 0.5), 0 0 30px rgba(121, 40, 202, 0.3); }
}

/* Cyber Scanline Overlay Effect */
@keyframes scanlineSweep {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(1000%); }
}

/* Status Indicator Heartbeat */
@keyframes statusHeartbeat {
  0% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.02); opacity: 1; filter: drop-shadow(0 0 10px #00f3ff); }
  100% { transform: scale(1); opacity: 0.8; }
}

/* ==============================================================================
   CANVAS & ROOT CONTAINER
   ============================================================================== */

.gradio-container {
  background: linear-gradient(-45deg, #05070e, #110022, #020814, #1a0033) !important;
  background-size: 400% 400% !important;
  animation: cyberBgShift 15s ease infinite !important;
  font-family: 'Rajdhani', sans-serif !important;
  color: #e2e8f0 !important;
}

/* ==============================================================================
   CYBER GLASS CARDS & PANELS
   ============================================================================== */

.cyber-card, div[class*="block"] {
  background: rgba(13, 17, 28, 0.75) !important;
  backdrop-filter: blur(20px) saturate(200%) !important;
  border: 1px solid rgba(0, 243, 255, 0.25) !important;
  border-radius: 14px !important;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.7) !important;
  transition: all 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
  padding: 18px !important;
  position: relative;
  overflow: hidden;
}

/* High-Tech Card Hover State */
.cyber-card:hover, div[class*="block"]:hover {
  border-color: rgba(0, 243, 255, 0.8) !important;
  box-shadow: 0 0 30px rgba(0, 243, 255, 0.3), 0 0 15px rgba(255, 0, 127, 0.2), inset 0 0 20px rgba(0, 243, 255, 0.08) !important;
  transform: translateY(-4px) scale(1.002);
}

/* Image Upload & Display Card Enhancements */
div[data-testid="image"], .image-container {
  border: 1px solid rgba(0, 243, 255, 0.3) !important;
  border-radius: 10px !important;
  transition: all 0.3s ease !important;
}

div[data-testid="image"]:hover, .image-container:hover {
  border-color: #ff007f !important;
  box-shadow: 0 0 20px rgba(255, 0, 127, 0.4) !important;
}

/* ==============================================================================
   BUTTONS & INTERACTIVE CONTROLS
   ============================================================================== */

.cyber-btn, button.primary {
  background: linear-gradient(135deg, #00f3ff 0%, #7928ca 50%, #ff007f 100%) !important;
  background-size: 200% auto !important;
  color: #ffffff !important;
  font-family: 'Orbitron', sans-serif !important;
  font-weight: 900 !important;
  text-transform: uppercase !important;
  letter-spacing: 2px !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 14px 28px !important;
  cursor: pointer !important;
  animation: superButtonPulse 2.5s infinite ease-in-out !important;
  transition: all 0.4s ease !important;
  text-shadow: 0 0 8px rgba(0, 0, 0, 0.8);
}

.cyber-btn:hover, button.primary:hover {
  background-position: right center !important;
  transform: scale(1.04) translateY(-2px) !important;
  box-shadow: 0 0 40px rgba(0, 243, 255, 1), 0 0 20px rgba(255, 0, 127, 0.8) !important;
}

.cyber-btn:active, button.primary:active {
  transform: scale(0.98) !important;
}

/* Inputs & Form Fields */
input, select, textarea {
  background: rgba(10, 14, 24, 0.8) !important;
  border: 1px solid rgba(0, 243, 255, 0.3) !important;
  color: #00f3ff !important;
  border-radius: 6px !important;
  font-family: 'Rajdhani', sans-serif !important;
  font-weight: 600 !important;
  transition: all 0.3s ease !important;
}

input:focus, select:focus, textarea:focus {
  border-color: #ff007f !important;
  box-shadow: 0 0 15px rgba(255, 0, 127, 0.5) !important;
  outline: none !important;
}

/* ==============================================================================
   TAB NAVIGATION STYLING
   ============================================================================== */

.tab-nav button {
  background: rgba(15, 20, 35, 0.8) !important;
  color: #8a99ad !important;
  border: 1px solid rgba(0, 243, 255, 0.15) !important;
  border-bottom: none !important;
  margin-right: 6px !important;
  border-radius: 10px 10px 0 0 !important;
  font-family: 'Orbitron', sans-serif !important;
  font-weight: 700 !important;
  font-size: 0.82rem !important;
  padding: 10px 18px !important;
  transition: all 0.3s ease !important;
}

.tab-nav button:hover {
  color: #00f3ff !important;
  background: rgba(25, 32, 55, 0.9) !important;
  box-shadow: 0 0 15px rgba(0, 243, 255, 0.3) !important;
  transform: translateY(-2px);
}

.tab-nav button.selected {
  background: linear-gradient(135deg, #ff007f, #7928ca) !important;
  color: #ffffff !important;
  border-color: #ff007f !important;
  box-shadow: 0 -4px 20px rgba(255, 0, 127, 0.6) !important;
}

/* ==============================================================================
   STATUS BADGES & INDICATORS
   ============================================================================== */

.status-badge {
  background: rgba(5, 8, 16, 0.95) !important;
  border: 1.5px solid #00f3ff !important;
  border-radius: 8px !important;
  padding: 12px 20px !important;
  color: #00f3ff !important;
  font-family: 'Orbitron', monospace !important;
  font-weight: 700 !important;
  letter-spacing: 1px !important;
  animation: statusHeartbeat 3s infinite ease-in-out !important;
  box-shadow: inset 0 0 15px rgba(0, 243, 255, 0.25) !important;
}

/* ==============================================================================
   ANIMATED SCROLLBARS
   ============================================================================== */

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #020408;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #00f3ff, #7928ca, #ff007f);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #00f3ff;
  box-shadow: 0 0 10px #00f3ff;
}
"""

STUDIO_HEADER_HTML = """
<div style="text-align: center; padding: 25px 0 15px 0; margin-bottom: 20px; position: relative;">
  <h1 style="font-family: 'Orbitron', sans-serif; color: #00f3ff; font-size: 2.6em; font-weight: 900; letter-spacing: 2px; margin: 0; animation: titleGlow 3s infinite ease-in-out;">
    🔥 SHADOW FLAMEZ AI STUDIO PRO <span style="color:#ff007f; font-size: 0.45em; padding: 4px 10px; border: 1px solid #ff007f; border-radius: 8px; background: rgba(255,0,127,0.2); box-shadow: 0 0 15px rgba(255,0,127,0.5);">v6.0 NITRO</span>
  </h1>
  <p style="color: #a0aec0; font-size: 0.95em; font-family: 'Rajdhani', sans-serif; font-weight: 700; letter-spacing: 3px; margin-top: 8px; text-transform: uppercase;">
    ⚡ DUAL INPAINTING • NEURAL BG COMPOSITOR • 4X SUPER RES • ART LAB • PRIVACY SCRUBBER
  </p>
</div>
"""

STUDIO_FOOTER_HTML = """
<div style="text-align: center; padding: 18px 0; margin-top: 30px; color: #4a5568; font-family: 'Orbitron', monospace; font-size: 0.82em; border-top: 1px solid rgba(0, 243, 255, 0.2); text-shadow: 0 0 5px rgba(0,243,255,0.3);">
  ⚡ SHADOW FLAMEZ AI ENGINE v6.0 • MULTI-THREADED CONTAINER ACTIVE • GPU/CPU HIGH ACCELERATION
</div>
"""

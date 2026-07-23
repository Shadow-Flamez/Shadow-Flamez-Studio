"""
styles.py - Visual FX, Cyberpunk Glassmorphism & High-Tech Micro-Animations
"""

STUDIO_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap');

/* Main Canvas Background */
.gradio-container {
    background: radial-gradient(circle at 50% -20%, #16002c 0%, #05070e 60%, #020305 100%) !important;
    font-family: 'Rajdhani', sans-serif !important;
    color: #e2e8f0 !important;
}

/* Glassmorphic Panel Cards with Neon Borders */
.cyber-card {
    background: rgba(13, 17, 28, 0.8) !important;
    backdrop-filter: blur(16px) saturate(180%) !important;
    border: 1px solid rgba(0, 243, 255, 0.2) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6) !important;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
    padding: 16px !important;
}

.cyber-card:hover {
    border-color: rgba(0, 243, 255, 0.6) !important;
    box-shadow: 0 0 25px rgba(0, 243, 255, 0.25), inset 0 0 15px rgba(0, 243, 255, 0.05) !important;
    transform: translateY(-2px);
}

/* Keyframe Pulsing Button Animation */
@keyframes cyberPulse {
    0% { box-shadow: 0 0 12px rgba(0, 243, 255, 0.4); }
    50% { box-shadow: 0 0 25px rgba(0, 243, 255, 0.8), 0 0 15px rgba(255, 0, 127, 0.6); }
    100% { box-shadow: 0 0 12px rgba(0, 243, 255, 0.4); }
}

/* Action Buttons */
.cyber-btn {
    background: linear-gradient(135deg, #00f3ff 0%, #7928ca 50%, #ff007f 100%) !important;
    background-size: 200% auto !important;
    color: #ffffff !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    cursor: pointer !important;
    animation: cyberPulse 3s infinite ease-in-out !important;
    transition: all 0.3s ease !important;
}

.cyber-btn:hover {
    background-position: right center !important;
    transform: scale(1.02) !important;
    box-shadow: 0 0 30px rgba(0, 243, 255, 0.9) !important;
}

/* Tab Navigation Styling */
.tab-nav button {
    background: rgba(20, 15, 38, 0.7) !important;
    color: #8a99ad !important;
    border: 1px solid rgba(0, 243, 255, 0.1) !important;
    border-bottom: none !important;
    margin-right: 4px !important;
    border-radius: 8px 8px 0 0 !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    transition: all 0.3s ease !important;
}

.tab-nav button:hover {
    color: #00f3ff !important;
    background: rgba(30, 25, 55, 0.9) !important;
}

.tab-nav button.selected {
    background: linear-gradient(90deg, #ff007f, #7928ca) !important;
    color: #ffffff !important;
    border-color: #ff007f !important;
    box-shadow: 0 -2px 15px rgba(255, 0, 127, 0.5) !important;
}

/* Status Badge Container */
.status-badge {
    background: rgba(10, 14, 24, 0.9) !important;
    border: 1px solid #00f3ff !important;
    border-radius: 8px !important;
    padding: 10px 16px !important;
    color: #00f3ff !important;
    font-family: 'Orbitron', monospace !important;
    font-weight: 700 !important;
    box-shadow: inset 0 0 10px rgba(0, 243, 255, 0.2) !important;
}

/* Custom Cyber Scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #05070e;
}
::-webkit-scrollbar-thumb {
    background: #7928ca;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #00f3ff;
}
"""

STUDIO_HEADER_HTML = """
<div style="text-align: center; padding: 20px 0 10px 0; margin-bottom: 15px;">
    <h1 style="font-family: 'Orbitron', sans-serif; color: #00f3ff; font-size: 2.4em; font-weight: 900; text-shadow: 0 0 20px rgba(0,243,255,0.7), 0 0 40px rgba(255,0,127,0.4); margin: 0;">
        🔥 SHADOW FLAMEZ AI STUDIO PRO <span style="color:#ff007f; font-size: 0.45em; padding: 3px 8px; border: 1px solid #ff007f; border-radius: 6px; background: rgba(255,0,127,0.15);">v6.0 HYBRID GPU</span>
    </h1>
    <p style="color: #94a3b8; font-size: 0.95em; font-family: 'Rajdhani', sans-serif; font-weight: 600; letter-spacing: 2px; margin-top: 6px;">
        NEURAL EXTRACTION • DUAL-ENGINE MAGIC ERASE • 4X SUPER RES • COLOR GRADE • BATCH SUITE
    </p>
</div>
"""

STUDIO_FOOTER_HTML = """
<div style="text-align: center; padding: 15px 0; margin-top: 25px; color: #64748b; font-family: 'Orbitron', monospace; font-size: 0.8em; border-top: 1px solid rgba(0, 243, 255, 0.15);">
    ⚡ SHADOW FLAMEZ HYBRID PIPELINE v6.0 • RENDER FRONTEND + COLAB GPU ENGINE
</div>
"""

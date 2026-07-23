"""
styles.py - Hyper-Stylized Cyberpunk UI, Glassmorphism, Neon Backglow & Animations
"""

STUDIO_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&display=swap');

/* Main Canvas Background with CRT Scanlines & Radial Backglow */
.gradio-container {
    background: radial-gradient(circle at 50% -20%, #1a0033 0%, #05070e 60%, #020305 100%) !important;
    font-family: 'Rajdhani', sans-serif !important;
    color: #e2e8f0 !important;
}

/* Glassmorphic Panel Cards with Neon Borders */
.gr-panel, .gr-box, .gr-form {
    background: rgba(13, 17, 28, 0.75) !important;
    backdrop-filter: blur(16px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
    border: 1px solid rgba(0, 255, 255, 0.18) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6) !important;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.gr-panel:hover, .gr-box:hover {
    border-color: rgba(0, 255, 255, 0.45) !important;
    box-shadow: 0 0 25px rgba(0, 255, 255, 0.25), inset 0 0 15px rgba(0, 255, 255, 0.05) !important;
    transform: translateY(-2px);
}

/* Dynamic Pulsing & Backglow Keyframes */
@keyframes neonPulse {
    0% {
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.4), 0 0 30px rgba(0, 255, 255, 0.2);
        border-color: #00ffff;
    }
    50% {
        box-shadow: 0 0 25px rgba(255, 0, 127, 0.6), 0 0 50px rgba(255, 0, 127, 0.3);
        border-color: #ff007f;
    }
    100% {
        box-shadow: 0 0 15px rgba(0, 255, 255, 0.4), 0 0 30px rgba(0, 255, 255, 0.2);
        border-color: #00ffff;
    }
}

@keyframes scanline {
    0% { background-position: 0 0; }
    100% { background-position: 0 100%; }
}

/* Status Indicator Badge */
.status-badge {
    background: linear-gradient(135deg, rgba(20, 25, 40, 0.9), rgba(10, 14, 24, 0.95)) !important;
    backdrop-filter: blur(10px);
    color: #00ffff;
    padding: 14px 22px;
    border-radius: 8px;
    border-left: 4px solid #00ffff;
    font-family: 'Orbitron', monospace;
    font-weight: 700;
    letter-spacing: 1px;
    animation: neonPulse 4s infinite alternate;
}

/* Pro Cyberpunk Action Buttons with Backglow Hover */
.cyber-button {
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 50%, #ff007f 100%) !important;
    background-size: 200% auto !important;
    color: #000000 !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 14px 28px !important;
    cursor: pointer !important;
    transition: all 0.4s ease !important;
    box-shadow: 0 4px 20px rgba(0, 242, 254, 0.3) !important;
}

.cyber-button:hover {
    background-position: right center !important;
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 0 30px #00f2fe, 0 0 50px #ff007f !important;
    color: #ffffff !important;
}

/* Tab Headers Styling */
.tabs button {
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 700 !important;
    color: #8a99ad !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.3s ease !important;
}

.tabs button.selected {
    color: #00ffff !important;
    border-bottom-color: #00ffff !important;
    text-shadow: 0 0 12px rgba(0, 255, 255, 0.8) !important;
}
"""

STUDIO_HEADER_HTML = """
<div style="text-align: center; padding: 30px 0 20px 0; border-bottom: 1px solid rgba(0, 255, 255, 0.2); background: radial-gradient(ellipse at center, rgba(0,255,255,0.08) 0%, rgba(0,0,0,0) 75%); margin-bottom: 20px;">
    <h1 style="font-family: 'Orbitron', sans-serif; color: #00ffff; font-size: 2.8em; font-weight: 900; text-shadow: 0 0 20px rgba(0,255,255,0.7), 0 0 40px rgba(255,0,127,0.4); margin: 0;">
        🔥 SHADOW FLAMEZ AI STUDIO PRO <span style="color:#ff007f; font-size: 0.45em; padding: 4px 10px; background: rgba(255,0,127,0.15); border: 1px solid #ff007f; border-radius: 6px;">v5.5 ULTIMATE</span>
    </h1>
    <p style="color: #94a3b8; font-size: 1.1em; font-family: 'Rajdhani', sans-serif; font-weight: 600; letter-spacing: 2px; margin-top: 8px;">
        NEURAL EXTRACTION • 4X SUPER RES • CYBER FX • DROP SHADOWS • COLOR GRADE • LIGHTING STUDIO
    </p>
</div>
"""

STUDIO_FOOTER_HTML = """
<div style="text-align: center; padding: 20px 0; border-top: 1px solid rgba(0, 255, 255, 0.15); margin-top: 35px; color: #64748b; font-family: 'Orbitron', monospace; font-size: 0.85em;">
    ⚡ POWERED BY NEURAL PIPELINE v5.5 • RENDER HIGH-SPEED CONTAINER ACTIVE
</div>
"""

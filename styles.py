"""
styles.py - Dynamic Visuals, Animations & Cyberpunk Theme
"""

STUDIO_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Inter:wght@300;400;600&display=swap');

.gradio-container {
    background: #090a0f !important;
    font-family: 'Inter', sans-serif !important;
}

@keyframes cyberGlow {
    0% { box-shadow: 0 0 10px #00ffff44, 0 0 20px #00ffff22; }
    50% { box-shadow: 0 0 20px #ff007f88, 0 0 40px #ff007f44; }
    100% { box-shadow: 0 0 10px #00ffff44, 0 0 20px #00ffff22; }
}

@keyframes pulseNeon {
    0% { border-color: #00ffff; }
    50% { border-color: #ff007f; }
    100% { border-color: #00ffff; }
}

.status-badge {
    background: rgba(18, 22, 36, 0.85);
    backdrop-filter: blur(8px);
    color: #e0e6ed;
    padding: 14px 20px;
    border-radius: 8px;
    border-left: 5px solid #00ffff;
    font-family: 'Orbitron', monospace;
    font-size: 0.9em;
    letter-spacing: 0.5px;
    animation: cyberGlow 4s infinite alternate;
}

.cyber-button {
    background: linear-gradient(135deg, #00ffff, #ff007f) !important;
    color: #000 !important;
    font-family: 'Orbitron', sans-serif !important;
    font-weight: 900 !important;
    border: none !important;
    text-transform: uppercase;
    transition: all 0.3s ease !important;
}

.cyber-button:hover {
    transform: scale(1.02);
    box-shadow: 0 0 25px #00ffffaa !important;
}
"""

STUDIO_HEADER_HTML = """
<div style="text-align: center; padding: 25px 0; border-bottom: 2px solid #1f2438; background: radial-gradient(circle, rgba(0,255,255,0.05) 0%, rgba(0,0,0,0) 70%);">
    <h1 style="font-family: 'Orbitron', sans-serif; color: #00ffff; font-size: 2.5em; text-shadow: 0 0 15px #00ffffaa; margin-bottom: 5px;">
        🔥 SHADOW FLAMEZ AI STUDIO PRO <span style="color:#ff007f; font-size: 0.5em;">v5.0</span>
    </h1>
    <p style="color: #8b9bb4; font-size: 1.05em; font-weight: 300; letter-spacing: 1px;">
        NEURAL EXTRACTION • 4X SUPER RESOLUTION • NEON AURA & CYBER GRAPHICS
    </p>
</div>
"""

STUDIO_FOOTER_HTML = """
<div style="text-align: center; padding: 18px 0; border-top: 1px solid #1f2438; margin-top: 30px; color: #5a6b82; font-family: 'Orbitron', monospace; font-size: 0.85em;">
    ⚡ SHADOW FLAMEZ ENGINE • RENDER CLOUD ACTIVE • HIGH PERFORMANCE PIPELINE
</div>
"""

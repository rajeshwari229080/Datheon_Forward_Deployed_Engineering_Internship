"""High-craft light-theme visual asset generator for Sentinel Enterprise AI Fabric.

Generates:
1. assets/sentinel_hero_light.png
2. assets/sentinel_architecture_light.png
3. assets/sentinel_governance_light.png
4. image.png (LinkedIn showcase card)
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_browser():
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("msedge"),
        shutil.which("chrome"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def render_svg_to_png(svg_content: str, output_png_path: str, width: int = 1200, height: int = 630):
    browser = find_browser()
    if not browser:
        raise RuntimeError("No Chromium/Edge browser found for high-res SVG rasterization.")

    tmp_html = Path(output_png_path).with_suffix(".tmp.html")
    tmp_shot = Path(output_png_path).with_suffix(".tmp.png")

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  html, body {{
    margin: 0;
    padding: 0;
    width: {width}px;
    height: {height}px;
    overflow: hidden;
    background: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  }}
  svg {{
    width: {width}px;
    height: {height}px;
    display: block;
  }}
</style>
</head>
<body>
{svg_content}
</body>
</html>"""

    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html)

    cmd = [
        browser,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        f"--screenshot={str(tmp_shot)}",
        f"file:///{str(tmp_html).replace(os.sep, '/')}",
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if res.returncode != 0 or not tmp_shot.exists():
        raise RuntimeError(f"Browser screenshot failed: {res.stderr}")

    if Path(output_png_path).exists():
        os.remove(output_png_path)
    shutil.move(str(tmp_shot), str(output_png_path))

    if tmp_html.exists():
        os.remove(tmp_html)

    print(f"Generated: {output_png_path} ({width}x{height})")


# ==============================================================================
# SVG DEFINITIONS - LIGHT THEME (Pristine, Modern, Glassmorphic, Technical)
# ==============================================================================

def get_hero_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F8FAFC" />
      <stop offset="50%" stop-color="#F1F5F9" />
      <stop offset="100%" stop-color="#E2E8F0" />
    </linearGradient>
    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0284C7" />
      <stop offset="50%" stop-color="#2563EB" />
      <stop offset="100%" stop-color="#059669" />
    </linearGradient>
    <linearGradient id="shieldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0EA5E9" stop-opacity="0.2" />
      <stop offset="100%" stop-color="#10B981" stop-opacity="0.1" />
    </linearGradient>
    <filter id="cardShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="12" stdDeviation="16" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="1200" height="630" fill="url(#bgGrad)" />

  <!-- Technical Grid Background -->
  <g stroke="#CBD5E1" stroke-width="0.75" stroke-dasharray="4,4" opacity="0.6">
    <line x1="100" y1="0" x2="100" y2="630" />
    <line x1="300" y1="0" x2="300" y2="630" />
    <line x1="500" y1="0" x2="500" y2="630" />
    <line x1="700" y1="0" x2="700" y2="630" />
    <line x1="900" y1="0" x2="900" y2="630" />
    <line x1="1100" y1="0" x2="1100" y2="630" />
    <line x1="0" y1="100" x2="1200" y2="100" />
    <line x1="0" y1="200" x2="1200" y2="200" />
    <line x1="0" y1="315" x2="1200" y2="315" />
    <line x1="0" y1="430" x2="1200" y2="430" />
    <line x1="0" y1="530" x2="1200" y2="530" />
  </g>

  <!-- Decorative Ambient Glows -->
  <circle cx="200" cy="180" r="140" fill="#38BDF8" opacity="0.12" filter="blur(60px)" />
  <circle cx="1000" cy="380" r="160" fill="#34D399" opacity="0.12" filter="blur(60px)" />

  <!-- Brand Eyebrow Badge -->
  <g transform="translate(80, 50)">
    <rect width="330" height="36" rx="18" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#cardShadow)" />
    <circle cx="20" cy="18" r="6" fill="#10B981" />
    <text x="36" y="23" font-size="13" font-weight="700" fill="#0F172A" letter-spacing="1.2">ENTERPRISE AI SECURITY FABRIC</text>
  </g>

  <!-- Title & Subtitle -->
  <text x="80" y="145" font-size="46" font-weight="800" fill="#0F172A" letter-spacing="-0.8">SENTINEL AI FABRIC</text>
  <text x="80" y="195" font-size="20" font-weight="500" fill="#475569" letter-spacing="-0.2">
    Risk-Driven Multi-Tenant RAG • Governed Autonomous Agent • Vector ETL
  </text>

  <!-- Central Visual Diagram Architecture Shield (Glassmorphic) -->
  <g transform="translate(680, 80)">
    <!-- Base Shield Backdrop -->
    <path d="M 220 30 Q 380 40 420 180 Q 420 340 220 440 Q 20 340 20 180 Q 60 40 220 30 Z"
          fill="url(#shieldGrad)" stroke="#0284C7" stroke-width="2" filter="url(#cardShadow)" />

    <!-- Concentric Technical Rings -->
    <circle cx="220" cy="220" r="140" fill="none" stroke="#0EA5E9" stroke-width="1.5" stroke-dasharray="8,6" opacity="0.7" />
    <circle cx="220" cy="220" r="90" fill="#FFFFFF" stroke="#0284C7" stroke-width="2" filter="url(#cardShadow)" />
    
    <!-- Central Shield Emblem -->
    <path d="M 220 170 L 260 190 V 230 C 260 260 220 280 220 280 C 220 280 180 260 180 230 V 190 Z"
          fill="#0284C7" opacity="0.9" />
    <path d="M 210 225 L 218 233 L 234 217" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />

    <!-- Satellite Nodes -->
    <g transform="translate(220, 60)">
      <circle cx="0" cy="0" r="28" fill="#FFFFFF" stroke="#2563EB" stroke-width="2" filter="url(#cardShadow)" />
      <text x="0" y="5" font-size="11" font-weight="700" fill="#2563EB" text-anchor="middle">ETL</text>
    </g>
    <g transform="translate(370, 220)">
      <circle cx="0" cy="0" r="28" fill="#FFFFFF" stroke="#059669" stroke-width="2" filter="url(#cardShadow)" />
      <text x="0" y="5" font-size="11" font-weight="700" fill="#059669" text-anchor="middle">RAG</text>
    </g>
    <g transform="translate(220, 380)">
      <circle cx="0" cy="0" r="28" fill="#FFFFFF" stroke="#D97706" stroke-width="2" filter="url(#cardShadow)" />
      <text x="0" y="5" font-size="10" font-weight="700" fill="#D97706" text-anchor="middle">AGENT</text>
    </g>
    <g transform="translate(70, 220)">
      <circle cx="0" cy="0" r="28" fill="#FFFFFF" stroke="#7C3AED" stroke-width="2" filter="url(#cardShadow)" />
      <text x="0" y="5" font-size="10" font-weight="700" fill="#7C3AED" text-anchor="middle">AUTH</text>
    </g>
  </g>

  <!-- 4 Feature Cards (Glassmorphic Light Theme) -->
  <g transform="translate(80, 240)">
    <!-- Card 1: Vector ETL -->
    <rect x="0" y="0" width="260" height="150" rx="14" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#cardShadow)" />
    <rect x="18" y="16" width="36" height="36" rx="8" fill="#E0F2FE" />
    <text x="36" y="40" font-size="18" font-weight="700" fill="#0284C7" text-anchor="middle">⚡</text>
    <text x="18" y="78" font-size="16" font-weight="700" fill="#0F172A">Legacy Data ETL</text>
    <text x="18" y="102" font-size="13" font-weight="400" fill="#64748B">PDF, CSV &amp; Markdown ingestion</text>
    <text x="18" y="122" font-size="13" font-weight="400" fill="#64748B">with exact page &amp; row provenance.</text>

    <!-- Card 2: Adversarial RAG -->
    <rect x="280" y="0" width="260" height="150" rx="14" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#cardShadow)" />
    <rect x="298" y="16" width="36" height="36" rx="8" fill="#ECFDF5" />
    <text x="316" y="40" font-size="18" font-weight="700" fill="#059669" text-anchor="middle">🛡️</text>
    <text x="298" y="78" font-size="16" font-weight="700" fill="#0F172A">Adversarial RAG</text>
    <text x="298" y="102" font-size="13" font-weight="400" fill="#64748B">Zero-trust tenant isolation, hybrid</text>
    <text x="298" y="122" font-size="13" font-weight="400" fill="#64748B">BM25 + Chroma, verified citations.</text>

    <!-- Card 3: Governed Agent -->
    <rect x="0" y="170" width="260" height="150" rx="14" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#cardShadow)" />
    <rect x="18" y="186" width="36" height="36" rx="8" fill="#FEF3C7" />
    <text x="36" y="210" font-size="18" font-weight="700" fill="#D97706" text-anchor="middle">⚙️</text>
    <text x="18" y="248" font-size="16" font-weight="700" fill="#0F172A">Governed Agent</text>
    <text x="18" y="272" font-size="13" font-weight="400" fill="#64748B">Mock ERP/CRM tool execution with</text>
    <text x="18" y="292" font-size="13" font-weight="400" fill="#64748B">two-phase HMAC write approvals.</text>

    <!-- Card 4: Observability -->
    <rect x="280" y="170" width="260" height="150" rx="14" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#cardShadow)" />
    <rect x="298" y="186" width="36" height="36" rx="8" fill="#F3E8FF" />
    <text x="316" y="210" font-size="18" font-weight="700" fill="#7C3AED" text-anchor="middle">📊</text>
    <text x="298" y="248" font-size="16" font-weight="700" fill="#0F172A">Observability</text>
    <text x="298" y="272" font-size="13" font-weight="400" fill="#64748B">Prometheus metrics, JSON traces,</text>
    <text x="298" y="292" font-size="13" font-weight="400" fill="#64748B">non-root hardened Docker runtime.</text>
  </g>

  <!-- Bottom Verification Pill Bar -->
  <g transform="translate(80, 580)">
    <text x="0" y="0" font-size="12" font-weight="600" fill="#10B981">✓ 30 Atomic Commits</text>
    <text x="170" y="0" font-size="12" font-weight="600" fill="#0284C7">✓ 10/10 Adversarial Gates Passed</text>
    <text x="400" y="0" font-size="12" font-weight="600" fill="#6366F1">✓ 100% Citation Grounding</text>
    <text x="610" y="0" font-size="12" font-weight="600" fill="#059669">✓ 12.7ms p50 Retrieval</text>
  </g>
</svg>"""


def get_architecture_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bgArch" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" />
      <stop offset="100%" stop-color="#F1F5F9" />
    </linearGradient>
    <filter id="shadowLight">
      <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#0F172A" flood-opacity="0.05" />
    </filter>
  </defs>

  <rect width="1200" height="630" fill="url(#bgArch)" />

  <!-- Section Header -->
  <text x="60" y="55" font-size="13" font-weight="700" fill="#0284C7" letter-spacing="1.5">END-TO-END SYSTEM ARCHITECTURE</text>
  <text x="60" y="95" font-size="32" font-weight="800" fill="#0F172A">Four Integrated Zero-Trust Workstreams</text>

  <!-- Workstream A Box -->
  <g transform="translate(60, 130)">
    <rect width="250" height="440" rx="16" fill="#FFFFFF" stroke="#0284C7" stroke-width="2" filter="url(#shadowLight)" />
    <rect x="0" y="0" width="250" height="50" rx="16" fill="#E0F2FE" />
    <text x="20" y="32" font-size="15" font-weight="700" fill="#0369A1">A: Ingestion &amp; Vector ETL</text>

    <!-- Sub-steps -->
    <rect x="18" y="70" width="214" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="96" font-size="12" font-weight="600" fill="#334155">1. PDF / CSV / Markdown</text>

    <rect x="18" y="125" width="214" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="151" font-size="12" font-weight="600" fill="#334155">2. Structure-Aware Chunker</text>

    <rect x="18" y="180" width="214" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="206" font-size="12" font-weight="600" fill="#334155">3. SHA-256 Provenance</text>

    <rect x="18" y="235" width="214" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="261" font-size="12" font-weight="600" fill="#334155">4. Deduplication Filter</text>

    <rect x="18" y="290" width="214" height="60" rx="8" fill="#F0FDF4" stroke="#86EFAC" />
    <text x="30" y="315" font-size="12" font-weight="700" fill="#15803D">ChromaDB Persistent</text>
    <text x="30" y="335" font-size="11" font-weight="500" fill="#16A34A">+ Okapi BM25 Index</text>

    <text x="20" y="415" font-size="11" font-weight="600" fill="#64748B">Throughput: 17.7 docs/s</text>
  </g>

  <!-- Flow Arrow 1 -->
  <path d="M 320 350 L 340 350" stroke="#0284C7" stroke-width="3" stroke-linecap="round" marker-end="url(#arrow)" />

  <!-- Workstream B Box -->
  <g transform="translate(350, 130)">
    <rect width="250" height="440" rx="16" fill="#FFFFFF" stroke="#10B981" stroke-width="2" filter="url(#shadowLight)" />
    <rect x="0" y="0" width="250" height="50" rx="16" fill="#ECFDF5" />
    <text x="20" y="32" font-size="15" font-weight="700" fill="#047857">B: Adversarial RAG</text>

    <rect x="18" y="70" width="214" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="96" font-size="12" font-weight="600" fill="#334155">1. Zero-Trust Auth Guard</text>

    <rect x="18" y="125" width="214" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="151" font-size="12" font-weight="600" fill="#334155">2. Query Sanitizer</text>

    <rect x="18" y="180" width="214" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="206" font-size="12" font-weight="600" fill="#334155">3. Hybrid RRF Retrieval</text>

    <rect x="18" y="235" width="214" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="261" font-size="12" font-weight="600" fill="#334155">4. Cross-Encoder Rerank</text>

    <rect x="18" y="290" width="214" height="60" rx="8" fill="#FEF3C7" stroke="#FDE68A" />
    <text x="30" y="315" font-size="12" font-weight="700" fill="#B45309">Citation Grounding</text>
    <text x="30" y="335" font-size="11" font-weight="500" fill="#D97706">Abstain if score &lt; 0.45</text>

    <text x="20" y="415" font-size="11" font-weight="600" fill="#64748B">p50 Latency: 12.7 ms</text>
  </g>

  <!-- Flow Arrow 2 -->
  <path d="M 610 350 L 630 350" stroke="#10B981" stroke-width="3" stroke-linecap="round" />

  <!-- Workstream C Box -->
  <g transform="translate(640, 130)">
    <rect width="250" height="440" rx="16" fill="#FFFFFF" stroke="#F59E0B" stroke-width="2" filter="url(#shadowLight)" />
    <rect x="0" y="0" width="250" height="50" rx="16" fill="#FFFBEB" />
    <text x="20" y="32" font-size="15" font-weight="700" fill="#B45309">C: Governed Agent</text>

    <rect x="18" y="70" width="214" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="96" font-size="12" font-weight="600" fill="#334155">1. Typed Tool Registry</text>

    <rect x="18" y="125" width="214" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="151" font-size="12" font-weight="600" fill="#334155">2. Pydantic Validation</text>

    <rect x="18" y="180" width="214" height="42" rx="8" fill="#FEE2E2" stroke="#FCA5A5" />
    <text x="30" y="206" font-size="12" font-weight="700" fill="#B91C1C">3. State-Changing Gate</text>

    <rect x="18" y="235" width="214" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="261" font-size="12" font-weight="600" fill="#334155">4. HMAC-SHA256 Token</text>

    <rect x="18" y="290" width="214" height="60" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="30" y="315" font-size="12" font-weight="700" fill="#334155">Mock ERP/CRM Actions</text>
    <text x="30" y="335" font-size="11" font-weight="500" fill="#64748B">Single-use replay defense</text>

    <text x="20" y="415" font-size="11" font-weight="600" fill="#64748B">Zero Replay Violations</text>
  </g>

  <!-- Flow Arrow 3 -->
  <path d="M 900 350 L 920 350" stroke="#F59E0B" stroke-width="3" stroke-linecap="round" />

  <!-- Workstream D Box -->
  <g transform="translate(930, 130)">
    <rect width="210" height="440" rx="16" fill="#FFFFFF" stroke="#8B5CF6" stroke-width="2" filter="url(#shadowLight)" />
    <rect x="0" y="0" width="210" height="50" rx="16" fill="#F5F3FF" />
    <text x="16" y="32" font-size="15" font-weight="700" fill="#6D28D9">D: Observability</text>

    <rect x="14" y="70" width="182" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="24" y="96" font-size="12" font-weight="600" fill="#334155">FastAPI Gateway</text>

    <rect x="14" y="125" width="182" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="24" y="151" font-size="12" font-weight="600" fill="#334155">Prometheus /metrics</text>

    <rect x="14" y="180" width="182" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="24" y="206" font-size="12" font-weight="600" fill="#334155">X-Correlation-ID</text>

    <rect x="14" y="235" width="182" height="42" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="24" y="261" font-size="12" font-weight="600" fill="#334155">Redacted JSON Logs</text>

    <rect x="14" y="290" width="182" height="60" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="24" y="315" font-size="12" font-weight="700" fill="#334155">Non-Root Docker</text>
    <text x="24" y="335" font-size="11" font-weight="500" fill="#64748B">UID 10001 (Hardened)</text>

    <text x="16" y="415" font-size="11" font-weight="600" fill="#64748B">Ready Probes: 100%</text>
  </g>
</svg>"""


def get_governance_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bgGov" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#F8FAFC" />
      <stop offset="100%" stop-color="#E2E8F0" />
    </linearGradient>
    <filter id="cardGlow">
      <feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
  </defs>

  <rect width="1200" height="630" fill="url(#bgGov)" />

  <!-- Header -->
  <text x="60" y="55" font-size="13" font-weight="700" fill="#D97706" letter-spacing="1.5">GOVERNANCE &amp; POLICY CONTROLS</text>
  <text x="60" y="95" font-size="32" font-weight="800" fill="#0F172A">Two-Phase Cryptographic Approval Gate</text>

  <!-- Flow Steps -->
  <!-- Step 1 -->
  <g transform="translate(60, 140)">
    <rect width="320" height="200" rx="16" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#cardGlow)" />
    <circle cx="40" cy="40" r="18" fill="#E0F2FE" />
    <text x="40" y="46" font-size="14" font-weight="800" fill="#0284C7" text-anchor="middle">1</text>
    <text x="75" y="45" font-size="16" font-weight="700" fill="#0F172A">State-Change Intercepted</text>
    <text x="25" y="85" font-size="13" font-weight="400" fill="#475569">Agent classifies operation as</text>
    <text x="25" y="105" font-size="13" font-weight="600" fill="#B91C1C">STATE_CHANGING (e.g. Lead update).</text>
    <rect x="25" y="130" width="270" height="45" rx="8" fill="#F8FAFC" stroke="#E2E8F0" />
    <text x="35" y="158" font-size="12" font-family="monospace" fill="#0369A1">requires_approval = True</text>
  </g>

  <!-- Step 2 -->
  <g transform="translate(440, 140)">
    <rect width="320" height="200" rx="16" fill="#FFFFFF" stroke="#F59E0B" stroke-width="2" filter="url(#cardGlow)" />
    <circle cx="40" cy="40" r="18" fill="#FEF3C7" />
    <text x="40" y="46" font-size="14" font-weight="800" fill="#D97706" text-anchor="middle">2</text>
    <text x="75" y="45" font-size="16" font-weight="700" fill="#0F172A">HMAC Signature Binding</text>
    <text x="25" y="85" font-size="13" font-weight="400" fill="#475569">Generates cryptographic signature</text>
    <text x="25" y="105" font-size="13" font-weight="400" fill="#475569">bound to arguments + expiry (15m).</text>
    <rect x="25" y="130" width="270" height="45" rx="8" fill="#FFFBEB" stroke="#FDE68A" />
    <text x="35" y="158" font-size="11" font-family="monospace" fill="#B45309">HMAC(op_id, arg_hash, exp)</text>
  </g>

  <!-- Step 3 -->
  <g transform="translate(820, 140)">
    <rect width="320" height="200" rx="16" fill="#FFFFFF" stroke="#10B981" stroke-width="2" filter="url(#cardGlow)" />
    <circle cx="40" cy="40" r="18" fill="#ECFDF5" />
    <text x="40" y="46" font-size="14" font-weight="800" fill="#059669" text-anchor="middle">3</text>
    <text x="75" y="45" font-size="16" font-weight="700" fill="#0F172A">Replay-Guarded Execution</text>
    <text x="25" y="85" font-size="13" font-weight="400" fill="#475569">Token submitted to /approvals endpoint.</text>
    <text x="25" y="105" font-size="13" font-weight="600" fill="#15803D">Permanently consumed upon write.</text>
    <rect x="25" y="130" width="270" height="45" rx="8" fill="#F0FDF4" stroke="#BBF7D0" />
    <text x="35" y="158" font-size="12" font-family="monospace" fill="#166534">is_executed: True (No Replay)</text>
  </g>

  <!-- Lower Panel: Security Clearance Ladder -->
  <g transform="translate(60, 380)">
    <rect width="1080" height="190" rx="16" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#cardGlow)" />
    <text x="30" y="35" font-size="14" font-weight="700" fill="#0F172A">HIERARCHICAL CLEARANCE BOUNDARIES (OUTSIDE-THE-LLM)</text>

    <!-- 5 Levels -->
    <g transform="translate(30, 60)">
      <!-- Public -->
      <rect x="0" y="0" width="190" height="85" rx="10" fill="#F8FAFC" stroke="#CBD5E1" />
      <text x="20" y="32" font-size="13" font-weight="700" fill="#475569">PUBLIC (0)</text>
      <text x="20" y="58" font-size="11" fill="#64748B">General announcements</text>

      <!-- Internal -->
      <rect x="205" y="0" width="190" height="85" rx="10" fill="#F0FDF4" stroke="#86EFAC" />
      <text x="225" y="32" font-size="13" font-weight="700" fill="#15803D">INTERNAL (1)</text>
      <text x="225" y="58" font-size="11" fill="#166534">Employee handbooks</text>

      <!-- Confidential -->
      <rect x="410" y="0" width="190" height="85" rx="10" fill="#EFF6FF" stroke="#93C5FD" />
      <text x="430" y="32" font-size="13" font-weight="700" fill="#1E40AF">CONFIDENTIAL (2)</text>
      <text x="430" y="58" font-size="11" fill="#1D4ED8">Department financials</text>

      <!-- Secret -->
      <rect x="615" y="0" width="190" height="85" rx="10" fill="#FFFBEB" stroke="#FCD34D" />
      <text x="635" y="32" font-size="13" font-weight="700" fill="#B45309">SECRET (3)</text>
      <text x="635" y="58" font-size="11" fill="#92400E">C-Suite payroll, strategy</text>

      <!-- Top Secret -->
      <rect x="820" y="0" width="200" height="85" rx="10" fill="#FEF2F2" stroke="#FCA5A5" />
      <text x="840" y="32" font-size="13" font-weight="700" fill="#991B1B">TOP SECRET (4)</text>
      <text x="840" y="58" font-size="11" fill="#B91C1C">Proprietary M&amp;A, ciphers</text>
    </g>

    <text x="30" y="168" font-size="11" font-weight="600" fill="#64748B">Rule: User clearance rank must be >= document clearance rank. Checked prior to database retrieval.</text>
  </g>
</svg>"""


def get_linkedin_banner_svg() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bgLinkedIn" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" />
      <stop offset="60%" stop-color="#F8FAFC" />
      <stop offset="100%" stop-color="#EDF2F7" />
    </linearGradient>
    <linearGradient id="primaryGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#0284C7" />
      <stop offset="100%" stop-color="#059669" />
    </linearGradient>
    <filter id="bannerShadow">
      <feDropShadow dx="0" dy="16" stdDeviation="20" flood-color="#0F172A" flood-opacity="0.08" />
    </filter>
  </defs>

  <rect width="1200" height="630" fill="url(#bgLinkedIn)" />

  <!-- Subtle Ambient Glow -->
  <circle cx="1050" cy="120" r="220" fill="#0284C7" opacity="0.08" filter="blur(80px)" />
  <circle cx="150" cy="500" r="200" fill="#10B981" opacity="0.08" filter="blur(80px)" />

  <!-- Top Badge -->
  <g transform="translate(60, 50)">
    <rect width="270" height="34" rx="17" fill="#E0F2FE" />
    <text x="135" y="22" font-size="12" font-weight="700" fill="#0369A1" text-anchor="middle" letter-spacing="1.2">
      ENTERPRISE AI PLATFORM
    </text>
  </g>

  <!-- Title & Headline -->
  <text x="60" y="145" font-size="44" font-weight="800" fill="#0F172A" letter-spacing="-0.8">
    Sentinel Enterprise AI Fabric
  </text>
  <text x="60" y="195" font-size="20" font-weight="500" fill="#475569">
    Zero-Trust Multi-Tenant RAG &amp; Governed Autonomous ERP/CRM Agent
  </text>

  <!-- 4 Stat Metric Cards (Light Theme Hero Presentation) -->
  <g transform="translate(60, 240)">
    <!-- Stat 1 -->
    <rect x="0" y="0" width="250" height="140" rx="14" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#bannerShadow)" />
    <text x="24" y="55" font-size="34" font-weight="800" fill="#0284C7">12.7 ms</text>
    <text x="24" y="90" font-size="14" font-weight="700" fill="#0F172A">p50 Retrieval Latency</text>
    <text x="24" y="115" font-size="12" font-weight="400" fill="#64748B">Hybrid BM25 + ChromaDB</text>

    <!-- Stat 2 -->
    <rect x="275" y="0" width="250" height="140" rx="14" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#bannerShadow)" />
    <text x="299" y="55" font-size="34" font-weight="800" fill="#059669">100%</text>
    <text x="299" y="90" font-size="14" font-weight="700" fill="#0F172A">Citation Precision</text>
    <text x="299" y="115" font-size="12" font-weight="400" fill="#64748B">Zero phantom citations</text>

    <!-- Stat 3 -->
    <rect x="550" y="0" width="250" height="140" rx="14" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#bannerShadow)" />
    <text x="574" y="55" font-size="34" font-weight="800" fill="#D97706">10 / 10</text>
    <text x="574" y="90" font-size="14" font-weight="700" fill="#0F172A">Adversarial Gates</text>
    <text x="574" y="115" font-size="12" font-weight="400" fill="#64748B">Injection &amp; tenant isolation</text>

    <!-- Stat 4 -->
    <rect x="825" y="0" width="250" height="140" rx="14" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#bannerShadow)" />
    <text x="849" y="55" font-size="34" font-weight="800" fill="#7C3AED">30</text>
    <text x="849" y="90" font-size="14" font-weight="700" fill="#0F172A">Atomic Git Commits</text>
    <text x="849" y="115" font-size="12" font-weight="400" fill="#64748B">Pushed over SSH to main</text>
  </g>

  <!-- Key Architecture Bullets -->
  <g transform="translate(60, 420)">
    <rect width="1075" height="120" rx="14" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" filter="url(#bannerShadow)" />
    <text x="30" y="38" font-size="15" font-weight="700" fill="#0F172A">ENGINEERED FOR PRODUCTION ENVIRONMENTS</text>
    <text x="30" y="70" font-size="13" font-weight="500" fill="#475569">
      • Workstream A: PDF, CSV, Markdown ETL with page/row provenance tracking
    </text>
    <text x="30" y="95" font-size="13" font-weight="500" fill="#475569">
      • Workstream B: Adversarial RAG with Reciprocal Rank Fusion &amp; evidence-aware safe abstention
    </text>
    <text x="580" y="70" font-size="13" font-weight="500" fill="#475569">
      • Workstream C: Governed autonomous agent with HMAC-SHA256 write approval gates
    </text>
    <text x="580" y="95" font-size="13" font-weight="500" fill="#475569">
      • Workstream D: Hardened non-root Docker runtime with Prometheus &amp; JSON correlation IDs
    </text>
  </g>

  <!-- Footer Branding -->
  <text x="60" y="590" font-size="13" font-weight="600" fill="#94A3B8">
    Python 3.12 • FastAPI • ChromaDB • BM25 • Docker Compose • Prometheus • Apache 2.0
  </text>
</svg>"""


def main():
    root = Path(__file__).parent.parent
    assets_dir = root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    print("Generating Sentinel light-theme visual assets...")
    
    # 1. Hero Banner
    render_svg_to_png(get_hero_svg(), str(assets_dir / "sentinel_hero_light.png"), 1200, 630)

    # 2. System Architecture Visual
    render_svg_to_png(get_architecture_svg(), str(assets_dir / "sentinel_architecture_light.png"), 1200, 630)

    # 3. Governance Visual
    render_svg_to_png(get_governance_svg(), str(assets_dir / "sentinel_governance_light.png"), 1200, 630)

    # 4. LinkedIn Showcase Image (root image.png)
    render_svg_to_png(get_linkedin_banner_svg(), str(root / "image.png"), 1200, 630)

    print("All light-theme images generated successfully!")


if __name__ == "__main__":
    main()

from flask import Flask
from threading import Thread
import os

app = Flask('')

# ---------- Shared CSS/HTML helpers ----------

BASE_STYLE = """
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Inter', sans-serif;
    background: #0a0a0f;
    color: #e8e8f0;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }
  /* animated mesh background */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background:
      radial-gradient(ellipse 80% 60% at 20% 10%, rgba(88,101,242,.18) 0%, transparent 60%),
      radial-gradient(ellipse 60% 80% at 80% 80%, rgba(88,101,242,.10) 0%, transparent 60%),
      radial-gradient(ellipse 50% 50% at 50% 50%, rgba(10,10,15,1) 100%, transparent);
    z-index: -1;
    animation: pulse 8s ease-in-out infinite alternate;
  }
  @keyframes pulse {
    from { opacity: .7; }
    to   { opacity: 1; }
  }
  .card {
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 52px 56px;
    max-width: 520px;
    width: 92%;
    text-align: center;
    box-shadow: 0 8px 48px rgba(0,0,0,.5);
    animation: rise .6s cubic-bezier(.22,1,.36,1) both;
  }
  @keyframes rise {
    from { opacity:0; transform: translateY(28px); }
    to   { opacity:1; transform: translateY(0); }
  }
  .icon { font-size: 3.5rem; margin-bottom: 20px; }
  h1 {
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: -.03em;
    margin-bottom: 12px;
    background: linear-gradient(135deg, #5865F2, #4752C4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  p {
    font-size: 1.05rem;
    font-weight: 600;
    color: rgba(232,232,240,.65);
    line-height: 1.6;
  }
  .badge {
    display: inline-block;
    margin-top: 28px;
    padding: 8px 22px;
    border-radius: 999px;
    background: rgba(88,101,242,.15);
    border: 1px solid rgba(88,101,242,.35);
    font-size: .85rem;
    font-weight: 700;
    color: #5865F2;
    letter-spacing: .04em;
    text-transform: uppercase;
  }
  .footer {
    position: fixed;
    bottom: 32px;
    font-size: 0.95rem;
    font-weight: 600;
  }
  .footer a {
    color: rgba(232,232,240,.4);
    text-decoration: none;
    display: flex;
    align-items: center;
    gap: 10px;
    transition: all 0.3s ease;
  }
  .footer a:hover {
    color: rgba(232,232,240,.9);
    transform: translateY(-2px);
  }
  .footer svg {
    width: 24px;
    height: 24px;
    fill: currentColor;
  }
"""

def _page(title, icon, heading, body_html, extra_class=""):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>{title}</title>
      <style>{BASE_STYLE}</style>
    </head>
    <body>
      <div class="card {extra_class}">
        <div class="icon">{icon}</div>
        <h1>{heading}</h1>
        {body_html}
      </div>
      <div class="footer">
        <a href="https://github.com/vola727/wpmdiscordbot" target="_blank" rel="noopener noreferrer">
          <svg viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
          vola727 / wpmdiscordbot
        </a>
      </div>
    </body>
    </html>
    """

# ---------- Routes ----------

@app.route('/')
def home():
    return _page(
        title="TypeRace Bot • Online",
        icon="⌨️",
        heading="Bot is Online",
        body_html='''
          <p>Your TypeRace Discord bot is running smoothly and ready for some typing challenges.</p>
          <span class="badge">✓ All systems operational</span>
        '''
    )

def run():
    # Render binds dynamic port to OS, default to 8080 if locally testing
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

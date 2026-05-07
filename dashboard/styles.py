"""dashboard/styles.py — CSS Styles for the Dashboard"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html,body,.stApp{font-family:'Inter',sans-serif;background:#0f172a;}
.kcard{background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid rgba(99,102,241,.3);
 border-radius:14px;padding:20px;text-align:center;transition:.25s;margin-bottom:8px;}
.kcard:hover{transform:translateY(-3px);box-shadow:0 8px 24px rgba(99,102,241,.2);}
.kval{font-size:1.7rem;font-weight:800;background:linear-gradient(135deg,#a5b4fc,#6366f1);
 -webkit-background-clip:text;-webkit-text-fill-color:transparent;}
.klbl{font-size:.72rem;color:#94a3b8;margin-top:4px;text-transform:uppercase;letter-spacing:1px;}
.sh{font-size:1.1rem;font-weight:700;color:#e2e8f0;border-left:4px solid #6366f1;
 padding-left:10px;margin:20px 0 10px;}
.abc-a{background:#064e3b;color:#34d399;border-radius:6px;padding:2px 8px;font-size:.75rem;font-weight:700;}
.abc-b{background:#1e3a5f;color:#60a5fa;border-radius:6px;padding:2px 8px;font-size:.75rem;font-weight:700;}
.abc-c{background:#3b1f2b;color:#f472b6;border-radius:6px;padding:2px 8px;font-size:.75rem;font-weight:700;}
</style>
"""

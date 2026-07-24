import sqlite3, os, json, hashlib, hmac, uuid, time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
DB_PATH = os.path.join(os.path.dirname(__file__), "licencias.db")
SECRET_KEY = b"cambiame_por_una_clave_segura_32bytes!"

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head><title>Panel Licencias</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',-apple-system,sans-serif;background:#f0f2f5;color:#1a1a2e;min-height:100vh}
.navbar{background:#fff;border-bottom:1px solid #e5e7eb;padding:0 24px;display:flex;align-items:center;height:56px;box-shadow:0 1px 3px rgba(0,0,0,0.04)}
.navbar-brand{font-weight:700;font-size:16px;color:#1a1a2e;display:flex;align-items:center;gap:8px;text-decoration:none;margin-right:32px}
.navbar-brand::before{content:"🔑";font-size:18px}
.navbar-nav{display:flex;align-items:center;gap:4px;flex:1}
.navbar-nav a{padding:8px 14px;border-radius:6px;font-size:13px;font-weight:500;color:#6b7280;text-decoration:none;transition:all .15s}
.navbar-nav a:hover{background:#f3f4f6;color:#1a1a2e}
.navbar-nav a.active{background:#eef2ff;color:#4f46e5}
.navbar-end{margin-left:auto}
.wrapper{max-width:1000px;margin:24px auto;padding:0 20px}
.card{background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);overflow:hidden}
.card-body{padding:20px 24px 24px}
.login-box{max-width:340px;margin:60px auto}
.login-box h2{font-size:20px;font-weight:700;margin-bottom:4px}
.login-box p{color:#6b7280;font-size:14px;margin-bottom:20px}
.input-group{display:flex;flex-direction:column;gap:10px}
.input-group input{padding:10px 14px;border:1px solid #e5e7eb;border-radius:8px;font-size:14px;font-family:inherit;background:#f9fafb;transition:border .2s,box-shadow .2s;outline:none}
.input-group input:focus{border-color:#6366f1;box-shadow:0 0 0 3px rgba(99,102,241,0.1);background:#fff}
.top-bar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px}
.top-bar-left{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.top-bar-left select{padding:8px 12px;border:1px solid #e5e7eb;border-radius:8px;font-size:13px;font-family:inherit;background:#f9fafb;outline:none;cursor:pointer}
.top-bar-left select:focus{border-color:#6366f1}
.badge{padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;display:inline-block}
.badge-activa{background:#d1fae5;color:#065f46}
.badge-suspendida{background:#fee2e2;color:#991b1b}
table{width:100%;border-collapse:collapse;font-size:13px}
thead th{padding:10px 12px;text-align:left;font-weight:600;color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #f3f4f6;background:#fafafa;white-space:nowrap}
tbody tr{transition:background .1s}
tbody tr:hover{background:#f9fafb}
tbody td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
td code{font-size:12px;background:#f3f4f6;padding:2px 8px;border-radius:4px;word-break:break-all;font-family:'SF Mono',Consolas,monospace}
.actions{display:flex;gap:4px;flex-wrap:wrap;align-items:center}
.actions a{text-decoration:none}
.check-col{width:36px;text-align:center}
.btn{display:inline-flex;align-items:center;gap:4px;padding:6px 12px;border-radius:6px;font-size:12px;font-weight:500;font-family:inherit;border:none;cursor:pointer;transition:all .15s;text-decoration:none;white-space:nowrap}
.btn-primary{background:#6366f1;color:#fff}
.btn-primary:hover{background:#4f46e5}
.btn-success{background:#10b981;color:#fff}
.btn-success:hover{background:#059669}
.btn-danger{background:#ef4444;color:#fff}
.btn-danger:hover{background:#dc2626}
.btn-outline{background:transparent;color:#6b7280;border:1px solid #e5e7eb}
.btn-outline:hover{background:#f3f4f6;border-color:#d1d5db}
.btn-sm{padding:4px 10px;font-size:11px}
.alert{padding:12px 16px;background:#d1fae5;border:1px solid #a7f3d0;border-radius:8px;margin-bottom:16px;color:#065f46;font-size:13px;display:flex;align-items:center;gap:8px}
.alert::before{content:"\2713";font-weight:700;font-size:16px}
.empty-state{text-align:center;padding:40px 20px;color:#9ca3af;font-size:14px}
.empty-state::before{content:"\1F4CB";display:block;font-size:32px;margin-bottom:8px}
</style></head>
<body>
{% if session.get('logged_in') %}
<nav class="navbar">
<a href="/admin/" class="navbar-brand">Licencias</a>
<div class="navbar-nav">
<a href="/admin/" class="active">Licencias</a>
</div>
<div class="navbar-end">
<a href="/admin/logout" class="btn btn-outline btn-sm">Cerrar sesi&oacute;n</a>
</div>
</nav>
{% endif %}
<div class="wrapper">
<div class="card">
<div class="card-body">
{% if not session.get('logged_in') %}
<div class="login-box">
<h2>Iniciar sesi&oacute;n</h2>
<p>Ingrese sus credenciales de administrador</p>
<form method="post" action="/admin/login" class="input-group">
<input type="text" name="username" placeholder="Usuario" required autofocus>
<input type="password" name="password" placeholder="Contrase&ntilde;a" required>
<button class="btn btn-primary" style="padding:10px;justify-content:center;font-size:14px">Ingresar</button>
</form>
</div>
{% else %}
<div class="top-bar">
<div class="top-bar-left">
<form method="post" action="/admin/crear" style="display:flex;align-items:center;gap:8px">
<select name="dias">
<option value="30">30 d&iacute;as</option>
<option value="90">90 d&iacute;as</option>
<option value="365" selected>1 a&ntilde;o</option>
<option value="0">Ilimitado</option>
</select>
<button class="btn btn-success">+ Crear Licencia</button>
</form>
</div>
<form method="post" action="/admin/eliminar_masivo" onsubmit="return confirm('Eliminar licencias seleccionadas?')">
<button class="btn btn-danger btn-sm" id="deleteSelected" disabled>Eliminar seleccionadas</button>
</div>
{% if msg %}<div class="alert">{{ msg }}</div>{% endif %}
{% if licencias %}
<table>
<thead><tr>
<th class="check-col"><input type="checkbox" id="selectAll" onchange="toggleAll(this)"></th>
<th>ID</th><th>Clave</th><th>HW ID</th><th>Vencimiento</th><th>Estado</th><th>Acci&oacute;n</th>
</tr></thead>
<tbody>
{% for l in licencias %}
{% set estado = 'activa' if l[3]==1 else 'suspendida' %}
{% set badge = 'badge-activa' if estado=='activa' else 'badge-suspendida' %}
<tr>
<td class="check-col"><input type="checkbox" name="ids" value="{{ l[0] }}" onchange="updateDeleteBtn()"></td>
<td style="font-weight:600;color:#6b7280">{{ l[0] }}</td>
<td><code>{{ l[1][:20] }}...</code></td>
<td><code>{{ l[2][:12] if l[2] else '-' }}</code></td>
<td>{{ l[4][:10] if l[4] else 'Ilimitado' }}</td>
<td><span class="badge {{ badge }}">{{ estado }}</span></td>
<td class="actions">
<a href="/admin/ver/{{ l[0] }}" class="btn btn-primary btn-sm">Ver</a>
<a href="/admin/editar/{{ l[0] }}" class="btn btn-outline btn-sm">Editar</a>
{% if estado=='activa' %}
<a href="/admin/suspender/{{ l[0] }}" class="btn btn-danger btn-sm" onclick="return confirm('Suspender licencia #{{ l[0] }}?')">Suspender</a>
{% else %}
<a href="/admin/reactivar/{{ l[0] }}" class="btn btn-success btn-sm">Reactivar</a>
{% endif %}
</td></tr>
{% endfor %}
</tbody></table>
</form>
{% else %}
<div class="empty-state">No hay licencias creadas</div>
{% endif %}
{% endif %}
</div></div></div>
<script>
function toggleAll(source){
    document.querySelectorAll('input[name="ids"]').forEach(c=>c.checked=source.checked);
    updateDeleteBtn();
}
function updateDeleteBtn(){
    var btn=document.getElementById('deleteSelected');
    btn.disabled=!document.querySelectorAll('input[name="ids"]:checked').length;
}
</script>
</body></html>"""

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS licenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                hw_id TEXT,
                activo INTEGER DEFAULT 1,
                vencimiento TEXT,
                features TEXT DEFAULT '{}'
            )
        """)
        cur = c.execute("PRAGMA table_info(admin)")
        cols = [row[1] for row in cur.fetchall()]
        if "username" not in cols:
            c.execute("DROP TABLE IF EXISTS admin")
        c.execute("CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, pw TEXT)")
        if not c.execute("SELECT * FROM admin").fetchone():
            c.execute("INSERT INTO admin (username, pw) VALUES (?,?)",
                     ("admin", generate_password_hash("admin123")))

def generar_clave():
    raw = uuid.uuid4().hex[:12].upper()
    return f"LICS-{raw}"

def generar_token(key, hw_id, expira_ts):
    payload = {
        "key": key,
        "hw_id": hw_id,
        "exp": expira_ts,
        "iat": int(time.time())
    }
    firma = hmac.new(SECRET_KEY, json.dumps(payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()
    return json.dumps({"payload": payload, "firma": firma})

def verificar_token(token_str):
    try:
        data = json.loads(token_str)
        payload = data["payload"]
        firma = data["firma"]
        expected = hmac.new(SECRET_KEY, json.dumps(payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(firma, expected):
            return None
        if payload["exp"] > 0 and int(time.time()) > payload["exp"]:
            return None
        return payload
    except:
        return None

@app.route("/")
def index():
    return redirect("/admin/")

@app.route("/admin/")
def admin():
    with sqlite3.connect(DB_PATH) as c:
        licencias = c.execute("SELECT * FROM licenses ORDER BY id DESC").fetchall()
    return render_template_string(HTML, licencias=licencias,
                                 session=session, msg=request.args.get("msg"))

@app.route("/admin/login", methods=["POST"])
def login():
    user = request.form.get("username", "")
    pw = request.form.get("password", "")
    with sqlite3.connect(DB_PATH) as c:
        stored = c.execute("SELECT pw FROM admin WHERE username=?", (user,)).fetchone()
    if stored and check_password_hash(stored[0], pw):
        session["logged_in"] = True
        session["username"] = user
    return redirect("/admin/")

@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect("/admin/")

@app.route("/admin/crear", methods=["POST"])
def crear():
    if not session.get("logged_in"):
        return redirect("/admin/")
    dias = int(request.form.get("dias", "365"))
    clave = generar_clave()
    vencimiento = (datetime.now() + timedelta(days=dias)).isoformat() if dias > 0 else None
    with sqlite3.connect(DB_PATH) as c:
        try:
            c.execute("INSERT INTO licenses (key, vencimiento, activo, features) VALUES (?,?,1,'{}')",
                     (clave, vencimiento))
            return redirect("/admin/?msg=Licencia+creada+OK")
        except:
            return redirect("/admin/?msg=Error+al+crear")

@app.route("/admin/ver/<int:lid>")
def ver_licencia(lid):
    if not session.get("logged_in"):
        return redirect("/admin/")
    with sqlite3.connect(DB_PATH) as c:
        lic = c.execute("SELECT * FROM licenses WHERE id=?", (lid,)).fetchone()
    if not lic:
        return redirect("/admin/?msg=No+encontrada")
    return render_template_string("""
    <!DOCTYPE html><html lang="es"><head><title>Licencia #{{ l[0] }}</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Inter',-apple-system,sans-serif;background:#f0f2f5;color:#1a1a2e;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
    .card{background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,0.06);width:100%;max-width:520px;overflow:hidden}
    .card-header{padding:24px 28px 0;display:flex;align-items:center;justify-content:space-between}
    .card-header h2{font-size:18px;font-weight:700;display:flex;align-items:center;gap:8px}
    .card-body{padding:20px 28px 28px}
    .btn{display:inline-flex;align-items:center;gap:4px;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:500;font-family:inherit;border:none;cursor:pointer;transition:all .15s;text-decoration:none}
    .btn-outline{background:transparent;color:#6b7280;border:1px solid #e5e7eb}
    .btn-outline:hover{background:#f9fafb}
    table{width:100%;border-collapse:separate;border-spacing:0;font-size:14px;margin-top:16px}
    th,td{padding:10px 14px;text-align:left;border-bottom:1px solid #f3f4f6}
    th{font-weight:600;color:#6b7280;font-size:13px;width:120px;background:#fafafa}
    tr:last-child th,tr:last-child td{border-bottom:none}
    code{background:#f3f4f6;padding:3px 10px;border-radius:6px;word-break:break-all;font-size:13px;font-family:'SF Mono',Consolas,monospace;display:inline-block;max-width:100%}
    .badge{padding:3px 12px;border-radius:20px;font-size:12px;font-weight:600;display:inline-block}
    .badge-activa{background:#d1fae5;color:#065f46}
    .badge-suspendida{background:#fee2e2;color:#991b1b}
    pre{background:#f9fafb;padding:8px 12px;border-radius:6px;font-size:12px;overflow-x:auto;border:1px solid #f3f4f6}
    </style></head><body>
    <div class="card">
    <div class="card-header">
    <h2>Licencia #{{ l[0] }}</h2>
    <a href="/admin/" class="btn btn-outline">Volver</a>
    </div>
    <div class="card-body">
    <table>
    <tr><th>ID</th><td>{{ l[0] }}</td></tr>
    <tr><th>Clave</th><td><code>{{ l[1] }}</code></td></tr>
    <tr><th>HW ID</th><td><code>{{ l[2] if l[2] else '-' }}</code></td></tr>
    <tr><th>Estado</th><td><span class="badge {{ 'badge-activa' if l[3]==1 else 'badge-suspendida' }}">{{ 'Activa' if l[3]==1 else 'Suspendida' }}</span></td></tr>
    <tr><th>Vencimiento</th><td>{{ l[4][:10] if l[4] else 'Ilimitado' }}</td></tr>
    <tr><th>Features</th><td><pre>{{ l[5] }}</pre></td></tr>
    </table>
    <div style="margin-top:16px;display:flex;gap:8px">
    <a href="/admin/editar/{{ l[0] }}" class="btn btn-outline">Editar</a>
    <a href="/admin/eliminar/{{ l[0] }}" class="btn btn-danger" onclick="return confirm('Eliminar licencia #{{ l[0] }}?')">Eliminar</a>
    </div>
    </div></div>
    </body></html>""", l=lic)

@app.route("/admin/editar/<int:lid>", methods=["GET", "POST"])
def editar_licencia(lid):
    if not session.get("logged_in"):
        return redirect("/admin/")
    with sqlite3.connect(DB_PATH) as c:
        lic = c.execute("SELECT * FROM licenses WHERE id=?", (lid,)).fetchone()
    if not lic:
        return redirect("/admin/?msg=No+encontrada")
    if request.method == "POST":
        venc = request.form.get("vencimiento", "").strip()
        activo = 1 if request.form.get("activo") == "1" else 0
        if venc:
            venc_iso = venc + "T23:59:59"
        else:
            venc_iso = None
        with sqlite3.connect(DB_PATH) as c:
            c.execute("UPDATE licenses SET vencimiento=?, activo=? WHERE id=?", (venc_iso, activo, lid))
        return redirect("/admin/ver/" + str(lid) + "?msg=Guardado")
    venc_actual = lic[4][:10] if lic[4] else ""
    return render_template_string("""
    <!DOCTYPE html><html lang="es"><head><title>Editar Licencia #{{ lid }}</title>
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Inter',-apple-system,sans-serif;background:#f0f2f5;color:#1a1a2e;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
    .card{background:#fff;border-radius:16px;box-shadow:0 4px 24px rgba(0,0,0,0.06);width:100%;max-width:440px;overflow:hidden}
    .card-header{padding:24px 28px 0;display:flex;align-items:center;justify-content:space-between}
    .card-header h2{font-size:18px;font-weight:700}
    .card-body{padding:20px 28px 28px}
    .btn{display:inline-flex;align-items:center;gap:4px;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:500;font-family:inherit;border:none;cursor:pointer;transition:all .15s;text-decoration:none}
    .btn-primary{background:#6366f1;color:#fff}
    .btn-primary:hover{background:#4f46e5}
    .btn-outline{background:transparent;color:#6b7280;border:1px solid #e5e7eb}
    .btn-outline:hover{background:#f9fafb}
    .campo{margin-bottom:16px}
    .campo label{display:block;font-size:13px;font-weight:600;color:#6b7280;margin-bottom:4px}
    .campo input,.campo select{padding:10px 14px;border:1px solid #e5e7eb;border-radius:8px;font-size:14px;font-family:inherit;background:#f9fafb;width:100%;transition:border .2s;outline:none}
    .campo input:focus,.campo select:focus{border-color:#6366f1;box-shadow:0 0 0 3px rgba(99,102,241,0.1);background:#fff}
    .actions{display:flex;gap:8px;margin-top:20px}
    </style></head><body>
    <div class="card">
    <div class="card-header"><h2>Editar Licencia #{{ lid }}</h2><a href="/admin/ver/{{ lid }}" class="btn btn-outline">Cancelar</a></div>
    <div class="card-body">
    <form method="post">
    <div class="campo"><label>Vencimiento</label><input type="date" name="vencimiento" value="{{ venc }}"></div>
    <div class="campo"><label>Estado</label>
    <select name="activo"><option value="1" {{ 'selected' if activo==1 else '' }}>Activa</option><option value="0" {{ 'selected' if activo==0 else '' }}>Suspendida</option></select></div>
    <div class="actions"><button class="btn btn-primary">Guardar</button><a href="/admin/ver/{{ lid }}" class="btn btn-outline">Cancelar</a></div>
    </form>
    </div></div>
    </body></html>""", lid=lid, venc=venc_actual, activo=lic[3])

@app.route("/admin/suspender/<int:lid>")
def suspender(lid):
    if not session.get("logged_in"):
        return redirect("/admin/")
    with sqlite3.connect(DB_PATH) as c:
        c.execute("UPDATE licenses SET activo=0 WHERE id=?", (lid,))
    return redirect("/admin/?msg=Licencia+suspendida")

@app.route("/admin/reactivar/<int:lid>")
def reactivar(lid):
    if not session.get("logged_in"):
        return redirect("/admin/")
    with sqlite3.connect(DB_PATH) as c:
        c.execute("UPDATE licenses SET activo=1 WHERE id=?", (lid,))
    return redirect("/admin/?msg=Licencia+reactivada")

@app.route("/admin/eliminar/<int:lid>")
def eliminar(lid):
    if not session.get("logged_in"):
        return redirect("/admin/")
    with sqlite3.connect(DB_PATH) as c:
        c.execute("DELETE FROM licenses WHERE id=?", (lid,))
    return redirect("/admin/?msg=Licencia+eliminada")

@app.route("/admin/eliminar_masivo", methods=["POST"])
def eliminar_masivo():
    if not session.get("logged_in"):
        return redirect("/admin/")
    ids = request.form.getlist("ids")
    if ids:
        with sqlite3.connect(DB_PATH) as c:
            for lid in ids:
                c.execute("DELETE FROM licenses WHERE id=?", (lid,))
    return redirect("/admin/?msg=Licencias+eliminadas")

# --- API REST ---

@app.route("/api/license/verify", methods=["GET"])
def api_verify():
    key = request.args.get("key", "")
    if not key:
        return jsonify({"status": "error", "message": "key required"}), 400
    with sqlite3.connect(DB_PATH) as c:
        lic = c.execute("SELECT * FROM licenses WHERE key=?", (key,)).fetchone()
    if not lic:
        return jsonify({"status": "error", "message": "license not found"}), 404
    if not lic[3]:
        return jsonify({"status": "suspended", "message": "license suspended"}), 403
    if lic[4]:
        venc = datetime.fromisoformat(lic[4])
        if datetime.now() > venc:
            return jsonify({"status": "expired", "message": "license expired"}), 403
    hw_id = request.args.get("hw_id", "")
    expira_ts = int(datetime.fromisoformat(lic[4]).timestamp()) if lic[4] else 0
    token = generar_token(key, hw_id, expira_ts)
    return jsonify({
        "status": "ok",
        "token": token,
        "expira": lic[4]
    })

@app.route("/api/license/activate", methods=["POST"])
def api_activate():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "json required"}), 400
    key = data.get("key", "")
    hw_id = data.get("hw_id", "")
    if not key or not hw_id:
        return jsonify({"status": "error", "message": "key and hw_id required"}), 400
    with sqlite3.connect(DB_PATH) as c:
        lic = c.execute("SELECT * FROM licenses WHERE key=?", (key,)).fetchone()
    if not lic:
        return jsonify({"status": "error", "message": "license not found"}), 404
    if not lic[3]:
        return jsonify({"status": "suspended", "message": "license suspended"}), 403
    if lic[2] and lic[2] != hw_id:
        return jsonify({"status": "error", "message": "license already in use on another machine"}), 403
    with sqlite3.connect(DB_PATH) as c:
        c.execute("UPDATE licenses SET hw_id=? WHERE id=?", (hw_id, lic[0]))
    expira_ts = int(datetime.fromisoformat(lic[4]).timestamp()) if lic[4] else 0
    token = generar_token(key, hw_id, expira_ts)
    return jsonify({
        "status": "ok",
        "token": token,
        "expira": lic[4]
    })

@app.route("/api/license/revoke", methods=["POST"])
def api_revoke():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "json required"}), 400
    key = data.get("key", "")
    if not key:
        return jsonify({"status": "error", "message": "key required"}), 400
    with sqlite3.connect(DB_PATH) as c:
        c.execute("UPDATE licenses SET activo=0 WHERE key=?", (key,))
    return jsonify({"status": "ok", "message": "license revoked"})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

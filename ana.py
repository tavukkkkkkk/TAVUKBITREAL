from flask import Flask, render_template_string, request, session, redirect, url_for, jsonify
import random
import threading
import time

app = Flask(__name__)
app.secret_key = "gizli_tavuk"

fiyat = 14
log_kaydi = []
simulasyon_aktif = False
lock = threading.Lock()

HTML = '''
<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <title>💎 Elmas Fiyatı Takibi</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background:#121212; color:#eee; }
    #log { background:#111; color:#0f0; height:300px; overflow:auto; padding:10px; font-family: monospace; }
    #fiyat { font-size:2rem; color:lime; }
  </style>
</head>
<body class="container py-4">

  <h1>💎 Elmas Fiyatı Simülasyonu</h1>
  <div>📈 Güncel Fiyat: <span id="fiyat">{{ fiyat }}</span> elmas</div>
  <div>🔄 Durum: <span id="durum">{{ durum }}</span></div>

  {% if not session.get("giris") %}
    <form method="post" action="/login">
      <label>🔑 Şifre: <input type="password" name="password" class="form-control" required></label><br>
      <button class="btn btn-primary">Giriş Yap</button>
    </form>
  {% else %}
    <div class="my-3">
      <button id="devamBtn" class="btn btn-success">▶️ Devam (20sn)</button>
      <button id="temizleBtn" class="btn btn-secondary">🧹 Logu Temizle</button>
      <a href="/logout" class="btn btn-warning">🚪 Çıkış</a>
    </div>
  {% endif %}

  <pre id="log">{{ log }}</pre>

<script>
  function update() {
    fetch('/status')
      .then(res => res.json())
      .then(data => {
        document.getElementById('fiyat').textContent = data.fiyat;
        document.getElementById('durum').textContent = data.durum;
        document.getElementById('log').textContent = data.log;
        const logEl = document.getElementById('log');
        logEl.scrollTop = logEl.scrollHeight;
      });
  }

  const devamBtn = document.getElementById('devamBtn');
  if (devamBtn) {
    devamBtn.onclick = () => {
      fetch('/devam', { method: 'POST' }).then(update);
    };
  }

  const temizleBtn = document.getElementById('temizleBtn');
  if (temizleBtn) {
    temizleBtn.onclick = () => {
      fetch('/temizle', { method: 'POST' }).then(update);
    };
  }

  setInterval(update, 1000);
  update();
</script>
</body>
</html>
'''

def simulasyonu_baslat():
    global fiyat, log_kaydi, simulasyon_aktif
    simulasyon_aktif = True
    for saniye in range(1, 21):
        time.sleep(1)
        with lock:
            degisim = random.randint(-2, 2)
            fiyat = max(1, fiyat + degisim)
            log_kaydi.append(f"{saniye}. saniyede fiyat: {fiyat} elmas")
            if len(log_kaydi) > 100:
                log_kaydi.pop(0)
    with lock:
        simulasyon_aktif = False
        log_kaydi.append("⏹ Simülasyon otomatik durduruldu.")

@app.route("/")
def index():
    durum = "🟢 Çalışıyor" if simulasyon_aktif else "🔴 Durduruldu"
    return render_template_string(HTML, fiyat=fiyat, log="\n".join(log_kaydi), durum=durum, session=session)

@app.route("/status")
def status():
    durum = "🟢 Çalışıyor" if simulasyon_aktif else "🔴 Durduruldu"
    return jsonify({
        "fiyat": fiyat,
        "log": "\n".join(log_kaydi[-50:]),
        "durum": durum
    })

@app.route("/devam", methods=["POST"])
def devam():
    if not session.get("giris"):
        return "Yetkisiz", 403
    global simulasyon_aktif
    if not simulasyon_aktif:
        thread = threading.Thread(target=simulasyonu_baslat)
        thread.start()
    return ('', 204)

@app.route("/temizle", methods=["POST"])
def temizle():
    if not session.get("giris"):
        return "Yetkisiz", 403
    global log_kaydi
    with lock:
        log_kaydi.clear()
        log_kaydi.append("🧹 Log temizlendi.")
    return ('', 204)

@app.route("/login", methods=["POST"])
def login():
    sifre = request.form.get("password")
    if sifre == "tavuk123":
        session["giris"] = True
        log_kaydi.append("✅ Giriş yapıldı.")
    else:
        log_kaydi.append("🚫 Hatalı şifre denemesi!")
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.pop("giris", None)
    log_kaydi.append("👋 Çıkış yapıldı.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

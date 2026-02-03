from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import urllib3

# Silencio total para no dejar rastros en logs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__, template_folder='../templates')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/extraer')
def extraer():
    rfc = request.args.get('rfc', '').upper().strip()
    idcif = request.args.get('idcif', '').strip()

    if not rfc or not idcif:
        return jsonify({"status": "error"}), 400

    # URL Móvil que validamos manualmente
    url_sat = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
    
    # Cambiamos a un motor de renderizado más robusto para evitar el 404
    # Este puente simula un navegador completo
    puente_ninja = f"https://api.allorigins.win/get?url={requests.utils.quote(url_sat)}"

    try:
        # Iniciamos sesión efímera
        with requests.Session() as s:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Connection': 'close' # Muerte inmediata tras recibir datos
            }
            
            # El intento debe ser rápido (timeout corto) para no ser rastreado
            response = s.get(puente_ninja, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return jsonify({"status": "terminated"}), 404

            contenido = response.json().get('contents', '')
            
            if not contenido or "Error 404" in contenido:
                return jsonify({"status": "not_found"}), 404

            soup = BeautifulSoup(contenido, 'html.parser')
            datos = {}

            # Buscamos patrones de datos fiscales
            for span in soup.find_all(['span', 'td']):
                texto = span.get_text(strip=True)
                if ":" in texto:
                    partes = texto.split(":", 1)
                    if len(partes) > 1 and partes[1].strip():
                        datos[partes[0].strip()] = partes[1].strip()

            if not datos:
                return jsonify({"status": "ghost_mode"}), 404

            # Entregamos y el proceso muere
            return jsonify({"status": "success", "datos": datos})

    except:
        # Muere en el intento sin revelar por qué
        return jsonify({"status": "failed"}), 500

app = app

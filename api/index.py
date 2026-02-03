25from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import urllib3

# Desactivar advertencias de seguridad
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
        return jsonify({"status": "error", "detalle": "Faltan datos"}), 400

    # URL ORIGINAL DEL SAT
    url_sat = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3=22020213087_GUCK920822MB3"
    
    # --- CONFIGURACIÓN DEL PUENTE (CORS-ANYWHERE / PROXY) ---
    # Usamos un servicio de proxy para que Vercel no se bloquee con el SSL del SAT
    puente = "https://api.allorigins.win/get?url="
    url_final = f"{puente}{requests.utils.quote(url_sat)}"

    try:
        # Llamamos al puente en lugar de al SAT directamente
        response = requests.get(url_final, timeout=25)
        
        if response.status_code != 200:
            return jsonify({"status": "error", "detalle": "El puente no pudo conectar con el SAT"}), 500

        # AllOrigins devuelve un JSON con el HTML dentro del campo 'contents'
        json_data = response.json()
        html_sat = json_data.get('contents', '')

        if not html_sat:
            return jsonify({"status": "error", "detalle": "No se recibió respuesta del SAT"}), 404

        # Analizamos el HTML recuperado a través del puente
        soup = BeautifulSoup(html_sat, 'html.parser')
        celdas = soup.find_all('td')
        datos_extraidos = {}
        
        for i in range(0, len(celdas) - 1, 2):
            label = celdas[i].get_text(strip=True).replace(":", "")
            valor = celdas[i+1].get_text(strip=True)
            if label and valor:
                datos_extraidos[label] = valor

        if not datos_extraidos:
            return jsonify({"status": "error", "detalle": "Datos no encontrados (Revisa RFC/IDCIF)"}), 404

        return jsonify({
            "status": "success",
            "datos": datos_extraidos,
            "metodo": "Puente SSL Bypass"
        })

    except Exception as e:
        return jsonify({"status": "error", "detalle": f"Error en el puente: {str(e)}"}), 500

app = app

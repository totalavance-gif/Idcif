from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import urllib3

# Deshabilitamos advertencias de seguridad de urllib3 para evitar ruidos en los logs
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
        return jsonify({"status": "error", "detalle": "Faltan parámetros"}), 400

    # URL de escritorio (la que tiene todos los datos)
    url_sat = f"https://siat.sat.gob.mx/app/qr/faces/pages/rest/consultarDatosArt79.jsf?p1={idcif}&p2={rfc}"
    
    try:
        # Usamos una sesión simple pero con headers de un navegador muy común
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Intentamos la conexión ignorando la verificación SSL (verify=False)
        # Esto es lo que suele funcionar cuando el servidor remoto tiene protocolos viejos
        response = session.get(url_sat, headers=headers, timeout=20, verify=False)
        
        if response.status_code != 200:
            return jsonify({"status": "error", "detalle": f"SAT inaccesible (Código {response.status_code})"}), 500

        soup = BeautifulSoup(response.text, 'html.parser')
        celdas = soup.find_all('td')
        datos_extraidos = {}
        
        for i in range(0, len(celdas) - 1, 2):
            label = celdas[i].get_text(strip=True).replace(":", "")
            valor = celdas[i+1].get_text(strip=True)
            if label and valor:
                datos_extraidos[label] = valor

        if not datos_extraidos:
            return jsonify({"status": "error", "detalle": "No se hallaron datos. Verifica RFC/IDCIF"}), 404

        return jsonify({
            "status": "success",
            "datos": datos_extraidos,
            "url_oficial": url_sat
        })

    except Exception as e:
        # Enviamos un mensaje más amigable pero útil para debug
        return jsonify({"status": "error", "detalle": "Error de conexión segura con el SAT"}), 500

app = app

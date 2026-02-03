from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import urllib3

# Desactivamos los avisos de certificados no seguros
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

    # Cambiamos a la URL MÓVIL que sugeriste
    # Estructura: D1=10&D2=1&D3=IDCIF_RFC
    url_movil = f"https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={idcif}_{rfc}"
    
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        # Intentamos la conexión con verify=False para ignorar el error de la llave DH
        response = session.get(url_movil, headers=headers, timeout=15, verify=False)
        
        if response.status_code != 200:
            return jsonify({"status": "error", "detalle": f"Error móvil SAT: {response.status_code}"}), 500

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # En la versión móvil, el SAT suele usar etiquetas <span> o celdas distintas
        # Buscamos todas las celdas para intentar pescar la info
        celdas = soup.find_all(['td', 'span'])
        datos_extraidos = {}
        
        # Lógica de extracción genérica para ver qué nos devuelve la versión móvil
        for i in range(len(celdas)):
            texto = celdas[i].get_text(strip=True)
            if ":" in texto:
                label = texto.replace(":", "")
                # Intentamos tomar el texto del siguiente elemento
                if i + 1 < len(celdas):
                    valor = celdas[i+1].get_text(strip=True)
                    datos_extraidos[label] = valor

        if not datos_extraidos:
            # Si no hay tabla, enviamos al menos la confirmación de que la página cargó
            return jsonify({
                "status": "success",
                "mensaje": "Página móvil cargada, pero el formato de datos es distinto.",
                "url_utilizada": url_movil,
                "html_preview": response.text[:500] # Para debuguear qué ve Python
            })

        return jsonify({
            "status": "success",
            "datos": datos_extraidos,
            "url_oficial": url_movil
        })

    except Exception as e:
        return jsonify({"status": "error", "detalle": f"Fallo total: {str(e)}"}), 500

app = app
        

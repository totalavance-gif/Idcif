from flask import Flask, request, jsonify, render_template
import requests
from bs4 import BeautifulSoup
import ssl

# --- PARCHE DE SEGURIDAD PARA EL SAT (DH_KEY_TOO_SMALL) ---
# Obligamos a la conexión a usar un nivel de seguridad que el SAT soporte
class SATAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        # Bajamos el nivel a 1 para aceptar las llaves antiguas del SAT
        ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = ctx
        return super(SATAdapter, self).init_poolmanager(*args, **kwargs)

# Configuración de la App
# template_folder='../templates' permite que Vercel encuentre tu index.html
app = Flask(__name__, template_folder='../templates')

@app.route('/')
def home():
    """Ruta principal: Carga la interfaz HTML"""
    return render_template('index.html')

@app.route('/api/extraer')
def extraer():
    """Ruta de API: Procesa el RFC e IDCIF"""
    rfc = request.args.get('rfc', '').upper().strip()
    idcif = request.args.get('idcif', '').strip()

    if not rfc or not idcif:
        return jsonify({"status": "error", "detalle": "RFC e IDCIF son obligatorios"}), 400

    # Usamos la URL de escritorio porque es la que tiene la tabla completa de datos
    url_sat = f"https://siat.sat.gob.mx/app/qr/faces/pages/rest/consultarDatosArt79.jsf?p1={idcif}&p2={rfc}"
    
    try:
        # Iniciamos sesión con el parche de seguridad aplicado
        session = requests.Session()
        session.mount("https://", SATAdapter())
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        
        # Petición al SAT con un tiempo de espera de 15 segundos
        response = session.get(url_sat, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return jsonify({"status": "error", "detalle": f"Error del SAT: {response.status_code}"}), 500

        # Analizamos el HTML para extraer los datos de la tabla
        soup = BeautifulSoup(response.text, 'html.parser')
        celdas = soup.find_all('td')
        datos_extraidos = {}
        
        # El SAT pone [Etiqueta] en una celda y [Valor] en la siguiente
        for i in range(0, len(celdas) - 1, 2):
            label = celdas[i].get_text(strip=True).replace(":", "")
            valor = celdas[i+1].get_text(strip=True)
            if label and valor:
                datos_extraidos[label] = valor

        if not datos_extraidos:
            return jsonify({
                "status": "error", 
                "detalle": "No se encontraron datos. Revisa que el IDCIF sea el del QR."
            }), 404

        # Enviamos los datos de vuelta al HTML
        return jsonify({
            "status": "success",
            "datos": datos_extraidos,
            "url_oficial": url_sat
        })

    except Exception as e:
        # Si el error persiste, lo mostramos para depurar
        return jsonify({"status": "error", "detalle": str(e)}), 500

# Línea vital para que Vercel reconozca la app
app = app

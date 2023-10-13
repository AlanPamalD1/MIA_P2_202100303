from flask import Flask, jsonify, request
from flask_cors import CORS
import Scanner
from consola import Console
from mount import Mount
from Structs import UsuarioActivo

# Flask app
app = Flask(__name__)

datos = {} # Datos de la base de datos
datos['mount'] = Mount()
datos['logued'] = False
datos['logueado'] = UsuarioActivo()


# Configuracion de CORS
CORS(app, resources={r'/*': {'origins': '*', 
                             "methos":['GET', 'POST', 'PUT', 'DELETE'],
                             "headers": "Authorization"}})

# Ruta por defecto
@app.route("/", methods=['GET'])
def index():
    return jsonify({
        "message": "API REST INICIADA CORRECTAMENTE"
    })

@app.route("/exec", methods=['POST'])
def exec():
    comandos = request.json['comandos']
    try:
        for i in comandos:
            texto = i
            tk = Scanner.comando(texto)
            if texto:
                texto = texto[len(tk) + 1:]
                tks = Scanner.separar_tokens(texto)
                datos['mount'], datos['logued'], datos['logueado']  = Scanner.funciones(tk, tks, datos['mount'], datos['logued'], datos['logueado'])

        txt_consola = Console().getConsola()
        Console().limpiar()

        return jsonify({"message": "Ejecución terminada", "consola": txt_consola})
    except Exception as e:
        return jsonify({"message": e })

@app.route("/login", methods=['POST'])
def login():
    try:
        username = request.json['username']
        password = request.json['password']
        id = request.json['idparticion']

        logued = Scanner.existUser(username, password, id, datos['mount'])

        if logued:
            return jsonify({"message": "Usuario logueado correctamente"})
        return jsonify({"message": "Usuario no encontrado"})
    except Exception as e:
        print(e)
        return jsonify({"message": "Usuario no encontrado"})


@app.route("/getBaseDeDatos", methods=['GET'])
def getBaseDeDatos():

    db = "Base de datos obtenida correctamente\n"
    db += " (usuario logueado)\n" if datos['logued'] else " (usuario no logueado)\n"
    db += " (usuario: " + str(datos['logueado']) + ")\n" if datos['logued'] else ""
    db += "Los discos montados son:\n" + str(datos['mount'])

    return jsonify({"message": db})

@app.route("/resetBaseDeDatos", methods=['GET'])
def resetBaseDeDatos():
    datos['mount'] = Mount()
    datos['logueado'] = UsuarioActivo()
    datos['logued'] = False

    return jsonify({"message": "Base de datos reiniciada correctamente"})

# Iniciar servidor

if __name__ == "__main__":
    app.run(debug=True, port=4000, host='0.0.0.0')
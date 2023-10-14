import base64
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import Scanner
from consola import Console
from mount import Mount
from Structs import UsuarioActivo
import re

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
            return jsonify({"message": f"Bienvenido {username}!", "encontrado": True})
        return jsonify({"message": "Datos no correctos", "encontrado": False})
    except Exception as e:
        print(e)
        return jsonify({"message": "Datos no correctos","encontrado": False})

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


@app.route("/getRutasReportes", methods=['POST'])
def getRutasReportes():

    id_login = request.json['idparticion']

    ruta_carpeta = '/reportes/'
    extensiones = ('.jpg', '.png', '.jpeg', '.gif', '.bmp', 'txt', 'pdf')

    archivos = obtener_archivos_en_carpetas(ruta_carpeta, extensiones, id_login)
    rutas = get_directorios(archivos)

    return jsonify({"archivos": archivos, "rutas":rutas})

def obtener_archivos_en_carpetas(ruta_carpeta, extensiones_archivo, id_login):
    archivos = []
    # expresión regular para extraer el id del archivo
    patron = r"\[([\w\d]+)\]$"

    for ruta_actual, _, nombres_archivos in os.walk(ruta_carpeta):

        for nombre_archivo in nombres_archivos:
            ruta_completa = os.path.join(ruta_actual, nombre_archivo)
            
            #verificar que la ruta exista
            if not os.path.exists(ruta_completa):
                continue

            # Si termina con la extension que buscamos
            if ruta_completa.endswith(extensiones_archivo):
                # Extraemos el id del archivo
                id = re.search(patron, ruta_completa[:ruta_completa.rfind(".")])
                if id:
                    if id.group(1) == id_login: #si el id del archivo fue creado por el usuario logueado
                        #extension archivo
                        extension = ruta_completa[ruta_completa.rfind("."):]
                        longitudfinal = len(extension) + 2 + len(id.group(1))

                        #ruta - id
                        ruta_formato = ruta_completa[:-longitudfinal] + extension

                        #nombre archivo
                        nombreArchivo = ruta_completa.split(os.sep)[-1]

                        archivo ={
                            'id': id.group(1),
                            'size': os.path.getsize(ruta_completa),
                            'ruta': ruta_completa,
                            'ruta_formato': ruta_formato,
                            'nombre': nombreArchivo
                        }

                        archivos.append(archivo)

    # ordenamos la lista de archivos según su ruta
    archivos.sort(key=lambda x: x['ruta'].lower())

    return archivos

def get_directorios(archivos):
    estructura = {}

    for archivo in archivos:
        ruta = archivo['ruta_formato']
        directorios = ruta.split("/")
        nodo_actual = estructura

        for directorio in directorios[1:]:
            if directorio not in nodo_actual:
                nodo_actual[directorio] = {}
            nodo_actual = nodo_actual[directorio]

    lista_rutas = get_nodo(estructura, "", [])
    return lista_rutas

def get_nodo(nodo, prefijo, lista_rutas):
    for nombre, contenido in nodo.items():
        if contenido: # es un directorio
            impresion = prefijo + "▼ " + nombre
            lista_rutas.append(impresion)
            get_nodo(contenido, prefijo + " " * 2, lista_rutas)
        else: # es un archivo
            impresion = prefijo + nombre
            lista_rutas.append(impresion)
        
    return lista_rutas

@app.route("/getFileBin64", methods=['POST'])
def getFileBin64():
    ruta = request.json['ruta']

    print('ruta: ', ruta)

    #verificar que la ruta exista
    if not os.path.exists(ruta):
        print("No existe la ruta del reporte !!")
        return jsonify({"file_exists":False })

    #si el archivo es un txt
    if ruta.endswith(".txt"):
        try:
            with open(ruta, "r") as archivo:
                contenido = archivo.read()
            return jsonify({"file_exists":True, "file_type": 'text', "file_encoded": contenido})
        except Exception as e:
            print(e)
            return jsonify({"file_exists":False})

    #si el archivo es una imagen
    if ruta.endswith(".jpg") or ruta.endswith(".png") or ruta.endswith(".jpeg") or ruta.endswith(".gif") or ruta.endswith(".bmp"):
        try:
            with open(ruta, "rb") as archivo:
                contenido = base64.b64encode(archivo.read()).decode('utf-8')

                contenido = "data:image/png;base64," + contenido
            
            return jsonify({"file_exists":True, "file_type": 'image', "file_encoded": contenido})
        except Exception as e:
            print(e)
            return jsonify({"file_exists":False})

    #si es pdf
    if ruta.endswith(".pdf"):
        try:
            with open(ruta, "rb") as archivo:
                contenido = base64.b64encode(archivo.read()).decode('utf-8')
                contenido = "data:application/pdf;base64," + contenido
            
            return jsonify({"file_exists":True, "file_type": 'pdf', "file_encoded": contenido})
        except Exception as e:
            print(e)
            return jsonify({"file_exists":False})

    return jsonify({"file_exists":False})


    

# Iniciar servidor
if __name__ == "__main__":
    app.run(debug=True, port=4000, host='0.0.0.0')



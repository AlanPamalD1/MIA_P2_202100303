import mount as Mount
import Structs
import Scanner as Scanner
from Ext2 import *

class Sesion:
    def __init__(self):
        self.id_user = 0
        self.id_grp = 0
        self.inicioSuper = 0
        self.inicioJournal = 0
        self.tipo_sistema = 0
        self.direccion = ""
        self.fit = ""

actualSesion = Sesion()
logueado = Structs.UsuarioActivo()

class Usuarios:
    def __init__(self, m = Mount.Mount()):  
        self.mount = m

    def login(self, context, m):
        self.mount = m
        id = ""
        user = ""
        password = ""

        for current in context:
            id_ = current[:current.find('=')].strip().lower()
            current = current[current.find('=') + 1:]
            
            if current.startswith("\""):
                current = current[1:-1]

            if id_ == "id":
                id = current
            elif id_ == "user":
                user = current
            elif id_ == "pass":
                password = current

        if id == "" or user == "" or password == "":
            Scanner.mensaje("LOGIN", "Necesita parámetros obligatorios")
            return False, None

        return self.sesion_activa(user, password, id), logueado

    def sesion_activa(self, usr, pwd, id): 
        try:

            path, partition = self.mount.getmount(id)
            sprTemp = Structs.SuperBloque()  # Crear una instancia de SuperBloque
            sprTemp = desempaquetarSuperBloque(path, partition)

            if path == None or partition == None:
                raise RuntimeError("No se encontró la partición")

            #Obtener el contenido del archivo de usuarios.txt

            inodo = Structs.Inodos()
            inodo = getInodo(path, sprTemp, 1) #El inodo 1 es el archivo de usuarios.txt

            usuariosTXT = ""
            for i_block in inodo.i_block:
                if i_block != -1:
                    #Obtener el contenido del bloque de carpetas
                    bloque = getBloqueArchivo(path, sprTemp, i_block)
                    usuariosTXT += bloque.b_content.decode('ascii')

            #Eliminar bytes vacios
            usuariosTXT = usuariosTXT.replace('\x00', '')

            registros = usuariosTXT.split('\n') #Separar por saltos de linea
            registros = list(filter(lambda x: x != '', registros)) # elminar los vacios

            grupoUser = ''
            userEncontrado = False

            #Buscar el usuario
            for line in registros:
                registro = line.split(',')
                if len(registro) > 1:
                    if registro[1].lower() == 'u': #Si es usuario
                        if registro[2] == usr and registro[4] == pwd: #si se encontró el usuario y la contraseña es correcta
                            logueado.id = id
                            logueado.user = usr
                            logueado.password = pwd
                            logueado.uid = int(registro[0])
                            grupoUser = registro[3]
                            userEncontrado = True

            #Buscar el grupo
            for line in registros:
                registro = line.split(',')
                if len(registro) > 1:
                    if registro[1].lower() == 'g' and registro[2] == grupoUser: #Si se encontró al grupo
                        logueado.guid = int(registro[0]) #actualizar el guid del usuario

            if userEncontrado:
                Scanner.mensaje("LOGIN", f"Bienvenido {usr}")
                return True

            #<!> No se encontró el usuario
            raise RuntimeError("No se encontró el usuario")
        except Exception as e:
            Scanner.error("LOGIN", str(e))
            return False

    def logout(self):
        global logueado
        Scanner.mensaje("LOGOUT", f"Cerrando sesión\nHasta la proxima {logueado.user}...")
        logueado = Structs.UsuarioActivo()
        actualSesion = Sesion()
        return False

    #<+> MANEJO GRUPOS 
    def validarDatosGrp(self, context, action):
        name = ""
        for current in context:
            id_ = current[:current.find('=')]
            current = current[current.find('=') + 1:]
            if current.startswith("\"") and current.endswith("\""):
                current = current[1:-1]
            elif Scanner.comparar(id_, "name"):
                name = current

        try:

            if name == "":
                print(action + "GRP", "No se encontró el parámetro \"name\"")
                Scanner.error(action + "GRP", "No se encontró el parámetro \"name\"")
                return
            elif Scanner.comparar(action, "MK"):
                self.mkgrp(name)
            else:
                self.rmgrp(name)
        
        except Exception as e:
            Scanner.error(action + "GRP", "Error al ejecutar el comando")
            print(e)

    def mkgrp(self, name):
        try:
            global logueado
            if not logueado.user == "root":
                raise RuntimeError("Solo el usuario ROOT puede acceder a estos comandos")

            path = ""
            path, partition = self.mount.getmount(logueado.id)
            sprTemp = Structs.SuperBloque()  # Crear una instancia de SuperBloque
            sprTemp = desempaquetarSuperBloque(path, partition)


            #Obtener el contenido del archivo de usuarios.txt

            inodo = Structs.Inodos()
            inodo = getInodo(path, sprTemp, 1) #El inodo 1 es el archivo de usuarios.txt

            usuariosTXT = ""
            for i_block in inodo.i_block:
                if i_block != -1:
                    #Obtener el contenido del bloque de carpetas
                    bloque = getBloqueArchivo(path, sprTemp, i_block)
                    usuariosTXT += bloque.b_content.decode('ascii')

            #Eliminar bytes vacios
            usuariosTXT = usuariosTXT.replace('\x00', '')

            registros = usuariosTXT.split('\n') #Separar por saltos de linea y elminar los vacios
            registros = list(filter(lambda x: x != '', registros))

            gruposRegistrados = []
            contadorRegistros = 1
            for line in registros:
                registro = line.split(',')
                if len(registro) > 1:
                    if registro[1].lower() == 'g': #Si es grupo
                        contadorRegistros += 1
                        if registro[0] != '0': #si no está eliminado
                            gruposRegistrados.append(registro[2]) #Agregar el nombre del grupo a la lista

            if name in gruposRegistrados:
                raise RuntimeError(f"el grupo {name} ya existe")

            #Si no existe el grupo, crearlo
            nuevoGrupo = f"{contadorRegistros},G,{name}" #Crear el nuevo registro
            usuariosTXT += f"{nuevoGrupo}\n" #Agregar el nuevo registro al archivo de usuarios.txt

            addContentToBloqueArchivo(path, partition, 1, usuariosTXT) #Agregar el contenido al bloque de carpetas

        except Exception as e:
            print("MKGRP", str(e))

    def rmgrp(self, name):
        try:
            grupoEncontrado = False
            global logueado
            if not logueado.user == "root":
                raise RuntimeError("Solo el usuario ROOT puede acceder a estos comandos")

            path = ""
            path, partition = self.mount.getmount(logueado.id)
            sprTemp = Structs.SuperBloque()  # Crear una instancia de SuperBloque
            sprTemp = desempaquetarSuperBloque(path, partition)


            #Obtener el contenido del archivo de usuarios.txt

            inodo = Structs.Inodos()
            inodo = getInodo(path, sprTemp, 1) #El inodo 1 es el archivo de usuarios.txt

            usuariosTXT = ""
            for i_block in inodo.i_block:
                if i_block != -1:
                    #Obtener el contenido del bloque de carpetas
                    bloque = getBloqueArchivo(path, sprTemp, i_block)
                    usuariosTXT += bloque.b_content.decode('ascii')

            #Eliminar bytes vacios
            usuariosTXT = usuariosTXT.replace('\x00', '')

            registros = usuariosTXT.split('\n') #Separar por saltos de linea y elminar los vacios
            registros = list(filter(lambda x: x != '', registros))

            nuevoRegistro = ""

            for line in registros:
                registro = line.split(',')

                if registro[1].lower() == 'g' and registro[2] == name and registro[0] != '0': #Si se encontró el grupo activo
                    #agregar un 0 al inicio del registro
                    line = f"0,{registro[1]},{registro[2]}"
                    grupoEncontrado = True
                
                nuevoRegistro += line + "\n"

            if not grupoEncontrado:
                raise RuntimeError(f"el grupo {name} no existe")

            addContentToBloqueArchivo(path, partition, 1, nuevoRegistro) #Agregar el contenido al bloque de carpetas

        except Exception as e:
            print("RMGRP", str(e))

    #<+> MANEJO USUARIOS
    def validarDatosusr(self, context, action):
        usr = ""
        pwd = ""
        grp = ""

        for current in context:
            id_ = current[:current.find('=')]
            current = current[current.find('=') + 1:]
            if current[:1] == "\"":
                current = current[1:-1]

            if Scanner.comparar(id_, "user"):
                usr = current
            elif Scanner.comparar(id_, "pass"):
                pwd = current
            elif Scanner.comparar(id_, "grp"):
                grp = current

        if Scanner.comparar(action, "MK"):
            if usr == "" or pwd == "" or grp == "":
                print(action + "GRP", "Necesita parámetros obligatorios")
            else:
                self.mkusr(usr, pwd, grp)
        else:
            if usr == "":
                print(action + "GRP", "Necesita parámetros obligatorios")
            else:
                self.rmusr(usr)

    def mkusr(self, usr, pwd, grp):
        try:
            global logueado
            if not logueado.user == "root":
                raise RuntimeError("Solo el usuario ROOT puede acceder a estos comandos")

            path = ""
            path, partition = self.mount.getmount(logueado.id)
            sprTemp = Structs.SuperBloque()  # Crear una instancia de SuperBloque
            sprTemp = desempaquetarSuperBloque(path, partition)


            #Obtener el contenido del archivo de usuarios.txt

            inodo = Structs.Inodos()
            inodo = getInodo(path, sprTemp, 1) #El inodo 1 es el archivo de usuarios.txt

            usuariosTXT = ""
            for i_block in inodo.i_block:
                if i_block != -1:
                    #Obtener el contenido del bloque de carpetas
                    bloque = getBloqueArchivo(path, sprTemp, i_block)
                    usuariosTXT += bloque.b_content.decode('ascii')

            #Eliminar bytes vacios
            usuariosTXT = usuariosTXT.replace('\x00', '')

            registros = usuariosTXT.split('\n') #Separar por saltos de linea y elminar los vacios
            registros = list(filter(lambda x: x != '', registros))

            gruposRegistrados = []
            for line in registros:
                registro = line.split(',')
                if len(registro) > 1:
                    if registro[1].lower() == 'g' and registro[0] != '0': #Si es grupo y no está eliminado
                        gruposRegistrados.append(registro[2]) #Agregar el nombre del grupo a la lista

            usuariosRegistrados = []
            contadorRegistrosU = 1
            for line in registros:
                registro = line.split(',')
                if len(registro) > 1:
                    if registro[1].lower() == 'u': #Si es usuario
                        contadorRegistrosU += 1
                        if registro[0] != '0': #si no está eliminado
                            usuariosRegistrados.append(registro[2]) #Agregar el nombre del usuario a la lista

            if usr in usuariosRegistrados:
                raise RuntimeError(f"el usuario {usr} ya existe")
            
            if not grp in gruposRegistrados:
                raise RuntimeError(f"el grupo {grp} no existe")

            #Si no existe el grupo, crearlo
            nuevoUser = f"{contadorRegistrosU},U,{usr},{pwd}" #Crear el nuevo registro
            usuariosTXT += f"{nuevoUser}\n" #Agregar el nuevo registro al archivo de usuarios.txt

            addContentToBloqueArchivo(path, partition, 1, usuariosTXT) #Agregar el contenido al bloque de carpetas

        except Exception as e:
            print("MKUSR", str(e))

    def rmusr(self, usr):
        try:
            global logueado
            if not logueado.user == "root":
                raise RuntimeError("Solo el usuario ROOT puede acceder a estos comandos")

            usuarioEncontrado = False

            path = ""
            path, partition = self.mount.getmount(logueado.id)
            sprTemp = Structs.SuperBloque()  # Crear una instancia de SuperBloque
            sprTemp = desempaquetarSuperBloque(path, partition)


            #Obtener el contenido del archivo de usuarios.txt

            inodo = Structs.Inodos()
            inodo = getInodo(path, sprTemp, 1) #El inodo 1 es el archivo de usuarios.txt

            usuariosTXT = ""
            for i_block in inodo.i_block:
                if i_block != -1:
                    #Obtener el contenido del bloque de carpetas
                    bloque = getBloqueArchivo(path, sprTemp, i_block)
                    usuariosTXT += bloque.b_content.decode('ascii')

            #Eliminar bytes vacios
            usuariosTXT = usuariosTXT.replace('\x00', '')

            registros = usuariosTXT.split('\n') #Separar por saltos de linea y elminar los vacios
            registros = list(filter(lambda x: x != '', registros))

            nuevoRegistro = ""

            for line in registros:
                registro = line.split(',')
                if registro[1].lower() == 'u' and registro[2] == usr and registro[0] != '0':  #Si se encontró el usuario activo
                    #agregar un 0 al inicio del registro
                    line = f"0,{registro[1]},{registro[2]},{registro[3]}"
                    usuarioEncontrado = True
                
                nuevoRegistro += line + "\n"

            if not usuarioEncontrado:
                raise RuntimeError(f"el usuario {usr} no existe")

            addContentToBloqueArchivo(path, partition, 1, nuevoRegistro) #Agregar el contenido al bloque de carpetas

        except Exception as e:
            print("RMUSR", str(e))


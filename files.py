import os
import main
import Structs
from SystemExt2 import *

class FILES:
    def __init__(self, m, logueado):  
        self.mount = m
        self.logueado = logueado
    

    def mkfile(self, context): #path, ruta, tamaño, contenido segun archivo local

        required = main.Scanner.required_values("mkdir")
        path = ""
        size = 0
        cont = ""
        creacion = False
        
        for current in context:

            #Verificar si current tiene =
            if current.find("=") != -1:
                tk = current.split('=')[0].lower()
                current = current.split('=')[1]
            else:
                tk = current.lower()           

            if current.startswith('"') and current.endswith('"'):
                current = current[1:-1]
            
            if main.Scanner.comparar(tk, "path"):

                if not current.startswith("/"):
                    current = "/" + current #agregar / al inicio si no lo tiene

                if tk in required:
                    required.remove(tk)
                path = current
            elif main.Scanner.comparar(tk, "size"):
                size = int(current)
            elif main.Scanner.comparar(tk, "cont"):
                cont = current
            elif main.Scanner.comparar(tk, "r"):
                creacion = True
        
        if required:
            for r in required:
                main.Scanner.error("MKFILE", "El parámetro " + r + " es obligatorio")
            return
        
        try:
            self.crearArchivo(path, size, cont, creacion)
        except Exception as e:
            main.Scanner.error("MKFILE", "No se pudo crear el archivo: " + path)
            print(e)

    def mkdir(self, context):

        required = main.Scanner.required_values("mkdir")
        path = ""
        creacion = False
        
        for current in context:

            #Verificar si current tiene =
            if current.find("=") != -1:
                tk = current.split('=')[0].lower()
                current = current.split('=')[1]
            else:
                tk = current.lower()           

            if current.startswith('"') and current.endswith('"'):
                current = current[1:-1]
            
            if main.Scanner.comparar(tk, "path"):

                if not current.startswith("/"):
                    current = "/" + current #agregar / al inicio si no lo tiene

                if tk in required:
                    required.remove(tk)
                path = current
                
            elif main.Scanner.comparar(tk, "r"):
                creacion = True
        
        if required:
            for r in required:
                main.Scanner.error("MKDIR", "El parámetro " + r + " es obligatorio")
            return
        

        try:
            self.crearCarpeta(path, creacion)
        except Exception as e:
            main.Scanner.error("MKDIR", "No se pudo crear la carpeta: " + path)
            print(e)

    def crearArchivo(self, path, size, cont, creacion): #
        
        print(f"Creando archivo: {path} ...")

        idUsuario = self.logueado.id
        pathDisco, partition = self.mount.getmount(idUsuario)

        directorios = path.split('/') #separar la ruta en directorios
        directorios = list(filter(None, directorios)) #eliminar los elementos vacios

        nombreArchivo = directorios[-1] #obtener el nombre de la carpeta
        directorios = directorios[:-1] #obtener los directorios de la ruta

        indexInodoPadre = 0
        indexInodoPadreAnterior = 0

        contenidoArchivo = ""

        if cont != "" : #<#> Si se especifica un contenido, se creará un archivo con el contenido especificado 
            if not os.path.exists(cont):
                #verificar si existe la ruta en el sistema
                raise Exception(f"No existe el archivo {cont} en el sistema")

            try:
                with open(cont, "r") as file:
                    contenidoArchivo = file.read()
                    #Reemplazar los saltos de linea por \n
            except:
                raise Exception(f"No se pudo leer el archivo {cont}")
            finally:
                file.close()
        else: #<#> Si no se especifica un contenido, se creará un archivo con el tamaño especificado
            #Agregar el texto 0123456789 hasta completar el tamaño
            for i in range(size):
                contenidoArchivo += str(i % 10)
        
        #<#> Verificar que size no exceda el tamaño maximo de un archivo
        if len(contenidoArchivo) > 64*15: #15 bloques de 64 bytes
            raise Exception(f"El contenido excede el tamaño maximo de caracteres en un archivo")


        if len(directorios) == 0: #si solo hay 1 directorio, es una carpeta en la raiz
            #path, superbloque, indice del inodo, tipo de inodo [0 = carpeta, 1 = archivo], nombre del inodo, -r
            self.ajustarCreacionInodo(pathDisco, partition, indexInodoPadre, 1, nombreArchivo)
            FILES.addContentArchivo(pathDisco, partition, contenidoArchivo) #<+> Agregar contenido al archivo
            main.Scanner.mensaje("MKFILE", f"Se ha creado el archivo {nombreArchivo} con éxito")

            return

        else: #si hay directorios, es una carpeta en una ruta especifica
            concatenadorDirectorio = "/"
            for directorio in directorios:
                concatenadorDirectorio += directorio + "/" #concatenar el directorio en busqueda
            
                #Siempre empezará en el inodo raiz
                indexInodoPadreAnterior = indexInodoPadre
                indexInodoPadre, encontrado = FILES.verificarExistenciaRuta(pathDisco, partition, indexInodoPadre, directorio, 0)
                if not encontrado: 
                    if not creacion: #<_> No se encontro el directorio y no se creará
                        main.Scanner.error("MKFILE", "No se encontró el directorio: " + concatenadorDirectorio)
                        return
                    else: #<_> No se encontro el directorio, pero se creará
                        directoriosFaltantes = directorios[directorios.index(directorio):] #obtener los directorios faltantes

                        for directorioFaltante in directoriosFaltantes:
                            if not self.ajustarCreacionInodo(pathDisco, partition, indexInodoPadreAnterior, 0, directorioFaltante):
                                main.Scanner.error("MKFILE", "No se pudo crear la carpeta: " + directorioFaltante, " por falta de espacio")
                                return

                            
                            indexInodoPadre, _ = FILES.verificarExistenciaRuta(pathDisco, partition, indexInodoPadreAnterior, directorioFaltante, 0)
            
            #Si se llega a este punto, es porque se encontró la ruta completa o se creó
            if not self.ajustarCreacionInodo(pathDisco, partition, indexInodoPadre, 1, nombreArchivo):
                main.Scanner.error("MKFILE", "No se pudo crear el archivo: " + nombreArchivo, " por falta de espacio")
                return
            
            FILES.addContentArchivo(pathDisco, partition, contenidoArchivo) #<+> Agregar contenido al archivo
            main.Scanner.mensaje("MKFILE", f"Se ha creado el archivo {nombreArchivo} en la ruta {concatenadorDirectorio} con éxito")
    

    #<#> Verificar existencia apuntador a bloque desde el index del inodo padre, retorna el index del apuntador y si se encontró
    @staticmethod
    def verificarExistenciaRuta(pathDisco, partition, indexInodoPadre, directorio, type=0):
        sprBloque = Structs.SuperBloque()  # Crear una instancia de SuperBloque
        sprBloque = desempaquetarSuperBloque(pathDisco, partition)  # Obtener los bytes de la instancia

        #Obtener el inido segun el indice
        inodoTemp = Structs.Inodos()
        inodoTemp = getInodo(pathDisco, sprBloque, indexInodoPadre) #inodo segun el indice, [0 = raiz]

        apuntadorDirectorio = -1 #indice del inodo del directorio

        if inodoTemp.i_type == 0: #si es una carpeta

            for i_block in inodoTemp.i_block: #contador de los bloques del inodo
                if i_block == -1: #si el bloque no tiene apuntador, continuar
                    continue

                #bloque con apuntador a un bloque de carpetas
                bloque = Structs.BloquesCarpetas()
                bloque = getBloqueCarpeta(pathDisco, sprBloque, i_block)

                #i_content = 0 #contador del contenido del bloque
                for content in bloque.b_content:
                    if content.b_name == directorio: #Se encontro el directorio
                        apuntadorDirectorio = content.b_inodo #indice del inodo del directorio

                        #obtener el inodo del directorio
                        inodoDirectorio = Structs.Inodos()
                        inodoDirectorio = getInodo(pathDisco, sprBloque, apuntadorDirectorio)
                        
                        if inodoDirectorio.i_type == type: #si es del mismo tipo, continuar
                            return apuntadorDirectorio, True
                    #i_content += 1
                
        return apuntadorDirectorio, False

    @staticmethod
    def addContentArchivo(pathDisco, partition, contenido):
        sprBloque = Structs.SuperBloque()  # Crear una instancia de SuperBloque
        sprBloque = desempaquetarSuperBloque(pathDisco, partition)

        indexUltimoInodo = sprBloque.s_first_ino-1 #indice del ultimo inodo creado
        addContentToBloqueArchivo(pathDisco, partition, indexUltimoInodo, contenido)

    #<#> Crear un archivo nuevo dado un bloque de carpetas con apuntador libre
    def crearCarpeta(self, path, creacion): #
        
        print(f"Creando carpeta: {path} ...")
        idUsuario = self.logueado.id
        pathDisco, partition = self.mount.getmount(idUsuario)

        directorios = path.split('/') #separar la ruta en directorios
        directorios = list(filter(None, directorios)) #eliminar los elementos vacios

        nombreCarpeta = directorios[-1] #obtener el nombre de la carpeta
        directorios = directorios[:-1] #obtener los directorios de la ruta

        indexInodoPadre = 0
        indexInodoPadreAnterior = 0
        
        if len(directorios) == 0: #si solo hay 1 directorio, es una carpeta en la raiz
            #path, superbloque, indice del inodo, tipo de inodo [0 = carpeta, 1 = archivo], nombre del inodo, -r
            self.ajustarCreacionInodo(pathDisco, partition, indexInodoPadre, 0, nombreCarpeta)
            main.Scanner.mensaje("MKDIR", f"Se ha creado la carpeta {nombreCarpeta} con éxito")
            return

        else: #si hay directorios, es una carpeta en una ruta especifica
            concatenadorDirectorio = "/"
            for directorio in directorios:
                concatenadorDirectorio += directorio + "/" #concatenar el directorio en busqueda
            
                #Siempre empezará en el inodo raiz
                indexInodoPadreAnterior = indexInodoPadre
                indexInodoPadre, encontrado = FILES.verificarExistenciaRuta(pathDisco, partition, indexInodoPadre, directorio, 0)
                if not encontrado: 
                    if not creacion: #<_> No se encontro el directorio y no se creará
                        main.Scanner.error("MKDIR", "No se encontró el directorio: " + concatenadorDirectorio)
                        return
                    else: #<_> No se encontro el directorio, pero se creará
                        directoriosFaltantes = directorios[directorios.index(directorio):] #obtener los directorios faltantes

                        for directorioFaltante in directoriosFaltantes:
                            if not self.ajustarCreacionInodo(pathDisco, partition, indexInodoPadreAnterior, 0, directorioFaltante):
                                main.Scanner.error("MKDIR", "No se pudo crear la carpeta: " + directorioFaltante, " por falta de espacio")
                                return
                            indexInodoPadre, _ = FILES.verificarExistenciaRuta(pathDisco, partition, indexInodoPadreAnterior, directorioFaltante, 0)
                        
            
            #Si se llega a este punto, es porque se encontró la ruta completa
            if not self.ajustarCreacionInodo(pathDisco, partition, indexInodoPadre, 0, nombreCarpeta):
                main.Scanner.error("MKDIR", "No se pudo crear la carpeta: " + nombreCarpeta, " por falta de espacio")
                return
        
            main.Scanner.mensaje("MKDIR", f"Se ha creado el la carpeta {nombreCarpeta} en la ruta {concatenadorDirectorio} con éxito")

    #<#> Validar si hay bloques ya creados con espacio libre en el inodo padre, si no hay se agrega bloque y se crea la carpeta
    def ajustarCreacionInodo(self, pathDisco, partition, indexInodoPadre, type, nombre):
        creacion = self.creacionNodoIndex(pathDisco, partition, indexInodoPadre, type, nombre)
        if not creacion: #<_> No hay espacio libre en nigun bloque de carpetas
            if not addBlockToInode(pathDisco, partition, indexInodoPadre): #<#> Agregar un bloque vacio al inodo padre
                return False
            #<_> Ahora si se puede crear la carpeta
            self.creacionNodoIndex(pathDisco, partition, indexInodoPadre, type, nombre)
        
        return True

    #<#> Analizar inodo donde se creara la carpeta o el archivo
    def creacionNodoIndex(self, pathDisco, partition, indexInodoPadre, typeInodo, nombreCreacion): 
        #ruta al disco, superbloque, indice del inodo, tipo de inodo [0 = carpeta, 1 = archivo], nombre del inodo, -r
        #<!> indexInodo siempre debe ser un index de nodo tipo carpeta

        sprBloque = Structs.SuperBloque()  # Crear una instancia de SuperBloque
        sprBloque = desempaquetarSuperBloque(pathDisco, partition)  # Obtener los bytes de la instancia

        #Obtener el inido segun el indice
        inodoTemp = Structs.Inodos()
        inodoTemp = getInodo(pathDisco, sprBloque, indexInodoPadre) #inodo segun el indice, [0 = raiz]

        if inodoTemp.i_type == 0: #si es una carpeta
            for i_block in inodoTemp.i_block: #contador de los bloques del inodo
                if i_block == -1: #si el bloque no tiene apuntador, continuar
                    continue
                
                #bloque con apuntador
                bloque = Structs.BloquesCarpetas()
                bloque = getBloqueCarpeta(pathDisco, sprBloque, i_block) #

                if bloque == None:
                    return False

                i_content = 0 #contador del contenido del bloque
                for content in bloque.b_content:
                    if content.b_inodo == -1: #Espacio libre en bloque de carpetas de raiz
                        self.addInodoNuevo(pathDisco, partition, nombreCreacion, i_content, bloque, i_block, typeInodo)
                        print("Se ha creado la carpeta: " + nombreCreacion + " con éxito")
                        return True
                    i_content += 1
        
        #<!> Si se llega a este punto, es porque no hay espacio en el bloque de carpetas
        return False

    #<#> Crear un inodo nuevo dado un bloque de carpetas con apuntador libre
    def addInodoNuevo(self, pathDisco, partition, rutaFinal, i_content, bloque, i_block, typeInodo):
        #<!> i_block es el indice del bloque de carpetas donde se creara el nuevo inodo

        sprBloque = Structs.SuperBloque()  # Crear una instancia de SuperBloque
        sprBloque = desempaquetarSuperBloque(pathDisco, partition)  # Obtener los bytes de la instancia

        #<+> Crear nuevo inodo  
        primerBloqueLibre = sprBloque.s_first_blo #primer bloque libre

        inodo = Structs.Inodos()
        inodo.i_uid = 1 #usuario root
        if self.logueado != None:
            inodo.i_gid = self.logueado.id

        inodo.i_gid = 1 #grupo root
        inodo.i_size = 0 #tamaño del archivo
        inodo.i_atime = sprBloque.s_umtime #ultima fecha de acceso
        inodo.i_ctime = sprBloque.s_umtime #ultima fecha de modificacion
        inodo.i_mtime = sprBloque.s_umtime #ultima fecha de creacion
        inodo.i_type = typeInodo # 0 = carpeta, 1 = archivo
        inodo.i_perm = 664 #permisos de lectura y escritura
        inodo.i_block[0] = primerBloqueLibre #Apuntador al primer bloque libre

        addInodo(pathDisco, partition, inodo)

        #Crear content
        content = Structs.Content()
        content.b_name = rutaFinal

        primerInodoLibre = sprBloque.s_first_ino #primer inodo libre
        content.b_inodo = primerInodoLibre #Apuntador al inodo recien creado


        #actualizar el bloque padre
        bloquePadre = getBloqueCarpeta(pathDisco, sprBloque, i_block)
        bloquePadre.b_content[i_content] = content
        updateBloque(sprBloque, pathDisco, bloquePadre, i_block) 

        #Crear el primer bloque del inodo recien creado
        bloque = Structs.BloquesCarpetas()
        if typeInodo == 1: #si es una carpeta, crear su bloque
            bloque = Structs.BloquesArchivos()
        addBloque(pathDisco, partition, bloque)

        return True


    

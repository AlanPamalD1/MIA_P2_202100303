import Structs
import struct

#<#> MANEJO DEL SUPER BLOQUE

def desempaquetarSuperBloque(path, p):
    try:
        sprTemp = Structs.SuperBloque()  # Crear una instancia de SuperBloque
        bytes_super_bloque = bytes(sprTemp)  # Obtener los bytes de la instancia

        recuperado = bytearray(len(bytes_super_bloque))  # Crear un bytearray del mismo tamaño
        with open(path, "rb") as archivo:
            archivo.seek(p.part_start - 1)
            archivo.readinto(recuperado)
        
        # Desempaquetar los datos del bytearray recuperado
        sprTemp.s_filesystem_type = struct.unpack("<i", recuperado[:4])[0]
        sprTemp.s_inodes_count = struct.unpack("<i", recuperado[4:8])[0]
        sprTemp.s_blocks_count = struct.unpack("<i", recuperado[8:12])[0]
        sprTemp.s_free_blocks_count = struct.unpack("<i", recuperado[12:16])[0]
        sprTemp.s_free_inodes_count = struct.unpack("<i", recuperado[16:20])[0]
        sprTemp.s_mtime = struct.unpack("<d", recuperado[20:28])[0]
        sprTemp.s_umtime = struct.unpack("<d", recuperado[28:36])[0]
        sprTemp.s_mnt_count = struct.unpack("<i", recuperado[36:40])[0]
        sprTemp.s_magic = struct.unpack("<i", recuperado[40:44])[0]
        sprTemp.s_inode_size = struct.unpack("<i", recuperado[44:48])[0]
        sprTemp.s_block_size = struct.unpack("<i", recuperado[48:52])[0]
        sprTemp.s_first_ino = struct.unpack("<i", recuperado[52:56])[0]
        sprTemp.s_first_blo = struct.unpack("<i", recuperado[56:60])[0]
        sprTemp.s_bm_inode_start = struct.unpack("<i", recuperado[60:64])[0]
        sprTemp.s_bm_block_start = struct.unpack("<i", recuperado[64:68])[0]
        sprTemp.s_inode_start = struct.unpack("<i", recuperado[68:72])[0]
        sprTemp.s_block_start = struct.unpack("<i", recuperado[72:76])[0] 
        return sprTemp
    except Exception as e:
        print(e) 
        return None
    finally:
        archivo.close()

def actualizarSuperBloqueEnParticion(path, partition, newSB):
    try:
        with open(path, "rb+") as bfile:
            bfile.seek(partition.part_start - 1)
            bfile.write(bytes(newSB))
    
    except Exception as e:
        print("MBR", "Error al actualizar el super bloque en la paticion: %s" % partition.part_name)
        print(e)
    finally:
        bfile.close()

#<#> MANEJO DE INODOS Y BLOQUES

#<*> BLOQUES

def addBloque(path, partition, bloque):

    sprBloque = Structs.SuperBloque()
    sprBloque = desempaquetarSuperBloque(path, partition)
    tamanioBloques = sprBloque.s_block_size
    bloquesOcupados = sprBloque.s_blocks_count - sprBloque.s_free_blocks_count

    print("Agregando el bloque No. %d" % bloquesOcupados)
    print(bloque)

    try: #escribir los datos de los inodos y bloques en el archivo
        with open(path, "rb+") as bfiles:
            bfiles.seek(sprBloque.s_block_start + (tamanioBloques * bloquesOcupados))
            bfiles.write(bytes(bloque))
    except Exception as e:
        print(e)
    finally:
        bfiles.close()

    #actualizar superbloque
    sprBloque.s_free_blocks_count -= 1
    sprBloque.s_first_blo += 1

    #actualizar el superbloque en la particion
    actualizarSuperBloqueEnParticion(path, partition, sprBloque)

    #actualizar el bitmap de bloques
    addBloqueBitmap(path, partition, 1)

def getBloqueCarpeta(path, sprBloque, num):
    sizeBloques = len(bytes(Structs.BloquesCarpetas()))
    bloqueObtenido = Structs.BloquesCarpetas() #crear una instancia de inodo
    sizeContent = len(bytes(Structs.Content()))
    try:
        with open(path, "rb+") as bfiles:
            bfiles.seek(sprBloque.s_block_start + (sizeBloques * num)) #posicionarse en el inicio del bloque segun el numero
            bloque_data  = bfiles.read(sizeBloques) #leer el inodo
            # Ahora, debes desempaquetar los datos en la instancia de BloquesCarpetas
            for i in range(4):
                content_data = bloque_data[i * sizeContent: (i + 1) * sizeContent]
                content = Structs.Content()
                content.b_name = content_data[:12].decode('utf-8').rstrip('\0')
                content.b_inodo = struct.unpack("<i", content_data[12:])[0]
                bloqueObtenido.b_content[i] = content
        
        return bloqueObtenido
    except Exception as e:
        print(e)
        return None
    finally:
        bfiles.close()
    
def getBloqueArchivo(path, sprBloque, num):
    sizeBloques = len(bytes(Structs.BloquesCarpetas()))
    bloqueObtenido = Structs.BloquesArchivos()
    try:
        bytes_bloque_archivo = bytes(bloqueObtenido)
        content_data = bytearray(len(bytes_bloque_archivo))
        with open(path, "rb+") as bfiles:
            bfiles.seek(sprBloque.s_block_start + (sizeBloques * num)) #posicionarse en el inicio del bloque segun el numero
            bfiles.readinto(content_data) #leer el inodo
            # Ahora, debes desempaquetar los datos en la instancia de BloquesCarpetas
            bloqueObtenido.b_content = struct.unpack("<64s", content_data[:64])[0] #64 bytes de datos

        return bloqueObtenido
    except Exception as e:
        print(e)
        return None
    finally:
        bfiles.close()

def updateBloque(sprBloque, pathDisco, bloque, i_block):
    print("Actualizando bloque No. %d" % i_block)
    print(bloque)
    tamanioBloquesCarpetas = len(bytes(Structs.BloquesCarpetas()))
    inicioBloque = sprBloque.s_block_start 

    try: #escribir los datos del bloque de carpetas
        with open(pathDisco, "rb+") as bfiles:                 
            bfiles.seek(inicioBloque + (tamanioBloquesCarpetas * i_block))
            bfiles.write(bytes(bloque)) 
    except Exception as e:
        print(e)
    finally:
        bfiles.close()

def addContentToBloqueArchivo(pathDisco, partition, indexInodo, contenido):
    sprBloque = Structs.SuperBloque()  # Crear una instancia de SuperBloque
    sprBloque = desempaquetarSuperBloque(pathDisco, partition)
    
    #remplazar saltos de linea por \n en contenido
    #contenido = contenido.replace("\n", "\\n")

    inodo = Structs.Inodos()
    inodo = getInodo(pathDisco, sprBloque, indexInodo)
    inodo.i_size += len(contenido)

    #separar contenido en 64 caracteres
    lista_contenido = []
    i = 0
    while i < len(contenido):
        lista_contenido.append(contenido[i:i+64])
        i += 64
    
    #Si la lista tiene mas de 15 elementos, solo se tomaran los primeros 15
    if len(lista_contenido) > 15:
        lista_contenido = lista_contenido[:15]

    indiceContent = 0

    for content in lista_contenido: #<#> Iterar con los contenidos
        apuntador = inodo.i_block[indiceContent]
        if apuntador != -1: #<#> Si el bloque tiene apuntador, se actualiza el bloque
            bloque = Structs.BloquesArchivos()
            bloque = getBloqueArchivo(pathDisco, sprBloque, apuntador)
            bloque.b_content = content
            updateBloque(sprBloque, pathDisco, bloque, apuntador)
        else: #<#> Sin apuntador, se crea un bloque
            #actualizar el inodo con el apuntador del bloque
            inodo.i_block[indiceContent] = sprBloque.s_first_blo

            bloque = Structs.BloquesArchivos()
            bloque.b_content = content
            addBloque(pathDisco, partition, bloque)

        indiceContent += 1
    
    #actualizar el inodo
    updateNodo(sprBloque, pathDisco, inodo, indexInodo)

def getContentBloqueArchivo(pathDisco, partition, indexInodo):
    sprBloque = Structs.SuperBloque()  # Crear una instancia de SuperBloque
    sprBloque = desempaquetarSuperBloque(pathDisco, partition)
    
    contenido = ""

    inodo = Structs.Inodos()
    inodo = getInodo(pathDisco, sprBloque, indexInodo)

    for i_block in inodo.i_block: #<#> Iterar con los contenidos
        if i_block != -1: #<#> Si el bloque tiene apuntador, se actualiza el bloque
            bloque = Structs.BloquesArchivos()
            bloque = getBloqueArchivo(pathDisco, sprBloque, i_block)
            contenido += bloque.b_content

    #remplazar \n por saltos de linea
    contenido = contenido.replace("\\n", "\n")
    
    return contenido

#<*> INODOS

def addInodo(path, partition, inode):
    sprBloque = Structs.SuperBloque()
    sprBloque = desempaquetarSuperBloque(path, partition)
    tamanioInodos = struct.calcsize("<iiiddd15ici")
    primerInodoLibre = sprBloque.s_first_ino #primer inodo libre 
    print("Agregando el inodo No. %d" % primerInodoLibre)
    print(inode)

    inodosOcupados = sprBloque.s_inodes_count - sprBloque.s_free_inodes_count   
    try: #escribir los datos de los inodos y bloques en el archivo
        with open(path, "rb+") as bfiles:                 
            bfiles.seek(sprBloque.s_inode_start + (tamanioInodos * inodosOcupados))
            bfiles.write(bytes(inode)) 
    except Exception as e:
        print(e)
    finally:
        bfiles.close()
    
    #actualizar superbloque
    sprBloque.s_free_inodes_count -= 1
    sprBloque.s_first_ino += 1

    #actualizar el superbloque en la particion
    actualizarSuperBloqueEnParticion(path, partition, sprBloque)

    #actualizar el bitmap de inodos con 1 inodo nuevo
    addInodoBitmap(path, partition, 1)

def getInodo(path, sprBloque, num):
    sizeInodos = struct.calcsize("<iiiddd15ici")
    try:
        with open(path, "rb+") as bfiles:
            bfiles.seek(sprBloque.s_inode_start + (sizeInodos * num)) #posicionarse en el inicio de cada inodo
            data = bfiles.read(sizeInodos) #leer el inodo

            inodo = Structs.Inodos() #crear una instancia de inodo
            # Usamos el mismo orden en que empaquetamos los datos
            inodo.i_uid = struct.unpack("<i", data[:4])[0]
            inodo.i_gid = struct.unpack("<i", data[4:8])[0]
            inodo.i_size = struct.unpack("<i", data[8:12])[0]
            inodo.i_atime = struct.unpack("<d", data[12:20])[0]
            inodo.i_ctime = struct.unpack("<d", data[20:28])[0]
            inodo.i_mtime = struct.unpack("<d", data[28:36])[0]
            inodo.i_block = list(struct.unpack("<15i", data[36:96]))
            inodo.i_type = struct.unpack("<B", data[96:97])[0]
            inodo.i_perm = struct.unpack("<i", data[97:101])[0]

            return inodo
    except Exception as e:
        print(e)
        return None
    finally:
        bfiles.close()

def getListaInodos(path, partition): #path, particion, tipo [0 = carpeta, 1 = archivo]

    sprBloque = Structs.SuperBloque()
    sprBloque = desempaquetarSuperBloque(path, partition)

    if sprBloque == None:
        return None

    numeroInodos = sprBloque.s_inodes_count - sprBloque.s_free_inodes_count #numero de inodos que hay en el sistema
    sizeInodos = len(bytes(Structs.Inodos())) #tamaño de los inodos

    LInodos = []
    try:
        with open(path, "rb+") as bfile:
            for i in range(numeroInodos):
                print("Leyendo inodo: %d" % i)
                bfile.seek(sprBloque.s_inode_start + (sizeInodos * i)) #posicionarse en el inicio de cada inodo
                data = bfile.read(sizeInodos) #leer el inodo

                inodo = Structs.Inodos() #crear una instancia de inodo
                # Usamos el mismo orden en que empaquetamos los datos
                inodo.i_uid = struct.unpack("<i", data[:4])[0]
                inodo.i_gid = struct.unpack("<i", data[4:8])[0]
                inodo.i_size = struct.unpack("<i", data[8:12])[0]
                inodo.i_atime = struct.unpack("<d", data[12:20])[0]
                inodo.i_ctime = struct.unpack("<d", data[20:28])[0]
                inodo.i_mtime = struct.unpack("<d", data[28:36])[0]
                inodo.i_block = list(struct.unpack("<15i", data[36:96]))
                inodo.i_type = struct.unpack("<B", data[96:97])[0]
                inodo.i_perm = struct.unpack("<i", data[97:101])[0]

                LInodos.append(inodo) #agregar el inodo a la lista de inodos
        
        return LInodos
    except Exception as e:
        print(e)
        return []
    finally:
        bfile.close()

def updateNodo(sprBloque, pathDisco, inodo, i_node):
    print("Actualizando inodo No. %d" % i_node)
    print(inodo)
    tamanioInodos = struct.calcsize("<iiiddd15ici")
    inicioInodo = sprBloque.s_inode_start

    try: #escribir los datos del bloque de carpetas
        with open(pathDisco, "rb+") as bfiles:                 
            bfiles.seek(inicioInodo + (tamanioInodos * i_node))
            bfiles.write(bytes(inodo)) 
    except Exception as e:
        print(e)
    finally:
        bfiles.close()

def addBlockToInode(pathDisco, partition, indexInodo, type=0):
    sprBloque = Structs.SuperBloque()  # Crear una instancia de SuperBloque
    sprBloque = desempaquetarSuperBloque(pathDisco, partition)  # Obtener los bytes de la instancia

    #Obtener el inido segun el indice
    inodoTemp = Structs.Inodos()
    inodoTemp = getInodo(pathDisco, sprBloque, indexInodo) #inodo segun el indice, [0 = raiz]

    indiceBloque = 0
    for i_block in inodoTemp.i_block: #contador de los bloques del inodo

        if i_block == -1: #si el bloque no tiene apuntador, se creara un bloque
            
            #actualizar el inodo
            inodoTemp.i_block[indiceBloque] = sprBloque.s_first_blo
            
            updateNodo(sprBloque, pathDisco, inodoTemp, indexInodo)

            bloque = Structs.BloquesCarpetas()
            if type == 1: #si es una carpeta, crear su bloque
                bloque = Structs.BloquesArchivos()
            
            addBloque(pathDisco, partition, bloque)
            return True
        indiceBloque += 1

    #Se llego al limite de bloques del inodo
    return False

#<#> Añadir datos a bitmaps

def addBloqueBitmap(path, partition,  num):

    sprBloque = Structs.SuperBloque()
    sprBloque = desempaquetarSuperBloque(path, partition)

    sizeBitmap = sprBloque.s_inode_start - sprBloque.s_bm_block_start

    texto = ""
    if num > 0:
        valor = b'1'
        try:            
            with open(path, "rb+") as bfiles:
                bfiles.seek(sprBloque.s_bm_block_start)
                texto = bfiles.read(sizeBitmap) #leer el bitmap de bloques

                #encontrar el primer ultimo 1
                pos = texto.rfind(b'1') + 1
                
                #coloar el valor el numero de veces que se requiera
                texto = texto[:pos] + valor*num + texto[pos+num:]
                pos = texto.find(b'1')

                bfiles.seek(sprBloque.s_bm_block_start)
                bfiles.write(texto) #escribir el bitmap de bloques

            return
        except Exception as e:
            print(e)
        finally:
            bfiles.close()
    else: #Eliminar inodos
        valor = b'0'
        try:
            with open(path, "rb+") as bfiles:
                
                bfiles.seek(sprBloque.s_bm_block_start)
                texto = bfiles.read(sizeBitmap) #leer el bitmap de inodos

                #encontrar el primer ultimo 1
                pos = texto.rfind(b'1')

                if pos == -1: #No hay inodos para eliminar
                    return
                
                if num > pos: #si el numero de inodos a eliminar es mayor al numero de inodos que hay
                    return

                #colocar el valor el numero de veces que se requiera
                texto = texto[:pos-num] + valor*num + texto[pos:]

                bfiles.seek(sprBloque.s_bm_block_start)
                bfiles.write(texto) #escribir el bitmap de inodos

            return
        except Exception as e:
            print(e)
        finally:
            bfiles.close()
   
def addInodoBitmap(path, partition, num):

    sprBloque = Structs.SuperBloque()
    sprBloque = desempaquetarSuperBloque(path, partition)
    
    sizeBitmap = sprBloque.s_bm_block_start - sprBloque.s_bm_inode_start

    if num > 0: #Agregar inodos
        valor = b'1'
        try:            
            with open(path, "rb+") as bfiles:
                
                bfiles.seek(sprBloque.s_bm_inode_start)
                texto = bfiles.read(sizeBitmap) #leer el bitmap de inodos

                #encontrar el primer ultimo 1
                pos1 = texto.rfind(b'1') + 1
                
                #coloar el valor el numero de veces que se requiera
            
                texto = texto[:pos1] + valor*num + texto[pos1+num:]

                bfiles.seek(sprBloque.s_bm_inode_start)
                bfiles.write(texto) #escribir el bitmap de inodos

            return
        except Exception as e:
            print(e)
        finally:
            bfiles.close()
    else: #Eliminar inodos
        valor = b'0'
        try:
            with open(path, "rb+") as bfiles:
                
                bfiles.seek(sprBloque.s_bm_inode_start)
                texto = bfiles.read(sizeBitmap) #leer el bitmap de inodos

                #encontrar el primer ultimo 1
                pos1 = texto.rfind(b'1')

                if pos1 == -1: #No hay inodos para eliminar
                    return
                
                if num > pos1: #si el numero de inodos a eliminar es mayor al numero de inodos que hay
                    return

                #colocar el valor el numero de veces que se requiera
                texto = texto[:pos1-num] + valor*num + texto[pos1:]

                bfiles.seek(sprBloque.s_bm_inode_start)
                bfiles.write(texto) #escribir el bitmap de inodos

            return
        except Exception as e:
            print(e)
        finally:
            bfiles.close()
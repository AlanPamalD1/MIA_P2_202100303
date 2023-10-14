from datetime import datetime
import os
import sys
import time
import random
import Structs
import struct
import Scanner as Scanner
from graphviz import Digraph
from Ext2 import *

class Disk:
    def __init__(self):
        pass
    
    #<b> CREACION PARTICIONES

    @staticmethod
    def generarParticion(s, u, p, t, f, n, a): #size, unit, path, type, fit, name, add
        try:
            i = int(s)
            if i <= 0:
                raise RuntimeError("-size debe de ser mayor que 0")
            
            if u.lower() in ["b", "k", "m"]:
                if u.lower() != "b":
                    if u.lower() == "k":
                        i *= 1024
                    else:
                        i *= 1024 * 1024
            else:
                raise RuntimeError("-unit no contiene los valores esperados...")
            
            if p[:1] == "\"":
                p = p[1:-1]
            
            if t.lower() not in ["p", "e", "l"]:
                raise RuntimeError("-type no contiene los valores esperados...")
            
            if f.lower() not in ["bf", "ff", "wf"]:
                raise RuntimeError("-fit no contiene los valores esperados...")
            
            try:
                mbr = Disk.desempaquetarMbr(p)

            except Exception as e:
                print(e)

            partitions = mbr.getParticiones()
            between = []
            used = 0
            ext = 0
            c = 1
            base = sys.getsizeof(mbr) 
            extended = Structs.Particion()
            for prttn in partitions:
                if prttn.part_status == '1':
                    trn = Structs.Transition()
                    trn.partition = c
                    trn.start = prttn.part_start
                    trn.end = prttn.part_start + prttn.part_size
                    trn.before = trn.start - base
                    base = trn.end
                    if used != 0:
                        between[used - 1].after = trn.start - (between[used - 1].end)
                    between.append(trn)
                    used += 1

                    if prttn.part_type.lower() == 'e':
                        ext += 1
                        extended = prttn
                else: 
                    partitions[c - 1] = Structs.Particion()

                if used == 4 and t.lower() != "l":
                    raise RuntimeError("Limite de particiones alcanzado")
                elif ext == 1 and t.lower() == "e":
                    raise RuntimeError("Solo se puede crear una particion Extendida.")

                mbr.mbr_Partition_1 = partitions[0]
                mbr.mbr_Partition_2 = partitions[1]
                mbr.mbr_Partition_3 = partitions[2]
                mbr.mbr_Partition_4 = partitions[3]
                
                c += 1
            
            if ext == 0 and t.lower() == "l":
                raise RuntimeError("No existe particion Extendida para crear la Logica")
            
            if used != 0:
                between[-1].after = mbr.mbr_tamano - between[-1].end
            
            try:
                Disk.buscarParticiones(mbr, n, p)
                Scanner.mensaje("FDISK", "El nombre: %s ya existe en el disco" %n)
                return
            except Exception as e:
                print(e)
            
            temporal = Structs.Particion()
            temporal.part_status = '1'
            temporal.part_size = i
            temporal.part_type = t[0].upper()
            temporal.part_fit = f[0].upper()
            temporal.part_name = n
            
            if t.lower() == "l": 
                Disk.generarParticionLogica(temporal, extended, p)
                return
            
            mbr = Disk.ajustar(mbr, temporal, between, partitions, used)
            try:
                with open(p, "rb+") as bfile:
                    bfile.write(mbr.__bytes__())
                    if t.lower() == "e":
                        ebr = Structs.EBR()
                        ebr.part_start = startValue 
                        bfile.seek(startValue, 0)
                        bfile.write(ebr.__bytes__())
                        Scanner.mensaje("FDISK", "partición extendida: %s creada correctamente" %n)
                        return
                    Scanner.mensaje("FDISK", "partición primaria: %s creada correctamente" %n)
            finally:
                bfile.close()  # Cierra el archivo
        except ValueError as e: 
            Scanner.error("FDISK", "-size debe ser un entero")
        except Exception as e: 
            Scanner.error("FDISK", str(e))

    @staticmethod
    def generarParticionLogica(partition, ep, p): #temporal, extended, path
        nlogic = Structs.EBR()
        nlogic.part_status = '1'
        nlogic.part_fit = partition.part_fit
        nlogic.part_size = partition.part_size
        nlogic.part_next = -1
        nlogic.part_name = partition.part_name

        try:
            with open(p, "rb+") as file:
                file.seek(0)
                tmp = Structs.EBR()
                file.seek(ep.part_start -1)
                tmp_data = file.read(struct.calcsize("c2s3i3i16s"))
                tmp.__setstate__(tmp_data)
                size = 0
                while True:
                    size += struct.calcsize("c2s3i3i16s") + tmp.part_size
                    if (tmp.part_status == '0' or tmp.part_status == '\x00') and tmp.part_next == -1:
                        nlogic.part_start = tmp.part_start
                        nlogic.part_next = nlogic.part_start + nlogic.part_size + struct.calcsize("c2s3i3i16s")
                        if (ep.part_size - size) <= nlogic.part_size:
                            raise RuntimeError("no hay espacio para más particiones lógicas")
                        file.seek(nlogic.part_start-1) 
                        file.write(nlogic.__bytes__())
                        file.seek(nlogic.part_next)
                        addLogic = Structs.EBR()
                        addLogic.part_status = '0'
                        addLogic.part_next = -1
                        addLogic.part_start = nlogic.part_next
                        file.seek(addLogic.part_start)
                        file.write(addLogic.__bytes__())
                        name = nlogic.part_name
                        Scanner.mensaje("Particion", "partición lógica: %s creada correctamente" %name)
                        return
                    file.seek(tmp.part_next-1)
                    tmp_data = file.read(struct.calcsize("c2s3i3i16s"))
                    tmp.__setstate__(tmp_data)
        finally:
            file.close()  # Cierra el archivo

    @staticmethod
    def actualizarMbr(path, disco):
        
        #Actualizar datos en disco
        try:
            with open(path, "rb+") as bfile: #Abrir el archivo en modo lectura binaria
                bfile.write(disco.__bytes__()) #Escribir el mbr actualizado en el archivo
            
            Scanner.mensaje("FDISK", "Particiones actualizadas correctamente en el disco: %s" %path)
            return
        except Exception as e:
            Scanner.error("MBR", "Error al actualizar particiones en el disco: %s" % path)
            print(e)
        finally:
            bfile.close()

    @staticmethod
    def getLogicas(partition, path):
        ebrs = []
        try: 
            with open(path, "rb+") as file:
                start_position = partition.part_start -1
                if start_position < 0:
                    start_position = 0
                    
                file.seek(start_position, 0)
                tmp_data = file.read(struct.calcsize("c2s3i3i16s"))

                while len(tmp_data) == struct.calcsize("c2s3i3i16s"):
                    tmp = Structs.EBR()
                    tmp.__setstate__(tmp_data)
                    if tmp.part_next != -1:
                        ebrs.append(tmp)
                        file.seek(tmp.part_next-1, 0)
                        tmp_data = file.read(struct.calcsize("c2s3i3i16s"))
                    else:
                        break
        except Exception as e:
            print(e)
            Scanner.error("EBR", "Error al leer el disco en la ruta: %s" % path)
            return [] # Si no se pudo leer el disco, se retorna una lista vacia
        finally:
            file.close()  # Cierra el archivo

        return ebrs

    @staticmethod
    def buscarParticiones(mbr, name, path):
        partitions = mbr.getParticiones() #Obtener lista de particiones
        ext = False
        extended = Structs.Particion()

        for partition in partitions:
            if partition.part_status == '1':
                if partition.part_name == name:
                    return partition
                elif partition.part_type == 'E':
                    ext = True
                    extended = partition

        if ext:
            ebrs = Disk.getLogicas(extended, path)
            for ebr in ebrs:
                if ebr.part_status == '1':
                    if ebr.part_name == name:
                        tmp = Structs.Particion()
                        tmp.part_status = '1'
                        tmp.part_type = 'L'
                        tmp.part_fit = ebr.part_fit
                        tmp.part_start = ebr.part_start
                        tmp.part_size = ebr.part_size
                        tmp.part_name = ebr.part_name
                        return tmp
        raise RuntimeError("Creando la partición: " + name + "...")
    
    @staticmethod
    def existParticion(mbr, name, path):
        partitions = mbr.getParticiones()
        ext = False
        extended = Structs.Partition()
        
        for partition in partitions:
            if partition.part_status == '1':
                if partition.part_name == name:
                    return True
                elif partition.part_type == 'E':
                    ext = True
                    extended = partition

        if ext:
            ebrs = Disk.getLogicas(extended, path)
            for ebr in ebrs:
                if ebr.part_status == '1':
                    if ebr.part_name == name:
                        tmp = Structs.Partition()
                        tmp.part_status = '1'
                        tmp.part_type = 'L'
                        tmp.part_fit = ebr.part_fit
                        tmp.part_start = ebr.part_start
                        tmp.part_size = ebr.part_size
                        tmp.part_name = ebr.part_name
                        return True
        
        return False

    @staticmethod
    def buscarNumParticion(mbr, name, path):
        partitions = mbr.getParticiones()
        ext = False
        extended = Structs.Partition()

        contador = 1
        for partition in partitions:
            if partition.part_status == '1':
                if partition.part_name == name:
                    return contador
                elif partition.part_type == 'E':
                    ext = True
                    extended = partition
            contador += 1
        
        contador = 1
        if ext:
            ebrs = Disk.getParticionesLogicas(extended, path)
            for ebr in ebrs:
                if ebr.part_status == '1':
                    if ebr.part_name == name:
                        return contador
            
            contador += 1
        
        raise RuntimeError("No se encontró el id de la particion con nombre: " + name ) 

    @staticmethod
    def desempaquetarMbr(path):
        mbr = Structs.MBR()
        try:
            with open(path, "rb") as file:
                mbr_data = file.read()
                mbr.mbr_tamano = struct.unpack("<i", mbr_data[:4])[0]
                mbr.mbr_fecha_creacion = struct.unpack("<i", mbr_data[4:8])[0]
                mbr.mbr_disk_signature = struct.unpack("<i", mbr_data[8:12])[0]
                mbr.disk_fit = mbr_data[12:14].decode('utf-8')

                partition_size = struct.calcsize("<iii16s")*4
                partition_data = mbr_data[14:14 + partition_size]
                mbr.mbr_Partition_1.__setstate__(partition_data[0:28]) 
                mbr.mbr_Partition_2.__setstate__(partition_data[27:56]) 
                mbr.mbr_Partition_3.__setstate__(partition_data[54:84]) 
                mbr.mbr_Partition_4.__setstate__(partition_data[81:112])
            
            return mbr
        except IOError as e:
            # Maneja otros errores de E/S (lectura/escritura)
            Scanner.error("E/S", "Error de escritura y/o lectura con el archivo.")
            print(e)
        except Exception as e:
            print(e)
            return
        finally:
            file.close()  # Cierra el archivo

    #<b> Modificar las particiones
       
    @staticmethod
    def ajustar(mbr, p, t, ps, u): #mbr, temporal, between, partitions, used
        if u == 0:
            p.part_start = sys.getsizeof(mbr) + struct.calcsize("<iii16s")*4
            update_start_value(p.part_start)
            mbr.mbr_Partition_1 = p
            return mbr
        else:
            usar = Structs.Transition()
            c = 0
            for tr in t:
                if c == 0:
                    usar = tr
                    c += 1
                    continue

                if mbr.disk_fit[0].upper() == 'F':
                    if usar.before >= p.part_size or usar.after >= p.part_size:
                        break
                    usar = tr
                elif mbr.disk_fit[0].upper() == 'B':
                    if usar.before < p.part_size or usar.after < p.part_size:
                        usar = tr
                    else:
                        if tr.before >= p.part_size or tr.after >= p.part_size:
                            b1 = usar.before - p.part_size
                            a1 = usar.after - p.part_size
                            b2 = tr.before - p.part_size
                            a2 = tr.after - p.part_size

                            if (b1 < b2 and b1 < a2) or (a1 < b2 and a1 < a2):
                                c += 1
                                continue
                            usar = tr
                elif mbr.disk_fit[0].upper() == 'W':
                    if usar.before < p.part_size or usar.after < p.part_size:
                        usar = tr
                    else:
                        if tr.before >= p.part_size or tr.after >= p.part_size:
                            b1 = usar.before - p.part_size
                            a1 = usar.after - p.part_size
                            b2 = tr.before - p.part_size
                            a2 = tr.after - p.part_size
                            if (b1 > b2 and b1 > a2) or (a1 > b2 and a1 > a2):
                                c += 1
                                continue
                            usar = tr
                c += 1

            if usar.before >= p.part_size or usar.after >= p.part_size:
                if mbr.disk_fit[0].upper() == 'F':
                    if usar.before >= p.part_size:
                        p.part_start = (usar.start - usar.before)
                        update_start_value(p.part_start)
                    else:
                        p.part_start = usar.end
                        update_start_value(p.part_start)
                elif mbr.disk_fit[0].upper() == 'B':
                    b1 = usar.before - p.part_size
                    a1 = usar.after - p.part_size

                    if (usar.before >= p.part_size and b1 < a1) or usar.after < p.part_start:
                        p.part_start = (usar.start - usar.before)
                        update_start_value(p.part_start)
                    else:
                        p.part_start = usar.end
                        update_start_value(p.part_start)
                elif mbr.disk_fit[0].upper() == 'W':
                    b1 = usar.before - p.part_size
                    a1 = usar.after - p.part_size

                    if (usar.before >= p.part_size and b1 > a1) or usar.after < p.part_start:
                        p.part_start = (usar.start - usar.before)
                        update_start_value(p.part_start)
                    else:
                        p.part_start = usar.end
                        update_start_value(p.part_start)

                partitions = [Structs.Particion() for _ in range(4)]

                for i in range(len(ps)):
                    partitions[i] = ps[i]
                
                for i in range(len(partitions)):
                    if partitions[i].part_status == '0':
                        partitions[i] = p
                        break
                mbr.mbr_Partition_1 = partitions[0]
                mbr.mbr_Partition_2 = partitions[1]
                mbr.mbr_Partition_3 = partitions[2]
                mbr.mbr_Partition_4 = partitions[3]
                return mbr
            else:
                raise RuntimeError("no hay espacio suficiente")
    
    #<+> FUNCIONES
    #<b> MKDISK
    @staticmethod
    def mkdisk(tokens): #Funcion mdisk
        size = ""
        fit = ""
        unit = ""
        path = ""

        required = Scanner.required_values("mkdisk") #size, path

        for token in tokens:
            tk = token[:token.find('=')]
            token = token[token.find('=') + 1:]

            if Scanner.comparar(tk, "fit"):
                if fit:
                    Scanner.error("MKDISK","Parametro f repetido en el comando.")
                    return
                fit = token
                
            elif Scanner.comparar(tk, "size"):
                if size:
                    Scanner.error("MKDISK","Parametro size repetido en el comando.")
                    return
                if tk in required:
                    required.remove(tk)
                    size = token

            elif Scanner.comparar(tk, "unit"):
                if unit:
                    Scanner.error("MKDISK","Parametro unit repetido en el comando.")
                    return
                if tk in required:
                    required.remove(tk)
                    unit = token
            elif Scanner.comparar(tk, "path"):
                if unit:
                    Scanner.error("MKDISK","Parametro path repetido en el comando.")
                    return
                if tk in required:
                    required.remove(tk)
                    path = token
            else:
                Scanner.mensaje("MKDISK", "no se esperaba el parametro %s" % tk)
                break

        if not fit:
            fit = "FF"
        if not unit:
            unit = "M"

        if required:
            for r in required:
                Scanner.error("MKDISK", "Falta el parametro %s en el comando" % r)
            return

        
        if fit not in ["BF", "FF", "WF"]:
            Scanner.error("MKDISK", "Valor ingresado no válido para  el parametro FIT")
            return
        if unit not in ["K", "M"]:
            Scanner.error("MKDISK", "Valor ingresado no válido para  el parametro UNIT")
            return
        
        print("se va a crear el disco con los siguientes parametros")
        print("fit: ", fit)
        print("size: ", size)
        print("unit: ", unit)
        print("path: ", path)
        Disk.make(size, fit, unit, path)

    @staticmethod
    def make(s, f, u, path):
        disco = Structs.MBR()
        try:
            size = int(s)
            if size <= 0:
                Scanner.error("MKDISK", "El parámetro size del comando MKDISK debe ser mayor a 0")
                return

            if u == "M":
                size = 1024 * 1024 * size
            elif u == "K":
                size = 1024 * size

            f = f[0].upper()
            disco.mbr_tamano = size
            disco.mbr_fecha_creacion = int(time.time())
            disco.disk_fit = f
            disco.mbr_disk_signature = random.randint(100, 9999)

            if os.path.exists(path):
                Scanner.error("MKDISK", "Disco ya existente en la ruta: "+path)
                return

            folder_path = os.path.dirname(path)
            os.makedirs(folder_path, exist_ok=True)

            disco.mbr_Partition_1 = Structs.Particion()
            disco.mbr_Partition_2 = Structs.Particion()
            disco.mbr_Partition_3 = Structs.Particion()
            disco.mbr_Partition_4 = Structs.Particion()

            if path.startswith("\""):
                path = path[1:-1]

            if not path.lower().endswith(".dsk"):
                Scanner.error("MKDISK", "Extensión de archivo no válida para la creación del Disco.")
                return

            # Manejar carpeta
            carpetaReporte = os.path.dirname(path)
            if not os.path.exists(carpetaReporte): #Si no existe la carpeta, se crea
                os.makedirs(carpetaReporte, exist_ok=True)

            try:
                with open(path, "w+b") as file:
                    file.write(b"\x00")
                    file.seek(size - 1)
                    file.write(b"\x00")
                    file.seek(0)
                    file.write(bytes(disco))
                Scanner.mensaje("MKDISK", "Disco creado exitosamente en la ruta: %s " %path)
            except Exception as e:
                print(e)
                Scanner.error("MKDISK", "Error al crear el disco en la ruta: "+path)
            finally:
                file.close()  # Cierra el archivo
        except ValueError:
            Scanner.error("MKDISK", "El parámetro size del comando MKDISK debe ser un número entero")
    
    #<b> RMDISK
    @staticmethod
    def rmdisk(tokens):
        path = ""
        required = Scanner.required_values("rmdisk") #path

        for token in tokens:
            tk, _, token = token.partition("=")
            if Scanner.comparar(tk, "path"):
                if tk in required:
                    required.remove(tk)
                    path = token
            else:
                path = ""
                Scanner.error("RMDISK", "No se esperaba el parametro %s" % tk) 
                return

        if required:
            for r in required:
                Scanner.error("RMDISK", "Falta el parametro %s en el comando" % r)
            return

            
        if path:
            if path.startswith("\"") and path.endswith("\""):
                path = path[1:-1]

            if not os.path.exists(path): #Si no existe la carpeta, se crea
                Scanner.error("RMDISK", "No existe el disco en la ruta %s" % path)
                return

            try:
                if os.path.isfile(path):
                    if not path.endswith(".dsk"):
                        Scanner.error("RMDISK", "El archivo debe de tener la extensión .dsk")
                    # Eliminar el archivo
                    os.remove(path)
                    Scanner.mensaje("RMDISK", "Disco eliminado de la ruta %s" % path)
                else:
                    Scanner.error("RMDISK", "No existe el disco en la ruta %s" % path)
            except Exception as e:
                print(e)
                Scanner.error("RMDISK", "Error al eliminar el disco en la ruta: %s" % path)

    #<b> REP
    @staticmethod
    def rep(tokens, mountInstance): #name, path, id
        name = ""
        path = ""
        id_part = ""
        ruta = ""

        required = Scanner.required_values("rep")
        
        for token in tokens:
            
            id = (token[:token.find('=')]).lower()
            token = token[token.find('=')+1:]

            if token.startswith("\"") and token.endswith("\""):
                token = token[1:-1]

            if Scanner.comparar(id, "name"):
                if id in required:
                    required.remove(id)
                name = token
            elif Scanner.comparar(id, "path"):
                if id in required:
                    required.remove(id)
                path = token
            elif Scanner.comparar(id, "id"):
                if id in required:
                    required.remove(id)
                id_part = token
            elif Scanner.comparar(id, "ruta"):
                ruta = token
            else:
                Scanner.mensaje("REP", "no se esperaba el parametro %s" % token)
                break
        
        if required:
            for r in required:
                Scanner.error("REP", "Falta el parametro %s en el comando" % r)
            return

        if name not in ["mbr","disk", "bm_inode", "bm_block", "tree", "sb", "file"]:
            Scanner.error("REP", "El parametro name debe ser uno de los siguientes: mbr, ebr, disk, inode, journaling, block, bm_inode, bm_block, tree, sb, file, ls")
            return
        
        if name in ["file", "ls"]:
            if not ruta:
                Scanner.error("REP", "El parametro ruta es obligatorio para los comandos con name file y ls")
                return

        try: 

            pathDisco, particion = mountInstance.getmount(id_part)

            mbr_format = "<iiiiB"
            mbr_size = struct.calcsize(mbr_format)
            try:
                with open(pathDisco, "rb") as file:
                    mbr_data = file.read(mbr_size)
                    mbr = Structs.MBR()
                    (mbr.mbr_tamano, mbr.mbr_fecha_creacion, mbr.mbr_disk_signature, disk_fit, *_) = struct.unpack(mbr_format, mbr_data)
                    mbr.disk_fit = chr(disk_fit % 128)
            finally:
                file.close()  # Cierra el archivo

            # Desempaquetar datos de MBR
            try:
                mbr = Disk.desempaquetarMbr(pathDisco)
            except Exception as e:
                print(e)
                return
            
            # Manejar carpeta
            carpetaReporte = os.path.dirname(path)
            if not os.path.exists(carpetaReporte): #Si no existe la carpeta, se crea
                os.makedirs(carpetaReporte, exist_ok=True)
            
            identificador =  '[' + id_part + ']'
            Disk.graficarReporte(pathDisco, path, name, mbr, particion, ruta, identificador)
            return
        
        except Exception as e:
            Scanner.error("REP", "Error al leer el disco en la ruta: %s" % path)
            print("ERROR: ",e)
           
    @staticmethod
    def graficarReporte(pathDisco, path, name, mbr, particion, ruta, identificador): 
        #path del disco en el sistema, path del reporte, nombre del reporte, mbr del disco, particion, ruta del archivo en el disco binario, identificador

        lista_particiones = mbr.getParticiones() #Obtener lista de particiones
        
        #todos los reportes se generaran en la carpeta home
        if path.startswith("/"):
            path = '/reportes' + path
        else:
            path = '/reportes/' + path
        
        #Quitar y guardar en otra variable la extension de path
        extension = os.path.splitext(path)[1][1:] #Obtener la extension del archivo sin el punto
        pathRep = path[:path.rfind(".")] #Quitar la extension del path
        pathRep += identificador #Agregar identificador reporte
        pathFinal = pathRep + "." + extension #Agregar la extension al path

        #Nombre del disco
        nombreDisco = os.path.basename(pathDisco)

        sprBloque = desempaquetarSuperBloque(pathDisco, particion) #Obtener el super bloque de la particion

        # colores de las celdas de las columnas segun el tipo de particion
        colores = {
            "MBR": '#F5B041', #<td> Naranja
            "P": '#836096', #<_> Morado
            "E": '#C70039', #<!> Rojo
            "L": '#6585a5', #<?> Azul
            "EBR": '#4477CE', #<?> Azul
            "Libre": '#A8A196', # Gris
            "SBloque": '#79AC78', #<td> Naranja
            "Inodo": '#3085C3', #<?> Azul
            "BloqueC": '#79AC78', #<*> Verde
            "BloqueA": '#F4E869', #<+> Amarillo
        }

        #Generar reporte en graphviz segun el tipo

        match name:
            case "mbr": #Reporte del disco
                # Grafo 
                graph = Digraph('G',format=extension, engine='dot',comment='Reporte mbr')

                # Agrega el texto superior al grafo
                graph.attr(label="Reporte MBR "+ nombreDisco , labelloc='t', labeljust='c', fontsize='20', fontname='arial')

                #atributos del nodo de la tabla
                graph.attr('node', shape='plaintext', border='1', cellborder='1', cellpadding='8')

                # texto de la tabla
                texto_tabla = '''<
                    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="7">
                '''

                #Fila MBR siempre al inicio
                texto_tabla += '''
                    <TR>
                        <TD PORT="mbr" BGCOLOR="{color}" COLSPAN="2">{texto}</TD>
                    </TR>'''.format(color=colores["MBR"], texto="REPORTE DE MBR")
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="50">{texto2}</TD>
                    </TR>'''.format(texto1="Tamaño", texto2=mbr.mbr_tamano)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="50">{texto2}</TD>
                    </TR>'''.format(texto1="Fecha creación", texto2=datetime.fromtimestamp(mbr.mbr_fecha_creacion))
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="50">{texto2}</TD>
                    </TR>'''.format(texto1="Signature", texto2=mbr.mbr_disk_signature)
                
                for part in lista_particiones: #Primera filas
                    if part.part_name != "": #Si la particion tiene datos, sea activa o no
                        texto_tabla += '''
                            <TR>
                                <TD BGCOLOR="{color}" COLSPAN="2">{texto}</TD>
                            </TR>'''.format(color=colores[part.part_type.upper()], texto="Particion")
                        texto_tabla += '''
                            <TR>
                                <TD WIDTH="40">{texto1}</TD>
                                <TD WIDTH="50">{texto2}</TD>
                            </TR>'''.format(texto1="part status", texto2=part.part_status)
                        texto_tabla += '''
                            <TR>
                                <TD WIDTH="40">{texto1}</TD>
                                <TD WIDTH="60">{texto2}</TD>
                            </TR>'''.format(texto1="part name", texto2=part.part_name)
                        texto_tabla += '''s
                            <TR>
                                <TD WIDTH="40">{texto1}</TD>
                                <TD WIDTH="60">{texto2}</TD>
                            </TR>'''.format(texto1="part type", texto2=part.part_type)
                        texto_tabla += '''
                            <TR>
                                <TD WIDTH="40">{texto1}</TD>
                                <TD WIDTH="60">{texto2}F</TD>
                            </TR>'''.format(texto1="part fit", texto2=part.part_fit)
                        texto_tabla += '''
                            <TR>
                                <TD WIDTH="40">{texto1}</TD>
                                <TD WIDTH="60">{texto2}</TD>
                            </TR>'''.format(texto1="part start", texto2=part.part_start)
                        texto_tabla += '''
                            <TR>
                                <TD WIDTH="40">{texto1}</TD>
                                <TD WIDTH="60">{texto2}</TD>
                            </TR>'''.format(texto1="part size", texto2=part.part_size)
                        
                        
                        if part.part_type.upper() == "E": #Particion extendida
                            parts_logicas = Disk.getLogicas(part, pathDisco) #Obtener las particiones logicas
                            #obtener logicas con un size mayor a 0

                            parts_logicas = [logica for logica in parts_logicas if int(logica.part_size) > 0 ]

                            for logica in parts_logicas:
                                
                                texto_tabla += '''
                                    <TR>
                                        <TD BGCOLOR="{color}" COLSPAN="2">{texto}</TD>
                                    </TR>'''.format(color=colores["L"], texto="Particion Lógica")
                                texto_tabla += '''
                                    <TR>
                                        <TD WIDTH="40">{texto1}</TD>
                                        <TD WIDTH="60">{texto2}</TD>
                                    </TR>'''.format(texto1="part status", texto2=logica.part_status)
                                texto_tabla += '''
                                    <TR>
                                        <TD WIDTH="40">{texto1}</TD>
                                        <TD WIDTH="60">{texto2}</TD>
                                    </TR>'''.format(texto1="part name", texto2=logica.part_name)
                                texto_tabla += '''
                                    <TR>
                                        <TD WIDTH="40">{texto1}</TD>
                                        <TD WIDTH="60">{texto2}</TD>
                                    </TR>'''.format(texto1="part next", texto2=logica.part_next)
                                texto_tabla += '''
                                    <TR>
                                        <TD WIDTH="40">{texto1}</TD>
                                        <TD WIDTH="60">{texto2}F</TD>
                                    </TR>'''.format(texto1="part fit", texto2=logica.part_fit)
                                texto_tabla += '''
                                    <TR>
                                        <TD WIDTH="40">{texto1}</TD>
                                        <TD WIDTH="60">{texto2}</TD>
                                    </TR>'''.format(texto1="part start", texto2=logica.part_start)
                                texto_tabla += '''
                                    <TR>
                                        <TD WIDTH="40">{texto1}</TD>
                                        <TD WIDTH="60">{texto2}</TD>
                                    </TR>'''.format(texto1="part size", texto2=logica.part_size)
                                
                #Cerrar tabla
                texto_tabla += '''
                    </TABLE> >'''
                
                texto_tabla = (texto_tabla)
                # Nodos de la tabla
                graph.node('node', label=texto_tabla)

                # Renderizar y guardar
                graph.render(pathRep, cleanup=True) 

                Scanner.mensaje("REP", "Reporte MBR generado exitosamente en la ruta: %s" % path)
                return
            case "disk": #Reporte del disco
                tamanoDisco = mbr.mbr_tamano
                numEspaciosExt = 0
                #<+> Datos de particiones logicas
                #Obtener datos de particiones logicas (necesario para ancho de encabezado extendida)
                for part in lista_particiones: #Particiones del disco
                    if part.part_name != "" and part.part_type.upper() == "E": #Si la particion es extendida y en uso
                        
                        parts_logicas = Disk.getLogicas(part, pathDisco) #Obtener las particiones logicas

                        #obtener numero de part_logicas que tengan un size mayor a 0
                        parts_logicas = [part for part in parts_logicas if int(part.part_size) > 0]
                        numEspaciosExt = len(parts_logicas)*2 #Numero de ebr encontrados * 2 (ebr y su logica)

                        for logica in parts_logicas: #verificar si hay espacio libre entre las logicas
                            nextEsperado = logica.part_start + logica.part_size
                            if nextEsperado < logica.part_next:
                                numEspaciosExt += 1 #Sumar un espacio libre entre logicas

                #<+> Grafo 
                graph = Digraph('G',format=extension, engine='dot',comment='Reporte disk')

                #<+> Encabezado
                # Agrega el texto superior al grafo
                graph.attr(label="Reporte disk "+ nombreDisco, labelloc='t', labeljust='c', fontsize='20', fontname='arial')
                #atributos del nodo de la tabla
                graph.attr('node', shape='plaintext', border='1', cellborder='1', cellpadding='8')
                # texto de la tabla
                texto_tabla = '''<
                    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="8">
                    <TR>
                '''

                #<b> Fila MBR siempre al inicio
                texto_tabla += '''
                    <TD PORT="mbr" BGCOLOR="{color}" ROWSPAN="2">{texto}</TD>'''.format(color=colores["MBR"], texto="MBR")

                #<+> Verificar si hay espacio libre entre el mbr y la primera particion
                
                l_part_activas = [part for part in lista_particiones if part.part_name != ' '] #Lista de particiones activas

                #<+> Graficar primera fila de tabla (primarias, extendidas, espacios libre en disco)
                if len(l_part_activas) == 0: #Si no hay particiones en uso
                    texto_tabla += '''
                        <TD BGCOLOR="{color}" ROWSPAN="2">{tipo}<BR/>{porc}% del disco</TD>'''.format(color=colores["Libre"], tipo="Libre", porc=100)            
                else: #Si hay particiones en uso
                    if l_part_activas[0].part_start > 168: #Si hay espacio libre entre inicio del disco y la primera particion
                        espacioVacio = l_part_activas[0].part_start - 168 #Espacio libre entre particiones
                        porcPart = round((espacioVacio * 100) / tamanoDisco,2) #Porcentaje del espacio ocupado
                        
                        if porcPart > 0: #<!> Errores de redondeo
                            texto_tabla += '''
                                <TD BGCOLOR="{color}" ROWSPAN="2">{tipo}<BR/>{porc}% del disco</TD>'''.format(color=colores["Libre"], tipo="Libre", porc=porcPart)
                    
                    for i in range(len(l_part_activas)) : #Primera filas
                        part = l_part_activas[i]
                        partNext = l_part_activas[i+1] if i+1 < len(l_part_activas) else None

                        if part.part_type.upper() == "E": #Particion extendida
                            porcPart = round((part.part_size * 100) / tamanoDisco,2) #Porcentaje del espacio ocupado por la particion
                            texto_tabla += '''
                                <TD BGCOLOR="{color}" COLSPAN="{width}">{tipo} {texto}<BR/>{porc}% del disco</TD>'''.format(color=colores[part.part_type.upper()], width=numEspaciosExt, texto=part.part_name, tipo=part.getTipoString(), porc=porcPart)
                        else: #Particion primaria
                            porcPart = round((part.part_size * 100) / tamanoDisco,2) #Porcentaje del espacio ocupado por la particion
                            texto_tabla += '''
                                <TD BGCOLOR="{color}" ROWSPAN="2">{tipo}<BR/>{texto}<BR/>{porc}% del disco</TD>'''.format(color=colores[part.part_type.upper()], tipo=part.getTipoString(), texto=part.part_name, porc=porcPart)

                        #<+> Verificar si hay espacio libre entre particiones
                        if partNext: #Si hay una siguiente particion
                            if part.part_start + part.part_size < partNext.part_start: #Si hay espacio libre entre particiones
                                espacioVacio = partNext.part_start - (part.part_start + part.part_size) #Espacio libre entre particiones
                                porcPart = round((espacioVacio * 100) / tamanoDisco,2) #Porcentaje del espacio ocupado
                                if porcPart > 0: #<!> Errores de redondeo
                                    texto_tabla += '''
                                        <TD BGCOLOR="{color}" ROWSPAN="2">{tipo}<BR/>{porc}% del disco</TD>'''.format(color=colores["Libre"], tipo="Libre", porc=porcPart)         
                        else: #No hay siguiente particion, se llego a la ultima
                            if part.part_start + part.part_size < tamanoDisco: #Si hay espacio libre entre particiones
                                espacioVacio = tamanoDisco - (part.part_start + part.part_size) #Espacio libre entre particiones
                                porcPart = round((espacioVacio * 100) / tamanoDisco,2) #Porcentaje del espacio ocupado
                                if porcPart > 0: #<!> Errores de redondeo
                                    texto_tabla += '''
                                        <TD BGCOLOR="{color}" ROWSPAN="2">{tipo}<BR/>{porc}% del disco</TD>'''.format(color=colores["Libre"], tipo="Libre", porc=porcPart)

                #<+> cerrar primera fila
                texto_tabla += '''
                    </TR>'''
                
                #<+> Crear segunda fila para los ebr
                for part in l_part_activas: #Primera filas
                    if part.part_type.upper() == "E": #Si la particion esta activa
                        contador = 1
                        parts_logicas = Disk.getLogicas(part, pathDisco)
                        parts_logicas = [part for part in parts_logicas if int(part.part_size) > 0]
                        sizeEbr = struct.calcsize("c2s3i3i16s")

                        #<+> abrir segunda fila
                        texto_tabla += '''
                            <TR>'''

                        if len(parts_logicas) > 0: #CREAR TABLA PARA LOS LOGICAS
                            sobranteEbr = part.part_size
                            for logi in parts_logicas:
                                sobranteEbr -= logi.part_size
                                porcPart = round((logi.part_size * 100) / tamanoDisco,2)
                                texto_tabla += '''
                                    <TD PORT="ebr{num}" BGCOLOR="{color}">EBR</TD>'''.format(num=contador, color=colores["EBR"])
                                texto_tabla += '''
                                    <TD PORT="ebr{num}" BGCOLOR="{color}">Lógica<BR/>{texto}<BR/>{porc}% del disco</TD>'''.format(num=contador, color=colores["L"], texto=logi.part_name, porc=porcPart)
                                contador += 1

                                #<#> Verificar si hay espacio libre entre particiones logicas

                                #<+> Si es la ultima particion logica, verificar si hay espacio libre en la extendida
                                if logi == parts_logicas[-1]: #Si es la ultima particion logica
                                    porcPart = round((sobranteEbr * 100) / tamanoDisco,2) #Porcentaje del espacio ocupado
                                    texto_tabla += '''
                                        <TD PORT="ebr{num}" BGCOLOR="{color}">Libre<BR/>{porc}% del disco</TD>'''.format(num=contador, color=colores["Libre"], porc=porcPart)
                                elif logi.part_next > (logi.part_start + logi.part_size + sizeEbr): #Si hay espacio libre entre particiones logicas, tomando en cuenta el ebr (44)
                                    espacioVacio = logi.part_next - (logi.part_start + logi.part_size) #Espacio libre entre particiones logicas
                                    porcPart = round((espacioVacio * 100) / tamanoDisco,2) #Porcentaje del espacio ocupado
                                    texto_tabla += '''
                                        <TD PORT="ebr{num}" BGCOLOR="{color}">Libre<BR/>{porc}% del disco</TD>'''.format(num=contador, color=colores["Libre"], porc=porcPart)

                                    contador += 1
                                
                        else:#Particion extendida no tiene logicas
                            porcPart = round((part.part_size * 100) / tamanoDisco,2)
                            texto_tabla += '''
                                <TD PORT="ebr{num}" BGCOLOR="{color}">Libre<BR/>{porc}% del disco</TD>'''.format(num=contador, color=colores["Libre"], porc=porcPart)

                        #<+> cerrar segunda fila
                        texto_tabla += '''
                                </TR>
                                '''
                
                #<+> Cerrar tabla
                texto_tabla += '''
                    </TABLE> >'''
                
                texto_tabla = (texto_tabla)
                # Nodos de la tabla
                graph.node('node1', label=texto_tabla)

                # Renderizar y guardar
                graph.render(pathRep, cleanup=True)

                Scanner.mensaje("REP", "Reporte disk generado en %s" % pathRep)
                return
            case "bm_inode": #Reporte del disco

                if sprBloque == None:
                    Scanner.error("REP", "No se pudo leer el super bloque del disco en la ruta: %s" % pathDisco)
                    return
                
                if extension != "txt":
                    Scanner.error("REP", "El reporte bm_inode solo se puede generar en formato txt")
                    return
                
                textoBitmap = ""
                tamanioBitmap = sprBloque.s_bm_block_start - sprBloque.s_bm_inode_start
                try:
                    with open(pathDisco, "r+") as bfile:
                        bfile.seek(sprBloque.s_bm_inode_start)
                        textoBitmap = bfile.read(tamanioBitmap)
                    
                    #Decodificar texto
                    textoBitmap = textoBitmap.replace(b'\x00'.decode('utf-8'), "0")
                    textoBitmap = textoBitmap.replace(b'\x01'.decode('utf-8'), "1")
                    
                    #crear archivo de texto
                    with open(pathFinal, 'w') as archivo:
                        for i in range(0, len(textoBitmap), 20):
                            linea = textoBitmap[i:i+20]  # Extrae una línea de longitud_linea
                            linea = linea.replace("0", "0 ")
                            linea = linea.replace("1", "1 ")
                            archivo.write(linea + '\n')  # Escribe la línea en el archivo con un salto de línea

                    Scanner.mensaje("REP", "Reporte bm_inode generado exitosamente en la ruta: %s" % path)
                    return
                except Exception as e:
                    Scanner.error("REP", "Error al leer el disco en la ruta: %s" % pathDisco)
                    print("ERROR: ",e)
                    return
            case "bm_block": #Reporte del disco
                sprBloque =desempaquetarSuperBloque(pathDisco, particion)

                if sprBloque == None:
                    Scanner.error("REP", "No se pudo leer el super bloque del disco en la ruta: %s" % pathDisco)
                    return
                
                if extension != "txt":
                    Scanner.error("REP", "El reporte bm_inode solo se puede generar en formato txt")
                    return
                
                textoBitmap = ""
                tamanioBitmap = sprBloque.s_inode_start - sprBloque.s_bm_block_start
                try:
                    with open(pathDisco, "r+") as bfile:
                        bfile.seek(sprBloque.s_bm_block_start)
                        textoBitmap = bfile.read(tamanioBitmap)

                    with open(pathFinal, 'w') as archivo:
                        for i in range(0, len(textoBitmap), 20):
                            linea = textoBitmap[i:i+20]  # Extrae una línea de longitud_linea
                            linea = linea.replace("0", "0 ")
                            linea = linea.replace("1", "1 ")
                            archivo.write(linea + '\n')  # Escribe la línea en el archivo con un salto de línea

                    Scanner.mensaje("REP", "Reporte bm_inode generado exitosamente en la ruta: %s" % path)
                    return
                except Exception as e:
                    Scanner.error("REP", "Error al leer el disco en la ruta: %s" % pathDisco)
                    print("ERROR: ",e)
                    return
            case "tree": #Reporte del disco
                graph = Digraph('G',format=extension, engine='dot',comment='Reporte sb')

                #definir rankdir LR
                graph.attr(rankdir='LR', nodesep='0.5', ranksep='1.0')
                sprBloque = desempaquetarSuperBloque(pathDisco, particion)
                numeroInodos = sprBloque.s_inodes_count - sprBloque.s_free_inodes_count

                for i in range(numeroInodos):
                    inodoTemp = getInodo(pathDisco, sprBloque, i)

                    if inodoTemp == None:
                        continue

                    labelInodo = '''<
                    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="7">
                    '''
                    #encabezado
                    labelInodo += '''
                    <TR>
                        <TD PORT=\"c\" BGCOLOR="{color}" COLSPAN="2">{texto}</TD>
                    </TR>'''.format(color=colores["Inodo"], texto=f"Inodo {i}")
                    
                    #datos del nodo
                    labelInodo += '''
                    <TR>
                        <TD WIDTH="60">i_uid</TD>
                        <TD WIDTH="40">{t1}</TD>
                    </TR>
                    <TR>
                        <TD WIDTH="60">i_gid</TD>
                        <TD WIDTH="40">{t2}</TD>
                    </TR>
                    <TR>
                        <TD WIDTH="60">i_size</TD>
                        <TD WIDTH="40">{t3}</TD>
                    </TR>
                    <TR>
                        <TD WIDTH="60">i_atime</TD>
                        <TD WIDTH="40">{t4}</TD>
                    </TR>
                    <TR>
                        <TD WIDTH="60">i_ctime</TD>
                        <TD WIDTH="40">{t5}</TD>
                    </TR>
                    <TR>
                        <TD WIDTH="60">i_mtime</TD>
                        <TD WIDTH="40">{t6}</TD>
                    </TR>
                    <TR>
                        <TD WIDTH="60">i_type</TD>
                        <TD WIDTH="40">{t7}</TD>
                    </TR>
                    <TR>
                        <TD WIDTH="60">i_perm</TD>
                        <TD WIDTH="40">{t8}</TD>
                    </TR>
                    '''.format(t1= inodoTemp.i_uid, t2= inodoTemp.i_gid, t3= inodoTemp.i_size, t4= datetime.fromtimestamp(inodoTemp.i_atime), t5= datetime.fromtimestamp(inodoTemp.i_ctime), t6= datetime.fromtimestamp(inodoTemp.i_mtime), t7= inodoTemp.i_type, t8= inodoTemp.i_perm)
                    
                    contadorIblock = 0
                    for i_block in inodoTemp.i_block:

                        #<#> datos del apuntador
                        labelInodo += '''
                        <TR>
                            <TD WIDTH="60">i_block</TD>
                            <TD WIDTH="40" PORT=\"{port}\">{t1}</TD>
                        </TR>
                        '''.format(t1= i_block, port=contadorIblock)

                        if i_block != -1: #el apuntador esta en uso
                            
                            #<#> creacion de bloque
                            if inodoTemp.i_type == 0: #<*> carpeta
                                #creacion de tabla de carpetas
                                bloqueTemp = getBloqueCarpeta(pathDisco, sprBloque, i_block)
                                labelBloque = '''<
                                    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="7">
                                '''
                                #encabezado
                                labelBloque += '''
                                    <TR>
                                        <TD BGCOLOR="{color}" PORT=\"c\" COLSPAN="2">{texto}</TD>
                                    </TR>'''.format(color=colores["BloqueC"], texto=f"Bloque {i_block}")
                                
                                contadorContentBlock = 0

                                for content in bloqueTemp.b_content: #contenido del bloque
                                    labelBloque += '''
                                        <TR>
                                            <TD WIDTH="60">{t1}</TD>
                                            <TD WIDTH="40" PORT=\"{port}\">{t2}</TD>
                                        </TR>
                                        '''.format(t1= content.b_name, t2= content.b_inodo, port = contadorContentBlock)
                                    
                                    #crear arista entre bloque a inodo
                                    if content.b_inodo != -1 and content.b_name != "." and content.b_name != "..":
                                        graph.edge(f'bloque{i_block}:{contadorContentBlock}', f'inodo{content.b_inodo}:c')
                                    
                                    contadorContentBlock += 1

                                #cerrar tabla
                                labelBloque += '''
                                    </TABLE> >'''
                                
                                #crear nodo
                                graph.node(f'bloque{i_block}', label=labelBloque, shape='box')

                                #crear arista entre inodo y bloque
                                graph.edge(f'inodo{i}:{contadorIblock}', f'bloque{i_block}:c')

                            elif inodoTemp.i_type == 1: #<+> archivo
                                #creacion de tabla de archivos
                                bloqueTemp = getBloqueArchivo(pathDisco, sprBloque, i_block)
                                labelBloque = '''<
                                    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="7">
                                '''
                                #encabezado
                                labelBloque += '''
                                    <TR>
                                        <TD PORT=\"c\" BGCOLOR="{color}">{texto}</TD>
                                    </TR>'''.format(color=colores["BloqueA"], texto=f"Bloque {i_block}")
                                #contenido del bloque

                                contentArchivo = str(bloqueTemp.b_content.decode('ascii').replace('\x00', ''))

                                labelBloque += '''
                                    <TR>
                                        <TD WIDTH="60">{texto}</TD>
                                    </TR>
                                    '''.format(texto=contentArchivo)
                                #cerrar tabla
                                labelBloque += '''
                                    </TABLE> >'''
                                
                                #crear nodo
                                graph.node(f'bloque{i_block}', label=labelBloque, shape='box')

                                #crear arista entre inodo y bloque
                                graph.edge(f'inodo{i}:{contadorIblock}', f'bloque{i_block}:c')
                        
                        contadorIblock += 1
                        
                    #cerrar tabla
                    labelInodo += '''
                    </TABLE> >'''

                    graph.node(f'inodo{i}', label=labelInodo, shape='box')

                # Renderizar y guardar
                graph.render(pathRep, cleanup=True)
                Scanner.mensaje("REP", "Reporte TREE generado exitosamente en la ruta: %s" % path)

                return
            case "sb": #Reporte del super bloque
                # Grafo 
                graph = Digraph('G',format=extension, engine='dot',comment='Reporte sb')

                # Agrega el texto superior al grafo
                graph.attr(label="Reporte SB", labelloc='t', labeljust='c', fontsize='20', fontname='arial')

                #atributos del nodo de la tabla
                graph.attr('node', shape='plaintext', border='1', cellborder='1', cellpadding='8')

                # texto de la tabla
                texto_tabla = '''<
                    <TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="7">
                '''
                
                if sprBloque == None:
                    Scanner.error("REP", "No se pudo leer el super bloque del disco en la ruta: %s" % pathDisco)
                    return

                texto_tabla += '''
                    <TR>
                        <TD BGCOLOR="{color}" COLSPAN="2">{texto}</TD>
                    </TR>'''.format(color=colores["SBloque"], texto="Super bloque")
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="sb_nombre_hd", texto2=nombreDisco)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_filesystem_type", texto2=sprBloque.s_filesystem_type)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_inodes_count", texto2=sprBloque.s_inodes_count)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_blocks_count", texto2=sprBloque.s_blocks_count)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_free_inodes_count", texto2=sprBloque.s_free_inodes_count)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_free_blocks_count", texto2=sprBloque.s_free_blocks_count)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_mtime", texto2=datetime.fromtimestamp(sprBloque.s_mtime))
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_umtime", texto2=datetime.fromtimestamp(sprBloque.s_umtime))
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_mnt_count", texto2=sprBloque.s_mnt_count)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_magic", texto2=sprBloque.s_magic)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_inode_size", texto2=sprBloque.s_inode_size)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_block_size", texto2=sprBloque.s_block_size)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_first_ino", texto2=sprBloque.s_first_ino)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_first_blo", texto2=sprBloque.s_first_blo)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_bm_inode_start", texto2=sprBloque.s_bm_inode_start)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_bm_block_start", texto2=sprBloque.s_bm_block_start)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_inode_start", texto2=sprBloque.s_inode_start)
                texto_tabla += '''
                    <TR>
                        <TD WIDTH="40">{texto1}</TD>
                        <TD WIDTH="60">{texto2}</TD>
                    </TR>'''.format(texto1="s_block_start", texto2=sprBloque.s_block_start)
                
                #Cerrar tabla
                texto_tabla += '''
                    </TABLE> >'''
                texto_tabla = (texto_tabla)

                # Nodos de la tabla
                graph.node('node', label=texto_tabla)

                # Renderizar y guardar
                graph.render(pathRep, cleanup=True) 

                Scanner.mensaje("REP", "Reporte SB generado exitosamente en la ruta: %s" % path)
                return
            case "file": #Reporte del disco
                
                if not path.endswith(".txt"):
                    Scanner.error("REP", "El reporte file solo se puede generar en formato txt")
                    return

                if ruta.startswith("\"") and ruta.endswith("\""):
                    ruta = ruta[1:-1]

                sprBloque = desempaquetarSuperBloque(pathDisco, particion)
                inodo = getInodoByPath(pathDisco, sprBloque, ruta)

                if inodo == None:
                    Scanner.error("REP", "No se encontro el archivo en la ruta: %s" % ruta)
                    return
                
                if inodo.i_type != 1:
                    Scanner.error("REP", "El inodo encontrado no es un archivo")
                    return
                
                concatenadorTexto = ""

                for i_block in inodo.i_block:
                    if i_block != -1:
                        bloque = getBloqueArchivo(pathDisco, sprBloque, i_block)
                        concatenadorTexto += bloque.b_content.decode('ascii').replace('\x00', '')

                #crear archivo de texto
                try:
                    with open(pathFinal, 'w') as archivo:
                        archivo.write(concatenadorTexto)
                except Exception as e:
                    Scanner.error("REP", "Error al crear el archivo en la ruta: %s" % path)
                    print("ERROR: ",e)
                    return
                finally:
                    archivo.close()

                Scanner.mensaje("REP", "Reporte file generado exitosamente en la ruta: %s" % path)
                return
            case _:
                Scanner.error("REP", "El reporte con nombre %s no existe" % name)

    #<b> FDISK
    @staticmethod
    def fdisk(tokens, mountInstance=None):
        eliminar = False
        for current in tokens:
            id = (current[:current.find('=')]).lower()
            current = current[current.find('=') + 1:]
            if current[:1] == "\"":
                current = current[1:-1]
            if Scanner.comparar(id, "delete"):
                eliminar = True


        if not eliminar:
            required = Scanner.required_values("fdisk")
            size = ""
            path = ""
            unit = "K" # Kilobytes por defecto
            fit = "WF" # Worst Fit por defecto
            type = "P" # Primaria por defecto
            name = ""
            add = ""

            for current in tokens:
                id = (current[:current.find('=')]).lower()
                current = current[current.find('=') + 1:]

                if current.startswith("\"") and current.endswith("\""):
                    current = current[1:-1]

                if Scanner.comparar(id, "size"):
                    size = current
                elif Scanner.comparar(id, "name"):
                    if id in required:
                        required.remove(id)
                        name = current
                elif Scanner.comparar(id, "path"):
                    if id in required:
                        required.remove(id)
                        path = current
                elif Scanner.comparar(id, "unit"):
                    unit = current
                elif Scanner.comparar(id, "type"):
                    type = current
                elif Scanner.comparar(id, "fit"):
                    fit = current
                elif Scanner.comparar(id, "add"):
                    add = current

            if required:
                for r in required:
                    Scanner.error("FDISK", "Falta el parametro %s en el comando" % r)
                return
            
            if add:
                if unit.lower() not in ["b", "k", "m"]:
                    Scanner.error("FDISK", "El parametro unit solo permite B, K o M")
                    return

                _size = int(add)
                if unit.lower() == "k":
                    _size *= 1024
                elif unit.lower() == "m":
                    _size *= 1024 * 1024

                if _size == 0 :
                    Scanner.error("FDISK", "El parametro size no puede ser0")
                    return

                Disk.agregarEspacio(_size, name, path) #Agregar espacio (positivo o negativo) a particion
                return
            else: # Se creara una particion
                if not size:
                    Scanner.error("FDISK", "El parametro size es obligatorio.")
                    return
            
                Disk.generarParticion(size, unit, path, type, fit, name, add)
                return
        else: # Se eliminara una particion
            required = Scanner.required_values("fdisk-delete")
            elimi = ""
            path = ""
            name = ""

            for current in tokens:
                id = (current[:current.find('=')]).lower()
                current = current[len(id) + 1:]

                if current.startswith("\"") and current.endswith("\""):
                    current = current[1:-1]

                if Scanner.comparar(id, "path"):
                    if id in required:
                        required.remove(id)
                        path = current
                elif Scanner.comparar(id, "name"):
                    if id in required:
                        required.remove(id)
                        name = current
                elif Scanner.comparar(id, "delete"):
                    elimi = current

            if required:
                for r in required:
                    Scanner.error("FDISK", "Falta el parametro %s en el comando" % r)
                return

            if mountInstance.isMountedPartition( name ):
                Scanner.error("FDISK", "No se puede eliminar la partición si esta montada.")
                return
        
            Disk.eliminarParticion(path, name, elimi)

    @staticmethod
    def eliminarParticion(path, name, elimi):
        #path: ruta del disco
        #name: nombre de la particion a eliminar
        #elimi: tipo de eliminacion, solo permite full
        if elimi.lower() != "full":
            Scanner.error("FDISK", "El parametro delete solo permite full")
            return
        
        try:
            mbr = Disk.desempaquetarMbr(path)
        except Exception as e:
            Scanner.error("FDISK", "Error al desampaquetar mbr en: %s" % path)
            print(e)

        lista_particiones = mbr.getParticiones() #Obtener lista de particiones

        contador = 1

        
        for part in lista_particiones: #Particiones primarias y extendidas
            # Eliminar datos de la particion
            if part.part_name == name:
                
                #Llenar de ceros el espacio de la particion
                Disk.vaciarParticionEnDisco(path, part) #Llenar de ceros la particion
                
                #Actualizar mbr
                part = Structs.Particion()
                part.part_fit = part.part_fit[0]
                mbr.setPartitionWIndex(part, contador)
                
                #Actualizar datos en disco
                Disk.actualizarMbr(path, mbr)
                return
            
            contador += 1

        #Particiones logicas
        contador = 0
        for part in lista_particiones: #Particiones primarias y extendidas
            if part.part_type.upper() == "E": #Particion extendida
                parts_logicas = Disk.getLogicas(part, path) #Obtener las particiones logicas
                for logica in parts_logicas:
                    if logica.part_name == name: #Se encontró la particion logica
                        #Llenar de ceros el espacio de la particion
                        Disk.vaciarLogicaEnDisco(path, part, contador, parts_logicas) #Llenar de ceros la particion logica
                        Scanner.mensaje("FDISK", "Particion %s eliminada correctamente" % name)
                        return
                    contador += 1
        
        Scanner.error("FDISK", "No se encontró la particion %s" % name)
        

    @staticmethod
    def vaciarParticionEnDisco(path, part):

        print("Eliminando particion: ", part.part_name, ", desde el byte: ", part.part_start, "hasta el byte: ", part.part_start + part.part_size-1)
        try:
            with open(path, "rb+") as file:
                # Mover el puntero al final del archivo y colocar otro byte nulo
                zero = b'0'
                file.seek(part.part_start)
                #file.write(b"\x00"*(part.part_size-1))
                file.write(zero*(part.part_size-1))

        except IOError as e:
            Scanner.error("E/S", "Error de escritura y/o lectura con el archivo.")
            print(e)
        except Exception as e:
            print(e)
            Scanner.error("PARTICION", "Error al eliminar la particion %s" % part.part_name)
        finally:
            file.close()  # Cierra el archivo

    @staticmethod
    def vaciarLogicaEnDisco(path, partE, contador, logicas):
        p_logica = logicas[contador]
        print("Eliminando particion logica: ", p_logica.part_name, ", desde el byte: ", p_logica.part_start, "hasta el byte: ", p_logica.part_next-1)
        
        ebr = Structs.EBR() #ebr vacio
        sizeEbr = struct.calcsize("c2s3i3i16s")
        zero = b'0'

        if contador == 0: #Primer ebr no se elimina
            ebr.part_start = p_logica.part_start
            ebr.part_next = p_logica.part_next #inlcuye ebr
            ebr.part_fit = 'W'
            ebr.part_name = ' '

            try: #Actualizar datos en disco
                with open(path, "rb+") as file:
                    file.seek(partE.part_start -1) #Mover el puntero al inicio de la particion extendida
                    file.write(ebr.__bytes__()) #Escribir el ebr
                    file.seek(partE.part_start + sizeEbr) #Mover el puntero al inicio de los datos de la logia
                    sizeDatos = (ebr.part_next - sizeEbr) - ebr.part_start - 1 #Tamaño de los datos de la logica
                    file.write(zero*sizeDatos) #Escribir el ebr
            
                return
            except Exception as e: 
                Scanner.error("PARTICION", "Error al eliminar la particion logica %s" % p_logica.part_name)
                print(e)
            finally:
                file.close()  # Cierra el archivo
        else: #No es el primero   
            p_logica_anterior = logicas[contador-1]
            p_logica_anterior.part_next = p_logica.part_next #Ajustar apuntador de la anterior logica

            ebr = logicas[contador] #ebr a eliminar

            try: #Actualizar datos en disco
                with open(path, "rb+") as file:

                    file.seek(p_logica_anterior.part_start -1) #Mover el puntero al inicio de la particion extendida
                    file.write(p_logica_anterior.__bytes__()) #Escribir el ebr
                    file.seek(ebr.part_start -1) #Mover el puntero al inicio de la particion extendida
                    file.write(zero*ebr.part_size) #Escribir el ebr 
            
                return
            except Exception as e: 
                Scanner.error("PARTICION", "Error al eliminar la particion logica %s" % p_logica.part_name)
                print(e)
            finally:
                file.close()  # Cierra el archivo

    @staticmethod
    def agregarEspacio(size, name, path):
        
        mbr = Disk.desempaquetarMbr(path)

        for part in mbr.getParticiones():
            if part.part_name == name:
                Disk.agregarEspacioParti(size, name, path, mbr)
                Scanner.mensaje("FDISK", "Espacio agregado correctamente")
                return

            if part.part_type == 'E':
                for logica in Disk.getLogicas(part, path):
                    if logica.part_name == name:

                        Disk.agregarEspacioLogi(size, part, name, path)
                        Scanner.mensaje("FDISK", "Espacio agregado correctamente")
                        return
    
    @staticmethod
    def agregarEspacioParti(size, name, path, mbr):
        contador = 0
        l_particiones = mbr.getParticiones()
        #obtener particiones que tengan datos
        l_particiones = [part for part in l_particiones if part.part_name != ' ']
        #ordenar particiones segun su start
        l_particiones.sort(key=lambda x: x.part_start, reverse=False)

        for prt in l_particiones:
            if prt.part_name == name:
                nuevoTamano = prt.part_size + size

                if nuevoTamano < 0: #Si se quiere eliminar mas espacio del que tiene la particion
                    Scanner.error("FDISK", "No se puede eliminar mas espacio del que tiene la particion")
                    return

                if prt.part_start + nuevoTamano > mbr.mbr_tamano: #Si se quiere agregar mas espacio del que tiene el disco
                    Scanner.error("FDISK", "No hay espacio suficiente en el disco para agregar el espacio")
                    return
                
                #obtener particion siguiente
                partSiguiente = l_particiones[contador+1] if contador+1 < len(l_particiones) else None
                if partSiguiente: #Si hay una siguiente particion
                    if prt.part_start + nuevoTamano >= partSiguiente.part_start: #Si se quiere agregar mas espacio del que tiene el disco
                        Scanner.error("FDISK", "No hay espacio suficiente espacio despues de la particion.")
                        return

                prt.part_size = nuevoTamano

                #Actualizar mbr
                mbr.setParticionWName(prt, prt.part_name)
                Disk.actualizarMbr(path, mbr)
                return
                
            contador += 1
        
        Scanner.error("FDISK", "No se encontró la particion %s" % name)
        return

    @staticmethod
    def agregarEspacioLogi(size, extended, name, path):
        contador = 0
        l_logicas = Disk.getLogicas(extended, path)
        #obtener particiones que tengan datos
        l_logicas = [part for part in l_logicas if int(part.part_size) > 0]
        #ordenar particiones segun su start
        l_logicas.sort(key=lambda x: x.part_start, reverse=False)

        sizeEbr = struct.calcsize("c2s3i3i16s")

        for logi in l_logicas:
            if logi.part_name == name:
                nuevoTamano = logi.part_size + size

                if nuevoTamano < 0:
                    Scanner.error("FDISK", "No se puede eliminar mas espacio del que tiene la particion logica.")
                    return

                if logi.part_start + nuevoTamano > extended.part_start + extended.part_size:
                    Scanner.error("FDISK", "No hay espacio suficiente en la particion extendida para agregar el espacio.")
                    return

                #obtener particion siguiente
                partSiguiente = l_logicas[contador+1] if contador+1 < len(l_logicas) else None

                if partSiguiente: #Si hay una siguiente particion
                    if logi.part_start + nuevoTamano > partSiguiente.part_start - sizeEbr:
                        Scanner.error("FDISK", "No hay espacio suficiente espacio despues de la particion.")
                        return
                
                logi.part_size += size
                    
                try: #Actualizar datos en disco
                    with open(path, "rb+") as file:
                        file.seek(logi.part_start) #Mover el puntero al inicio de los datos de la logia
                        file.write(logi.__bytes__()) #Escribir el ebr
                    
                    Scanner.mensaje("FDISK", "Espacio agregado correctamente")
                    return
                except Exception as e: 
                    Scanner.error("PARTICION", "Error al cambiar tamaño de la particion %s" % logi.part_name)
                    print(e)
                finally:
                    file.close()  # Cierra el archivo
                

#<*> VALOR PARA INICIO DEL DISCO LOGICO
def update_start_value(new_value):
    global startValue
    startValue = new_value
    
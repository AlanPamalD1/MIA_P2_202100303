import os
import Structs
import struct
import Scanner as Scanner
import disk as Disco

class Mount:
    def __init__(self):
        self.discoMontado = []   
        for _ in range(99): 
            tmp = Structs.DiscoMontado()
            self.discoMontado.append(tmp) 

    def __str__(self) -> str:

        string = ""
        string += ("\n<---------------------- LISTADO DE MOUNTS ---------------------->\n")
        for i in range(99):
            for j in range(26):
                disco = self.discoMontado[i].particiones[j]
                if disco.estado == '1':
                    string += (str(j)+")\t  03"+str(j + 1) + disco.nombre_disco)+"\n"
        string += ("\n<--------------------------------------------------------------->")

        return string

    def validarDatos(self, context): 
        if not context:
            self.listaMount()
            return
        
        required = Scanner.required_values("mount")
        path = ""
        name = ""

        for current in context:
            id = current.split('=')[0]
            current = current.split('=')[1]
            if current[0] == "\"":
                current = current[1:-1]

            if Scanner.comparar(id, "name"):
                if id in required:
                    required.remove(id)
                    name = current
            elif Scanner.comparar(id, "path"):
                if id in required:
                    required.remove(id)
                    path = current
            else:
                Scanner.error("MOUNT", "no se esperaba el parametro %s" % tk)
                break

        if required:
            for r in required:
                Scanner.error("MOUNT", "falta el parametro obligatorio %s" % r)
            return
        
        self.mount(path, name)
 
    def mount(self, p, n):
        try:
            if not os.path.exists(p):
                raise RuntimeError("disco no existente")

            disk = Disco.Disk().desempaquetarMbr(p)

            partition = Disco.Disk.buscarParticiones(disk, n, p) 
            if partition.part_type == 'E':
                raise RuntimeError("no se puede montar una partición extendida")
 
            for i in range(99):
                if self.discoMontado[i].path == p:
                    for j in range(26):
                        if self.discoMontado[i].particiones[j].estado == '0':
                            self.discoMontado[i].particiones[j].estado = '1'
                            self.discoMontado[i].particiones[j].nombre = n
                            self.discoMontado[i].particiones[j].num_particion = j+1
                            self.discoMontado[i].particiones[j].path_disco = p
                           
                            nombreDiscoSegunPath, _ = os.path.splitext(os.path.basename(p))
                            self.discoMontado[i].particiones[j].nombre_disco = nombreDiscoSegunPath

                            idDisco = str(j + 1) + nombreDiscoSegunPath
                            Scanner.mensaje("MOUNT", "se ha realizado correctamente el mount nuevo -id=03" + idDisco)
                            return

            for i in range(99):
                if self.discoMontado[i].estado == '0':
                    self.discoMontado[i].estado = '1'
                    self.discoMontado[i].path = p
                    for j in range(26):
                        if self.discoMontado[i].particiones[j].estado == '0':
                            self.discoMontado[i].particiones[j].estado = '1'
                            self.discoMontado[i].particiones[j].nombre = n
                            self.discoMontado[i].particiones[j].num_particion = j+1
                            self.discoMontado[i].particiones[j].path_disco = p
                            
                            nombreDiscoSegunPath, _ = os.path.splitext(os.path.basename(p))
                            self.discoMontado[i].particiones[j].nombre_disco = nombreDiscoSegunPath

                            idDisco = str(j + 1) + nombreDiscoSegunPath
                            Scanner.mensaje("MOUNT", "se ha realizado correctamente el mount -id=03" + idDisco)
                            return
        except Exception as e:
            Scanner.error("MOUNT", e)
 
    def validarDatosU(self, context):
        required = ["id"]
        id_ = ""

        for current in context:
            id = current.split('=')[0]
            current = current.split('=')[1]

            if Scanner.comparar(id, "id"):
                if id in required:
                    required.remove(id)
                    id_ = current
            else:
                Scanner.error("UNMOUNT", "no se esperaba el parametro %s" % current)
                break

        if required:
            for r in required:
                Scanner.error("UNMOUNT", "falta el parametro obligatorio %s" % r)
            return
        
        self.unmount(id_)
 
    def unmount(self, id):
        try:
            if not (id.startswith('03')):
                raise RuntimeError("el primer identificador no es válido")
            
            past = id

            for i in range(99):
                for j in range(26):
                    if self.discoMontado[i].particiones[j].estado == '1':
                        if past.endswith(self.discoMontado[i].particiones[j].nombre_disco): #Si el id lleva al final el nombre del disco

                            #Obtener los textos que estan antes del nombre del disco de past
                            idBusqueda = past[2:-len(self.discoMontado[i].particiones[j].nombre_disco)] #Obtener el id sin el 03 y el nombre de la particion
                            if idBusqueda == str(self.discoMontado[i].particiones[j].num_particion): #Si el idBusqueda es igual al numero de particion
                                mp = Structs.ParticionMontada()
                                self.discoMontado[i].particiones[j] = mp
                                Scanner.mensaje("UNMOUNT", "se ha realizado correctamente el unmount -id=" + past)
                                return

            raise RuntimeError("No se encontró el id= " + id + ", no se desmontó nada")
        except ValueError:
            Scanner.error("UNMOUNT", "identificador de disco incorrecto, debe ser entero")
        except Exception as e:
            Scanner.error("UNMOUNT", e)
  
    def getmount(self, id):
        if not (id.startswith('03')):
            raise RuntimeError("el primer identificador no es válido")
        past = id
        if int(id[2]) < 0:
            raise RuntimeError("identificador de disco inválido")

        for i in range(99):
            for j in range(26):
                if self.discoMontado[i].particiones[j].estado == '1':
                    if past.endswith(self.discoMontado[i].particiones[j].nombre_disco):
                        if not os.path.exists(self.discoMontado[i].path):
                            raise RuntimeError("disco no existente")
                        #Obtener los textos que estan antes del nombre del disco de past
                        idBusqueda = past[2:-len(self.discoMontado[i].particiones[j].nombre_disco)] #Obtener el id sin el 03 y el nombre de la particion
                        if idBusqueda == str(self.discoMontado[i].particiones[j].num_particion): #Si el idBusqueda es igual al numero de particion
                            disk = Structs.MBR()  # Replace with actual initialization
                            with open(self.discoMontado[i].path, "rb") as validate:
                                mbr_data = validate.read()
                                disk.mbr_tamano = struct.unpack("<i", mbr_data[:4])[0]
                                disk.mbr_fecha_creacion = struct.unpack("<i", mbr_data[4:8])[0]
                                disk.mbr_disk_signature = struct.unpack("<i", mbr_data[8:12])[0]
                                disk.disk_fit = mbr_data[12:14].decode('utf-8')

                                partition_size = struct.calcsize("<iii16s")
                                partition_data = mbr_data[14:14 + partition_size]
                                disk.mbr_Partition_1.__setstate__(partition_data)
                                
                                partition_data = mbr_data[13 + partition_size:14 + 2 * partition_size]
                                disk.mbr_Partition_2.__setstate__(partition_data)
                                
                                partition_data = mbr_data[12 + 2 * partition_size:14 + 3 * partition_size]
                                disk.mbr_Partition_3.__setstate__(partition_data)
                                
                                partition_data = mbr_data[11 + 3 * partition_size:14 + 4 * partition_size]
                                disk.mbr_Partition_4.__setstate__(partition_data)

                            p = self.discoMontado[i].path
                            return p, Disco.Disk.buscarParticiones(disk, self.discoMontado[i].particiones[j].nombre, self.discoMontado[i].path)
        raise RuntimeError("partición no existente")
    
    def isMountedId(self, id):
        if not (id.startswith("03")):
            return False
        for i in range(99):
            for j in range(26):
                disco = self.discoMontado[i].particiones[j]
                idActual = "03"+ str(j + 1) + disco.nombre_disco
                if idActual == id:
                    return True

    def isMountedPartition(self, name):
        for i in range(99):
            for j in range(26):
                disco = self.discoMontado[i].particiones[j] #ParticionMontada
                if disco.nombre == name:
                    return True
        
        return False

    def listaMount(self):
        print("\n<---------------------- LISTADO DE MOUNTS ---------------------->")
        for i in range(99):
            for j in range(26):
                disco = self.discoMontado[i].particiones[j]
                if disco.estado == '1':
                    print(str(j)+")\t  03"+str(j + 1) + disco.nombre_disco)
        print("<--------------------------------------------------------------->")

import struct
from objprint import add_objprint

class Structs:
    def __init__(self):
        pass



@add_objprint
class UsuarioActivo:
    def __init__(self):
        self.user = ""
        self.password = ""
        self.id = ""
        self.uid = 0
        self.guid = 0
    
    def __str__(self) -> str:
        return f"Usuario: {self.user}\nPassword: {self.password}\nID: {self.id}\nUID: {self.uid}\nGUID: {self.guid}"

@add_objprint
class Particion:
    def __init__(self):
        self.part_status = '0'
        self.part_type = 'P'
        self.part_fit = 'BF'
        self.part_start = 0
        self.part_size = 0
        self.part_name = ' '

    def __bytes__(self):
        return (self.part_status.encode('utf-8') +
                self.part_type.encode('utf-8') +
                self.part_fit.encode('utf-8') +
                struct.pack("<i", self.part_start) +
                struct.pack("<i", self.part_size) +
                self.part_name.ljust(16, '\0').encode('utf-8'))
    
    def __setstate__(self, data):
        self.part_status = data[:1].decode('utf-8')
        self.part_type = data[1:2].decode('utf-8')
        self.part_fit = data[2:3].decode('utf-8')
        self.part_start = struct.unpack("<i", data[3:7])[0]
        self.part_size = struct.unpack("<i", data[7:11])[0]
        self.part_name = data[11:27].decode('utf-8').rstrip('\0')
    
    def getTipoString(self):
        if self.part_type == 'P':
            return 'Primaria'
        elif self.part_type == 'E':
            return 'Extendida'
        elif self.part_type == 'L':
            return 'Logica'
        else:
            return 'Desconocido'

@add_objprint
class MBR:
    def __init__(self):
        self.mbr_tamano = 0
        self.mbr_fecha_creacion = 0
        self.mbr_disk_signature = 0
        self.disk_fit = 'FF'  # Valor por defecto: First Fit
        self.mbr_Partition_1 = Particion()
        self.mbr_Partition_2 = Particion()
        self.mbr_Partition_3 = Particion()
        self.mbr_Partition_4 = Particion()

    def __bytes__(self):
        return (struct.pack("<i", self.mbr_tamano) +
                struct.pack("<i", self.mbr_fecha_creacion) +
                struct.pack("<i", self.mbr_disk_signature) +
                self.disk_fit.encode('utf-8') +
                bytes(self.mbr_Partition_1) +
                bytes(self.mbr_Partition_2) +
                bytes(self.mbr_Partition_3) +
                bytes(self.mbr_Partition_4))
    
    def setPartitionWIndex(self, partition, index):
        
        if index == 1:
            self.mbr_Partition_1 = partition
        elif index == 2:
            self.mbr_Partition_2 = partition
        elif index == 3:
            self.mbr_Partition_3 = partition
        elif index == 4:
            self.mbr_Partition_4 = partition
        else:
            return False
        
    
    def getParticiones(self):
        return [self.mbr_Partition_1, self.mbr_Partition_2, self.mbr_Partition_3, self.mbr_Partition_4]

    def setParticionWName(self, part, name):
        
        #Si es primaria o extendida
        for partition in self.getParticiones():
            if partition.part_name == name:
                partition = part
                return True

        #Si es logica
        return False
        
@add_objprint
class EBR:
    def __init__(self):
        self.part_status = '0'
        self.part_fit = ''
        self.part_start = 0
        self.part_size = 0
        self.part_next = -1
        self.part_name = ' '
    
    def __bytes__(self):
        return (self.part_status.encode('utf-8') +
                self.part_fit.encode('utf-8') +
                struct.pack("<i", self.part_start) +
                struct.pack("<i", self.part_size) +
                struct.pack("<i", self.part_next) +
                self.part_name.encode('utf-8').ljust(16, b'\x00'))

    def __setstate__(self, data):
        self.part_status = data[:1].decode('utf-8')
        self.part_fit = data[1:2].decode('utf-8')
        self.part_start = struct.unpack("<i", data[2:6])[0]
        self.part_size = struct.unpack("<i", data[6:10])[0]
        self.part_next = struct.unpack("<i", data[10:14])[0]
        self.part_name = data[14:30].decode('utf-8').rstrip('\0')

    def getStringStatus(self):
        if self.part_status == '0':
            return 'Inactiva'
        elif self.part_status == '1':
            return 'Activa'
        else:
            return 'Desconocido'
        
@add_objprint
class Transition:
    def __init__(self):
        self.partition = 0
        self.start = 0
        self.end = 0
        self.before = 0
        self.after = 0

    def __bytes__(self):
        return struct.pack("<5i", self.partition, self.start, self.end, self.before, self.after)

@add_objprint
class DiscoMontado:
    def __init__(self):
        self.path = ''
        self.estado = '0'
        self.particiones = [ParticionMontada() for _ in range(26)]

@add_objprint
class ParticionMontada:
    def __init__(self):
        self.estado = '0'
        self.nombre = '' #Nombre de la particion
        self.nombre_disco = '' #Nombre del disco al que pertenece la particion
        self.num_particion = -1 #Numero de particion
        self.path_disco = '' #Path del disco

@add_objprint
class Inodos:
    def __init__(self):
        self.i_uid = -1 #uid del usuario propietario del archivo
        self.i_gid = -1 #gid del grupo al que pertenece el archivo
        self.i_size = -1 #tamaño del archivo en bytes
        self.i_atime = 0 #ultima fecha en la que se leyo el inodo sin modificarlo
        self.i_ctime = 0 #fecha en la que se creo el inodo
        self.i_mtime = 0 #fecha en la que se modifico el inodo
        self.i_block = [-1] * 15 #15 apuntadores directos
        self.i_type = 0     # 0 = carpeta, 1 = archivo
        self.i_perm = -1    #3 bits para usuario, 3 bits para grupo, 3 bits para otros, 
                            #primer bit para lectura R, segundo para escritura W, tercero para ejecucion X

    def __bytes__(self):
        return (struct.pack("<i", self.i_uid) +
                struct.pack("<i", self.i_gid) +
                struct.pack("<i", self.i_size) +
                struct.pack("<d", self.i_atime) +
                struct.pack("<d", self.i_ctime) +
                struct.pack("<d", self.i_mtime) +
                struct.pack("<15i", *self.i_block) +
                struct.pack("<B", self.i_type) +  # Use "<B" format for a single byte
                struct.pack("<i", self.i_perm))
    
@add_objprint
class SuperBloque:
    def __init__(self):
        self.s_filesystem_type = 0 #identificador
        self.s_inodes_count = 0 #cantidad de inodos
        self.s_blocks_count = 0 #cantidad de bloques
        self.s_free_blocks_count = 0 #cantidad de bloques libres
        self.s_free_inodes_count = 0 #cantidad de inodos libres
        self.s_mtime = 0 #ultima fecha de montaje
        self.s_umtime = 0 #ultima fecha de desmontaje
        self.s_mnt_count = 0 #cantidad de montajes
        self.s_magic = 0xEF53 #identifica el sistema de archivos
        self.s_inode_size = 0 #tamaño del inodo
        self.s_block_size = 0 #tamaño del bloque
        self.s_first_ino = 0 #primer inodo libre, el 0 es la carpeta raiz
        self.s_first_blo = 0 #primer bloque libre, el 0 es la carpeta raiz
        self.s_bm_inode_start = 0 #inicio del bitmap de inodos
        self.s_bm_block_start = 0 #inicio del bitmap de bloques
        self.s_inode_start = 0 #inicio de la tabla de inodos
        self.s_block_start = 0 #inicio de la tabla de bloques

    def __bytes__(self):
        return (struct.pack("<i", self.s_filesystem_type) +
                struct.pack("<i", self.s_inodes_count) +
                struct.pack("<i", self.s_blocks_count) +
                struct.pack("<i", self.s_free_blocks_count) +
                struct.pack("<i", self.s_free_inodes_count) +
                struct.pack("<d", self.s_mtime) +
                struct.pack("<d", self.s_umtime) +
                struct.pack("<i", self.s_mnt_count) +
                struct.pack("<i", self.s_magic) +
                struct.pack("<i", self.s_inode_size) +
                struct.pack("<i", self.s_block_size) +
                struct.pack("<i", self.s_first_ino) +
                struct.pack("<i", self.s_first_blo) +
                struct.pack("<i", self.s_bm_inode_start) +
                struct.pack("<i", self.s_bm_block_start) +
                struct.pack("<i", self.s_inode_start) +
                struct.pack("<i", self.s_block_start))
    
@add_objprint
class Content:
    def __init__(self):
        self.b_name = '\x00' * 12
        self.b_inodo = -1 #numero de inodo

    def __bytes__(self):
        return (self.b_name.ljust(12, '\0').encode('utf-8') +
                struct.pack("<i", self.b_inodo))

@add_objprint   
class BloquesCarpetas:
    def __init__(self): 
        self.b_content = [Content() for _ in range(4)] #4 bloques de contenido
        self.b_content[0].b_name = '.'
        self.b_content[1].b_name = '..'
        self.b_content[0].b_inodo = 0
        self.b_content[1].b_inodo = 0

    def __bytes__(self):
        return b"".join(bytes(c) for c in self.b_content)


@add_objprint
class BloquesArchivos:
    def __init__(self):
        self.b_content = '\x00' * 64

    def __bytes__(self):
        return self.b_content.ljust(64, '\0').encode('utf-8')
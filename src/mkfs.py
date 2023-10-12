import Scanner as Scanner
import time
import Structs
import mount as Mount
import struct
from Ext2 import *

class MKFS:
    def __init__(self, m = Mount.Mount()):  
        self.mount = m
    
    def mkfs(self, context):
        required = Scanner.required_values("mkfs")
        id = ""
        type = "Full"
        
        for current in context:
            tk = current.split('=')[0].lower()
            current = current.split('=')[1]

            if current.startswith('"') and current.endswith('"'):
                current = current[1:-1]
            
            if Scanner.comparar(tk, "id"):
                if not self.mount.isMountedId(current):
                    Scanner.error("MKFS", "La partición no existe")
                    return
                if tk in required:
                    required.remove(tk)
                id = current
                
            elif Scanner.comparar(tk, "type"):
                type = current
        
        if required:
            for r in required:
                Scanner.error("MKFS", "El parámetro " + r + " es obligatorio")
            return
        
        self.formateo(id, type)
    
    def formateo(self, id, type="Full"):
        try:
            
            p = ""
            p , partition = self.mount.getmount(id)
            
            n = 0
            tamanioSuperBloque = struct.calcsize("<iiiiiddiiiiiiiiii")
            tamanioInodos = struct.calcsize("<iiiddd15ici")
            tamanioBloquesArchivos = len(bytes(Structs.BloquesArchivos()))
            
            n = (partition.part_size -  tamanioSuperBloque) // (4 + tamanioInodos + 3 * tamanioBloquesArchivos)
            
            spr = Structs.SuperBloque()
            spr.s_inodes_count = spr.s_free_inodes_count = n
            spr.s_blocks_count = spr.s_free_blocks_count = 3 * n
            spr.s_mtime = int(time.time())
            spr.s_umtime = int(time.time())
            spr.s_mnt_count = 1
            
            spr.s_filesystem_type = 2
            self.ext2(spr, partition, n, p)
            Scanner.mensaje("MKFS", "Se ha formateado la partición: " + partition.part_name + " con formato EXT2 con éxito")
             
        except Exception as e:
            Scanner.error("MKFS", e)
    
    def ext2(self, spr, p, n, path): #superbloque, particion, numero inodos, path
        # n -> número inodos y bloques
        # superbloque -> triple el número de inodos 3n
        tamanioSuperBloque = struct.calcsize("<iiiiiddiiiiiiiiii")
        tamanioInodos = struct.calcsize("<iiiddd15ici")
        tamanioBloquesCarpetas = len(bytes(Structs.BloquesCarpetas()))
        
        spr.s_bm_inode_start = p.part_start + tamanioSuperBloque #Bitmap de inodos
        spr.s_bm_block_start = spr.s_bm_inode_start + n #Bitmap de bloques
        spr.s_inode_start = spr.s_bm_block_start + (3 * n) #Inodos
        spr.s_block_start = spr.s_bm_inode_start + (n * tamanioInodos) #Bloques
        spr.s_inode_size = tamanioInodos
        spr.s_block_size = tamanioBloquesCarpetas

        actualizarSuperBloqueEnParticion(path, p, spr) #Incluir superbloque en la particion

        try: #escribir los datos de los inodos y bloques en el archivo
            with open(path, "rb+") as bfile: #formato inicial de ext2
                zero = b'0'
                bfile.seek(spr.s_bm_inode_start)
                bfile.write(zero * n)
                
                bfile.seek(spr.s_bm_block_start)
                bfile.write(zero * (3 * n))
                
                inode = Structs.Inodos()
                bfile.seek(spr.s_inode_start)
                for _ in range(n):
                    bfile.write(bytes(inode))
                
                folder = Structs.BloquesCarpetas()
                bfile.seek(spr.s_block_start)
                for _ in range(3 * n):
                    bfile.write(bytes(folder))
        except Exception as e:
            print(e)
        finally:
            bfile.close()

        inode = Structs.Inodos() #Inodo raiz (/)
        inode.i_uid = 1 #usuario root
        inode.i_gid = 1 #grupo root
        inode.i_size = 0 #tamaño del archivo
        inode.i_atime = spr.s_umtime #ultima fecha de acceso
        inode.i_ctime = spr.s_umtime #ultima fecha de modificacion
        inode.i_mtime = spr.s_umtime #ultima fecha de creacion
        inode.i_type = 0 # 0 = carpeta, 1 = archivo
        inode.i_perm = 664 #permisos de lectura y escritura
        inode.i_block[0] = 0 #porque es una carpeta
        
        fb = Structs.BloquesCarpetas() #Bloque carpeta de la carpeta raiz
        fb.b_content[0].b_name = "."
        fb.b_content[0].b_inodo = 0
        fb.b_content[1].b_name = ".."
        fb.b_content[1].b_inodo = 0
        fb.b_content[2].b_name = "user.txt" #archivo de usuarios
        fb.b_content[2].b_inodo = 1
        
        inodeArchivo = Structs.Inodos() #Inodo del archivo de usuarios.txt
        data = "1,G,root\n1,U,root,root,123\n" #Usuarios por defecto
        inodeArchivo.i_uid = 1
        inodeArchivo.i_gid = 1
        inodeArchivo.i_size = len(data) + tamanioBloquesCarpetas
        inodeArchivo.i_atime = spr.s_umtime
        inodeArchivo.i_ctime = spr.s_umtime
        inodeArchivo.i_mtime = spr.s_umtime
        inodeArchivo.i_type = 1 # 0 = carpeta, 1 = archivo
        inodeArchivo.i_perm = 664
        inodeArchivo.i_block[0] = 1 #primer bloque de datos, sobran 14 bloques
        
        #tamaño inodo raiz = tamaño inodo archivo + tamaño bloque carpeta + tamaño inodo archivo
        inode.i_size = inodeArchivo.i_size + tamanioBloquesCarpetas + tamanioInodos #actualizar el tamaño del inodo raiz
        
        fileb = Structs.BloquesArchivos() #crear una instancia de bloque de archivos
        fileb.b_content = data
        
        #actualizar datos en superbloque

        addInodo(path, p, inode) #agregar el inodo raiz
        addBloque(path, p, fb) #agregar el bloque de la carpeta raiz

        addInodo(path, p, inodeArchivo) #agregar el inodo del archivo user.txt
        addBloque(path, p, fileb) #agregar el bloque de archivo de user.txt

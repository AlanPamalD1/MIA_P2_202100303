#!/usr/bin/python
import os
import disk 
import mount 
import mkfs 
import users
from Structs import UsuarioActivo
import files
 
mountInstance = mount.Mount() 
logued = False
logueado = UsuarioActivo()

class Scanner:
    def __init__(self):
        pass
    
    @staticmethod
    def required_values(function):
        required_value = {
            "mkdisk": ["size", "path"],
            "rmdisk": ["path"],
            "fdisk": ["path", "name"],
            "fdisk-delete": ["path", "name"],
            "rep" : ["name", "path", "id"],
            "mount" : ["path", "name"],
            "unmount" : ["id"],
            "mkfs" : ["id"],
            "mkdir" : ["path"],
            "mkfile" : ["path"],
        }
        return required_value[function]

    @staticmethod
    def error(operacion, mensaje):
        print("!ERROR COMANDO {}¡;\t{}".format(operacion, mensaje))

    @staticmethod
    def comparar(text1, text2):
        if not text1 or not text2:
            return False
        return text1.upper() == text2.upper()
 
    @staticmethod
    def confirmar(mensaje):
        respuesta = input(f"{mensaje} (Y/N) ").upper()
        return respuesta == "Y"

    @staticmethod
    def mensaje(operacion, mensaje):
        print("COMANDO {};\t{}".format(operacion, mensaje))

    def comando(self, text):
        tkn = ""
        terminar = False
        for c in text:
            if terminar:
                if c == ' ' or c == '-':
                    break
                tkn += c
            elif c != ' ' and not terminar:
                if c == '#':
                    tkn = text
                    break
                else:
                    tkn += c
                    terminar = True
        return tkn

    def separar_tokens_wip(self, text):
        tokens = []
        if not text:
            return tokens
        text += ' '
        token = ""
        estado = 0
        for c in text:
            if estado == 0 and c == '-':
                estado = 1
            elif estado == 0 and c == '#':
                continue
            elif estado != 0:
                if estado == 1:
                    if c == '=':
                        estado = 2
                    elif c == ' ':
                        continue
                elif estado == 2:
                    if c == '\"':
                        estado = 3
                        continue
                    else:
                        estado = 4
                elif estado == 3:
                    if c == '\"':
                        estado = 4
                        continue
                elif estado == 4 and c == '\"':
                    tokens.clear()
                    continue
                elif estado == 4 and c == ' ':
                    estado = 0
                    tokens.append(token)
                    token = ""
                    continue
                token += c
        return tokens

    def separar_tokens(self, text):
        tokens = []
        if not text:
            return tokens
        text += ' '
        token = ""
        estado = 0
        for c in text:
            if estado == 0 and c == '-':
                estado = 1
            elif estado == 0 and c == '#':
                continue
            elif estado != 0:
                if estado == 1:
                    if c == '=':
                        estado = 2
                    elif c == ' ':
                        tokens.append(token)  # Agregar el token actual antes de comenzar con "-r"
                        token = ""
                        estado = 0
                elif estado == 2:
                    if c == '\"':
                        estado = 3
                        continue
                    else:
                        estado = 4
                elif estado == 3:
                    if c == '\"':
                        estado = 4
                        continue
                elif estado == 4 and c == '\"':
                    tokens.clear()
                    continue
                elif estado == 4 and c == ' ':
                    estado = 0
                    tokens.append(token)
                    token = ""
                    continue
                token += c
        
        return tokens

    def funciones(self, token, tokens):
        if token:
            if self.comparar( token, "MKDISK"):
                print("************** FUNCION MKDISK **************")
                disk.Disk.mkdisk(tokens)
                print("\n")
            elif self.comparar( token,  "RMDISK"):
                print("************** FUNCION RMDISK **************")
                disk.Disk.rmdisk(tokens)
                print("\n") 
            elif self.comparar( token,  "FDISK"):
                print("************** FUNCION FDISK **************")
                disk.Disk.fdisk(tokens, mountInstance)
                print("\n")
            elif self.comparar( token,  "EXECUTE"):
                print("************** FUNCION EXECUTE **************")
                self.funcion_excec(tokens)
                print("\n")
            elif self.comparar( token,  "MOUNT"):
                print("************** FUNCION MOUNT **************")
                mountInstance.validarDatos(tokens)
                print("\n") 
            elif self.comparar( token,  "UNMOUNT"):
                print("************** FUNCION UNMOUNT **************")
                mountInstance.validarDatosU(tokens)
                print("\n")
            elif self.comparar( token,  "MKFS"):
                print("************** FUNCION MKFS **************")
                fileSystem = mkfs.MKFS(mountInstance)
                fileSystem.mkfs(tokens) 
                print("\n")
            elif self.comparar( token,  "REP"):
                print("************** REP **************")
                disk.Disk.rep(tokens, mountInstance)
                print("\n")
            elif self.comparar( token,  "MOUNTS"):
                print("************** FUNCION MOUNTS **************")
                mountInstance.listaMount()
                print("\n") 
            elif self.comparar( token,  "LOGIN"):
                print("************** FUNCION LOGIN **************")
                global logued
                global logueado
                if(logued):
                    print("Ya hay una sesión activa")
                else:
                    logued, logueado = users.Usuarios().login(tokens, mountInstance)
                print("\n")
            elif self.comparar( token,  "LOGOUT"):
                print("************** FUNCION LOGOUT **************") 
                if(logued):
                    logued = users.Usuarios(mountInstance).logout()
                    logueado = UsuarioActivo() # Se limpia el usuario logueado
                else:
                    print("No hay una sesión activa")
                print("\n")
            elif self.comparar( token,  "MKGRP"):
                print("************** FUNCION MKGRP **************")
                if(logued):
                    users.Usuarios(mountInstance).validarDatosGrp(tokens, "MK")
                else:
                    print("No hay una sesión activa")
                print("\n")
            elif self.comparar( token,  "RMGRP"):
                print("************** FUNCION RMGRP **************")
                if(logued):
                    users.Usuarios(mountInstance).validarDatosGrp(tokens, "RM")
                else:
                    print("No hay una sesión activa")
                print("\n")
            elif self.comparar( token,  "MKUSR"):
                print("************** FUNCION MKUSR **************")
                if(logued):
                    users.Usuarios(mountInstance).validarDatosusr(tokens, "MK")
                else:
                    print("No hay una sesión activa")
                print("\n")
            elif self.comparar( token,  "RMUSR"):
                print("************** FUNCION RMUSR **************")
                if(logued):
                    users.Usuarios(mountInstance).validarDatosusr(tokens, "RM")
                else:
                    print("No hay una sesión activa")
                print("\n")
            elif self.comparar( token,  "MKDIR"):
                print("************** FUNCION MKDIR **************")
                if(logued):
                    fileSystem = files.FILES(mountInstance, logueado)
                    fileSystem.mkdir(tokens)
                else:
                    print("No hay una sesión activa")
                print("\n")
            elif self.comparar( token,  "MKFILE"):
                print("************** FUNCION MKFILE **************")
                if(logued):
                    fileSystem = files.FILES(mountInstance, logueado)
                    fileSystem.mkfile(tokens)
                else:
                    print("No hay una sesión activa")
                print("\n")
            elif self.comparar( token,  "EXIT"):
                print("************** FUNCION EXIT **************")
                print("Saliendo del programa...")
                exit()
            elif token.startswith("#"):
                print("************** COMENTARIO **************")
                print(token)
                print("\n")
            else:
                self.error("ERROR","No se reconoce el comando: " + token)
                print("\n")

    def funcion_excec(self, tokens):
        path = ""
        for token in tokens:
            tk = token[:token.find("=")]
            token = token[len(tk) + 1:]
            if self.comparar(tk, "path"):
                path = token
        if not path:
            self.error("EXECUTE","Se requiere path para el metodo execute: " + token)
            return
        self.excec(path)

    def excec(self, path):
        lines = []

        # Manejar carpeta
        if not os.path.exists(path): #Si no existe la carpeta, se crea
            self.error("EXECUTE","No existe el archivo en la ruta " + path)
            return

        with open(path, "r") as input_file:
            for line in input_file:
                lines.append(line.strip())
        for i in lines:
            texto = i
            tk = self.comando(texto)
            if texto:
                if self.comparar(texto, "pause"):
                    print("************** FUNCION PAUSE **************")
                    input("Presione enter para continuar...")
                    print("\n")
                    continue
                texto = texto[len(tk) + 1:]
                tokens = self.separar_tokens(texto)
                self.funciones(tk, tokens)

    def inicio(self):
        while True:
            print(">>>>>>>>>>>>>>>>>>>>>>>>> INGRESE UN COMANDO <<<<<<<<<<<<<<<<<<<<<<<<<")
            print("->Si deseas salir escribe \"exit\"<-")
            entrada = "execute -path=ejecucion-windows.adsj"
            #entrada = "execute -path=ejecucion-linux.adsj"
            #entrada = input("-> ")
            if entrada.lower() == "exit":
                break
            token = self.comando(entrada)
            entrada = entrada[len(token) + 1:] # se quita el primer comando, ej: exec, deja el path
            tokens = self.separar_tokens(entrada) # Se separan los tokens
            self.funciones(token, tokens) # Se ejecuta la funcion

if __name__ == "__main__":
    scanner = Scanner()
    scanner.inicio()

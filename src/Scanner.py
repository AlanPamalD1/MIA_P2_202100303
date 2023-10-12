#!/usr/bin/python
import os
import disk
import mount 
import mkfs 
import users
from Structs import UsuarioActivo
import files
from consola import Console
 
mountInstance = mount.Mount() 
logued = False
logueado = UsuarioActivo()

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

def error(operacion, mensaje):
    print('!ERROR {:10s}¡;\t{}'.format(operacion, mensaje))
    consola = Console()
    consola.escribir( '!ERROR {:10s}¡;\t{}'.format(operacion, mensaje) )


def comparar(text1, text2):
    if not text1 or not text2:
        return False
    return text1.upper() == text2.upper()

def mensaje(operacion, mensaje):
    print('COMANDO {:9s};\t{}'.format(operacion, mensaje))

    consola = Console()
    consola.escribir( 'COMANDO {:9s};\t{}'.format(operacion, mensaje) )


def comando( text):
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

def separar_tokens_wip( text):
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

def separar_tokens( text):
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

def funciones( token, tokens, mnt, islgd, lgdo):
    
    # Se asignan las variables globales
    global mountInstance
    global logued
    global logueado
    mountInstance = mnt
    logued = islgd
    logueado = lgdo
    
    if token:
        if comparar( token, "PAUSE"):
            print("************** PAUSE **************")
            print("Pause ...")
            consola = Console()
            consola.escribir("Pause ...")
        if comparar( token, "MKDISK"):
            print("************** FUNCION MKDISK **************")
            disk.Disk.mkdisk(tokens)
            print("\n")
        elif comparar( token,  "RMDISK"):
            print("************** FUNCION RMDISK **************")
            disk.Disk.rmdisk(tokens)
            print("\n") 
        elif comparar( token,  "FDISK"):
            print("************** FUNCION FDISK **************")
            disk.Disk.fdisk(tokens, mountInstance)
            print("\n")
        elif comparar( token,  "EXECUTE"):
            print("************** FUNCION EXECUTE **************")
            funcion_excec(tokens)
            print("\n")
        elif comparar( token,  "MOUNT"):
            print("************** FUNCION MOUNT **************")
            mountInstance.validarDatos(tokens)
            print("\n") 
        elif comparar( token,  "UNMOUNT"):
            print("************** FUNCION UNMOUNT **************")
            mountInstance.validarDatosU(tokens)
            print("\n")
        elif comparar( token,  "MKFS"):
            print("************** FUNCION MKFS **************")
            fileSystem = mkfs.MKFS(mountInstance)
            fileSystem.mkfs(tokens) 
            print("\n")
        elif comparar( token,  "REP"):
            print("************** REP **************")
            disk.Disk.rep(tokens, mountInstance)
            print("\n")
        elif comparar( token,  "MOUNTS"):
            print("************** FUNCION MOUNTS **************")
            mountInstance.listaMount()
            print("\n") 
        elif comparar( token,  "LOGIN"):
            print("************** FUNCION LOGIN **************")
            if(logued):
                print("Ya hay una sesión activa")
                consola = Console()
                consola.escribir("Ya hay una sesión activa")
            else:
                logued, logueado = users.Usuarios().login(tokens, mountInstance)
            print("\n")
        elif comparar( token,  "LOGOUT"):
            print("************** FUNCION LOGOUT **************") 
            if(logued):
                logued = users.Usuarios(mountInstance).logout()
                logueado = UsuarioActivo() # Se limpia el usuario logueado
            else:
                print("No hay una sesión activa")
                consola = Console()
                consola.escribir("No hay una sesión activa")
            print("\n")
        elif comparar( token,  "MKGRP"):
            print("************** FUNCION MKGRP **************")
            if(logued):
                users.Usuarios(mountInstance).validarDatosGrp(tokens, "MK")
            else:
                print("No hay una sesión activa")
                consola = Console()
                consola.escribir("No hay una sesión activa")
            print("\n")
        elif comparar( token,  "RMGRP"):
            print("************** FUNCION RMGRP **************")
            if(logued):
                users.Usuarios(mountInstance).validarDatosGrp(tokens, "RM")
            else:
                print("No hay una sesión activa")
                consola = Console()
                consola.escribir("No hay una sesión activa")
            print("\n")
        elif comparar( token,  "MKUSR"):
            print("************** FUNCION MKUSR **************")
            if(logued):
                users.Usuarios(mountInstance).validarDatosusr(tokens, "MK")
            else:
                print("No hay una sesión activa")
                consola = Console()
                consola.escribir("No hay una sesión activa")
            print("\n")
        elif comparar( token,  "RMUSR"):
            print("************** FUNCION RMUSR **************")
            if(logued):
                users.Usuarios(mountInstance).validarDatosusr(tokens, "RM")
            else:
                print("No hay una sesión activa")
            print("\n")
        elif comparar( token,  "MKDIR"):
            print("************** FUNCION MKDIR **************")
            if(logued):
                fileSystem = files.FILES(mountInstance, logueado)
                fileSystem.mkdir(tokens)
            else:
                print("No hay una sesión activa")
                consola = Console()
                consola.escribir("No hay una sesión activa")
            print("\n")
        elif comparar( token,  "MKFILE"):
            print("************** FUNCION MKFILE **************")
            if(logued):
                fileSystem = files.FILES(mountInstance, logueado)
                fileSystem.mkfile(tokens)
            else:
                print("No hay una sesión activa")
            print("\n")
        elif comparar( token,  "EXIT"):
            print("************** FUNCION EXIT **************")
            print("Saliendo del programa...")
            consola = Console()
            consola.escribir("Saliendo del programa...")
            exit()
        elif token.startswith("#"):
            print("************** COMENTARIO **************")
            print(token)
            print("\n")
        else:
            error("ERROR","No se reconoce el comando: " + token)
            print("\n")
    
    return  mountInstance, logued, logueado

def funcion_excec( tokens):
    path = ""
    for token in tokens:
        tk = token[:token.find("=")]
        token = token[len(tk) + 1:]
        if comparar(tk, "path"):
            path = token
    if not path:
        error("EXECUTE","Se requiere path para el metodo execute: " + token)
        return
    excec(path)

def excec( path):
    lines = []

    # Manejar carpeta
    if not os.path.exists(path): #Si no existe la carpeta, se crea
        error("EXECUTE","No existe el archivo en la ruta " + path)
        return

    with open(path, "r") as input_file:
        for line in input_file:
            lines.append(line.strip())
    for i in lines:
        texto = i
        tk = comando(texto)
        if texto:
            if comparar(texto, "pause"):
                print("************** FUNCION PAUSE **************")
                input("Presione enter para continuar...")
                print("\n")
                continue
            texto = texto[len(tk) + 1:]
            tokens = separar_tokens(texto)
            funciones(tk, tokens)

def inicio():
    while True:
        print(">>>>>>>>>>>>>>>>>>>>>>>>> INGRESE UN COMANDO <<<<<<<<<<<<<<<<<<<<<<<<<")
        print("->Si deseas salir escribe \"exit\"<-")
        entrada = "execute -path=src/ejecucion-windows.adsj"
        #entrada = "execute -path=SystemExt/ejecucion-linux.adsj"
        #entrada = input("-> ")
        if entrada.lower() == "exit":
            break
        token = comando(entrada)
        entrada = entrada[len(token) + 1:] # se quita el primer comando, ej: exec, deja el path
        tokens = separar_tokens(entrada) # Se separan los tokens
        funciones(token, tokens) # Se ejecuta la funcion

if __name__ == "__main__":
    inicio()

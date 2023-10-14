// Espera a que el DOM esté listo

function guardarDatos(){
    const idparticion = document.getElementById('idparticion').value;
    const usuario = document.getElementById('usuario').value;
    const password = document.getElementById('password').value;

    return {idparticion, usuario, password};
}
// Espera a que el DOM esté listo
document.addEventListener("DOMContentLoaded", function () {
    // Aquí puedes escribir la lógica para guardar los datos del formulario
    

});

function guardarDatos(){
    const idparticion = document.getElementById('idparticion').value;
    const usuario = document.getElementById('usuario').value;
    const password = document.getElementById('password').value;

    return {idparticion, usuario, password};
}
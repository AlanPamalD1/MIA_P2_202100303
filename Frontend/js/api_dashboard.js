
txtAreaEntrada = document.getElementById("entrada");
txtAreaConsola = document.getElementById("consola");

inputPath = document.getElementById("file_path");

btnExaminar = document.getElementById("btn_examinar"); //Abrir modal para examinar archivo
btnEjecutar = document.getElementById("btn_ejecutar");
btnDataBase = document.getElementById("btn_ver_database");
btnLogin = document.getElementById("btn_login");

const file_input = document.getElementById('file_input');

btnLogin.addEventListener("click", async function (e) {
    e.preventDefault();

    //redigir a pagina de login
    window.location.href = "login.html";
});

btnEjecutar.addEventListener("click", async function (e) {
    e.preventDefault();
    ejecutarComandos()
});

btnDataBase.addEventListener("click", async function (e) {
	e.preventDefault()
	
    const res = await endpoint_getDb()

    if (res != undefined) {
        console.log(res.message)
    }

});


async function procesarComandos(codigo) {

    //separar el codigo por saltos de linea
    const comandos = codigo.split('\n');

    for (let i = 0; i < comandos.length; i++) {
        const cmd = comandos[i];
        console.log('comando ',i)
        if (cmd.replace(/\s/g, '').toLowerCase().startsWith('login')) {

            // Mostrar el modal
            const modal = new bootstrap.Modal(document.getElementById("modalLogin"));
            label_login = document.getElementById("label_login_line");
            label_login.innerHTML = "Linea " + i
            modal.show();

            // Crear una promesa para esperar el clic en el botón "registrarLogin"
            const buttonClickedPromise = new Promise((resolve) => {
                document.getElementById("registrarLogin").addEventListener("click", resolve);
            });
            
            // Crear una promesa para esperar el cierre del modal
            const modalClosedPromise = new Promise((resolve) => {
                modal._element.addEventListener("hide.bs.modal", resolve);
            });

            // Esperar a que se resuelva la primera de las dos promesas
            await Promise.race([modalClosedPromise, buttonClickedPromise]);

            // Continuar con el procesamiento después de hacer clic en el botón
            const idparticion = document.getElementById('idparticion').value;
            const usuario = document.getElementById('usuario').value;
            const password = document.getElementById('password').value;

            const txtLogin = 'login -user=' + usuario + ' -pass=' + password + ' -id=' + idparticion;
            console.log(txtLogin, 'en la línea:', i);
            
            // Resetear input
            document.getElementById('idparticion').value = "";
            document.getElementById('usuario').value = "";
            document.getElementById('password').value = "";
        }
    }

    const modal = new bootstrap.Modal(document.getElementById("modalLogin"));
    modal.hide();

}

async function ejecutarComandos() {
    try {

        //limpiar consola
        txtAreaConsola.value = "";

        const codigo = txtAreaEntrada.value;
        
        endpoint_resetDb()

        const res = await endpoint_exec(codigo)

        if (res != undefined) {
            txtAreaConsola.value += res.consola
            console.log(res.message)
        }
    } catch (error) {
        console.error(error)
    }

}

async function endpoint_exec(codigo) {

    const url = "http://localhost:4000/exec";
    const cmds = codigo.split('\n');
    const cmdsData = { comandos: cmds };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(cmdsData)
        });

        if (!response.ok) {
            throw new Error(`Error de la API: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error:', error);
        return undefined;
    }
}

async function endpoint_getDb(){

	const url = "http://localhost:4000/getBaseDeDatos";

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
            })
    
            if (!response.ok) {
                throw new Error(`Error de la API: ${response.status}`);
            }
    
            const data = await response.json();
            return data;
        
    } catch (error) {
        console.error('Error:', error);
        return undefined;
    }
}

async function endpoint_resetDb(){

	const url = "http://localhost:4000/resetBaseDeDatos";

	try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
            })
    
            if (!response.ok) {
                throw new Error(`Error de la API: ${response.status}`);
            }
    
            const data = await response.json();
            return data;
        
    } catch (error) {
        console.error('Error:', error);
        return undefined;
    }
}


//otros eventos
file_input.addEventListener('change', (e) => { //cuando se selecciona un archivo

    const file = e.target.files[0];

    if (file) {
        const reader = new FileReader();
        
        const fileName = file.name;
        // Guardar el nombre en el sessionStorage
        //sessionStorage.setItem('archivo_nombre', fileName);
        
        //Colocar contenido del archivo en el textarea de entrada
        reader.onload = (event) => {
            const fileContent = event.target.result;
            txtAreaEntrada.value = fileContent;
        };

        //Colocar la ruta del archivo en el input de la ruta
        inputPath.value = fileName;
        

        reader.readAsText(file);
    }else{
        inputPath.value = "";
    }

    const modal = new bootstrap.Modal(document.getElementById("modalArchivo"));
    modal.hide();

    file_input.value = null;

});

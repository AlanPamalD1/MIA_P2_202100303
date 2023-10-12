txtAreaEntrada = document.getElementById("entrada");
txtAreaConsola = document.getElementById("consola");

inputPath = document.getElementById("file_path");

btnExaminar = document.getElementById("btn_examinar");
btnEjecutar = document.getElementById("btn_ejecutar");
btnDataBase = document.getElementById("btn_ver_database");

const file_input = document.getElementById('file_input');

btnExaminar.addEventListener("click", function (e) {
    e.preventDefault(); 
});

btnEjecutar.addEventListener("click", async function (e) {
    e.preventDefault();

    ejecutar()

});

btnDataBase.addEventListener("click", async function (e) {
	e.preventDefault()
	clearDataBaseApi()
});

async function ejecutar() {

    const codigo = txtAreaEntrada.value;
    //separar el codigo por saltos de linea
    const comandos = codigo.split('\n');

	bloqueCmd = []

	comandos.forEach(cmd => {
		if (cmd.replace(/\s/g, '').toLowerCase().startsWith('login')) { //si es un comando de login

			console.log("Se encontró un comando login")

			//ejecutar el endpoint con los comandos que han sido leidos
			if( bloqueCmd.length > 0) {
				//ejecutar el bloque de comandos
				ejecutarComandos(bloqueCmd);
				bloqueCmd = [];
			}

			//ejecutar endpoint con el comando login
			//login -user=*** -pass=*** -id=***
			user = 'root'
			pwd = '123'
			id = '031d1'
			txtLogin = 'login -user=' + user + ' -pass=' + pwd + ' -id=' + id
			cmds = [txtLogin]
			console.log(cmds)
			ejecutarComandos(cmds);

			
		}else{ // Cualquier otro comando
			//agregar el comando al bloque de comandos
			bloqueCmd.push(cmd);
		}
	});

	//ejecutar los comandos que quedaron en el bloque
	if( bloqueCmd.length > 0) {
		ejecutarComandos(bloqueCmd);
		bloqueCmd = [];
	}

	//clearDataBaseApi()

}

function ejecutarComandos(commands){

	console.log(commands.length,' en ejecucion...')

	const url = "http://localhost:4000/exec";
    const data = { comandos: commands };

    fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      })
        .then(response => response.json())
        .then(data => {
          // Maneja la respuesta de la API aquí
          console.log(data.message);
          console.log(data.baseDeDatos);
          txtAreaConsola.value = data.consola;
        })
        .catch(error => {
          console.error('Error:', error);
          txtAreaConsola.value = "Error: " + error + "\n"
        });
}


function clearDataBaseApi(){
	const url = "http://localhost:4000/getBaseDeDatos";

	fetch(url, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
		}
		})
		.then(response => response.json())
		.then(data => {
			// Maneja la respuesta de la API aquí
			console.log(data.message);
		})
		.catch(error => {
			console.error('Error:', error);
		});
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

    file_input.value = null;
});

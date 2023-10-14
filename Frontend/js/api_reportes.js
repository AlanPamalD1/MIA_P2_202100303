//Cuando cargue la pagina
document.addEventListener("DOMContentLoaded", function () {
    // obtener idparticion de localstorage
    btnLogout = document.getElementById("btn_logout");
    btnLogout.addEventListener("click", async function (e) {

        //redigir a pagina de login
        window.location.href = "dashboard.html";
    });

    llenarTabla()

    //Cerrar popup
    const divOverlay = document.getElementById("overlay");
    const divPopup = document.getElementById("popup");
    divOverlay.addEventListener("click", function () {
        divOverlay.style.display = "none";
        divPopup.style.display = "none";
    });

});

const idparticion = localStorage.getItem("idparticion");

// si no existe idparticion, redirigir a login
if (idparticion == undefined) {
    alert("Debe iniciar sesión primero para acceder a esta pagina")
    window.location.href = "dashboard.html";
}

async function llenarTabla() {

    const data = await endpoint_getRutasReportes(idparticion);

    archivos = data.archivos;
    rutas = data.rutas;

    rutas.forEach(ruta => {
        agregarFila(ruta, archivos)
    });

}

function agregarFila(ruta, archivos) {
    var tabla = document.getElementById("tablaReportes").getElementsByTagName('tbody')[0];
    var newRow = tabla.insertRow(tabla.rows.length);
    var cell1 = newRow.insertCell(0);
    var cell2 = newRow.insertCell(1);
    var cell3 = newRow.insertCell(2);
    
    //verificar si en archivos hay un archivo["ruta_formato"] que termine con la ruta

    var archivo = archivos.find(archivo => archivo.ruta_formato.endsWith(ruta.replace(/ /g,"").replace("▼","")));

    if (archivo != undefined) {

        if (archivo.size > 1024) {
            archivo.size = archivo.size / 1024;
            archivo.size = archivo.size.toFixed(2);
            archivo.size = archivo.size + " KB";
        } else if (archivo.size > (1024 * 1024)) {
            archivo.size = archivo.size / (1024 * 1024);
            archivo.size = archivo.size.toFixed(2);
            archivo.size = archivo.size + " MB";
        } else {
            archivo.size = archivo.size + " bytes";
        }

        cell2.innerHTML = archivo.size;
        cell3.innerHTML = '<button class="btn btn-primary"><i class="fas fa-eye"></i></button>';

        //agregar evento al boton
        cell3.addEventListener("click", async function (e) {

            //obtener ruta del archivo
            const ruta_archivo = archivo.ruta;
            alert(ruta_archivo);

            //obtener archivo en binario
            const data = await endpoint_getFileBin64(ruta_archivo);

            if (! data.file_exists) { // si el archivo no existe
                alert("El archivo no existe");
                return;
            }

            // Configurar el popup
            configurarPopup(data);

            // Mostrar el popup
            const divOverlay = document.getElementById("overlay");
            const divPopup = document.getElementById("popup");
            divOverlay.style.display = "block";
            divPopup.style.display = "block";


        });
    } 

    //configurar ruta para que cada espacio en blanco se mire en la tabla
    ruta = ruta.replace(/ /g, "&nbsp&nbsp&nbsp;");

    cell1.innerHTML = ruta;
    
}

// Función para vaciar la tabla
function vaciarTabla() {
    var tabla = document.getElementById("tablaReportes").getElementsByTagName('tbody')[0];
    tabla.innerHTML = "";
}

async function endpoint_getRutasReportes(idparticion){

	const url = "http://localhost:4000/getRutasReportes";
    const cmdsData = { idparticion: idparticion };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body : JSON.stringify(cmdsData)
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

async function endpoint_getFileBin64(file){
    
    const url = "http://localhost:4000/getFileBin64";
    const cmdsData = { ruta: file };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body : JSON.stringify(cmdsData)
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

async function configurarPopup (data) {
    
    const divPopup = document.getElementById("popup");
    divPopup.innerHTML = "";

    const base64String = data.file_encoded;
    const file_type = data.file_type;

    if (file_type == 'image') {
        // Mostrar la imagen en una etiqueta <img>
        const img = document.createElement("img");
        img.setAttribute("id", "popup-content");
        img.src = base64String;
        divPopup.appendChild(img);
    } else if (file_type == 'pdf') {
        // Mostrar el PDF en un <iframe>
        const binaryPdfData = atob(base64String.substring(28));
        const pdfByteArray = new Uint8Array(binaryPdfData.length);
        for (let i = 0; i < binaryPdfData.length; i++) {
            pdfByteArray[i] = binaryPdfData.charCodeAt(i);
        }
        const pdfBlob = new Blob([pdfByteArray], { type: "application/pdf" });
        const pdfUrl = URL.createObjectURL(pdfBlob);
        const iframe = document.createElement("iframe");
        iframe.setAttribute("id", "popup-content");
        iframe.src = pdfUrl;
        iframe.width = "100%";
        iframe.height = "600px";
        divPopup.appendChild(iframe);
    } else if (file_type == 'text') {
        const textarea = document.createElement("textarea"); // crear un elemento textarea
        textarea.setAttribute("id", "popup-content");
        textarea.value = base64String; // establecer el contenido del textarea con la cadena base64 decodificada
        divPopup.appendChild(textarea); // agregar el textarea al div popup
    }
}
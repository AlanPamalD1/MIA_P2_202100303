// focus inputs
(function () {
    //[ Focus input ]
    inputs100 = document.getElementsByClassName('input100');
    for (let i = 0; i < inputs100.length; i++) {        
        inputs100[i].addEventListener('blur', function(){
            if(inputs100[i].value.trim() != "") {
                inputs100[i].classList.add('has-val');
            }
            else {
                inputs100[i].classList.remove('has-val');
            }
        });
    }
})();


async function endpoint_login(user, pwd, id) {

    const url = "http://localhost:4000/login";
    const loginData = { username: user, password: pwd, idparticion: id };

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(loginData)
        });

        if (!response.ok) {
            throw new Error(`Error de la API: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        return undefined;
    }
}

//Manejo endpoints
const btnIngresar = document.getElementById("btn_ingresar")
const btnCargarArchivos = document.getElementById("btn_cargar_archivos")

btnIngresar.addEventListener("click", async () => {
    const inputIdParticion = document.getElementById("input_id_particion")
    const inputUsername = document.getElementById("input_username")
    const inputPassword = document.getElementById("input_password")

    const usuario = inputUsername.value
    const password = inputPassword.value
    const idparticion = inputIdParticion.value
    
    try {

        const res = await endpoint_login(usuario, password, idparticion)

        if (res != undefined) {
            alert(res.message)
        }else{
            alert("Error al ingresar")
        }

    } catch (error) {
        console.error(error)
        alert("Error al ingresar")
    }


    //resetear inputs
    document.getElementById("input_id_particion").value = ""
    document.getElementById("input_username").value = ""
    document.getElementById("input_password").value = ""
})

btnCargarArchivos.addEventListener("click", async () => {
    //redirigir a dashboard
    window.location.href = "dashboard.html"
})
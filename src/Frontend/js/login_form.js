
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
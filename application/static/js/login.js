// Login
const usernameInput = document.querySelector('#username')
const passwordInput = document.querySelector('#password')
const loginBtn = document.querySelector('#login')
const loginWrp = document.querySelector('#login-wrp')
const userSection = document.querySelector('#user-section')
const welcome = document.querySelector('#welcome')
const logoutBtn = document.querySelector('#logout')

const currentUser = () => {
    if (localStorage.getItem('username')) {
        loginWrp.style.display = 'none';
        userSection.style.display = 'block';
        welcome.innerHTML = `<strong>${localStorage.getItem('username')}</strong>`;
    }
    else{
        loginWrp.style.display = 'block';
        userSection.style.display = 'none';
        welcome.innerHTML = 'Unauthorized';
    }
}

currentUser()

function logout(){
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    document.cookie="user="+  "None" + ";path=/";

    loginWrp.style.display = 'block';
    userSection.style.display = 'none';
    welcome.innerHTML = 'Unauthorized';
}

function login(){
    let formData = new FormData()
    formData.append('username', usernameInput.value)
    formData.append('password', passwordInput.value)

    fetch('/login/token', {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if(response.status!==200)
                throw Error(response.status)
            return response.json();
        })
        .then(data => {
            console.log(data)
            localStorage.setItem('token', data.access_token)
            localStorage.setItem('username', data.username)
            console.log(data.username)
            document.cookie="user="+  data.username + ";path=/";

            currentUser()
        })
        .catch(error => {
            console.log("in catch")
            if(error.message == "422"){
                alert("Неверные данные");
            }else if(error.message == "404"){
                alert("Пользователь не найден");
            }
            else{
            }
        })
}

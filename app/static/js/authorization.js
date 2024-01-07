function add_todo(){
formData = new FormData()
    formData.append("title", document.getElementById('title_add').value)
    formData.append("details", document.getElementById('details_add').value)
    formData.append("type", document.getElementById('type').value)
    formData.append("fullname", document.getElementById('fullname').value)
    fetch(`/add`, {
        method: "POST",
        body: formData,
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token') }`
        },
    })
        .then(response => {
            if(response.status==401)
                throw new Error(response.status);
            return response.json();
        })
        .then(data => {
            if(data["answer"] == "title not found"){
                console.log(data);
            }
            else if(data["answer"] == "ok"){
                window.location.href = "/list";
            }

        })
        .catch(error => {
            if(error.message == "401"){
                alert("Ошибка авторизации");
                window.location.href = "/log_in";
            }else{
                console.error('Произошла ошибка:', error);
            }
        })
}

function change_status(todo_id){
    var path = "/change_status/" + todo_id
    fetch(path, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token') }`
        },
    })
        .then(response => {
            console.log("response");
            if(response.status!=200)
                throw new Error(response.status);
            return response.json();
        })
        .then(data => {
            location.reload();
        })
        .catch(error => {
            if(error.message == "401"){
                alert("Ошибка авторизации");
                window.location.href = "/log_in";
            }else{
                console.error('Произошла ошибка:', error);
                window.location.href = "/log_in";
            }
        })
}

function delete_entry(todo_id){
    var path = "/delete/" + todo_id;
    fetch(path, {
        method: "DELETE",
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token') }`
        },
    })
        .then(response => {
            console.log("response");
            if(response.status!=200)
                throw new Error(response.status);
            return response.json();
        })
        .then(data => {
            location.reload();
        })
        .catch(error => {
            if(error.message == "401"){
                alert("Ошибка авторизации");
                window.location.href = "/log_in";
            }else{
                console.error('Произошла ошибка:', error);
                window.location.href = "/log_in";
            }
        })
}

function delete_every_todo(){
    var path = "/delete_all/";
    fetch(path, {
        method: "DELETE",
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token') }`
        },
    })
        .then(response => {
            console.log("response");
            if(response.status!=200)
                throw new Error(response.status);
            return response.json();
        })
        .then(data => {
            location.reload();
        })
        .catch(error => {
            if(error.message == "401"){
                alert("Ошибка авторизации");
                window.location.href = "/log_in";
            }else{
                console.error('Произошла ошибка:', error);
                window.location.href = "/log_in";
            }
        })
}
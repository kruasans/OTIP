function add_todo(){
    formData = new FormData()
    formData.append("title", document.getElementById('title_add').value)
    formData.append("details", document.getElementById('details_add').value)
    formData.append("type", document.getElementById('type').value)
    formData.append("fullname", document.getElementById('fullname').value)
    fetch(`/todo/add`, {
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
                window.location.href = "/todo/list";
            }

        })
        .catch(error => {
            if(error.message == "401"){
                alert("Ошибка авторизации");
                console.error('Произошла ошибка:', error);
                window.location.href = "/login/log_in";
            }else{
                alert("Ошибка");
                console.error('Произошла ошибка:', error);
                window.location.href = "/";
            }
        })
}

function change_status(todo_id){
    var path = "/todo/change_status/" + todo_id
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
                window.location.href = "/login/log_in";
            }else{
                console.error('Произошла ошибка:', error);
                window.location.href = "/";
            }
        })
}

function delete_entry(todo_id){
    var path = "/todo/delete/" + todo_id;
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
                window.location.href = "/login/log_in";
            }else{
                console.error('Произошла ошибка:', error);
                window.location.href = "/";
            }
        })
}

function delete_every_todo(){
    var path = "/todo/delete_all/";
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
                window.location.href = "/login/log_in";
            }else{
                console.error('Произошла ошибка:', error);
                window.location.href = "/";
            }
        })
}

function upload(){
    var path = "/todo/upload/";
    formData = new FormData();
    var file_input = document.getElementById('file_input');
    var file = file_input.files[0];
    formData.append("file_input", file);
    fetch(path, {
        method: "POST",
        body: formData,
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token') }`
        },
    })
        .then(response => {
            console.log("response");
            console.log(response);
            if(response.status!=200)
                throw new Error(response.status);
            return response.json();
        })
        .then(data => {
            window.location.href = "/todo/list";
        })
        .catch(error => {
            if(error.message == "401"){
                alert("Ошибка авторизации");
                window.location.href = "/login/log_in";
            }else if(error.message == "403"){
                alert("Файл неподходящего формата");
                window.location.href = "/todo/list";
            }else{
                console.error('Произошла ошибка:', error);
                alert("Ошибка");
                window.location.href = "/";
            }
        })
}

function edit(todo_id){
    var path = "/todo/edit/" + todo_id;
    formData = new FormData();
    formData.append("title", document.getElementById('title').value);
    formData.append("details", document.getElementById('details').value);
    formData.append("completed", document.getElementById('completed').checked);
    formData.append("fullname", document.getElementById('fullname').value);
    fetch(path, {
        method: "POST",
        body: formData,
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token') }`
        },
    })
        .then(response => {
            console.log("response");
            console.log(response);
            if(response.status!=200)
                throw new Error(response.status);
            return response.json();
        })
        .then(data => {
            console.log(data);
            window.location.href = "/todo/list";
        })
        .catch(error => {
            if(error.message == "401"){
                alert("Ошибка авторизации");
                window.location.href = "/login/log_in";
            }else if(error.message == "422"){
                alert("Неверный формат данных");
                window.location.href = "/todo/list";
            }else{
                console.error('Произошла ошибка:', error);
                alert("Ошибка");
                window.location.href = "/";
            }
        })
}


function load_image(todo_id){
    var path = "/todo/load_image/" + todo_id;
    formData = new FormData();
    var file_input = document.getElementById('file_input');
    var file = file_input.files[0];
    formData.append("file_input", file);
    fetch(path, {
        method: "POST",
        body: formData,
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token') }`
        },
    })
        .then(response => {
            console.log("response");
            console.log(response);
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
                window.location.href = "/login/log_in";
            }else if(error.message == "422"){
                alert("Неверный формат данных");
                location.reload();
            }else if(error.message == "415"){
                alert("Неверный формат картинки");
                location.reload();
            }else{
                if(error.message == "409"){
                    alert("Выбран дубликат");
                    location.reload();
                }else{
                console.error('Произошла ошибка:', error);
                alert("Ошибка");
                window.location.href = "/";
                }
            }
        })
}

function import_gitlab(){
    var path = "/todo/import_issues/";
    formData = new FormData();
    formData.append("url", document.getElementById('url').value);
    formData.append("token", document.getElementById('token_gitlab').value);
    fetch(path, {
        method: "POST",
        body: formData,
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token') }`
        },
    })
        .then(response => {
            console.log("response");
            console.log(response);
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
                window.location.href = "/login/log_in";
            }else if(error.message == "422"){
                alert("Неверный формат данных");
                location.reload();
            }else if(error.message == "415"){
                alert("Неверный формат картинки");
                location.reload();
            }else if(error.message == "301"){
                alert("Ошибка авторизации по токену");
                location.reload();
            }else{
                console.error('Произошла ошибка:', error);
                alert("Ошибка");
                window.location.href = "/";
            }
        })
}

function generation(count){
    var path = "/todo/generate/";
    formData = new FormData();
    formData.append("count", count);
    fetch(path, {
        method: "POST",
        body: formData,
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token') }`
        },
    })
        .then(response => {
            console.log("response");
            console.log(response);
            if(response.status!==200)
                throw new Error(response.status);
            return response.json();
        })
        .then(data => {
            window.location.href = "/todo/list";
        })
        .catch(error => {
            if(error.message == "401"){
                alert("Ошибка авторизации");
                window.location.href = "/login/log_in";
            }else if(error.message == "422"){
                alert("Неверный формат данных");
                location.reload();
            }else if(error.message == "409"){
                alert("Введено число больше 50");
                window.location.href = "/todo/generator";
            }else{
                console.error('Произошла ошибка:', error);
                alert("Ошибка");
                window.location.href = "/";
            }
        })
}

function delete_todo_in_range(start, end, type){
    var path = "/todo/delete_range?start=" + start + "&end=" + end + "&type=" + type;
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
            window.location.href = "/todo/list?type=" + type;
        })
        .catch(error => {
            if(error.message == "401"){
                alert("Ошибка авторизации");
                window.location.href = "/login/log_in";
            }else{
                console.error('Произошла ошибка:', error);
                window.location.href = "/";
            }
        })
}

function extend(id) {
    var path = "/todo/extend_detail/"+id;
    fetch(path, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${localStorage.getItem('token') }`
        },
    })
        .then(response => {
            console.log("response");
            console.log(response);
            if(response.status!=200)
                throw new Error(response.status);
            return response.json();
        })
        .then(data => {
            window.location.href = "/todo/edit/"+id;
        })
        .catch(error => {
            if(error.message == "401"){
                alert("Ошибка авторизации");
                window.location.href = "/login/log_in";
            }else{
                console.error('Произошла ошибка:', error);
                alert("Ошибка");
                window.location.href = "/";
            }
        })
}
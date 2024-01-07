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
            else if(data["answer"] == "good"){
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

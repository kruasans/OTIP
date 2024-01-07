
const blogPostBtn = document.querySelector('#add_new_todo')

blogPostBtn.addEventListener('click', () => {
    console.log(document.getElementById("title_add").value)
    formData = new FormData()
    formData.append("title", document.getElementById('title_add').value)
    formData.append("details", document.getElementById('details_add').value)
    formData.append("type", document.getElementById('type').value)
    formData.append("fullname", document.getElementById('fullname').value)
    fetch(`/add`, {
        method: "POST",
        body: formData,
        headers: {
            // Authorization: `Bearer ${token}`
            Authorization: `Bearer ${localStorage.getItem('token') }`
        },
    })
        .then(response => response.json())
        .then(data => {
            if(data["answer"] == "title not found"){
                console.log(data);
            }
            else if(data["answer"] == "login"){
                window.location.href = "/log_in";
            }
            else if(data["answer"] == "good"){
                window.location.href = "/list";
            }
        })
        .catch(error => console.error(error))
})
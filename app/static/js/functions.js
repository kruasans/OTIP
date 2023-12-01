function change_status(id){
    var path = "/change_status/" + id;
    fetch(path, {method : "POST"});
    location.reload();
}

function delete_entry(id){
    var path = "/delete/" + id;
    fetch(path, {method : "DELETE"});
    location.reload();
}

function ask_and_submit(button, id){
    var answer = confirm("Вы действительно хотите удалить эту запись?");
    if (answer){
        delete_entry(id)
    }
}

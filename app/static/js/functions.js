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

function generation(count){
    var path;
    console.log("here1");
    console.log(count);
    if(!Number.isInteger(count)){
        if(count == ""){
            fetch("/generate", {method : "POST"});
            location.reload();
            return;
        }
    }
    path = "/generate?count=" + count;
    fetch(path, {method : "POST"});
    location.reload();
}
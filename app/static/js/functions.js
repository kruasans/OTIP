function delete_entry(id) {
    var path = "/delete/" + id;
    fetch(path, {method: "DELETE"});
    location.reload();
}

function ask_and_submit(button, id) {
    var answer = confirm("Вы действительно хотите удалить эту запись?");
    if (answer) {
        delete_entry(id)
    }
}

function delete_every_todo(){
    var path = "/delete_all";
    fetch(path, {method : "DELETE"});
    window.location.href = "/";
}

function generation(count) {
    var path;
    if (!Number.isInteger(count)) {
        if (count == "") {
            fetch("/generate", {method: "POST"});
            window.location.href = "/list";
            return;
        }
    }
    path = "/generate?count=" + count;
    fetch(path, {method: "POST"})
    window.location.href = "/list";
}

function ask_and_submit_2() {
    var answer = confirm("Вы действительно хотите удалить все записи?");
    if (answer) {
        delete_every_todo()
    }
    }

function limit(lim) {
    var path = "/?limit="+lim;
    fetch(path, {method: "GET"});
    }


const currentUserName = () => {
    if (localStorage.getItem('username')) {
        welcome.innerHTML = `Hi, <strong>${localStorage.getItem('username')}</strong>!`
    }
}
currentUserName()
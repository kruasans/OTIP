function ask_and_submit(button, id) {
    var answer = confirm("Вы действительно хотите удалить эту запись?");
    if (answer) {
        delete_entry(id)
    }
}

function ask_and_submit_2() {
    var answer = confirm("Вы действительно хотите удалить все записи?");
    if (answer) {
        delete_every_todo()
    }
    }

function limit(lim) {
    var limit;
    if (lim > 10){
        limit=10;
    }
    else{
        limit=lim;
    }
    var path = "/?limit="+limit;
    fetch(path, {method: "GET"});
    }


const currentUserName = () => {
    if (localStorage.getItem('username')) {
        welcome.innerHTML = `<strong>${localStorage.getItem('username')}</strong>`;
    } else{
        welcome.innerHTML = ``;
    }
}
currentUserName()

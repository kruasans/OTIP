function change_status(id){
            var path = "/change_status/" + id;
            fetch(path, {method : "POST"});
            location.reload();
        }
function ask_and_submit(button){
    var answer = confirm("Вы действительно хотите удалить эту запись?");
    if (answer){
        button.form.submit();
    }
}
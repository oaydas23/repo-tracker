//COMMIT.HTML **************************************************************************************************************
$(document).ready(function () {
    $('#commit-table').DataTable({
        "paging": true,
        columnDefs: [{
            targets: -1,
            className: 'dt-head-center'
        }]
    });
});

function progressBar() {
    var progressBar = document.getElementById("progress-bar");
    progressBar.style.display = "block";
    var duration = 15 * 60 * 1000; // 15 minutes in milliseconds
    var interval = 100; // Update interval in milliseconds
    var increment = (interval / duration) * 100; // Progress increment per update

    var progress = 0;
    var timerId = setInterval(function () {
        progress += increment;
        progressBar.style.width = progress + "%";

        if (progress >= 100) {
            clearInterval(timerId);
        }
    }, interval);
}
//ARTIFACTS.HTML **************************************************************************************************************
$(document).ready(function () {
    $('#table-artifacts').DataTable();
});

//HOME.HTML *******************************************************************************************************************
var object = document.getElementById("object");
var containerWidth = document.getElementById("container").offsetWidth;
var objectWidth = object.offsetWidth;
var currentPosition = 0;
var direction = 1;
var speed = 1;

setInterval(function() {
    currentPosition += speed * direction;
    object.style.left = currentPosition + "px";

    if (currentPosition >= containerWidth - objectWidth || currentPosition <= 0) {
        direction *= -1;
    }
}, 20);
//REGISTER.HTML ***************************************************************************************************************

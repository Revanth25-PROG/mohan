function loadData(){

    fetch('/get_counts')

    .then(response => response.json())

    .then(data => {

        document.getElementById("total").innerHTML =
        data.total

        document.getElementById("pending").innerHTML =
        data.pending

        document.getElementById("solved").innerHTML =
        data.solved

    })

}

loadData()

setInterval(loadData, 5000)
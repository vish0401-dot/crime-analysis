let map = L.map('map').setView([20.5937, 78.9629], 5);

let markers = [];

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: 'OSM'
}).addTo(map);

function loadClusters() {

    let season = document.getElementById("season").value;
    let festival = document.getElementById("festival").value;

    fetch("/cluster", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({season: season, festival: festival})
    })
    .then(res => res.json())
    .then(data => {

        console.log("DATA:", data);

        // CLEAR OLD MARKERS
        markers.forEach(m => map.removeLayer(m));
        markers = [];

        data.forEach(p => {

            let color;

            if (p.risk === "High") color = "red";
            else if (p.risk === "Medium") color = "blue";
            else color = "green";

            let marker = L.circleMarker([p.lat, p.lon], {
                radius: 8,
                color: color,
                fillColor: color,
                fillOpacity: 0.8
            }).addTo(map);

            marker.bindPopup(`City: ${p.city}<br>Risk: ${p.risk}`);

            markers.push(marker);
        });

        alert("Points: " + data.length);
    });
}
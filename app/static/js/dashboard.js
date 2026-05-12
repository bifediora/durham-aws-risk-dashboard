console.log("Durham Risk Intelligence Dashboard loaded.");

const DURHAM_CENTER = [35.9940, -78.8986];
const DURHAM_DEFAULT_ZOOM = 11;

async function fetchJson(endpoint) {
    const response = await fetch(endpoint);
    return await response.json();
}

async function fetchMapPoints() {
    const data = await fetchJson("/api/map-points?limit=250");

    if (data.status !== "success") {
        console.error("Map point API error:", data);
        return [];
    }

    return data.points;
}

function buildPopup(point) {
    return `
        <strong>${point.description || "Arrest record"}</strong><br>
        <strong>Date:</strong> ${point.arrest_date || "Not available"}<br>
        <strong>Time:</strong> ${point.arrest_time || "Not available"}<br>
        <strong>Severity:</strong> ${point.severity || "Not available"}<br>
        <strong>District:</strong> ${point.district || "Not available"}<br>
        <strong>Beat:</strong> ${point.beat || "Not available"}<br>
        <strong>Tract:</strong> ${point.tract || "Not available"}
    `;
}

async function addGeoJsonLayer(map, endpoint, options) {
    try {
        const geojson = await fetchJson(endpoint);
        return L.geoJSON(geojson, options).addTo(map);
    } catch (error) {
        console.error(`Failed to load GeoJSON layer from ${endpoint}`, error);
        return null;
    }
}

function styleCountyBoundary() {
    return {
        color: "#38bdf8",
        weight: 3,
        fillOpacity: 0.03
    };
}

function stylePoliceBeats() {
    return {
        color: "#60a5fa",
        weight: 1.25,
        fillOpacity: 0.03
    };
}

function onEachPoliceBeat(feature, layer) {
    const properties = feature.properties || {};

    const district = properties.LAWDIST || "Not available";
    const beat = properties.LAWBEAT || "Not available";
    const cad = properties.CAD || "Not available";

    layer.bindPopup(`
        <strong>Police Beat</strong><br>
        <strong>District:</strong> ${district}<br>
        <strong>Beat:</strong> ${beat}<br>
        <strong>CAD:</strong> ${cad}
    `);
}

async function initializeMap() {
    const mapElement = document.getElementById("map");

    if (!mapElement) {
        console.warn("Map element not found.");
        return;
    }

    if (typeof L === "undefined") {
        console.error("Leaflet is not loaded. Check the Leaflet script tag in dashboard.html.");
        return;
    }

    const map = L.map("map").setView(DURHAM_CENTER, DURHAM_DEFAULT_ZOOM);

    const openStreetMap = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    });

    const grayMap = L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors &copy; CARTO"
    });

    const darkMap = L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors &copy; CARTO"
    });

    grayMap.addTo(map);

    const countyBoundaryLayer = await addGeoJsonLayer(
        map,
        "/static/geojson/durham_county_boundary.geojson",
        {
            style: styleCountyBoundary
        }
    );

    const policeBeatsLayer = await addGeoJsonLayer(
        map,
        "/static/geojson/police_beats.geojson",
        {
            style: stylePoliceBeats,
            onEachFeature: onEachPoliceBeat
        }
    );

    const points = await fetchMapPoints();
    const arrestPointsLayer = L.featureGroup();

    points.forEach((point) => {
        const lat = Number(point.latitude);
        const lon = Number(point.longitude);

        if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
            return;
        }

        const marker = L.circleMarker([lat, lon], {
            radius: 4.5,
            color: "#f97316",
            weight: 1,
            fillColor: "#f97316",
            fillOpacity: 0.75
        });

        marker.bindPopup(buildPopup(point));
        marker.addTo(arrestPointsLayer);
    });

    if (arrestPointsLayer.getLayers().length > 0) {
        arrestPointsLayer.addTo(map);

        map.fitBounds(arrestPointsLayer.getBounds(), {
            padding: [32, 32],
            maxZoom: 14
        });
    } else if (countyBoundaryLayer) {
        map.fitBounds(countyBoundaryLayer.getBounds(), {
            padding: [32, 32]
        });
    } else {
        map.setView(DURHAM_CENTER, DURHAM_DEFAULT_ZOOM);
        console.warn("No valid map points or boundary available. Showing Durham default view.");
    }

    const baseMaps = {
        "Gray Map": grayMap,
        "Dark Map": darkMap,
        "OpenStreetMap": openStreetMap
    };

    const overlays = {};

    if (countyBoundaryLayer) {
        overlays["Durham County Boundary"] = countyBoundaryLayer;
    }

    if (policeBeatsLayer) {
        overlays["Police Beats"] = policeBeatsLayer;
    }

    if (arrestPointsLayer) {
        overlays["Arrest Points"] = arrestPointsLayer;
    }

    L.control.layers(baseMaps, overlays, {
        collapsed: false
    }).addTo(map);
}

async function renderDistrictChart() {
    const chartElement = document.getElementById("districtChart");

    if (!chartElement) {
        return;
    }

    const data = await fetchJson("/api/by-district");

    if (data.status !== "success") {
        console.error("District chart API error:", data);
        return;
    }

    const labels = data.records.map((record) => record.district);
    const values = data.records.map((record) => record.count);

    new Chart(chartElement, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Arrests",
                    data: values
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

async function renderSeverityChart() {
    const chartElement = document.getElementById("severityChart");

    if (!chartElement) {
        return;
    }

    const data = await fetchJson("/api/by-severity");

    if (data.status !== "success") {
        console.error("Severity chart API error:", data);
        return;
    }

    const labels = data.records.map((record) => record.severity);
    const values = data.records.map((record) => record.count);

    new Chart(chartElement, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Records",
                    data: values
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });
}

async function renderTopOffensesChart() {
    const chartElement = document.getElementById("topOffensesChart");

    if (!chartElement) {
        return;
    }

    const data = await fetchJson("/api/top-offenses?limit=10");

    if (data.status !== "success") {
        console.error("Top offenses chart API error:", data);
        return;
    }

    const labels = data.records.map((record) => record.offense);
    const values = data.records.map((record) => record.count);

    new Chart(chartElement, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Records",
                    data: values
                }
            ]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

async function renderHourChart() {
    const chartElement = document.getElementById("hourChart");

    if (!chartElement) {
        return;
    }

    const data = await fetchJson("/api/by-hour");

    if (data.status !== "success") {
        console.error("Hour chart API error:", data);
        return;
    }

    const labels = data.records.map((record) => record.hour_label);
    const values = data.records.map((record) => record.count);

    new Chart(chartElement, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Arrests",
                    data: values,
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

initializeMap();
renderDistrictChart();
renderSeverityChart();
renderTopOffensesChart();
renderHourChart();

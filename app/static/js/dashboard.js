console.log("Durham Risk Intelligence Dashboard loaded.");

const DURHAM_CENTER = [35.9940, -78.8986];
const DURHAM_DEFAULT_ZOOM = 11;

let dashboardMap = null;
let activeDataLayer = null;
let cityBoundaryLayer = null;
let intersectingTractsLayer = null;
let countyBoundaryLayer = null;
let policeBeatsLayer = null;
let currentMapMode = "points";
let currentChoroplethMetric = "total_arrests";
let currentTemporalView = "month";
let pointsVisible = true;
let lastPointLayer = null;

const charts = {};

const activeFilters = {
    districts: new Set(),
    severities: new Set(),
    offenses: new Set(),
    tractGeoids: new Set()
};

const dateFilters = {
    startDate: "",
    endDate: "",
    minDate: "",
    maxDate: ""
};

const CHOROPLETH_METRIC_LABELS = {
    total_arrests: "Total arrests",
    felony_share: "Felony share",
    activity_density: "Activity density",
    night_share: "Night activity share"
};

const TEMPORAL_VIEW_CONFIG = {
    month: {
        title: "Monthly Pattern",
        endpoint: "/api/by-month",
        labelKey: "month_label",
        valueKey: "count",
        chartType: "line",
        datasetLabel: "Monthly arrests"
    },
    weekday: {
        title: "Day of Week",
        endpoint: "/api/by-weekday",
        labelKey: "weekday",
        valueKey: "count",
        chartType: "bar",
        datasetLabel: "Arrests by weekday"
    },
    hour: {
        title: "Hour of Day",
        endpoint: "/api/by-hour",
        labelKey: "hour_label",
        valueKey: "count",
        chartType: "line",
        datasetLabel: "Hourly arrests"
    }
};

function getElement(id) {
    return document.getElementById(id);
}

async function fetchJson(endpoint) {
    const response = await fetch(endpoint);

    if (!response.ok) {
        throw new Error(`Request failed: ${endpoint} (${response.status})`);
    }

    return await response.json();
}

function buildFilterQuery() {
    const params = new URLSearchParams();

    if (activeFilters.districts.size > 0) {
        params.set("districts", Array.from(activeFilters.districts).join(","));
    }

    if (activeFilters.severities.size > 0) {
        params.set("severities", Array.from(activeFilters.severities).join(","));
    }

    if (activeFilters.offenses.size > 0) {
        params.set("offenses", Array.from(activeFilters.offenses).join(","));
    }

    if (activeFilters.tractGeoids.size > 0) {
        params.set("tract_geoids", Array.from(activeFilters.tractGeoids).join(","));
    }

    if (dateFilters.startDate) {
        params.set("start_date", dateFilters.startDate);
    }

    if (dateFilters.endDate) {
        params.set("end_date", dateFilters.endDate);
    }

    const query = params.toString();

    return query ? `?${query}` : "";
}

function formatNumber(value) {
    return new Intl.NumberFormat("en-US").format(Number(value || 0));
}

function formatPercent(value) {
    return `${Number(value || 0).toFixed(1)}%`;
}

function setText(id, value) {
    const element = getElement(id);

    if (element) {
        element.textContent = value;
    }
}

function toggleFilter(filterName, value) {
    if (!activeFilters[filterName]) {
        return;
    }

    if (activeFilters[filterName].has(value)) {
        activeFilters[filterName].delete(value);
    } else {
        activeFilters[filterName].add(value);
    }
}

function clearFilters() {
    activeFilters.districts.clear();
    activeFilters.severities.clear();
    activeFilters.offenses.clear();
    activeFilters.tractGeoids.clear();
}

function clearDateFilters() {
    dateFilters.startDate = "";
    dateFilters.endDate = "";

    const startInput = getElement("startDateInput");
    const endInput = getElement("endDateInput");

    if (startInput) {
        startInput.value = "";
    }

    if (endInput) {
        endInput.value = "";
    }

    updateDateRangeStatus();
}

function updateDateRangeStatus() {
    const statusElement = getElement("dateRangeStatus");

    if (!statusElement) {
        return;
    }

    if (dateFilters.startDate && dateFilters.endDate) {
        statusElement.textContent = `Showing records from ${dateFilters.startDate} through ${dateFilters.endDate}`;
        return;
    }

    if (dateFilters.startDate) {
        statusElement.textContent = `Showing records from ${dateFilters.startDate} forward`;
        return;
    }

    if (dateFilters.endDate) {
        statusElement.textContent = `Showing records through ${dateFilters.endDate}`;
        return;
    }

    if (dateFilters.minDate && dateFilters.maxDate) {
        statusElement.textContent = `Showing full available date range: ${dateFilters.minDate} through ${dateFilters.maxDate}`;
        return;
    }

    statusElement.textContent = "Showing full available date range";
}

async function initializeDateRangeControls() {
    const startInput = getElement("startDateInput");
    const endInput = getElement("endDateInput");

    try {
        const data = await fetchJson("/api/filter-options");

        if (data.status === "success" && data.date_range) {
            dateFilters.minDate = data.date_range.min || "";
            dateFilters.maxDate = data.date_range.max || "";

            if (startInput && dateFilters.minDate) {
                startInput.min = dateFilters.minDate;
                startInput.max = dateFilters.maxDate || "";
                startInput.placeholder = dateFilters.minDate;
            }

            if (endInput && dateFilters.maxDate) {
                endInput.min = dateFilters.minDate || "";
                endInput.max = dateFilters.maxDate;
                endInput.placeholder = dateFilters.maxDate;
            }
        }
    } catch (error) {
        console.warn("Unable to initialize date range controls.", error);
    }

    updateDateRangeStatus();
}

function validateDateRange(startDate, endDate) {
    if (startDate && endDate && startDate > endDate) {
        return {
            valid: false,
            message: "Start date cannot be after end date."
        };
    }

    return {
        valid: true,
        message: ""
    };
}

function updateFilterChips() {
    const chipContainer = getElement("activeFilterChips");

    if (!chipContainer) {
        return;
    }

    const chips = [];

    activeFilters.districts.forEach((value) => {
        chips.push({ label: `District: ${value}`, type: "districts", value });
    });

    activeFilters.severities.forEach((value) => {
        chips.push({ label: `Severity: ${value}`, type: "severities", value });
    });

    activeFilters.offenses.forEach((value) => {
        chips.push({ label: `Offense: ${value}`, type: "offenses", value });
    });

    activeFilters.tractGeoids.forEach((value) => {
        chips.push({ label: `Tract: ${value}`, type: "tractGeoids", value });
    });

    if (dateFilters.startDate || dateFilters.endDate) {
        const dateLabel = `${dateFilters.startDate || "Start"} to ${dateFilters.endDate || "End"}`;
        chips.push({ label: `Date: ${dateLabel}`, type: "dateRange", value: "dateRange" });
    }

    if (chips.length === 0) {
        chipContainer.innerHTML = `<span class="empty-chip">No chart filters selected</span>`;
        return;
    }

    chipContainer.innerHTML = chips.map((chip) => {
        return `
            <button class="filter-chip" data-filter-type="${chip.type}" data-filter-value="${encodeURIComponent(chip.value)}" type="button">
                ${chip.label}
                <span>×</span>
            </button>
        `;
    }).join("");

    chipContainer.querySelectorAll(".filter-chip").forEach((button) => {
        button.addEventListener("click", async () => {
            const filterType = button.dataset.filterType;
            const filterValue = decodeURIComponent(button.dataset.filterValue);

            if (filterType === "dateRange") {
                clearDateFilters();
            } else {
                toggleFilter(filterType, filterValue);
            }

            await refreshDashboard();
        });
    });
}

function destroyChart(chartName) {
    if (charts[chartName]) {
        charts[chartName].destroy();
        delete charts[chartName];
    }
}

function getBarColors(labels, filterName) {
    return labels.map((label) => {
        if (!activeFilters[filterName] || activeFilters[filterName].size === 0) {
            return "rgba(56, 189, 248, 0.72)";
        }

        return activeFilters[filterName].has(label)
            ? "rgba(34, 197, 94, 0.92)"
            : "rgba(71, 85, 105, 0.56)";
    });
}

function getSeverityColors(labels) {
    return labels.map((label) => {
        if (activeFilters.severities.size === 0) {
            return label === "Felony"
                ? "rgba(249, 115, 22, 0.88)"
                : "rgba(56, 189, 248, 0.78)";
        }

        return activeFilters.severities.has(label)
            ? "rgba(34, 197, 94, 0.94)"
            : "rgba(71, 85, 105, 0.56)";
    });
}

function baseChartScales() {
    return {
        x: {
            ticks: {
                color: "#94a3b8"
            },
            grid: {
                color: "rgba(148, 163, 184, 0.14)"
            }
        },
        y: {
            beginAtZero: true,
            ticks: {
                color: "#94a3b8"
            },
            grid: {
                color: "rgba(148, 163, 184, 0.14)"
            }
        }
    };
}

function defaultChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                labels: {
                    color: "#cbd5e1"
                }
            }
        },
        scales: baseChartScales()
    };
}

function temporalChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: baseChartScales()
    };
}

function sideBarChartOptions(onClickHandler) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        resizeDelay: 100,
        plugins: {
            legend: {
                display: false
            }
        },
        scales: baseChartScales(),
        onClick: onClickHandler
    };
}

function sideDoughnutOptions(onClickHandler) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        resizeDelay: 100,
        cutout: "58%",
        plugins: {
            legend: {
                position: "bottom",
                labels: {
                    color: "#cbd5e1",
                    boxWidth: 12,
                    padding: 12
                }
            }
        },
        onClick: onClickHandler
    };
}

async function updateSummary() {
    const data = await fetchJson(`/api/summary${buildFilterQuery()}`);

    if (data.status !== "success") {
        console.error("Summary API error:", data);
        return;
    }

    const summary = data.summary;

    setText("totalRecordsValue", formatNumber(summary.total_records));
    setText("activeHotspotsValue", formatNumber(summary.active_hotspot_areas));
    setText("felonyShareValue", formatPercent(summary.felony_share));

    const trendValue = `${summary.recent_activity_trend_symbol} ${summary.recent_activity_trend_label}`;
    setText("recentTrendValue", trendValue);

    const trendSubtitle = `${Math.abs(Number(summary.recent_activity_trend_pct || 0)).toFixed(1)}% vs previous 30 days`;
    setText("recentTrendSubtitle", trendSubtitle);

    const recentTrendElement = getElement("recentTrendValue");

    if (recentTrendElement) {
        recentTrendElement.classList.remove("trend-up", "trend-down", "trend-stable");

        if (summary.recent_activity_trend_label === "Increasing") {
            recentTrendElement.classList.add("trend-up");
        } else if (summary.recent_activity_trend_label === "Decreasing") {
            recentTrendElement.classList.add("trend-down");
        } else {
            recentTrendElement.classList.add("trend-stable");
        }
    }
}

async function refreshDashboardPanels() {
    updateFilterChips();
    updateDateRangeStatus();
    await updateSummary();
    await renderDistrictChart();
    await renderSeverityChart();
    await renderTopOffensesChart();
    await renderTemporalChart();
    await renderRecordsTable();
}

function buildPopup(point) {
    return `
        <strong>${point.description || "Arrest record"}</strong><br>
        <strong>Date:</strong> ${point.arrest_date || "Not available"}<br>
        <strong>Time:</strong> ${point.arrest_time || "Not available"}<br>
        <strong>Type:</strong> ${point.arrest_type || "Not available"}<br>
        <strong>Severity:</strong> ${point.severity || "Not available"}<br>
        <strong>District:</strong> ${point.district || "Not available"}<br>
        <strong>Beat:</strong> ${point.beat || "Not available"}<br>
        <strong>Location:</strong> ${point.location || "Not available"}
    `;
}

async function addGeoJsonLayer(map, endpoint, options, addToMap = true) {
    try {
        const geojson = await fetchJson(endpoint);
        const layer = L.geoJSON(geojson, options);

        if (addToMap) {
            layer.addTo(map);
        }

        return layer;
    } catch (error) {
        console.error(`Failed to load GeoJSON layer from ${endpoint}`, error);
        return null;
    }
}

function styleCityBoundary() {
    return {
        color: "#facc15",
        weight: 3.2,
        opacity: 0.96,
        fillColor: "#facc15",
        fillOpacity: 0.012
    };
}

function styleIntersectingTracts() {
    return {
        color: "#cbd5e1",
        weight: 0.65,
        opacity: 0.42,
        fillOpacity: 0
    };
}

function styleCountyBoundary() {
    return {
        color: "#38bdf8",
        weight: 1.4,
        opacity: 0.48,
        fillOpacity: 0
    };
}

function stylePoliceBeats() {
    return {
        color: "#60a5fa",
        weight: 1.0,
        opacity: 0.55,
        fillOpacity: 0.01
    };
}

function onEachCityBoundary(feature, layer) {
    layer.bindPopup(`
        <strong>Durham City Boundary</strong><br>
        Primary study-area boundary
    `);
}

function onEachIntersectingTract(feature, layer) {
    const properties = feature.properties || {};
    const geoid = properties.GEOID || properties.GEOID20 || properties.geoid || "Not available";
    const name = properties.NAME || properties.NAMELSAD || properties.name || "Census tract";

    layer.bindPopup(`
        <strong>Census tract intersecting Durham municipal boundary</strong><br>
        <strong>Tract:</strong> ${name}<br>
        <strong>GEOID:</strong> ${geoid}<br>
        Full tract geometry is preserved and not clipped to the city boundary.
    `);
}

function onEachCountyBoundary(feature, layer) {
    layer.bindPopup(`
        <strong>Durham County Boundary</strong><br>
        Secondary reference boundary
    `);
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
    const mapElement = getElement("map");

    if (!mapElement) {
        console.warn("Map element not found.");
        return;
    }

    if (typeof L === "undefined") {
        console.error("Leaflet is not loaded.");
        return;
    }

    dashboardMap = L.map("map", {
        zoomControl: false
    }).setView(DURHAM_CENTER, DURHAM_DEFAULT_ZOOM);

    L.control.zoom({
        position: "bottomright"
    }).addTo(dashboardMap);

    const darkMap = L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors &copy; CARTO"
    });

    const lightMap = L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors &copy; CARTO"
    });

    const openStreetMap = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
    });

    darkMap.addTo(dashboardMap);

    intersectingTractsLayer = await addGeoJsonLayer(
        dashboardMap,
        "/static/geojson/durham_city_intersecting_tracts.geojson",
        {
            style: styleIntersectingTracts,
            onEachFeature: onEachIntersectingTract
        },
        false
    );

    cityBoundaryLayer = await addGeoJsonLayer(
        dashboardMap,
        "/static/geojson/durham_city_boundary.geojson",
        {
            style: styleCityBoundary,
            onEachFeature: onEachCityBoundary
        },
        true
    );

    countyBoundaryLayer = await addGeoJsonLayer(
        dashboardMap,
        "/static/geojson/durham_county_boundary.geojson",
        {
            style: styleCountyBoundary,
            onEachFeature: onEachCountyBoundary
        },
        false
    );

    policeBeatsLayer = await addGeoJsonLayer(
        dashboardMap,
        "/static/geojson/police_beats.geojson",
        {
            style: stylePoliceBeats,
            onEachFeature: onEachPoliceBeat
        },
        false
    );

    if (cityBoundaryLayer) {
        cityBoundaryLayer.bringToFront();
    }

    const baseMaps = {
        "Dark": darkMap,
        "Light": lightMap,
        "OpenStreetMap": openStreetMap
    };

    const overlays = {};

    if (cityBoundaryLayer) {
        overlays["Durham City Boundary"] = cityBoundaryLayer;
    }

    if (intersectingTractsLayer) {
        overlays["Census Tracts Intersecting Durham City"] = intersectingTractsLayer;
    }

    if (countyBoundaryLayer) {
        overlays["Durham County Boundary"] = countyBoundaryLayer;
    }

    if (policeBeatsLayer) {
        overlays["Police Beats"] = policeBeatsLayer;
    }

    L.control.layers(baseMaps, overlays, {
        collapsed: true
    }).addTo(dashboardMap);

    if (cityBoundaryLayer && typeof cityBoundaryLayer.getBounds === "function") {
        const cityBounds = cityBoundaryLayer.getBounds();

        if (cityBounds && cityBounds.isValid()) {
            dashboardMap.fitBounds(cityBounds, {
                padding: [28, 28]
            });
        }
    }

    await updateMap();
}

function removeActiveDataLayer() {
    if (activeDataLayer && dashboardMap) {
        dashboardMap.removeLayer(activeDataLayer);
    }

    activeDataLayer = null;
    lastPointLayer = null;
}

function buildMapModeLabel(mode) {
    if (mode === "cluster") {
        return "cluster mode";
    }

    if (mode === "hex") {
        return "hex density mode";
    }

    if (mode === "choropleth") {
        return "choropleth mode";
    }

    return "point mode";
}

async function updateMap() {
    if (!dashboardMap) {
        return;
    }

    removeActiveDataLayer();

    const mapStatusText = getElement("mapStatusText");

    if (mapStatusText) {
        mapStatusText.textContent = `Loading ${buildMapModeLabel(currentMapMode)}`;
    }

    if (currentMapMode === "points") {
        await renderPointLayer();
    } else if (currentMapMode === "cluster") {
        await renderClusterLayer();
    } else if (currentMapMode === "hex") {
        await renderHexLayer();
    } else if (currentMapMode === "choropleth") {
        await renderChoroplethLayer();
    }

    if (cityBoundaryLayer) {
        cityBoundaryLayer.bringToFront();
    }
}

async function fetchMapPoints() {
    const query = buildFilterQuery();
    const separator = query ? `${query}&` : "?";
    const data = await fetchJson(`/api/map-points${separator}limit=3000`);

    if (data.status !== "success") {
        console.error("Map point API error:", data);
        return [];
    }

    return data.points;
}

function createPointMarker(point) {
    const lat = Number(point.latitude);
    const lon = Number(point.longitude);

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
        return null;
    }

    const marker = L.circleMarker([lat, lon], {
        radius: 4,
        color: "#38bdf8",
        weight: 1,
        fillColor: "#38bdf8",
        fillOpacity: 0.74
    });

    marker.bindPopup(buildPopup(point));

    return marker;
}

async function renderPointLayer() {
    const points = await fetchMapPoints();
    const pointLayer = L.featureGroup();

    points.forEach((point) => {
        const marker = createPointMarker(point);

        if (marker) {
            marker.addTo(pointLayer);
        }
    });

    activeDataLayer = pointLayer;
    lastPointLayer = pointLayer;

    if (pointsVisible) {
        activeDataLayer.addTo(dashboardMap);
    }

    setMapStatus(points.length, pointsVisible ? "points" : "points hidden");
    fitLayerIfPossible(pointLayer);
}

async function renderClusterLayer() {
    const points = await fetchMapPoints();

    if (typeof L.markerClusterGroup === "undefined") {
        console.error("Leaflet marker cluster plugin is not loaded.");
        return;
    }

    const clusterLayer = L.markerClusterGroup({
        showCoverageOnHover: false,
        spiderfyOnMaxZoom: true,
        disableClusteringAtZoom: 16,
        maxClusterRadius: 48
    });

    points.forEach((point) => {
        const lat = Number(point.latitude);
        const lon = Number(point.longitude);

        if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
            return;
        }

        const marker = L.marker([lat, lon]);
        marker.bindPopup(buildPopup(point));
        clusterLayer.addLayer(marker);
    });

    activeDataLayer = clusterLayer;

    if (pointsVisible) {
        activeDataLayer.addTo(dashboardMap);
    }

    setMapStatus(points.length, pointsVisible ? "clustered points" : "clusters hidden");
    fitLayerIfPossible(clusterLayer);
}

async function fetchAggregation(mode) {
    const query = buildFilterQuery();
    const separator = query ? `${query}&` : "?";
    const data = await fetchJson(`/api/map-aggregation${separator}mode=${mode}&limit=8000`);

    if (data.status !== "success") {
        console.error("Aggregation API error:", data);
        return [];
    }

    return data.cells;
}

function createHexagon(lat, lon, radius) {
    const points = [];

    for (let i = 0; i < 6; i += 1) {
        const angle = Math.PI / 3 * i;
        const pointLat = lat + radius * Math.sin(angle);
        const pointLon = lon + radius * Math.cos(angle);
        points.push([pointLat, pointLon]);
    }

    return points;
}

async function renderHexLayer() {
    const cells = await fetchAggregation("hex");
    const layer = L.featureGroup();

    cells.forEach((cell) => {
        const lat = Number(cell.latitude);
        const lon = Number(cell.longitude);
        const intensity = Number(cell.intensity || 0);

        if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
            return;
        }

        const radius = 0.0055 + intensity * 0.0065;

        const hexagon = L.polygon(createHexagon(lat, lon, radius), {
            color: "#f97316",
            weight: 1.2,
            fillColor: "#f97316",
            fillOpacity: Math.max(0.16, intensity * 0.82)
        });

        hexagon.bindPopup(`
            <strong>Hex Cell</strong><br>
            <strong>Records:</strong> ${cell.count}<br>
            <strong>Relative intensity:</strong> ${(intensity * 100).toFixed(1)}%
        `);

        hexagon.addTo(layer);
    });

    activeDataLayer = layer;
    activeDataLayer.addTo(dashboardMap);

    setMapStatus(cells.length, "hex cells");
    fitLayerIfPossible(layer);
}

function getChoroplethMetricValue(properties) {
    return Number(properties.selected_metric_value || 0);
}

function getChoroplethBreaks(values) {
    const cleanValues = values
        .map((value) => Number(value || 0))
        .filter((value) => Number.isFinite(value));

    const maxValue = Math.max(...cleanValues, 0);

    if (maxValue <= 0) {
        return [0, 1, 2, 3, 4];
    }

    return [
        maxValue * 0.2,
        maxValue * 0.4,
        maxValue * 0.6,
        maxValue * 0.8,
        maxValue
    ];
}

function getChoroplethColor(value, breaks) {
    if (!value || value <= 0) {
        return "rgba(15, 23, 42, 0.18)";
    }

    if (value <= breaks[0]) {
        return "#dbeafe";
    }

    if (value <= breaks[1]) {
        return "#93c5fd";
    }

    if (value <= breaks[2]) {
        return "#60a5fa";
    }

    if (value <= breaks[3]) {
        return "#3b82f6";
    }

    return "#1d4ed8";
}

function buildChoroplethPopup(properties) {
    const metricLabel = CHOROPLETH_METRIC_LABELS[properties.selected_metric] || "Selected metric";
    const metricValue = Number(properties.selected_metric_value || 0);

    return `
        <strong>${properties.name || "Census tract"}</strong><br>
        <strong>GEOID:</strong> ${properties.geoid || "Not available"}<br>
        <strong>${metricLabel}:</strong> ${metricValue.toFixed(properties.selected_metric === "total_arrests" ? 0 : 1)}<br>
        <strong>Total arrests:</strong> ${formatNumber(properties.total_arrests)}<br>
        <strong>Felony share:</strong> ${formatPercent(properties.felony_share)}<br>
        <strong>Density:</strong> ${Number(properties.activity_density || 0).toFixed(2)} per sq mi<br>
        <em>Full tract geometry preserved. Tract intersects Durham municipal boundary.</em>
    `;
}

function getChoroplethStyle(feature, breaks) {
    const properties = feature.properties || {};
    const value = getChoroplethMetricValue(properties);
    const geoid = String(properties.geoid || "");

    const isSelected = activeFilters.tractGeoids.has(geoid);

    return {
        color: isSelected ? "#facc15" : "rgba(226, 232, 240, 0.58)",
        weight: isSelected ? 2.4 : 0.75,
        opacity: isSelected ? 0.95 : 0.6,
        fillColor: getChoroplethColor(value, breaks),
        fillOpacity: value > 0 ? 0.58 : 0.18
    };
}

async function renderChoroplethLayer() {
    const query = buildFilterQuery();
    const separator = query ? `${query}&` : "?";
    const data = await fetchJson(`/api/choropleth${separator}metric=${currentChoroplethMetric}`);

    if (data.status !== "success") {
        console.error("Choropleth API error:", data);
        return;
    }

    const geojson = data.geojson || { type: "FeatureCollection", features: [] };

    const values = geojson.features.map((feature) => {
        return getChoroplethMetricValue(feature.properties || {});
    });

    const breaks = getChoroplethBreaks(values);

    const choroplethLayer = L.geoJSON(geojson, {
        style: (feature) => getChoroplethStyle(feature, breaks),

        onEachFeature: (feature, layer) => {
            const properties = feature.properties || {};
            const geoid = String(properties.geoid || "");

            layer.bindPopup(buildChoroplethPopup(properties), {
                maxWidth: 340,
                closeButton: true,
                autoClose: true,
                closeOnClick: true
            });

            layer.on("mouseover", () => {
                layer.setStyle({
                    weight: 2,
                    color: "#facc15",
                    opacity: 0.95
                });

                layer.bringToFront();

                if (cityBoundaryLayer) {
                    cityBoundaryLayer.bringToFront();
                }
            });

            layer.on("mouseout", () => {
                choroplethLayer.resetStyle(layer);

                if (cityBoundaryLayer) {
                    cityBoundaryLayer.bringToFront();
                }
            });

            layer.on("click", async () => {
                if (!geoid) {
                    return;
                }

                dashboardMap.closePopup();
                layer.openPopup();

                activeFilters.tractGeoids.clear();
                activeFilters.tractGeoids.add(geoid);

                await refreshDashboardPanels();

                choroplethLayer.setStyle((selectedFeature) => {
                    return getChoroplethStyle(selectedFeature, breaks);
                });

                if (cityBoundaryLayer) {
                    cityBoundaryLayer.bringToFront();
                }
            });

            layer.on("popupclose", async () => {
                if (!geoid || !activeFilters.tractGeoids.has(geoid)) {
                    return;
                }

                activeFilters.tractGeoids.delete(geoid);

                await refreshDashboardPanels();

                choroplethLayer.setStyle((selectedFeature) => {
                    return getChoroplethStyle(selectedFeature, breaks);
                });

                if (cityBoundaryLayer) {
                    cityBoundaryLayer.bringToFront();
                }
            });
        }
    });

    activeDataLayer = choroplethLayer;
    activeDataLayer.addTo(dashboardMap);

    const nonZeroTracts = values.filter((value) => Number(value || 0) > 0).length;
    setMapStatus(nonZeroTracts, "tracts with activity");

    fitLayerIfPossible(choroplethLayer);

    if (cityBoundaryLayer) {
        cityBoundaryLayer.bringToFront();
    }
}

function fitLayerIfPossible(layer) {
    if (!layer || !dashboardMap || typeof layer.getBounds !== "function") {
        return;
    }

    const bounds = layer.getBounds();

    if (!bounds || !bounds.isValid()) {
        return;
    }

    dashboardMap.fitBounds(bounds, {
        padding: [32, 32],
        maxZoom: 14
    });
}

function zoomToCurrentExtent() {
    if (!dashboardMap) {
        return;
    }

    if (activeDataLayer && typeof activeDataLayer.getBounds === "function") {
        const bounds = activeDataLayer.getBounds();

        if (bounds && bounds.isValid()) {
            dashboardMap.fitBounds(bounds, {
                padding: [36, 36],
                maxZoom: 14
            });
            return;
        }
    }

    if (cityBoundaryLayer && typeof cityBoundaryLayer.getBounds === "function") {
        const bounds = cityBoundaryLayer.getBounds();

        if (bounds && bounds.isValid()) {
            dashboardMap.fitBounds(bounds, {
                padding: [36, 36]
            });
            return;
        }
    }

    if (countyBoundaryLayer && typeof countyBoundaryLayer.getBounds === "function") {
        const bounds = countyBoundaryLayer.getBounds();

        if (bounds && bounds.isValid()) {
            dashboardMap.fitBounds(bounds, {
                padding: [36, 36]
            });
            return;
        }
    }

    dashboardMap.setView(DURHAM_CENTER, DURHAM_DEFAULT_ZOOM);
}

function setMapStatus(count, label) {
    const mapStatusText = getElement("mapStatusText");

    if (mapStatusText) {
        mapStatusText.textContent = `${formatNumber(count)} ${label}`;
    }
}

function updateTogglePointsButton() {
    const button = getElement("togglePointsButton");

    if (!button) {
        return;
    }

    if (currentMapMode === "choropleth" || currentMapMode === "hex") {
        button.disabled = true;
        button.textContent = "Points Hidden";
        return;
    }

    button.disabled = false;
    button.textContent = pointsVisible ? "Hide Points" : "Show Points";
}

async function togglePointsVisibility() {
    if (currentMapMode === "choropleth" || currentMapMode === "hex") {
        return;
    }

    pointsVisible = !pointsVisible;
    updateTogglePointsButton();

    if (!activeDataLayer || !dashboardMap) {
        return;
    }

    if (currentMapMode === "points" || currentMapMode === "cluster") {
        await updateMap();
    }
}

async function renderDistrictChart() {
    const chartElement = getElement("districtChart");

    if (!chartElement) {
        return;
    }

    const data = await fetchJson(`/api/by-district${buildFilterQuery()}`);

    if (data.status !== "success") {
        console.error("District chart API error:", data);
        return;
    }

    const labels = data.records.map((record) => record.district);
    const values = data.records.map((record) => record.count);

    destroyChart("districtChart");

    charts.districtChart = new Chart(chartElement, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Arrests",
                    data: values,
                    backgroundColor: getBarColors(labels, "districts"),
                    borderColor: "rgba(226, 232, 240, 0.28)",
                    borderWidth: 1
                }
            ]
        },
        options: sideBarChartOptions(async (event, elements) => {
            if (!elements.length) {
                return;
            }

            const index = elements[0].index;
            const district = labels[index];

            toggleFilter("districts", district);
            await refreshDashboard();
        })
    });
}

async function renderSeverityChart() {
    const chartElement = getElement("severityChart");

    if (!chartElement) {
        return;
    }

    const data = await fetchJson(`/api/by-severity${buildFilterQuery()}`);

    if (data.status !== "success") {
        console.error("Severity chart API error:", data);
        return;
    }

    const labels = data.records.map((record) => record.severity);
    const values = data.records.map((record) => record.count);

    destroyChart("severityChart");

    charts.severityChart = new Chart(chartElement, {
        type: "doughnut",
        data: {
            labels,
            datasets: [
                {
                    label: "Records",
                    data: values,
                    backgroundColor: getSeverityColors(labels),
                    borderColor: "rgba(15, 23, 42, 0.92)",
                    borderWidth: 2
                }
            ]
        },
        options: sideDoughnutOptions(async (event, elements) => {
            if (!elements.length) {
                return;
            }

            const index = elements[0].index;
            const severity = labels[index];

            toggleFilter("severities", severity);
            await refreshDashboard();
        })
    });
}

async function renderTopOffensesChart() {
    const chartElement = getElement("topOffensesChart");

    if (!chartElement) {
        return;
    }

    const query = buildFilterQuery();
    const separator = query ? `${query}&` : "?";
    const data = await fetchJson(`/api/top-offenses${separator}limit=12`);

    if (data.status !== "success") {
        console.error("Top offenses chart API error:", data);
        return;
    }

    const labels = data.records.map((record) => record.offense);
    const values = data.records.map((record) => record.count);

    destroyChart("topOffensesChart");

    charts.topOffensesChart = new Chart(chartElement, {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Records",
                    data: values,
                    backgroundColor: getBarColors(labels, "offenses"),
                    borderColor: "rgba(226, 232, 240, 0.28)",
                    borderWidth: 1
                }
            ]
        },
        options: {
            ...defaultChartOptions(),
            indexAxis: "y",
            plugins: {
                legend: {
                    display: false
                }
            },
            onClick: async (event, elements) => {
                if (!elements.length) {
                    return;
                }

                const index = elements[0].index;
                const offense = labels[index];

                toggleFilter("offenses", offense);
                await refreshDashboard();
            }
        }
    });
}

async function renderTemporalChart() {
    const chartElement = getElement("temporalChart");

    if (!chartElement) {
        return;
    }

    const config = TEMPORAL_VIEW_CONFIG[currentTemporalView] || TEMPORAL_VIEW_CONFIG.month;

    setText("temporalChartTitle", config.title);

    const data = await fetchJson(`${config.endpoint}${buildFilterQuery()}`);

    if (data.status !== "success") {
        console.error("Temporal chart API error:", data);
        return;
    }

    const labels = data.records.map((record) => {
        if (currentTemporalView === "weekday") {
            return String(record[config.labelKey] || "").slice(0, 3);
        }

        return record[config.labelKey];
    });

    const values = data.records.map((record) => record[config.valueKey]);

    destroyChart("temporalChart");

    const isBarChart = config.chartType === "bar";

    charts.temporalChart = new Chart(chartElement, {
        type: config.chartType,
        data: {
            labels,
            datasets: [
                {
                    label: config.datasetLabel,
                    data: values,
                    tension: isBarChart ? 0 : 0.35,
                    fill: !isBarChart,
                    backgroundColor: isBarChart
                        ? "rgba(129, 140, 248, 0.76)"
                        : "rgba(56, 189, 248, 0.13)",
                    borderColor: isBarChart
                        ? "rgba(226, 232, 240, 0.22)"
                        : "rgba(56, 189, 248, 0.88)",
                    borderWidth: 2
                }
            ]
        },
        options: temporalChartOptions()
    });
}

async function renderRecordsTable() {
    const tableBody = getElement("recordsTableBody");
    const recordCountText = getElement("recordCountText");

    if (!tableBody) {
        return;
    }

    const query = buildFilterQuery();
    const separator = query ? `${query}&` : "?";
    const data = await fetchJson(`/api/records${separator}limit=25`);

    if (data.status !== "success") {
        tableBody.innerHTML = `<tr><td colspan="7">Unable to load records</td></tr>`;
        return;
    }

    if (recordCountText) {
        recordCountText.textContent = `${formatNumber(data.total_matching_records || 0)} matching records`;
    }

    if (!data.records.length) {
        tableBody.innerHTML = `<tr><td colspan="7">No records match the selected query</td></tr>`;
        return;
    }

    tableBody.innerHTML = data.records.map((record) => {
        return `
            <tr>
                <td>${record["Arrest Date"] || "Not available"}</td>
                <td>${record["Arrest Time"] || "Not available"}</td>
                <td>${record["Arrest Type"] || "Not available"}</td>
                <td>${record["Description"] || "Not available"}</td>
                <td>${record["severity_label"] || "Not available"}</td>
                <td>${record["District"] || "Not available"}</td>
                <td>${record["Beat"] || "Not available"}</td>
            </tr>
        `;
    }).join("");
}

async function refreshDashboard() {
    updateFilterChips();
    updateDateRangeStatus();
    await updateSummary();
    await updateMap();
    await renderDistrictChart();
    await renderSeverityChart();
    await renderTopOffensesChart();
    await renderTemporalChart();
    await renderRecordsTable();
}

function setupEvents() {
    getElement("resetFiltersButton")?.addEventListener("click", async () => {
        clearFilters();
        clearDateFilters();
        await refreshDashboard();
    });

    getElement("zoomToExtentButton")?.addEventListener("click", () => {
        zoomToCurrentExtent();
    });

    getElement("togglePointsButton")?.addEventListener("click", async () => {
        await togglePointsVisibility();
    });

    getElement("choroplethMetricSelect")?.addEventListener("change", async (event) => {
        currentChoroplethMetric = event.target.value || "total_arrests";

        if (currentMapMode === "choropleth") {
            await updateMap();
        }
    });

    getElement("temporalViewSelect")?.addEventListener("change", async (event) => {
        currentTemporalView = event.target.value || "month";
        await renderTemporalChart();
    });

    getElement("applyDateRangeButton")?.addEventListener("click", async () => {
        const startInput = getElement("startDateInput");
        const endInput = getElement("endDateInput");

        const startDate = startInput ? startInput.value : "";
        const endDate = endInput ? endInput.value : "";

        const validation = validateDateRange(startDate, endDate);

        if (!validation.valid) {
            setText("dateRangeStatus", validation.message);
            return;
        }

        dateFilters.startDate = startDate;
        dateFilters.endDate = endDate;

        await refreshDashboard();
    });

    getElement("clearDateRangeButton")?.addEventListener("click", async () => {
        clearDateFilters();
        await refreshDashboard();
    });

    document.querySelectorAll("#mapModeControl button").forEach((button) => {
        button.addEventListener("click", async () => {
            document.querySelectorAll("#mapModeControl button").forEach((otherButton) => {
                otherButton.classList.remove("active");
            });

            button.classList.add("active");
            currentMapMode = button.dataset.mapMode;

            if (currentMapMode === "points" || currentMapMode === "cluster") {
                pointsVisible = true;
            }

            updateTogglePointsButton();
            await updateMap();
        });
    });
}

async function initializeDashboard() {
    setupEvents();
    await initializeDateRangeControls();
    updateTogglePointsButton();
    await initializeMap();
    await refreshDashboard();
}

initializeDashboard().catch((error) => {
    console.error("Dashboard initialization failed:", error);
});
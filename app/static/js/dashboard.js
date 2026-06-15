console.log("Durham Risk Intelligence Dashboard loaded.");

const DURHAM_CENTER = [35.9940, -78.8986];
const DURHAM_DEFAULT_ZOOM = 11;

let dashboardMap = null;
let activeDataLayer = null;
let cityBoundaryLayer = null;
let intersectingTractsLayer = null;
let countyBoundaryLayer = null;
let policeBeatsLayer = null;
let neighborhoodsLayer = null;
let pointOverlayLayer = null;
let lisaClusterLayer = null;
let selectedTractHighlightLayer = null;
let selectedNeighborhoodHighlightLayer = null;
let mapLegendControl = null;
let mapLegendElement = null;
let lisaLegendControl = null;
let lisaLegendElement = null;
let selectionControlElement = null;
let currentMapMode = "points";
let currentChoroplethMetric = "total_arrests";
let currentTemporalView = "month";
let pointsVisible = true;
let lisaLayerVisible = false;
let lisaClusterGeojson = null;
let lastPointLayer = null;
let selectionMode = null;
let selectionLayer = null;
let selectionStartLatLng = null;
let selectionLatLngs = [];
let activeSelectionCoordinates = [];
let activeSelectionLayer = null;
let selectedNeighborhoodNames = new Set();
let isDrawingSelection = false;
let suppressNextMapClear = false;
let spatialSelectionSummary = null;
let suppressTractPopupClose = false;
let summaryRequestToken = 0;
let recordsRequestToken = 0;

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
    arrests_per_1000_population: "Arrests per 1,000 population",
    felony_share: "Felony share",
    median_household_income: "Median household income",
    average_household_size: "Average household size",
    poverty_rate: "Poverty rate",
    housing_vacancy_rate: "Vacancy rate",
    youth_population_share: "Population under 18",
    senior_population_share: "Population 65 and older",
    no_high_school_diploma_rate: "No high school diploma",
    bachelors_or_higher_rate: "Bachelor's degree or higher",
    white_non_hispanic_share: "White population share",
    black_non_hispanic_share: "Black population share",
    hispanic_or_latino_share: "Hispanic or Latino population share",
    asian_non_hispanic_share: "Asian population share"
};

const CHOROPLETH_METRIC_FORMATS = {
    total_arrests: "count",
    total_population: "count",
    arrests_per_1000_population: "rate",
    felony_share: "percent",
    median_household_income: "currency",
    average_household_size: "decimal",
    poverty_rate: "percent",
    housing_vacancy_rate: "percent",
    youth_population_share: "percent",
    senior_population_share: "percent",
    no_high_school_diploma_rate: "percent",
    bachelors_or_higher_rate: "percent",
    white_non_hispanic_share: "percent",
    black_non_hispanic_share: "percent",
    hispanic_or_latino_share: "percent",
    asian_non_hispanic_share: "percent"
};

const CENSUS_CONTEXT_METRICS = new Set([
    "total_population",
    "median_household_income",
    "average_household_size",
    "poverty_rate",
    "unemployment_rate",
    "housing_vacancy_rate",
    "youth_population_share",
    "senior_population_share",
    "no_high_school_diploma_rate",
    "bachelors_or_higher_rate",
    "white_non_hispanic_share",
    "black_non_hispanic_share",
    "hispanic_or_latino_share",
    "asian_non_hispanic_share",
    "american_indian_alaska_native_non_hispanic_share",
    "native_hawaiian_pacific_islander_non_hispanic_share",
    "other_race_non_hispanic_share",
    "two_or_more_races_non_hispanic_share",
    "population_density"
]);

const CHOROPLETH_COLORS = [
    "#eff6ff",
    "#bfdbfe",
    "#60a5fa",
    "#2563eb",
    "#1e3a8a"
];

const LISA_CLUSTER_STYLES = {
    "High-High": {
        label: "High-High",
        color: "#b91c1c",
        fillColor: "#ef4444"
    },
    "Low-Low": {
        label: "Low-Low",
        color: "#1d4ed8",
        fillColor: "#3b82f6"
    },
    "High-Low": {
        label: "High-Low",
        color: "#c2410c",
        fillColor: "#f97316"
    },
    "Low-High": {
        label: "Low-High",
        color: "#7c3aed",
        fillColor: "#a855f7"
    },
    "Not significant": {
        label: "Not significant",
        color: "#64748b",
        fillColor: "#94a3b8"
    }
};

const SELECTION_MODES = {
    rectangle: "Rectangle",
    lasso: "Lasso"
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

function formatRate(value) {
    return Number(value || 0).toFixed(1);
}

function formatLegendValue(value, metric = "") {
    const number = Number(value || 0);
    const format = CHOROPLETH_METRIC_FORMATS[metric] || "";

    if (!Number.isFinite(number)) {
        return "0";
    }

    if (format === "currency") {
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
            maximumFractionDigits: 0
        }).format(number);
    }

    if (format === "count") {
        return formatNumber(Math.round(number));
    }

    if (format === "decimal") {
        return number.toFixed(1);
    }

    if (format === "percent" || metric.includes("share")) {
        return formatPercent(number);
    }

    return number >= 10 ? number.toFixed(0) : number.toFixed(1);
}

function formatChoroplethPopupValue(value, metric = "") {
    return formatLegendValue(value, metric);
}

function setText(id, value) {
    const element = getElement(id);

    if (element) {
        element.textContent = value;
    }
}

async function initializeChoroplethMetricSelect() {
    const select = getElement("choroplethMetricSelect");

    if (!select) {
        return;
    }

    try {
        const data = await fetchJson("/api/choropleth-metrics");

        if (data.status !== "success") {
            return;
        }

        const metrics = data.catalog?.arrests || [];

        if (!metrics.length) {
            return;
        }

        select.innerHTML = "";

        metrics.forEach((metric) => {
            if (!metric.key || !metric.label) {
                return;
            }

            CHOROPLETH_METRIC_LABELS[metric.key] = metric.label;

            if (metric.format) {
                CHOROPLETH_METRIC_FORMATS[metric.key] = metric.format;
            }

            const option = document.createElement("option");
            option.value = metric.key;
            option.textContent = metric.label;
            select.appendChild(option);
        });

        currentChoroplethMetric = data.default_metric || metrics[0].key || "total_arrests";
        select.value = currentChoroplethMetric;
    } catch (error) {
        console.error("Choropleth metric catalog failed to load:", error);
    }
}

function toggleFilter(filterName, value) {
    if (!activeFilters[filterName]) {
        return;
    }

    if (filterName === "tractGeoids") {
        clearSpatialSelectionLayer();
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
    clearSpatialSelectionLayer();
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

    if (activeFilters.tractGeoids.size > 0) {
        if (spatialSelectionSummary) {
            chips.push({
                label: spatialSelectionSummary,
                type: "spatialSelection",
                value: "spatialSelection"
            });
        } else if (activeFilters.tractGeoids.size > 6) {
            chips.push({
                label: `Tracts: ${formatNumber(activeFilters.tractGeoids.size)} selected`,
                type: "tractGeoidsAll",
                value: "tractGeoidsAll"
            });
        } else {
            activeFilters.tractGeoids.forEach((value) => {
                chips.push({ label: `Tract: ${value}`, type: "tractGeoids", value });
            });
        }
    }

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
            } else if (filterType === "spatialSelection" || filterType === "tractGeoidsAll") {
                activeFilters.tractGeoids.clear();
                clearSpatialSelectionLayer();
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
            if (label === "Felony") {
                return "rgba(249, 115, 22, 0.88)";
            }

            if (label === "Misdemeanor") {
                return "rgba(56, 189, 248, 0.78)";
            }

            return "rgba(168, 85, 247, 0.78)";
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
    const requestToken = summaryRequestToken + 1;
    summaryRequestToken = requestToken;

    const query = buildFilterQuery();
    const data = await fetchJson(`/api/summary${query}`);

    if (requestToken !== summaryRequestToken || query !== buildFilterQuery()) {
        return;
    }

    if (data.status !== "success") {
        console.error("Summary API error:", data);
        return;
    }

    const summary = data.summary;

    setText("totalRecordsValue", formatNumber(summary.total_records));
    setText("arrestRateValue", formatRate(summary.arrest_rate_per_1000_population));
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
        const payload = await fetchJson(endpoint);
        const geojson = payload.geojson || payload;
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

function styleNeighborhoods() {
    return {
        color: "#f8fafc",
        weight: 0.75,
        opacity: 0.28,
        fillColor: "#38bdf8",
        fillOpacity: 0.045
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

function onEachNeighborhood(feature, layer) {
    const properties = feature.properties || {};
    const name = properties.neighborhood_name || properties.name || "Neighborhood";
    const labelTier = Number(properties.label_tier || 3);

    layer.bindPopup(`
        <strong>${name}</strong><br>
        Neighborhood context layer<br>
        <strong>Label tier:</strong> ${labelTier}
    `);

    layer.bindTooltip(name, {
        permanent: false,
        direction: "center",
        className: `neighborhood-label neighborhood-label-tier-${labelTier}`,
        opacity: 0.86
    });

    layer._neighborhoodLabelTier = labelTier;

    layer.on("mouseover", () => {
        layer.setStyle({
            opacity: 0.64,
            fillOpacity: 0.09
        });
        layer.openTooltip();
    });

    layer.on("mouseout", () => {
        layer.setStyle(styleNeighborhoods());
        layer.closeTooltip();
    });
}

function updateNeighborhoodLabelVisibility() {
    if (!dashboardMap || !neighborhoodsLayer || !dashboardMap.hasLayer(neighborhoodsLayer)) {
        return;
    }

    neighborhoodsLayer.eachLayer((layer) => {
        layer.closeTooltip();
    });
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

    dashboardMap.createPane("lisaClusterPane");
    dashboardMap.getPane("lisaClusterPane").style.zIndex = 425;

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
            interactive: false,
            style: styleIntersectingTracts,
            onEachFeature: onEachIntersectingTract
        },
        false
    );

    cityBoundaryLayer = await addGeoJsonLayer(
        dashboardMap,
        "/static/geojson/durham_city_boundary.geojson",
        {
            interactive: false,
            style: styleCityBoundary,
            onEachFeature: onEachCityBoundary
        },
        true
    );

    countyBoundaryLayer = await addGeoJsonLayer(
        dashboardMap,
        "/static/geojson/durham_county_boundary.geojson",
        {
            interactive: false,
            style: styleCountyBoundary,
            onEachFeature: onEachCountyBoundary
        },
        false
    );

    policeBeatsLayer = await addGeoJsonLayer(
        dashboardMap,
        "/static/geojson/police_beats.geojson",
        {
            interactive: false,
            style: stylePoliceBeats,
            onEachFeature: onEachPoliceBeat
        },
        false
    );

    neighborhoodsLayer = await addGeoJsonLayer(
        dashboardMap,
        "/api/neighborhoods",
        {
            style: styleNeighborhoods,
            onEachFeature: onEachNeighborhood
        },
        false
    );

    if (cityBoundaryLayer) {
        cityBoundaryLayer.bringToFront();
    }

    initializeMapLegend();
    initializeLisaLegend();
    initializeSelectionTools();

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

    if (neighborhoodsLayer) {
        overlays["Neighborhood Context"] = neighborhoodsLayer;
    }

    L.control.layers(baseMaps, overlays, {
        collapsed: true
    }).addTo(dashboardMap);

    dashboardMap.on("overlayadd", (event) => {
        if (event.layer === neighborhoodsLayer) {
            updateNeighborhoodLabelVisibility();
        }

        if (cityBoundaryLayer) {
            cityBoundaryLayer.bringToFront();
        }
    });

    dashboardMap.on("overlayremove", (event) => {
        if (event.layer === neighborhoodsLayer) {
            neighborhoodsLayer.eachLayer((layer) => layer.closeTooltip());
        }
    });

    dashboardMap.on("zoomend", updateNeighborhoodLabelVisibility);

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

    if (pointOverlayLayer && dashboardMap) {
        dashboardMap.removeLayer(pointOverlayLayer);
    }

    if (selectedTractHighlightLayer && dashboardMap) {
        dashboardMap.removeLayer(selectedTractHighlightLayer);
    }

    if (selectedNeighborhoodHighlightLayer && dashboardMap) {
        dashboardMap.removeLayer(selectedNeighborhoodHighlightLayer);
    }

    activeDataLayer = null;
    pointOverlayLayer = null;
    selectedTractHighlightLayer = null;
    selectedNeighborhoodHighlightLayer = null;
    lastPointLayer = null;
}

function initializeMapLegend() {
    if (!dashboardMap || mapLegendControl) {
        return;
    }

    mapLegendControl = L.control({
        position: "bottomleft"
    });

    mapLegendControl.onAdd = () => {
        mapLegendElement = L.DomUtil.create("div", "modern-map-legend is-hidden");
        L.DomEvent.disableClickPropagation(mapLegendElement);
        L.DomEvent.disableScrollPropagation(mapLegendElement);
        mapLegendElement.setAttribute("aria-live", "polite");
        return mapLegendElement;
    };

    mapLegendControl.addTo(dashboardMap);
}

function initializeLisaLegend() {
    if (!dashboardMap || lisaLegendControl) {
        return;
    }

    lisaLegendControl = L.control({
        position: "bottomleft"
    });

    lisaLegendControl.onAdd = () => {
        lisaLegendElement = L.DomUtil.create("div", "modern-map-legend lisa-map-legend is-hidden");
        L.DomEvent.disableClickPropagation(lisaLegendElement);
        L.DomEvent.disableScrollPropagation(lisaLegendElement);
        lisaLegendElement.setAttribute("aria-live", "polite");
        return lisaLegendElement;
    };

    lisaLegendControl.addTo(dashboardMap);
}

function initializeSelectionTools() {
    if (!dashboardMap) {
        return;
    }

    const selectionControl = L.control({
        position: "topleft"
    });

    selectionControl.onAdd = () => {
        const container = L.DomUtil.create("div", "selection-control leaflet-bar");
        selectionControlElement = container;
        container.innerHTML = `
            <button type="button" data-selection-mode="rectangle" title="Rectangle selection">□</button>
            <button type="button" data-selection-mode="lasso" title="Lasso selection">⌁</button>
        `;

        L.DomEvent.disableClickPropagation(container);
        L.DomEvent.disableScrollPropagation(container);

        container.querySelectorAll("button").forEach((button) => {
            button.addEventListener("click", () => {
                const requestedMode = button.dataset.selectionMode;
                selectionMode = selectionMode === requestedMode ? null : requestedMode;
                updateSelectionToolButtons(container);
            });
        });

        return container;
    };

    selectionControl.addTo(dashboardMap);

    dashboardMap.on("mousedown", startSpatialSelection);
    dashboardMap.on("mousemove", updateSpatialSelection);
    dashboardMap.on("mouseup", finishSpatialSelection);
    dashboardMap.on("click", clearSpatialSelectionFromMapClick);
    dashboardMap.getContainer().addEventListener("click", clearSpatialSelectionFromMapContainerClick, true);
}

function updateSelectionControlVisibility() {
    if (!selectionControlElement) {
        return;
    }

    selectionControlElement.classList.toggle("is-hidden", Boolean(spatialSelectionSummary));
}

function updateSelectionToolButtons(container = document.querySelector(".selection-control")) {
    if (!container) {
        return;
    }

    container.querySelectorAll("button").forEach((button) => {
        button.classList.toggle("active", button.dataset.selectionMode === selectionMode);
    });

    if (dashboardMap) {
        dashboardMap.getContainer().classList.toggle("selection-active", Boolean(selectionMode));
    }

    updateSelectionControlVisibility();
}

function getSelectionStyle() {
    return {
        color: "#facc15",
        weight: 1.4,
        opacity: 0.92,
        fillColor: "#facc15",
        fillOpacity: 0.1,
        dashArray: "4 4"
    };
}

function attachSelectionClearHandler() {
    if (!selectionLayer) {
        return;
    }

    selectionLayer.off("click");
    selectionLayer.on("click", async (event) => {
        L.DomEvent.stop(event);
        await clearSpatialSelection();
    });
}

function removeDrawnSelectionLayer() {
    if (selectionLayer && dashboardMap) {
        dashboardMap.removeLayer(selectionLayer);
    }

    selectionLayer = null;
    selectionStartLatLng = null;
    selectionLatLngs = [];
}

function startSpatialSelection(event) {
    if (!selectionMode) {
        return;
    }

    isDrawingSelection = true;
    suppressNextMapClear = true;
    selectionStartLatLng = event.latlng;
    selectionLatLngs = [event.latlng];

    if (selectionLayer) {
        dashboardMap.removeLayer(selectionLayer);
        selectionLayer = null;
    }

    dashboardMap.dragging.disable();

    if (selectionMode === "rectangle") {
        selectionLayer = L.rectangle(
            L.latLngBounds(selectionStartLatLng, selectionStartLatLng),
            getSelectionStyle()
        ).addTo(dashboardMap);
    } else if (selectionMode === "lasso") {
        selectionLayer = L.polygon(selectionLatLngs, getSelectionStyle()).addTo(dashboardMap);
    }
}

function updateSpatialSelection(event) {
    if (!isDrawingSelection || !selectionLayer || !selectionStartLatLng) {
        return;
    }

    if (selectionMode === "rectangle") {
        selectionLayer.setBounds(L.latLngBounds(selectionStartLatLng, event.latlng));
    } else if (selectionMode === "lasso") {
        selectionLatLngs.push(event.latlng);
        selectionLayer.setLatLngs(selectionLatLngs);
    }
}

async function finishSpatialSelection(event) {
    if (!isDrawingSelection || !selectionLayer) {
        return;
    }

    isDrawingSelection = false;
    dashboardMap.dragging.enable();

    if (selectionMode === "lasso") {
        selectionLatLngs.push(event.latlng);
        selectionLayer.setLatLngs(selectionLatLngs);
    }

    attachSelectionClearHandler();

    const coordinates = getSelectionCoordinates();

    if (coordinates.length < 3) {
        clearSpatialSelection();
        return;
    }

    selectionMode = null;
    updateSelectionToolButtons();

    await applySpatialSelection(coordinates);

    setTimeout(() => {
        suppressNextMapClear = false;
    }, 250);
}

function getSelectionCoordinates() {
    if (!selectionLayer) {
        return [];
    }

    let latLngs = [];

    if (selectionLayer instanceof L.Rectangle) {
        const bounds = selectionLayer.getBounds();
        const north = bounds.getNorth();
        const south = bounds.getSouth();
        const east = bounds.getEast();
        const west = bounds.getWest();

        latLngs = [
            L.latLng(south, west),
            L.latLng(south, east),
            L.latLng(north, east),
            L.latLng(north, west)
        ];
    } else {
        latLngs = selectionLayer.getLatLngs()[0] || [];
    }

    return latLngs.map((latLng) => [latLng.lng, latLng.lat]);
}

function getActiveSelectionLayer() {
    if (currentMapMode === "choropleth") {
        return "tracts";
    }

    if (currentMapMode === "points" || currentMapMode === "cluster") {
        return "points";
    }

    return null;
}

function isPointInsideSelection(lon, lat) {
    if (
        activeSelectionLayer !== "points"
        || !activeSelectionCoordinates
        || activeSelectionCoordinates.length < 3
    ) {
        return false;
    }

    let inside = false;

    for (
        let currentIndex = 0, previousIndex = activeSelectionCoordinates.length - 1;
        currentIndex < activeSelectionCoordinates.length;
        previousIndex = currentIndex, currentIndex += 1
    ) {
        const currentPoint = activeSelectionCoordinates[currentIndex];
        const previousPoint = activeSelectionCoordinates[previousIndex];
        const currentLon = Number(currentPoint[0]);
        const currentLat = Number(currentPoint[1]);
        const previousLon = Number(previousPoint[0]);
        const previousLat = Number(previousPoint[1]);

        const intersects = ((currentLat > lat) !== (previousLat > lat))
            && (lon < ((previousLon - currentLon) * (lat - currentLat)) / (previousLat - currentLat) + currentLon);

        if (intersects) {
            inside = !inside;
        }
    }

    return inside;
}

async function applySpatialSelection(coordinates) {
    const targetLayer = getActiveSelectionLayer();

    const response = await fetch("/api/spatial-selection", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            coordinates,
            target_layer: targetLayer
        })
    });

    if (!response.ok) {
        throw new Error("Spatial selection request failed.");
    }

    const data = await response.json();

    if (data.status !== "success") {
        console.error("Spatial selection API error:", data);
        return;
    }

    activeFilters.tractGeoids.clear();
    (data.tract_geoids || []).forEach((geoid) => activeFilters.tractGeoids.add(String(geoid)));

    activeSelectionCoordinates = coordinates;
    activeSelectionLayer = data.target_layer || targetLayer;
    selectedNeighborhoodNames = activeSelectionLayer === "neighborhoods"
        ? new Set((data.neighborhood_names || []).map((name) => String(name)))
        : new Set();
    spatialSelectionSummary = activeSelectionLayer === "points"
        ? `Spatial selection: ${formatNumber(data.arrest_point_count || 0)} points`
        : `Spatial selection: ${formatNumber(data.tract_count || 0)} tracts`;
    updateFilterChips();
    updateSelectionControlVisibility();

    await refreshDashboardPanels();
    await updateMap();

    removeDrawnSelectionLayer();

    setMapStatus(
        activeSelectionLayer === "points" ? data.arrest_point_count || 0 : data.tract_count || 0,
        activeSelectionLayer === "points"
            ? `selected points | ${formatNumber(data.tract_count || 0)} related tracts`
            : `selected tracts | ${formatNumber(data.arrest_point_count || 0)} arrests | ${formatNumber(data.shooting_point_count || 0)} shootings`
    );
}

function clearSpatialSelectionLayer() {
    removeDrawnSelectionLayer();

    activeSelectionCoordinates = [];
    activeSelectionLayer = null;
    selectedNeighborhoodNames.clear();
    spatialSelectionSummary = null;
    updateSelectionControlVisibility();
}

async function clearSpatialSelection() {
    clearSpatialSelectionLayer();
    activeFilters.tractGeoids.clear();
    updateFilterChips();
    await refreshDashboard();
}

async function clearSpatialSelectionFromMapClick(event) {
    if (suppressNextMapClear || isDrawingSelection || selectionMode || !spatialSelectionSummary) {
        return;
    }

    const target = event.originalEvent?.target;

    if (target?.closest?.(".leaflet-control, .leaflet-popup")) {
        return;
    }

    await clearSpatialSelection();
}

async function clearSpatialSelectionFromMapContainerClick(event) {
    if (suppressNextMapClear || isDrawingSelection || selectionMode || !spatialSelectionSummary) {
        return;
    }

    const target = event.target;

    if (target?.closest?.(".leaflet-control, .leaflet-popup, .modern-map-legend")) {
        return;
    }

    event.stopPropagation();
    await clearSpatialSelection();
}

function setMapLegendContent(content) {
    if (!mapLegendElement) {
        return;
    }

    if (!content) {
        mapLegendElement.classList.add("is-hidden");
        mapLegendElement.innerHTML = "";
        return;
    }

    mapLegendElement.innerHTML = content;
    mapLegendElement.classList.remove("is-hidden");
}

function renderPointClusterLegend(mode, count) {
    if (!pointsVisible || count <= 0) {
        setMapLegendContent("");
        return;
    }

    const title = mode === "cluster" ? "Clustered events" : "Point events";
    const detail = mode === "cluster"
        ? "Clusters expand as users zoom"
        : `${formatNumber(count)} sampled arrest events`;

    setMapLegendContent(`
        <div class="legend-title">${title}</div>
        <div class="legend-items">
            <span class="legend-item">
                <span class="legend-symbol point-symbol"></span>
                Arrest event
            </span>
            <span class="legend-item">
                <span class="legend-symbol boundary-symbol"></span>
                Durham boundary
            </span>
            <span class="legend-note">${detail}</span>
        </div>
    `);
}

function renderChoroplethLegend(breaks, metric, values) {
    const cleanValues = values
        .map((value) => Number(value || 0))
        .filter((value) => Number.isFinite(value) && value > 0);

    if (!cleanValues.length) {
        setMapLegendContent("");
        return;
    }

    const metricLabel = CHOROPLETH_METRIC_LABELS[metric] || "Selected metric";
    const minValue = Math.min(...cleanValues);
    const maxValue = Math.max(...cleanValues, Number(breaks[breaks.length - 1] || 0));
    const sequentialRamp = `linear-gradient(90deg, ${CHOROPLETH_COLORS.join(", ")})`;
    const tickMarks = breaks.map((breakValue) => {
        const position = maxValue === minValue
            ? 100
            : ((Number(breakValue || 0) - minValue) / (maxValue - minValue)) * 100;
        const boundedPosition = Math.max(0, Math.min(100, position));

        return `<span title="${formatLegendValue(breakValue, metric)}" style="left: ${boundedPosition}%"></span>`;
    }).join("");

    setMapLegendContent(`
        <div class="choropleth-legend">
            <div class="choropleth-legend-values">
                <span>${formatLegendValue(minValue, metric)}</span>
                <span>${formatLegendValue(maxValue, metric)}</span>
            </div>
            <div class="choropleth-legend-scale-wrap">
                <span class="legend-scale choropleth-scale" style="background: ${sequentialRamp}" aria-hidden="true"></span>
                <span class="legend-ticks" aria-hidden="true">
                    <span style="left: 0%"></span>
                    ${tickMarks}
                </span>
            </div>
            <div class="choropleth-legend-title">${metricLabel}</div>
            <div class="choropleth-legend-method">Natural breaks (Jenks) • sequential scale</div>
        </div>
    `);
}

function setLisaLegendContent(content) {
    if (!lisaLegendElement) {
        return;
    }

    if (!content) {
        lisaLegendElement.classList.add("is-hidden");
        lisaLegendElement.innerHTML = "";
        return;
    }

    lisaLegendElement.innerHTML = content;
    lisaLegendElement.classList.remove("is-hidden");
}

function renderLisaLegend() {
    const legendItems = Object.values(LISA_CLUSTER_STYLES).map((clusterStyle) => {
        return `
            <span class="legend-item lisa-legend-item">
                <span class="legend-symbol lisa-symbol" style="background: ${clusterStyle.fillColor}; border-color: ${clusterStyle.color};"></span>
                ${clusterStyle.label}
            </span>
        `;
    }).join("");

    setLisaLegendContent(`
        <div class="legend-title">Local spatial association</div>
        <div class="legend-items lisa-legend-items">
            ${legendItems}
        </div>
    `);
}

function getLisaClusterStyle(feature) {
    const properties = feature.properties || {};
    const cluster = properties.lisa_cluster || "Not significant";
    const clusterStyle = LISA_CLUSTER_STYLES[cluster] || LISA_CLUSTER_STYLES["Not significant"];
    const isSignificant = cluster !== "Not significant";

    return {
        pane: "lisaClusterPane",
        color: clusterStyle.color,
        weight: isSignificant ? 1.35 : 0.55,
        opacity: isSignificant ? 0.92 : 0.38,
        fillColor: clusterStyle.fillColor,
        fillOpacity: isSignificant ? 0.54 : 0.12
    };
}

function buildLisaPopup(properties) {
    const geoid = properties.tract_geoid || properties.GEOID || properties.geoid || "Not available";
    const neighborhood = properties.primary_neighborhood || "Not available";
    const cluster = properties.lisa_cluster || "Not significant";
    const arrestRate = Number(properties.arrests_per_1000_population || 0);
    const localMoran = Number(properties.local_moran_i || 0);
    const pValue = Number(properties.local_moran_p_sim || 0);

    return `
        <strong>Exploratory local spatial association result.</strong><br>
        <strong>Tract GEOID:</strong> ${geoid}<br>
        <strong>Neighborhood:</strong> ${neighborhood}<br>
        <strong>LISA cluster:</strong> ${cluster}<br>
        <strong>Arrests per 1,000 population:</strong> ${arrestRate.toFixed(1)}<br>
        <strong>Local Moran's I:</strong> ${localMoran.toFixed(3)}<br>
        <strong>p-value:</strong> ${pValue.toFixed(3)}
    `;
}

function onEachLisaCluster(feature, layer) {
    const properties = feature.properties || {};

    layer.bindTooltip(buildLisaPopup(properties), {
        sticky: true,
        direction: "top",
        className: "lisa-cluster-tooltip"
    });

    layer.on("mouseover", () => {
        layer.setStyle({
            weight: 2.2,
            opacity: 1,
            fillOpacity: 0.68
        });
    });

    layer.on("mouseout", () => {
        if (lisaClusterLayer) {
            lisaClusterLayer.resetStyle(layer);
        }
    });
}

async function getLisaClusterGeojson() {
    if (lisaClusterGeojson) {
        return lisaClusterGeojson;
    }

    const data = await fetchJson("/api/lisa-clusters");
    lisaClusterGeojson = data.geojson || { type: "FeatureCollection", features: [] };

    return lisaClusterGeojson;
}

function removeLisaLayer() {
    if (lisaClusterLayer && dashboardMap) {
        dashboardMap.removeLayer(lisaClusterLayer);
    }

    lisaClusterLayer = null;
    setLisaLegendContent("");
}

function bringPrimaryMapLayersToFront() {
    if (
        activeDataLayer
        && currentMapMode !== "choropleth"
        && typeof activeDataLayer.bringToFront === "function"
    ) {
        activeDataLayer.bringToFront();
    }

    if (pointOverlayLayer && typeof pointOverlayLayer.bringToFront === "function") {
        pointOverlayLayer.bringToFront();
    }

    if (selectedTractHighlightLayer && typeof selectedTractHighlightLayer.bringToFront === "function") {
        selectedTractHighlightLayer.bringToFront();
    }

    if (selectedNeighborhoodHighlightLayer && typeof selectedNeighborhoodHighlightLayer.bringToFront === "function") {
        selectedNeighborhoodHighlightLayer.bringToFront();
    }

    if (cityBoundaryLayer) {
        cityBoundaryLayer.bringToFront();
    }
}

async function renderLisaLayer() {
    if (!dashboardMap || !lisaLayerVisible) {
        removeLisaLayer();
        return;
    }

    removeLisaLayer();

    try {
        const geojson = await getLisaClusterGeojson();

        lisaClusterLayer = L.geoJSON(geojson, {
            pane: "lisaClusterPane",
            style: getLisaClusterStyle,
            onEachFeature: onEachLisaCluster
        });

        lisaClusterLayer.addTo(dashboardMap);
        renderLisaLegend();
        bringPrimaryMapLayersToFront();
    } catch (error) {
        console.warn("Unable to load LISA clusters layer.", error);
        lisaLayerVisible = false;
        updateLisaLayerToggle();
        removeLisaLayer();
    }
}

function buildMapModeLabel(mode) {
    if (mode === "cluster") {
        return "cluster mode";
    }

    if (mode === "choropleth") {
        return "choropleth mode";
    }

    return "point mode";
}

async function updateMap(options = {}) {
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
    } else if (currentMapMode === "choropleth") {
        await renderChoroplethLayer(options);
    }

    await renderSelectedTractHighlightLayer();
    await renderSelectedNeighborhoodHighlightLayer();
    await renderLisaLayer();

    bringPrimaryMapLayersToFront();

    updateSelectionControlVisibility();
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

    const isSelected = isPointInsideSelection(lon, lat);
    const marker = L.circleMarker([lat, lon], {
        radius: isSelected ? 6.5 : 4,
        color: isSelected ? "#f8fafc" : "#38bdf8",
        weight: isSelected ? 2 : 1,
        opacity: isSelected ? 0.96 : 0.82,
        fillColor: isSelected ? "#facc15" : "#38bdf8",
        fillOpacity: isSelected ? 0.92 : 0.74,
        selectedPoint: isSelected
    });

    marker.bindPopup(buildPopup(point));

    if (isSelected) {
        marker.on("click", async (event) => {
            L.DomEvent.stop(event);
            await clearSpatialSelection();
        });
    }

    return marker;
}

function createClusterIcon(cluster) {
    const markers = cluster.getAllChildMarkers();
    const selectedCount = markers.filter((marker) => marker.options?.selectedPoint).length;
    const childCount = cluster.getChildCount();
    const sizeClass = childCount >= 100 ? "large" : childCount >= 20 ? "medium" : "small";
    const selectedClass = selectedCount > 0 ? " selected-cluster" : "";

    return L.divIcon({
        html: `<div><span>${childCount}</span></div>`,
        className: `marker-cluster marker-cluster-${sizeClass}${selectedClass}`,
        iconSize: L.point(40, 40)
    });
}

function buildPointFeatureLayer(points) {
    const pointLayer = L.featureGroup();

    points.forEach((point) => {
        const marker = createPointMarker(point);

        if (marker) {
            marker.addTo(pointLayer);
        }
    });

    return pointLayer;
}

function buildClusterFeatureLayer(points) {
    if (typeof L.markerClusterGroup === "undefined") {
        console.error("Leaflet marker cluster plugin is not loaded.");
        return L.featureGroup();
    }

    const clusterLayer = L.markerClusterGroup({
        showCoverageOnHover: false,
        spiderfyOnMaxZoom: true,
        disableClusteringAtZoom: 16,
        maxClusterRadius: 48,
        iconCreateFunction: createClusterIcon
    });

    points.forEach((point) => {
        const lat = Number(point.latitude);
        const lon = Number(point.longitude);

        if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
            return;
        }

        const isSelected = isPointInsideSelection(lon, lat);
        const marker = L.circleMarker([lat, lon], {
            radius: isSelected ? 6.5 : 4,
            color: isSelected ? "#f8fafc" : "#38bdf8",
            weight: isSelected ? 2 : 1,
            opacity: isSelected ? 0.96 : 0.82,
            fillColor: isSelected ? "#facc15" : "#38bdf8",
            fillOpacity: isSelected ? 0.92 : 0.74,
            selectedPoint: isSelected
        });

        marker.bindPopup(buildPopup(point));

        if (isSelected) {
            marker.on("click", async (event) => {
                L.DomEvent.stop(event);
                await clearSpatialSelection();
            });
        }

        clusterLayer.addLayer(marker);
    });

    return clusterLayer;
}

async function renderPointLayer() {
    const points = await fetchMapPoints();
    const pointLayer = buildPointFeatureLayer(points);

    activeDataLayer = pointLayer;
    lastPointLayer = pointLayer;

    if (pointsVisible) {
        activeDataLayer.addTo(dashboardMap);
    }

    setMapStatus(points.length, pointsVisible ? "points" : "points hidden");
    renderPointClusterLegend("points", points.length);
    fitLayerIfPossible(pointLayer);
}

async function renderClusterLayer() {
    const points = await fetchMapPoints();
    const clusterLayer = buildClusterFeatureLayer(points);

    activeDataLayer = clusterLayer;

    if (pointsVisible) {
        activeDataLayer.addTo(dashboardMap);
    }

    setMapStatus(points.length, pointsVisible ? "clustered points" : "clusters hidden");
    renderPointClusterLegend("cluster", points.length);
    fitLayerIfPossible(clusterLayer);
}

function getChoroplethMetricValue(properties) {
    return Number(properties.selected_metric_value || 0);
}

function isEventActivityMetric(metric) {
    return [
        "total_arrests",
        "arrests_per_1000_population",
        "felony_arrests_per_1000_population",
        "felony_share",
        "activity_density",
        "arrests_density_per_sq_mi",
        "arrest_activity_share",
        "weekend_activity_share",
        "evening_night_activity_share",
        "night_share"
    ].includes(metric);
}

function getChoroplethBreaks(values) {
    const cleanValues = values
        .map((value) => Number(value || 0))
        .filter((value) => Number.isFinite(value) && value > 0)
        .sort((a, b) => a - b);

    const maxValue = Math.max(...cleanValues, 0);

    if (maxValue <= 0) {
        return [0, 1, 2, 3, 4];
    }

    const uniqueValues = [...new Set(cleanValues)];

    if (uniqueValues.length >= 5) {
        return getJenksUpperBreaks(cleanValues, 5);
    }

    return [
        maxValue * 0.2,
        maxValue * 0.4,
        maxValue * 0.6,
        maxValue * 0.8,
        maxValue
    ];
}

function getJenksUpperBreaks(sortedValues, classCount) {
    const values = sortedValues
        .filter((value) => Number.isFinite(value))
        .sort((a, b) => a - b);

    const dataCount = values.length;
    const classes = Math.min(classCount, dataCount);

    if (classes <= 1) {
        return [values[dataCount - 1] || 0];
    }

    const lowerClassLimits = Array.from(
        { length: dataCount + 1 },
        () => Array(classes + 1).fill(0)
    );
    const varianceCombinations = Array.from(
        { length: dataCount + 1 },
        () => Array(classes + 1).fill(Infinity)
    );

    for (let classIndex = 1; classIndex <= classes; classIndex += 1) {
        lowerClassLimits[1][classIndex] = 1;
        varianceCombinations[1][classIndex] = 0;
    }

    for (let valueIndex = 2; valueIndex <= dataCount; valueIndex += 1) {
        let sum = 0;
        let sumSquares = 0;
        let weight = 0;

        for (let lowerIndex = 1; lowerIndex <= valueIndex; lowerIndex += 1) {
            const offsetIndex = valueIndex - lowerIndex + 1;
            const value = values[offsetIndex - 1];

            sum += value;
            sumSquares += value * value;
            weight += 1;

            const variance = sumSquares - (sum * sum) / weight;
            const previousIndex = offsetIndex - 1;

            if (previousIndex !== 0) {
                for (let classIndex = 2; classIndex <= classes; classIndex += 1) {
                    const candidateVariance = variance + varianceCombinations[previousIndex][classIndex - 1];

                    if (varianceCombinations[valueIndex][classIndex] >= candidateVariance) {
                        lowerClassLimits[valueIndex][classIndex] = offsetIndex;
                        varianceCombinations[valueIndex][classIndex] = candidateVariance;
                    }
                }
            }
        }

        lowerClassLimits[valueIndex][1] = 1;
        varianceCombinations[valueIndex][1] = sumSquares - (sum * sum) / weight;
    }

    const boundaries = Array(classes + 1).fill(0);
    boundaries[classes] = values[dataCount - 1];
    boundaries[0] = values[0];

    let valueIndex = dataCount;

    for (let classIndex = classes; classIndex > 1; classIndex -= 1) {
        const lowerLimit = lowerClassLimits[valueIndex][classIndex];
        boundaries[classIndex - 1] = values[Math.max(0, lowerLimit - 2)];
        valueIndex = lowerLimit - 1;
    }

    return boundaries.slice(1);
}

function getChoroplethColor(value, breaks) {
    if (!value || value <= 0) {
        return "rgba(15, 23, 42, 0.18)";
    }

    if (value <= breaks[0]) {
        return CHOROPLETH_COLORS[0];
    }

    if (value <= breaks[1]) {
        return CHOROPLETH_COLORS[1];
    }

    if (value <= breaks[2]) {
        return CHOROPLETH_COLORS[2];
    }

    if (value <= breaks[3]) {
        return CHOROPLETH_COLORS[3];
    }

    return CHOROPLETH_COLORS[4];
}

function buildChoroplethPopup(properties) {
    const primaryNeighborhood = properties.primary_neighborhood || "Not assigned";
    const secondaryNeighborhoods = properties.secondary_neighborhoods || "";
    const secondaryLine = secondaryNeighborhoods
        ? `<strong>Secondary neighborhoods:</strong> ${secondaryNeighborhoods}<br>`
        : "";
    const selectedMetric = properties.selected_metric || currentChoroplethMetric;
    const selectedMetricLabel = CHOROPLETH_METRIC_LABELS[selectedMetric] || "Selected metric";
    const selectedMetricValue = Number(properties.selected_metric_value || 0);
    const selectedMetricLine = `<strong>${selectedMetricLabel}:</strong> ${formatChoroplethPopupValue(selectedMetricValue, selectedMetric)}<br>`;

    return `
        <strong>${properties.name || "Census tract"}</strong><br>
        <strong>GEOID:</strong> ${properties.geoid || "Not available"}<br>
        <strong>Primary neighborhood:</strong> ${primaryNeighborhood}<br>
        ${secondaryLine}
        ${selectedMetricLine}
        <em>Full tract geometry preserved. Tract intersects Durham municipal boundary.</em>
    `;
}

function getChoroplethStyle(feature, breaks) {
    const properties = feature.properties || {};
    const value = getChoroplethMetricValue(properties);
    const geoid = String(properties.geoid || "");

    const isSelected = activeSelectionLayer === "tracts" && activeFilters.tractGeoids.has(geoid);

    return {
        color: isSelected ? "#f59e0b" : "rgba(226, 232, 240, 0.58)",
        weight: isSelected ? 2.1 : 0.75,
        opacity: isSelected ? 0.98 : 0.6,
        fillColor: getChoroplethColor(value, breaks),
        fillOpacity: isSelected ? 0.68 : value > 0 ? 0.58 : 0.18
    };
}

function getSelectedTractHighlightStyle() {
    return {
        color: "#f59e0b",
        weight: 1.9,
        opacity: 0.96,
        fillColor: "#facc15",
        fillOpacity: 0.08,
        interactive: false
    };
}

async function renderSelectedTractHighlightLayer() {
    if (
        !spatialSelectionSummary
        || activeSelectionLayer !== "tracts"
        || currentMapMode === "choropleth"
        || activeFilters.tractGeoids.size === 0
    ) {
        return;
    }

    const data = await fetchJson(`/api/choropleth?metric=${currentChoroplethMetric}`);
    const geojson = data.geojson || { type: "FeatureCollection", features: [] };
    const selectedGeoids = activeFilters.tractGeoids;
    const selectedFeatures = geojson.features.filter((feature) => {
        const properties = feature.properties || {};
        const geoid = String(properties.geoid || properties.tract_geoid || "");

        return selectedGeoids.has(geoid);
    });

    if (!selectedFeatures.length) {
        return;
    }

    selectedTractHighlightLayer = L.geoJSON(
        {
            type: "FeatureCollection",
            features: selectedFeatures
        },
        {
            style: getSelectedTractHighlightStyle,
            interactive: false
        }
    );

    selectedTractHighlightLayer.addTo(dashboardMap);
    selectedTractHighlightLayer.bringToFront();
}

function getSelectedNeighborhoodHighlightStyle() {
    return {
        color: "#22d3ee",
        weight: 1.45,
        opacity: 0.88,
        fillColor: "#22d3ee",
        fillOpacity: 0.07,
        dashArray: "5 5",
        interactive: false
    };
}

async function renderSelectedNeighborhoodHighlightLayer() {
    if (
        !spatialSelectionSummary
        || activeSelectionLayer !== "neighborhoods"
        || selectedNeighborhoodNames.size === 0
    ) {
        return;
    }

    const data = await fetchJson("/api/neighborhoods");
    const geojson = data.geojson || { type: "FeatureCollection", features: [] };
    const selectedFeatures = geojson.features.filter((feature) => {
        const properties = feature.properties || {};
        const name = String(
            properties.neighborhood_name
            || properties.name
            || properties.Name
            || ""
        );

        return selectedNeighborhoodNames.has(name);
    });

    if (!selectedFeatures.length) {
        return;
    }

    selectedNeighborhoodHighlightLayer = L.geoJSON(
        {
            type: "FeatureCollection",
            features: selectedFeatures
        },
        {
            style: getSelectedNeighborhoodHighlightStyle,
            interactive: false
        }
    );

    selectedNeighborhoodHighlightLayer.addTo(dashboardMap);
    selectedNeighborhoodHighlightLayer.bringToFront();
}

async function renderChoroplethLayer(options = {}) {
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
                if (selectionLayer || spatialSelectionSummary) {
                    await clearSpatialSelection();
                    return;
                }

                if (!geoid) {
                    return;
                }

                suppressTractPopupClose = true;
                dashboardMap.closePopup();
                layer.openPopup();

                clearSpatialSelectionLayer();
                activeSelectionLayer = "tracts";
                activeFilters.tractGeoids.clear();
                activeFilters.tractGeoids.add(geoid);

                await refreshDashboardPanels();

                choroplethLayer.setStyle((selectedFeature) => {
                    return getChoroplethStyle(selectedFeature, breaks);
                });

                if (cityBoundaryLayer) {
                    cityBoundaryLayer.bringToFront();
                }

                setTimeout(() => {
                    suppressTractPopupClose = false;
                }, 350);
            });

            layer.on("popupclose", async () => {
                if (suppressTractPopupClose) {
                    return;
                }

                if (activeSelectionLayer !== "tracts" || !geoid || !activeFilters.tractGeoids.has(geoid)) {
                    return;
                }

                activeFilters.tractGeoids.delete(geoid);

                if (activeFilters.tractGeoids.size === 0) {
                    activeSelectionLayer = null;
                }

                await refreshDashboardPanels();

                choroplethLayer.setStyle((selectedFeature) => {
                    return getChoroplethStyle(selectedFeature, breaks);
                });

                if (cityBoundaryLayer) {
                    cityBoundaryLayer.bringToFront();
                }

                suppressTractPopupClose = false;
            });
        }
    });

    activeDataLayer = choroplethLayer;
    activeDataLayer.addTo(dashboardMap);

    const nonZeroTracts = values.filter((value) => Number(value || 0) > 0).length;
    setMapStatus(
        nonZeroTracts,
        isEventActivityMetric(currentChoroplethMetric) ? "tracts with activity" : "tracts with data"
    );
    renderChoroplethLegend(breaks, currentChoroplethMetric, values);

    if (options.fitBounds !== false) {
        fitLayerIfPossible(choroplethLayer);
    }

    if (pointsVisible) {
        await renderChoroplethPointOverlay();
    }

    if (cityBoundaryLayer) {
        cityBoundaryLayer.bringToFront();
    }
}

async function renderChoroplethPointOverlay() {
    const points = await fetchMapPoints();

    pointOverlayLayer = buildClusterFeatureLayer(points);
    pointOverlayLayer.addTo(dashboardMap);

    setMapStatus(points.length, "clustered points over choropleth");
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
    const toggle = getElement("pointsLayerToggle");

    if (!toggle) {
        return;
    }

    toggle.checked = pointsVisible;
    toggle.closest(".map-layer-toggle")?.classList.toggle("active", pointsVisible);
}

function updateLisaLayerToggle() {
    const toggle = getElement("lisaLayerToggle");

    if (!toggle) {
        return;
    }

    toggle.checked = lisaLayerVisible;
    toggle.closest(".map-layer-toggle")?.classList.toggle("active", lisaLayerVisible);
}

async function togglePointsVisibility() {
    pointsVisible = !pointsVisible;
    updateTogglePointsButton();

    await updateMap();
}

async function toggleLisaLayerVisibility() {
    lisaLayerVisible = !lisaLayerVisible;
    updateLisaLayerToggle();

    await renderLisaLayer();
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
    const requestToken = recordsRequestToken + 1;
    recordsRequestToken = requestToken;
    const separator = query ? `${query}&` : "?";
    const data = await fetchJson(`/api/records${separator}limit=25`);

    if (requestToken !== recordsRequestToken || query !== buildFilterQuery()) {
        return;
    }

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

    getElement("pointsLayerToggle")?.addEventListener("change", async () => {
        await togglePointsVisibility();
    });

    getElement("lisaLayerToggle")?.addEventListener("change", async () => {
        await toggleLisaLayerVisibility();
    });

    getElement("choroplethMetricSelect")?.addEventListener("change", async (event) => {
        currentChoroplethMetric = event.target.value || "total_arrests";

        if (currentMapMode === "choropleth") {
            await updateMap({ fitBounds: false });
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
            } else if (currentMapMode === "choropleth") {
                pointsVisible = false;
            }

            updateTogglePointsButton();
            await updateMap();
        });
    });
}

async function initializeDashboard() {
    setupEvents();
    await initializeDateRangeControls();
    await initializeChoroplethMetricSelect();
    updateTogglePointsButton();
    await initializeMap();
    await refreshDashboard();
}

initializeDashboard().catch((error) => {
    console.error("Dashboard initialization failed:", error);
});

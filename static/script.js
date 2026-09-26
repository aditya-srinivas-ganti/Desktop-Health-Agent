// ============================================================
// COMPUTER HEALTH AGENT
// FRONTEND CONTROLLER
// ============================================================


document.addEventListener("DOMContentLoaded", () => {

    initializeNavigation();

    initializeChart();

    initializeModelFeed();

    initializeButtons();

    loadSystemData();

    loadProcesses();

    loadActivity();

    loadLogs();


    // Refresh system information every 3 seconds
    setInterval(loadSystemData, 3000);


    // Refresh process list every 10 seconds
    setInterval(loadProcesses, 10000);


    // Refresh activity every 10 seconds
    setInterval(loadActivity, 10000);


    // Refresh logs every 15 seconds
    setInterval(loadLogs, 15000);

});


// ============================================================
// GLOBAL STATE
// ============================================================

let resourceChart = null;

let allModels = [];


// ============================================================
// NAVIGATION
// ============================================================

function initializeNavigation() {

    const navigationItems =
        document.querySelectorAll(".nav-item");


    navigationItems.forEach(item => {

        item.addEventListener("click", () => {

            const pageName =
                item.dataset.page;


            navigationItems.forEach(nav => {
                nav.classList.remove("active");
            });


            item.classList.add("active");


            document
                .querySelectorAll(".page")
                .forEach(page => {
                    page.classList.remove("active-page");
                });


            const targetPage =
                document.getElementById(
                    `${pageName}-page`
                );


            if (targetPage) {

                targetPage.classList.add(
                    "active-page"
                );

            }


            updatePageTitle(pageName);

        });

    });

}


// ============================================================
// PAGE TITLE
// ============================================================

function updatePageTitle(pageName) {

    const title =
        document.getElementById("page-title");


    const titles = {

        overview: "Overview",

        processes: "Processes",

        activity: "Activity",

        logs: "Logs"

    };


    title.textContent =
        titles[pageName] || "Overview";

}


// ============================================================
// SYSTEM INFORMATION
// ============================================================

async function loadSystemData() {

    try {

        const response =
            await fetch("/api/system");


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        if (data.error) {
            throw new Error(data.error);
        }


        updateSystemUI(data);

    }

    catch (error) {

        console.error(
            "System API error:",
            error
        );

    }

}


// ============================================================
// UPDATE SYSTEM UI
// ============================================================

function updateSystemUI(data) {

    const cpu =
        Number(data.cpu) || 0;

    const memory =
        Number(data.memory) || 0;

    const disk =
        Number(data.disk) || 0;


    document.getElementById(
        "hostname"
    ).textContent =
        data.hostname || "Unknown";


    document.getElementById(
        "cpu-value"
    ).textContent =
        `${cpu.toFixed(1)}%`;


    document.getElementById(
        "memory-value"
    ).textContent =
        `${memory.toFixed(1)}%`;


    document.getElementById(
        "disk-value"
    ).textContent =
        `${disk.toFixed(1)}%`;


    document.getElementById(
        "cpu-progress"
    ).style.width =
        `${Math.min(cpu, 100)}%`;


    document.getElementById(
        "memory-progress"
    ).style.width =
        `${Math.min(memory, 100)}%`;


    document.getElementById(
        "disk-progress"
    ).style.width =
        `${Math.min(disk, 100)}%`;


    document.getElementById(
        "system-time"
    ).textContent =
        data.timestamp || "--";


    updateHealthStatus(
        cpu,
        memory,
        disk
    );


    updateChart(
        cpu,
        memory,
        disk
    );

}


// ============================================================
// HEALTH STATUS
// ============================================================

function updateHealthStatus(
    cpu,
    memory,
    disk
) {

    const healthElement =
        document.getElementById(
            "health-status"
        );


    const highest =
        Math.max(
            cpu,
            memory,
            disk
        );


    if (highest >= 90) {

        healthElement.textContent =
            "Attention Required";

        healthElement.className =
            "health-value danger";

    }

    else if (highest >= 75) {

        healthElement.textContent =
            "Under Heavy Load";

        healthElement.className =
            "health-value warning";

    }

    else {

        healthElement.textContent =
            "System Healthy";

        healthElement.className =
            "health-value";

    }

}


// ============================================================
// CHART
// ============================================================

function initializeChart() {

    const canvas =
        document.getElementById(
            "resourceChart"
        );


    if (!canvas) {
        return;
    }


    const context =
        canvas.getContext("2d");


    resourceChart =
        new Chart(
            context,
            {

                type: "line",

                data: {

                    labels: [],

                    datasets: [

                        {
                            label: "CPU",
                            data: [],
                            tension: 0.35,
                            borderWidth: 2,
                            pointRadius: 0
                        },

                        {
                            label: "Memory",
                            data: [],
                            tension: 0.35,
                            borderWidth: 2,
                            pointRadius: 0
                        },

                        {
                            label: "Disk",
                            data: [],
                            tension: 0.35,
                            borderWidth: 2,
                            pointRadius: 0
                        }

                    ]

                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {
                        intersect: false,
                        mode: "index"
                    },

                    plugins: {

                        legend: {
                            position: "top",
                            align: "end"
                        }

                    },

                    scales: {

                        y: {

                            min: 0,

                            max: 100,

                            ticks: {
                                callback: value =>
                                    `${value}%`
                            }

                        }

                    }

                }

            }
        );

}


// ============================================================
// UPDATE CHART
// ============================================================

function updateChart(
    cpu,
    memory,
    disk
) {

    if (!resourceChart) {
        return;
    }


    const currentTime =
        new Date().toLocaleTimeString(
            [],
            {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            }
        );


    resourceChart.data.labels.push(
        currentTime
    );


    resourceChart.data.datasets[0]
        .data.push(cpu);


    resourceChart.data.datasets[1]
        .data.push(memory);


    resourceChart.data.datasets[2]
        .data.push(disk);


    const maxPoints = 30;


    if (
        resourceChart.data.labels.length
        > maxPoints
    ) {

        resourceChart.data.labels.shift();

        resourceChart.data.datasets
            .forEach(dataset => {
                dataset.data.shift();
            });

    }


    resourceChart.update(
        "none"
    );

}


// ============================================================
// AI MODEL FEED
// ============================================================

function initializeModelFeed() {

    const search =
        document.getElementById(
            "model-search"
        );


    const year =
        document.getElementById(
            "model-year"
        );


    if (search) {

        search.addEventListener(
            "input",
            applyModelFilters
        );

    }


    if (year) {

        year.addEventListener(
            "change",
            applyModelFilters
        );

    }


    loadModels();

}


// ============================================================
// LOAD MODELS
// ============================================================

async function loadModels() {

    const feed =
        document.getElementById(
            "model-feed"
        );


    const errorElement =
        document.getElementById(
            "model-error"
        );


    try {

        feed.innerHTML = `
            <div class="feed-loading">
                <div class="spinner"></div>
                Loading AI model releases...
            </div>
        `;


        errorElement.classList.add(
            "hidden"
        );


        const response =
            await fetch("/api/models");


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        if (
            !data.models ||
            !Array.isArray(data.models)
        ) {

            throw new Error(
                "Invalid model feed received."
            );

        }


        allModels =
            data.models;


        document.getElementById(
            "model-count"
        ).textContent =
            allModels.length;


        applyModelFilters();

    }

    catch (error) {

        console.error(
            "AI model feed error:",
            error
        );


        feed.innerHTML = "";


        errorElement.textContent =
            `AI model feed unavailable — ${error.message}`;


        errorElement.classList.remove(
            "hidden"
        );

    }

}


// ============================================================
// MODEL FILTERS
// ============================================================

function applyModelFilters() {

    const searchInput =
        document.getElementById(
            "model-search"
        );


    const yearSelect =
        document.getElementById(
            "model-year"
        );


    const searchTerm =
        (
            searchInput?.value || ""
        )
        .trim()
        .toLowerCase();


    const selectedYear =
        yearSelect?.value || "all";


    const filtered =
        allModels.filter(model => {

            const searchableText = [

                model.name,

                model.company,

                model.type,

                model.category,

                model.description

            ]
            .join(" ")
            .toLowerCase();


            const matchesSearch =
                !searchTerm ||
                searchableText.includes(
                    searchTerm
                );


            const modelYear =
                model.date.substring(
                    0,
                    4
                );


            const matchesYear =
                selectedYear === "all" ||
                modelYear === selectedYear;


            return (
                matchesSearch &&
                matchesYear
            );

        });


    renderModels(filtered);

}


// ============================================================
// RENDER MODELS
// ============================================================

function renderModels(models) {

    const feed =
        document.getElementById(
            "model-feed"
        );


    if (!models.length) {

        feed.innerHTML = `
            <div class="empty-state">
                No AI model releases match your search.
            </div>
        `;

        return;

    }


    feed.innerHTML =
        models
            .map(
                createModelCard
            )
            .join("");

}


// ============================================================
// MODEL CARD
// ============================================================

function createModelCard(model) {

    const date =
        new Date(
            `${model.date}T00:00:00`
        );


    const formattedDate =
        date.toLocaleDateString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );


    const year =
        model.date.substring(
            0,
            4
        );


    return `

        <article class="model-card">

            <div class="model-card-top">

                <div class="model-date">
                    ${formattedDate}
                </div>

                <div class="model-year">
                    ${year}
                </div>

            </div>


            <div class="model-card-main">

                <div class="model-icon">
                    AI
                </div>


                <div class="model-info">

                    <h3>
                        ${escapeHTML(model.name)}
                    </h3>

                    <div class="model-company">
                        ${escapeHTML(model.company)}
                    </div>

                </div>

            </div>


            <div class="model-tags">

                <span class="model-tag">
                    ${escapeHTML(model.type)}
                </span>

                <span class="model-tag">
                    ${escapeHTML(model.category)}
                </span>

            </div>


            <p class="model-description">
                ${escapeHTML(model.description)}
            </p>

        </article>

    `;

}


// ============================================================
// HTML ESCAPING
// ============================================================

function escapeHTML(value) {

    if (value === null || value === undefined) {
        return "";
    }


    return String(value)

        .replaceAll("&", "&amp;")

        .replaceAll("<", "&lt;")

        .replaceAll(">", "&gt;")

        .replaceAll('"', "&quot;")

        .replaceAll("'", "&#039;");

}


// ============================================================
// PROCESSES
// ============================================================

async function loadProcesses() {

    const table =
        document.getElementById(
            "process-table"
        );


    if (!table) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/processes"
            );


        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const processes =
            await response.json();


        table.innerHTML =
            processes.map(
                process => `

                    <tr>

                        <td>
                            ${process.pid}
                        </td>

                        <td class="process-name">
                            ${escapeHTML(process.name)}
                        </td>

                        <td>
                            ${Number(process.cpu).toFixed(1)}%
                        </td>

                        <td>
                            ${Number(process.memory).toFixed(1)}%
                        </td>

                    </tr>

                `
            ).join("");


    }

    catch (error) {

        console.error(
            "Process API error:",
            error
        );


        table.innerHTML = `

            <tr>

                <td colspan="4">
                    Unable to load processes.
                </td>

            </tr>

        `;

    }

}


// ============================================================
// ACTIVITY
// ============================================================

async function loadActivity() {

    const container =
        document.getElementById(
            "activity-list"
        );


    if (!container) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/activity"
            );


        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const events =
            await response.json();


        if (
            !Array.isArray(events) ||
            events.length === 0
        ) {

            container.innerHTML = `
                <div class="empty-state">
                    No recent activity.
                </div>
            `;

            return;

        }


        container.innerHTML =
            events.map(
                event => {

                    const eventTime =
                        event.time ||
                        event.timestamp ||
                        event.date ||
                        "--";


                    const eventMessage =
                        event.message ||
                        event.event ||
                        event.action ||
                        JSON.stringify(event);


                    return `

                        <div class="activity-item">

                            <div class="activity-dot"></div>

                            <div class="activity-content">

                                <div class="activity-time">
                                    ${escapeHTML(eventTime)}
                                </div>

                                <div class="activity-message">
                                    ${escapeHTML(eventMessage)}
                                </div>

                            </div>

                        </div>

                    `;

                }
            ).join("");


    }

    catch (error) {

        console.error(
            "Activity API error:",
            error
        );


        container.innerHTML = `
            <div class="empty-state">
                Unable to load activity.
            </div>
        `;

    }

}


// ============================================================
// LOGS
// ============================================================

async function loadLogs() {

    const container =
        document.getElementById(
            "logs"
        );


    if (!container) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/logs"
            );


        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const logs =
            await response.json();


        if (
            !Array.isArray(logs) ||
            logs.length === 0
        ) {

            container.innerHTML = `
                <div class="empty-state">
                    No logs available.
                </div>
            `;

            return;

        }


        container.innerHTML =
            logs.map(
                log => `

                    <div class="log-row">

                        <div class="log-time">
                            ${escapeHTML(log.time)}
                        </div>

                        <div class="log-type ${String(
                            log.type || "INFO"
                        ).toLowerCase()}">
                            ${escapeHTML(log.type)}
                        </div>

                        <div class="log-message">
                            ${escapeHTML(log.message)}
                        </div>

                    </div>

                `
            ).join("");


    }

    catch (error) {

        console.error(
            "Logs API error:",
            error
        );


        container.innerHTML = `
            <div class="empty-state">
                Unable to load logs.
            </div>
        `;

    }

}


// ============================================================
// BUTTONS
// ============================================================

function initializeButtons() {

    const refreshProcesses =
        document.getElementById(
            "refresh-processes"
        );


    const refreshLogs =
        document.getElementById(
            "refresh-logs"
        );


    if (refreshProcesses) {

        refreshProcesses.addEventListener(
            "click",
            loadProcesses
        );

    }


    if (refreshLogs) {

        refreshLogs.addEventListener(
            "click",
            loadLogs
        );

    }

}
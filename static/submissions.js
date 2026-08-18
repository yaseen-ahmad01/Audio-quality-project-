const statusBox = document.getElementById("status");
const tableWrap = document.getElementById("tableWrap");

function fmt(value, suffix) {
    if (value === null || value === undefined) return "—";
    return `${value}${suffix || ""}`;
}

async function loadSubmissions() {
    statusBox.textContent = "Loading...";

    try {
        const response = await fetch("/api/submissions");
        if (!response.ok) throw new Error("Failed to load submissions.");
        const rows = await response.json();

        if (rows.length === 0) {
            statusBox.textContent = "No submissions yet.";
            tableWrap.innerHTML = "";
            return;
        }

        statusBox.textContent = "";

        const table = document.createElement("table");
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Phone</th>
                    <th>Audio</th>
                    <th>Duration</th>
                    <th>Sample rate</th>
                    <th>Bitrate</th>
                    <th>Loudness</th>
                    <th>Submitted</th>
                </tr>
            </thead>
            <tbody></tbody>
        `;

        const tbody = table.querySelector("tbody");

        rows.forEach((row) => {
            const tr = document.createElement("tr");

            const audioCell = row.stored_filename
                ? `<audio controls preload="none" src="/uploads/${row.stored_filename}"></audio>`
                : "—";

            tr.innerHTML = `
                <td>${row.name}</td>
                <td>${row.phone}</td>
                <td>${audioCell}</td>
                <td>${fmt(row.duration_seconds, " s")}</td>
                <td>${fmt(row.sample_rate_khz, " kHz")}</td>
                <td>${fmt(row.bitrate_kbps, " kbps")}</td>
                <td>${fmt(row.loudness_db, " dB")}</td>
                <td>${row.created_at}</td>
            `;

            tbody.appendChild(tr);
        });

        tableWrap.innerHTML = "";
        tableWrap.appendChild(table);
    } catch (error) {
        statusBox.textContent = error.message;
    }
}

loadSubmissions();

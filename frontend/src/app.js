let chart;

async function fetchData() {
    try {
        const [current, stats, history, alerts] = await Promise.all([
            fetch('/api/temperature/current').then(r => r.json()),
            fetch('/api/temperature/stats').then(r => r.json()),
            fetch('/api/temperature/history?timerange=day').then(r => r.json()),
            fetch('/api/alerts/recent').then(r => r.json())
        ]);

        updateCurrentTemperature(current);
        updateStats(stats);
        updateChart(history);
        updateAlerts(alerts);
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

function updateCurrentTemperature(data) {
    document.getElementById('currentTempC').textContent = data.temperature_c.toFixed(1);
    document.getElementById('currentTempF').textContent = data.temperature_f.toFixed(1);
    document.getElementById('lastUpdate').textContent = new Date(data.timestamp).toLocaleString();
}

function updateStats(data) {
    document.getElementById('minTemp').textContent = data.min_temperature.toFixed(1);
    document.getElementById('maxTemp').textContent = data.max_temperature.toFixed(1);
}

function updateChart(data) {
    const ctx = document.getElementById('tempChart').getContext('2d');
    
    if (chart) {
        chart.destroy();
    }

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => new Date(d.time).toLocaleTimeString()),
            datasets: [{
                label: 'Temperature (°C)',
                data: data.map(d => d.temperature),
                borderColor: '#2563eb',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function updateAlerts(alerts) {
    const alertsList = document.getElementById('alertsList');
    alertsList.innerHTML = alerts.map(alert => `
        <div class="alert-item">
            <p>${alert.message}</p>
            <p class="alert-time">${new Date(alert.timestamp).toLocaleString()}</p>
        </div>
    `).join('');
}

// Event listeners for time range buttons
document.querySelectorAll('.chart-controls button').forEach(button => {
    button.addEventListener('click', async (e) => {
        const range = e.target.dataset.range;
        document.querySelectorAll('.chart-controls button').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        
        const history = await fetch(`/api/temperature/history?timerange=${range}`).then(r => r.json());
        updateChart(history);
    });
});

// Initial load
fetchData();

// Update every minute
setInterval(fetchData, 60000); 
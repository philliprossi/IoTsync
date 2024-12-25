let chart;
const API_BASE_URL = 'http://localhost:8000';

const fetchOptions = {
    method: 'GET',
    mode: 'cors',
    headers: {
        'Accept': 'application/json',
        'Origin': 'http://localhost:3000'
    },
    credentials: 'omit'
};

async function fetchWithDebug(url, options) {
    console.log(`Fetching ${url}...`);
    try {
        const response = await fetch(url, options);
        console.log(`Response status: ${response.status}`);
        console.log(`Response headers:`, response.headers);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`Data received:`, data);
        return data;
    } catch (error) {
        console.error(`Error fetching ${url}:`, error);
        throw error;
    }
}

async function fetchData() {
    console.log('Starting data fetch...');
    try {
        const [current, stats, history, alerts] = await Promise.all([
            fetchWithDebug(`${API_BASE_URL}/api/temperature/current`, fetchOptions),
            fetchWithDebug(`${API_BASE_URL}/api/temperature/stats`, fetchOptions),
            fetchWithDebug(`${API_BASE_URL}/api/temperature/history?timerange=day`, fetchOptions),
            fetchWithDebug(`${API_BASE_URL}/api/alerts/recent`, fetchOptions)
        ]);

        console.log('All data fetched successfully');
        updateCurrentTemperature(current);
        updateStats(stats);
        updateChart(history);
        updateAlerts(alerts);
    } catch (error) {
        console.error('Error in fetchData:', error);
        document.getElementById('currentTempC').textContent = 'Error';
        document.getElementById('currentTempF').textContent = 'Error';
        document.getElementById('lastUpdate').textContent = 'Failed to fetch data';
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
    document.getElementById('alertThreshold').textContent = data.alert_threshold.toFixed(1);
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
        console.log(`Changing time range to: ${range}`);
        document.querySelectorAll('.chart-controls button').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
        
        try {
            const history = await fetchWithDebug(`${API_BASE_URL}/api/temperature/history?timerange=${range}`, fetchOptions);
            updateChart(history);
        } catch (error) {
            console.error(`Error fetching history for range ${range}:`, error);
        }
    });
});

// Initial load
fetchData();

// Update every minute
setInterval(fetchData, 60000); 
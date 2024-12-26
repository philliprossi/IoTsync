let chart;
const API_BASE_URL = window.env.API_URL || 'http://localhost:8000';

const fetchOptions = {
    method: 'GET',
    mode: 'cors',
    headers: {
        'Accept': 'application/json',
        'Origin': window.location.origin
    },
    credentials: 'omit'
};

async function fetchWithDebug(url, options) {
    console.log(`Fetching ${url}...`);
    console.log('API Base URL:', API_BASE_URL);
    console.log('Full URL:', url);
    console.log('Fetch options:', JSON.stringify(options, null, 2));
    
    try {
        const response = await fetch(url, options);
        console.log(`Response status: ${response.status}`);
        console.log('Response headers:', Object.fromEntries([...response.headers]));
        
        if (!response.ok) {
            console.error(`HTTP error! status: ${response.status}`);
            console.error('Response:', await response.text());
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Data received:', JSON.stringify(data, null, 2));
        return data;
    } catch (error) {
        console.error('Detailed error information:');
        console.error('Error name:', error.name);
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
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
    
    // Convert UTC to EST
    const utcDate = new Date(data.timestamp + 'Z'); // Ensure UTC parsing by adding 'Z'
    document.getElementById('lastUpdate').textContent = utcDate.toLocaleString('en-US', {
        timeZone: 'America/New_York',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });
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
            labels: data.map(d => {
                const utcDate = new Date(d.time + 'Z'); // Ensure UTC parsing
                return utcDate.toLocaleTimeString('en-US', {
                    timeZone: 'America/New_York',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }),
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
    alertsList.innerHTML = alerts.map(alert => {
        const utcDate = new Date(alert.timestamp + 'Z'); // Ensure UTC parsing
        return `
            <div class="alert-item">
                <p>${alert.message}</p>
                <p class="alert-time">${utcDate.toLocaleString('en-US', {
                    timeZone: 'America/New_York',
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: true
                })}</p>
            </div>
        `;
    }).join('');
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
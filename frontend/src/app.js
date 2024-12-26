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
        const [current, stats] = await Promise.all([
            fetchWithDebug(`${API_BASE_URL}/api/temperature/current`, fetchOptions),
            fetchWithDebug(`${API_BASE_URL}/api/temperature/stats`, fetchOptions)
        ]);

        console.log('Current data fetched successfully');
        updateCurrentTemperature(current);
        updateStats(stats);
        
        // Add new data point to chart if it exists
        if (chart && current) {
            const time = new Date(current.timestamp + 'Z').toLocaleTimeString('en-US', {
                timeZone: 'America/New_York',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            // Only add if it's a new timestamp
            const lastTimestamp = chart.data.labels[chart.data.labels.length - 1];
            if (lastTimestamp !== time) {
                chart.data.labels.push(time);
                chart.data.datasets[0].data.push(current.temperature_f);
                
                // Remove oldest point if we have more than 24 hours of data (assuming 1-minute intervals)
                if (chart.data.labels.length > 1440) {
                    chart.data.labels.shift();
                    chart.data.datasets[0].data.shift();
                }
                
                chart.update('none'); // Update with minimal animation
            }
        }
    } catch (error) {
        console.error('Error in fetchData:', error);
        document.getElementById('currentTempC').textContent = 'Error';
        document.getElementById('currentTempF').textContent = 'Error';
        document.getElementById('lastUpdate').textContent = 'Failed to fetch data';
    }
}

async function fetchChartData(range = 'day') {
    try {
        const [history, alerts] = await Promise.all([
            fetchWithDebug(`${API_BASE_URL}/api/temperature/history?timerange=${range}`, fetchOptions),
            fetchWithDebug(`${API_BASE_URL}/api/alerts/recent`, fetchOptions)
        ]);
        
        console.log('Chart data fetched successfully');
        initializeChart(history);
        updateAlerts(alerts);
    } catch (error) {
        console.error(`Error fetching history for range ${range}:`, error);
    }
}

function initializeChart(data) {
    const ctx = document.getElementById('tempChart').getContext('2d');
    const alertThreshold = parseFloat(document.getElementById('alertThreshold').textContent);
    
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
                label: 'Temperature (°F)',
                data: data.map(d => d.temperature_f),
                borderColor: '#2563eb',
                tension: 0.4,
                pointRadius: 0,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                annotation: {
                    annotations: {
                        alertLine: {
                            type: 'line',
                            yMin: alertThreshold,
                            yMax: alertThreshold,
                            borderColor: 'rgba(255, 0, 0, 0.7)',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            label: {
                                display: true,
                                content: 'Alert Threshold',
                                position: 'end',
                                backgroundColor: 'rgba(255, 0, 0, 0.7)',
                                color: 'white',
                                padding: 4
                            }
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

function updateCurrentTemperature(data) {
    document.getElementById('currentTempC').textContent = data.temperature_c.toFixed(1);
    document.getElementById('currentTempF').textContent = data.temperature_f.toFixed(1);
    
    // Convert UTC to EST and format as YYYY-MM-DD HH:MM AM/PM
    const utcDate = new Date(data.timestamp + 'Z'); // Ensure UTC parsing by adding 'Z'
    const formattedDate = utcDate.toLocaleString('en-US', {
        timeZone: 'America/New_York',
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
    
    // Convert MM/DD/YYYY to YYYY-MM-DD format
    const [date, time] = formattedDate.split(', ');
    const [month, day, year] = date.split('/');
    const formattedString = `${year}-${month}-${day}, ${time}`;
    
    document.getElementById('lastUpdate').textContent = formattedString;
}

function updateStats(data) {
    document.getElementById('minTemp').textContent = data.min_temperature.toFixed(1);
    document.getElementById('maxTemp').textContent = data.max_temperature.toFixed(1);
    document.getElementById('alertThreshold').textContent = data.alert_threshold.toFixed(1);
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
        
        await fetchChartData(range);
    });
});

// Initial load
fetchData();
fetchChartData();

// Update current temperature and stats every minute
setInterval(fetchData, 60000);

// Only fetch full chart data when changing time ranges
// Remove the 5-minute interval for chart updates since we're updating incrementally 
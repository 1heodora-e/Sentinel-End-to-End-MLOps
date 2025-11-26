const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const audioFileInput = document.getElementById('audioFile');
const uploadArea = document.getElementById('uploadArea');
const fileName = document.getElementById('fileName');
const predictBtn = document.getElementById('predictBtn');
const resultsSection = document.getElementById('resultsSection');
const statusIcon = document.getElementById('statusIcon');
const statusTitle = document.getElementById('statusTitle');
const statusSubtitle = document.getElementById('statusSubtitle');
const confidenceFill = document.getElementById('confidenceFill');
const confidenceValue = document.getElementById('confidenceValue');
const retrainBtn = document.getElementById('retrainBtn');
const retrainFile = document.getElementById('retrainFile');
const retrainStatus = document.getElementById('retrainStatus');
const modelLoadedStatus = document.getElementById('modelLoadedStatus');
const trainingStatus = document.getElementById('trainingStatus');

// Chart instances
let dataChart, trainingChart, confidenceChart;
let confidenceHistory = []; // Store prediction confidences

// Initialize all charts and check model status
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    checkModelStatus();
    setInterval(checkModelStatus, 5000); // Check every 5 seconds
});

// 1. Initialize Charts
function initializeCharts() {
    // Dataset Distribution Chart
    const dataCtx = document.getElementById('dataChart').getContext('2d');
    dataChart = new Chart(dataCtx, {
        type: 'doughnut',
        data: {
            labels: ['Safe Audio', 'Distress Signals'],
            datasets: [{
                data: [50, 50],
                backgroundColor: ['#98FF98', '#FF6961'],
                borderColor: '#1a1f2e',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { labels: { color: 'white' } },
                title: { display: false }
            }
        }
    });

    // Training History Chart
    const trainingCtx = document.getElementById('trainingChart').getContext('2d');
    trainingChart = new Chart(trainingCtx, {
        type: 'line',
        data: {
            labels: ['Epoch 1', 'Epoch 2', 'Epoch 3', 'Epoch 4', 'Epoch 5', 'Epoch 6', 'Epoch 7', 'Epoch 8', 'Epoch 9', 'Epoch 10'],
            datasets: [
                {
                    label: 'Training Accuracy',
                    data: [0.54, 0.62, 0.72, 0.68, 0.74, 0.78, 0.80, 0.79, 0.81, 0.79],
                    borderColor: '#98FF98',
                    backgroundColor: 'rgba(152, 255, 152, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Validation Accuracy',
                    data: [0.58, 0.73, 0.70, 0.75, 0.73, 0.78, 0.75, 0.77, 0.80, 0.78],
                    borderColor: '#FFB7C5',
                    backgroundColor: 'rgba(255, 183, 197, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Training Loss',
                    data: [0.76, 0.66, 0.60, 0.65, 0.52, 0.49, 0.46, 0.44, 0.41, 0.41],
                    borderColor: '#FF6961',
                    backgroundColor: 'rgba(255, 105, 97, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { labels: { color: 'white' } },
                title: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: 'white' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    ticks: { color: 'white' },
                    grid: { drawOnChartArea: false }
                },
                x: {
                    ticks: { color: 'white' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        }
    });

    // Confidence Distribution Chart
    const confidenceCtx = document.getElementById('confidenceChart').getContext('2d');
    confidenceChart = new Chart(confidenceCtx, {
        type: 'bar',
        data: {
            labels: ['0-20%', '21-40%', '41-60%', '61-80%', '81-100%'],
            datasets: [{
                label: 'Number of Predictions',
                data: [0, 0, 0, 0, 0],
                backgroundColor: ['#FF6961', '#FFB7C5', '#E0B0FF', '#98FF98', '#98FF98'],
                borderColor: '#1a1f2e',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { labels: { color: 'white' }, display: false },
                title: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: 'white', stepSize: 1 },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: 'white' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        }
    });
}

// Check Model Status
async function checkModelStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/model/status`);
        const data = await response.json();
        
        modelLoadedStatus.textContent = data.model_loaded ? '✅ Loaded' : '❌ Not Loaded';
        modelLoadedStatus.style.color = data.model_loaded ? '#98FF98' : '#FF6961';
        
        if (data.is_training) {
            const status = data.training_status;
            trainingStatus.textContent = `${status.status}: ${status.message} (${status.progress}%)`;
            trainingStatus.style.color = '#FFB7C5';
        } else {
            trainingStatus.textContent = 'Idle';
            trainingStatus.style.color = '#98FF98';
        }
    } catch (error) {
        modelLoadedStatus.textContent = '❌ Error';
        modelLoadedStatus.style.color = '#FF6961';
        trainingStatus.textContent = 'Unable to check';
    }
}

// Update Confidence Distribution Chart
function updateConfidenceChart(confidence) {
    confidenceHistory.push(confidence);
    
    // Keep only last 50 predictions
    if (confidenceHistory.length > 50) {
        confidenceHistory.shift();
    }
    
    // Categorize confidences
    const bins = [0, 0, 0, 0, 0]; // 0-20, 21-40, 41-60, 61-80, 81-100
    confidenceHistory.forEach(conf => {
        if (conf <= 20) bins[0]++;
        else if (conf <= 40) bins[1]++;
        else if (conf <= 60) bins[2]++;
        else if (conf <= 80) bins[3]++;
        else bins[4]++;
    });
    
    confidenceChart.data.datasets[0].data = bins;
    confidenceChart.update();
}

// 2. File Upload Logic
uploadArea.addEventListener('click', () => audioFileInput.click());
audioFileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        fileName.textContent = `Selected: ${e.target.files[0].name}`;
        fileName.classList.add('show');
        predictBtn.disabled = false;
    }
});

// 3. Prediction Logic (The Brain)
predictBtn.addEventListener('click', async () => {
    const file = audioFileInput.files[0];
    if (!file) return;

    // Show Loading
    resultsSection.style.display = 'block';
    statusTitle.textContent = "Analyzing...";
    statusIcon.textContent = "⏳";
    
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        // Update UI based on Python response
        const isDanger = data.prediction === "Danger";
        
        statusTitle.textContent = isDanger ? "Danger Detected" : "Safe Environment";
        statusSubtitle.textContent = isDanger ? "High-frequency distress signal identified." : "Audio signature matches safe background levels.";
        statusIcon.textContent = isDanger ? "⚠️" : "✅";
        
        // Colors
        const color = isDanger ? "#FF6961" : "#98FF98"; // Red or Green
        statusIcon.style.color = color;
        
        // Confidence
        const conf = data.confidence;
        confidenceValue.textContent = `${conf}%`;
        confidenceFill.style.width = `${conf}%`;
        confidenceFill.style.background = color;

        // Update confidence distribution chart
        updateConfidenceChart(conf);

    } catch (error) {
        alert("Error connecting to Sentinel Brain. Is Uvicorn running?");
        console.error(error);
    }
});

// 4. Retraining Logic (The Loop)
retrainBtn.addEventListener('click', async () => {
    const file = retrainFile.files[0];
    if (!file) {
        alert("Please select a .zip file first!");
        return;
    }

    retrainStatus.textContent = "Uploading to Database...";
    retrainStatus.className = "retrain-status show info";

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/retrain`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        retrainStatus.textContent = `✅ Success: ${data.message}`;
        retrainStatus.className = "retrain-status show success";
        
        // Start polling for training status
        const pollInterval = setInterval(async () => {
            await checkModelStatus();
            const statusResponse = await fetch(`${API_BASE_URL}/model/status`);
            const statusData = await statusResponse.json();
            
            if (!statusData.is_training) {
                clearInterval(pollInterval);
                retrainStatus.textContent = "✅ Retraining completed!";
            }
        }, 2000);
        
    } catch (error) {
        retrainStatus.textContent = "❌ Upload Failed";
        retrainStatus.className = "retrain-status show error";
    }
});

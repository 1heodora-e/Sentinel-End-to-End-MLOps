// Use Hugging Face deployment URL in production, localhost for development
const API_BASE_URL = 'https://TheodoraE-sentinel1-api.hf.space';

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
const retrainUploadArea = document.getElementById('retrainUploadArea');
const retrainFileName = document.getElementById('retrainFileName');
const retrainStatus = document.getElementById('retrainStatus');
const modelLoadedStatus = document.getElementById('modelLoadedStatus');
const trainingStatus = document.getElementById('trainingStatus');
const trainingProgress = document.getElementById('trainingProgress');
const trainingProgressContainer = document.getElementById('trainingProgressContainer');
const continueTrainingBtn = document.getElementById('continueTrainingBtn');
const continueTrainingStatus = document.getElementById('continueTrainingStatus');
const useExistingDatasetBtn = document.getElementById('useExistingDatasetBtn');
const existingDatasetStatus = document.getElementById('existingDatasetStatus');
const existingDatasetInfo = document.getElementById('existingDatasetInfo');
const baseModelSelect = document.getElementById('baseModelSelect');
const epochsInput = document.getElementById('epochsInput');
const modelInfoText = document.getElementById('modelInfoText');

// Navigation Elements
const navLinks = document.querySelectorAll('.nav-link');
const pages = document.querySelectorAll('.page');

// Tab Elements
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Chart instances
let dataChart, trainingChart, confidenceChart, classDistributionChart, featureAnalysisChart;

// Load from localStorage to persist across page refreshes
let confidenceHistory = JSON.parse(localStorage.getItem('confidenceHistory') || '[]');
let totalPredictions = parseInt(localStorage.getItem('totalPredictions') || '0', 10);

// Initialize all charts and check model status
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    initializeNavigation();
    initializeTabs();
    checkModelStatus();
    loadModelInfo();
    loadExistingDatasetInfo();
    
    // Initialize stats from localStorage (without incrementing)
    updateStats(); // Pass undefined to just update display
    updateHomeStats();
    
    setInterval(checkModelStatus, 5000); // Check every 5 seconds
    setInterval(updateHomeStats, 5000); // Update home stats every 5 seconds
});

// Navigation System
function initializeNavigation() {
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetPage = link.getAttribute('data-page');
            navigateToPage(targetPage);
        });
    });
}

// Navigate to page function (can be called from buttons)
function navigateToPage(pageName) {
    // Update active nav link
    navLinks.forEach(l => {
        if (l.getAttribute('data-page') === pageName) {
            l.classList.add('active');
        } else {
            l.classList.remove('active');
        }
    });
    
    // Show target page
    pages.forEach(page => page.classList.remove('active'));
    const targetPage = document.getElementById(`${pageName}-page`);
    if (targetPage) {
        targetPage.classList.add('active');
    }
}

// Tab System
function initializeTabs() {
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Update active tab button
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show target tab content
            tabContents.forEach(tab => tab.classList.remove('active'));
            document.getElementById(`${targetTab}-tab`).classList.add('active');
        });
    });
}

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

    // Class Distribution Comparison Chart
    const classDistCtx = document.getElementById('classDistributionChart').getContext('2d');
    classDistributionChart = new Chart(classDistCtx, {
        type: 'bar',
        data: {
            labels: ['Safe', 'Danger'],
            datasets: [
                {
                    label: 'Before Balancing',
                    data: [60, 40],
                    backgroundColor: 'rgba(255, 105, 97, 0.6)',
                    borderColor: '#FF6961',
                    borderWidth: 2
                },
                {
                    label: 'After Balancing',
                    data: [50, 50],
                    backgroundColor: 'rgba(152, 255, 152, 0.6)',
                    borderColor: '#98FF98',
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: 'white' },
                    display: true
                },
                title: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { 
                        color: 'white',
                        callback: function(value) {
                            return value + '%';
                        }
                    },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: 'white' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        }
    });

    // Audio Feature Analysis Chart
    const featureCtx = document.getElementById('featureAnalysisChart').getContext('2d');
    featureAnalysisChart = new Chart(featureCtx, {
        type: 'line',
        data: {
            labels: ['0-50', '51-100', '101-150', '151-200', '201-255'],
            datasets: [
                {
                    label: 'Frequency Distribution',
                    data: [1200, 3500, 4200, 2800, 1500],
                    borderColor: '#E0B0FF',
                    backgroundColor: 'rgba(224, 176, 255, 0.2)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Amplitude Distribution',
                    data: [800, 2800, 3800, 3200, 1800],
                    borderColor: '#FFB7C5',
                    backgroundColor: 'rgba(255, 183, 197, 0.2)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: 'white' },
                    display: true
                },
                title: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: 'white' },
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
        
        // Update Model Loaded Status
        if (modelLoadedStatus) {
            modelLoadedStatus.textContent = data.model_loaded ? "Online" : "Offline";
            modelLoadedStatus.className = `status-indicator ${data.model_loaded ? "online" : "offline"}`;
        }
        
        // Update Model Accuracy (if available)
        if (data.model_accuracy !== null && data.model_accuracy !== undefined) {
            const accuracyPercent = Math.round(data.model_accuracy * 100);
            const modelAccuracyEl = document.getElementById('modelAccuracy');
            const homeAccuracyEl = document.getElementById('homeAccuracy');
            
            if (modelAccuracyEl) {
                modelAccuracyEl.textContent = `${accuracyPercent}%`;
            }
            if (homeAccuracyEl) {
                homeAccuracyEl.textContent = `${accuracyPercent}%`;
            }
        }
        
        // Update Training Status
        if (trainingStatus) {
            if (data.is_training) {
                const status = data.training_status;
                trainingStatus.textContent = status.status.charAt(0).toUpperCase() + status.status.slice(1);
                trainingStatus.className = "status-indicator loading";
                
                // Show progress if training
                if (trainingProgressContainer) {
                    trainingProgressContainer.style.display = 'flex';
                    if (trainingProgress) {
                        trainingProgress.textContent = `${status.progress}% (Epoch ${status.epoch}/${status.total_epochs})`;
                        trainingProgress.className = "status-indicator loading";
                    }
                }
            } else {
                trainingStatus.textContent = "Idle";
                trainingStatus.className = "status-indicator online";
                if (trainingProgressContainer) {
                    trainingProgressContainer.style.display = 'none';
                }
            }
        }

        // Update Training History Chart (if data is available)
        if (data.training_history && trainingChart) {
            trainingChart.data.labels = Array.from({ length: data.training_history.accuracy.length }, (_, i) => `Epoch ${i + 1}`);
            trainingChart.data.datasets[0].data = data.training_history.accuracy;
            trainingChart.data.datasets[1].data = data.training_history.val_accuracy;
            trainingChart.data.datasets[2].data = data.training_history.loss;
            trainingChart.update();
        }

    } catch (error) {
        console.error("Error fetching model status:", error);
        if (modelLoadedStatus) {
            modelLoadedStatus.textContent = "Error";
            modelLoadedStatus.className = "status-indicator offline";
        }
        if (trainingStatus) {
            trainingStatus.textContent = "Error";
            trainingStatus.className = "status-indicator offline";
        }
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
    
    if (confidenceChart) {
        confidenceChart.data.datasets[0].data = bins;
        confidenceChart.update();
    }
}

// Update Stats
function updateStats(confidence) {
    // Only increment if a valid confidence is provided (not during initialization)
    if (confidence !== undefined && confidence !== null && confidence > 0) {
        totalPredictions++;
        // Save to localStorage to persist across page refreshes
        localStorage.setItem('totalPredictions', totalPredictions.toString());
    } else {
        // Just update display with existing values (initialization)
        localStorage.setItem('totalPredictions', totalPredictions.toString());
    }
    
    const avgConfidence = confidenceHistory.length > 0 
        ? Math.round(confidenceHistory.reduce((a, b) => a + b, 0) / confidenceHistory.length)
        : 0;
    
    // Save confidence history to localStorage
    localStorage.setItem('confidenceHistory', JSON.stringify(confidenceHistory));
    
    const totalPredictionsEl = document.getElementById('totalPredictions');
    const avgConfidenceEl = document.getElementById('avgConfidence');
    
    if (totalPredictionsEl) totalPredictionsEl.textContent = totalPredictions.toLocaleString();
    if (avgConfidenceEl) avgConfidenceEl.textContent = `${avgConfidence}%`;
    
    // Update home page stats
    updateHomeStats();
}

// Update Home Page Stats
function updateHomeStats() {
    const homeTotalEl = document.getElementById('homeTotalPredictions');
    const homeAccuracyEl = document.getElementById('homeAccuracy');
    const homeConfidenceEl = document.getElementById('homeAvgConfidence');
    
    const avgConfidence = confidenceHistory.length > 0 
        ? Math.round(confidenceHistory.reduce((a, b) => a + b, 0) / confidenceHistory.length)
        : 0;
    
    if (homeTotalEl) homeTotalEl.textContent = totalPredictions.toLocaleString();
    if (homeConfidenceEl) homeConfidenceEl.textContent = `${avgConfidence}%`;
    // Model accuracy is updated by checkModelStatus() from API
}

// 2. File Upload Logic (Predict Page)
const fileFormatError = document.getElementById('fileFormatError');

function validateAudioFile(file) {
    const allowedExtensions = ['.wav', '.mp3'];
    const fileName = file.name.toLowerCase();
    const isValid = allowedExtensions.some(ext => fileName.endsWith(ext));
    
    if (!isValid) {
        fileFormatError.textContent = `❌ Unsupported file format. Please upload only WAV or MP3 files.`;
        fileFormatError.style.display = 'block';
        fileFormatError.style.color = '#FF6961';
        fileFormatError.style.marginTop = '10px';
        fileFormatError.style.padding = '10px';
        fileFormatError.style.borderRadius = '8px';
        fileFormatError.style.backgroundColor = 'rgba(255, 105, 97, 0.1)';
        return false;
    }
    
    fileFormatError.style.display = 'none';
    return true;
}

uploadArea.addEventListener('click', () => audioFileInput.click());
audioFileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        if (validateAudioFile(file)) {
            fileName.textContent = `Selected: ${file.name}`;
            fileName.classList.add('show');
            predictBtn.disabled = false;
        } else {
            // Clear the file input
            audioFileInput.value = '';
            fileName.textContent = '';
            fileName.classList.remove('show');
            predictBtn.disabled = true;
        }
    }
});

// Drag and drop for predict
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (validateAudioFile(file)) {
            // Create a new FileList-like object for the input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            audioFileInput.files = dataTransfer.files;
            
            fileName.textContent = `Selected: ${file.name}`;
        fileName.classList.add('show');
        predictBtn.disabled = false;
        } else {
            // Clear any previous selection
            audioFileInput.value = '';
            fileName.textContent = '';
            fileName.classList.remove('show');
            predictBtn.disabled = true;
        }
    }
});

// 3. Prediction Logic
predictBtn.addEventListener('click', async () => {
    const file = audioFileInput.files[0];
    if (!file) return;
    
    // Validate file format before sending
    if (!validateAudioFile(file)) {
        return;
    }

    // Show Loading
    resultsSection.style.display = 'block';
    statusTitle.textContent = "Analyzing...";
    statusIcon.textContent = "⏳";
    statusIcon.className = "status-icon";
    
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            body: formData
        });

        // Parse response once
        const data = await response.json();
        
        // Debug: Log the response
        console.log("API Response:", data);
        
        // Check if response is OK
        if (!response.ok) {
            throw new Error(data.error || data.detail || `HTTP error! status: ${response.status}`);
        }
        
        // Check if response has error
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Validate required fields
        if (!data.prediction || data.confidence === undefined) {
            console.error("Invalid response structure:", data);
            throw new Error("Invalid response from server. Missing prediction or confidence.");
        }
        
        // Update UI based on Python response
        const isDanger = data.prediction === "Danger";
        
        statusTitle.textContent = isDanger ? "Danger Detected" : "Safe Environment";
        statusSubtitle.textContent = isDanger ? "High-frequency distress signal identified." : "Audio signature matches safe background levels.";
        statusIcon.textContent = isDanger ? "⚠️" : "✅";
        statusIcon.className = `status-icon ${isDanger ? 'danger' : 'safe'}`;
        
        // Confidence - ensure it's a valid number
        const conf = data.confidence !== undefined && data.confidence !== null 
            ? parseFloat(data.confidence) 
            : 0;
        
        if (isNaN(conf)) {
            console.error("Invalid confidence value:", data.confidence);
            confidenceValue.textContent = "N/A";
            confidenceFill.style.width = "0%";
        } else {
            confidenceValue.textContent = `${Math.round(conf)}%`;
            confidenceFill.style.width = `${Math.round(conf)}%`;
            confidenceFill.className = `confidence-fill ${isDanger ? 'danger' : 'safe'}`;

            // Update confidence distribution chart and stats
            updateConfidenceChart(Math.round(conf));
            updateStats(Math.round(conf));
        }

    } catch (error) {
        console.error("Prediction error:", error);
        console.error("Response data:", error.response || "No response data");
        alert(`Error: ${error.message || "Failed to connect to API. Please check if the backend is running."}`);
        
        // Reset UI on error
        statusTitle.textContent = "Error";
        statusSubtitle.textContent = "Failed to analyze audio file.";
        statusIcon.textContent = "❌";
        statusIcon.className = "status-icon error";
        confidenceValue.textContent = "N/A";
        confidenceFill.style.width = "0%";
    }
});

// 4. Retraining Logic
retrainUploadArea.addEventListener('click', () => retrainFile.click());

retrainFile.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        retrainFileName.textContent = `Selected: ${e.target.files[0].name}`;
        retrainFileName.classList.add('show');
        retrainBtn.disabled = false;
    }
});

// Drag and drop for retrain
retrainUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    retrainUploadArea.classList.add('dragover');
});

retrainUploadArea.addEventListener('dragleave', () => {
    retrainUploadArea.classList.remove('dragover');
});

retrainUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    retrainUploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].name.endsWith('.zip')) {
        retrainFile.files = files;
        retrainFileName.textContent = `Selected: ${files[0].name}`;
        retrainFileName.classList.add('show');
        retrainBtn.disabled = false;
    }
});

retrainBtn.addEventListener('click', async () => {
    const file = retrainFile.files[0];
    if (!file) {
        alert("Please select a .zip file first!");
        return;
    }

    retrainBtn.disabled = true;
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
        retrainBtn.disabled = false;
        
        // Start polling for training status
        const pollInterval = setInterval(async () => {
            await checkModelStatus();
            try {
                const statusResponse = await fetch(`${API_BASE_URL}/model/status`);
                const statusData = await statusResponse.json();
                
                if (!statusData.is_training) {
                    clearInterval(pollInterval);
                    if (statusData.training_status && statusData.training_status.status === 'error') {
                        retrainStatus.textContent = `❌ Retraining Failed: ${statusData.training_status.message}`;
                        retrainStatus.className = "retrain-status show error";
                    } else {
                        retrainStatus.textContent = "✅ Retraining completed!";
                        retrainStatus.className = "retrain-status show success";
                    }
                }
            } catch (error) {
                console.error("Error checking training status:", error);
            }
        }, 2000);
        
    } catch (error) {
        retrainStatus.textContent = "❌ Upload Failed: " + error.message;
        retrainStatus.className = "retrain-status show error";
        retrainBtn.disabled = false;
    }
});

// Load Model Information
async function loadModelInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/model/status`);
        const data = await response.json();
        
        if (data.model_loaded) {
            const accuracy = data.model_accuracy !== null && data.model_accuracy !== undefined
                ? `${Math.round(data.model_accuracy * 100)}%`
                : "N/A";
            modelInfoText.textContent = `Model loaded. Accuracy: ${accuracy}`;
        } else {
            modelInfoText.textContent = "Model not loaded. Please wait...";
        }
    } catch (error) {
        console.error("Error loading model info:", error);
        modelInfoText.textContent = "Unable to load model information.";
    }
}

// Load Existing Dataset Information
async function loadExistingDatasetInfo() {
    try {
        // We'll fetch this from the backend or calculate from available data
        // For now, we'll show a placeholder that gets updated when the page loads
        existingDatasetInfo.textContent = "Checking available datasets...";
        
        // Try to get dataset info from backend (we can add an endpoint for this later)
        // For now, we'll use a default message
        existingDatasetInfo.textContent = "Click 'Use This Dataset' to retrain with existing data";
    } catch (error) {
        console.error("Error loading dataset info:", error);
        existingDatasetInfo.textContent = "Unable to load dataset information.";
    }
}

// Continue Training Button Event Listener
if (continueTrainingBtn) {
    continueTrainingBtn.addEventListener('click', async () => {
        const selectedModel = baseModelSelect.value;
        const epochs = parseInt(epochsInput.value) || 3;
        
        if (!selectedModel) {
            alert("Please select a model first!");
            return;
        }
        
        if (epochs < 1 || epochs > 50) {
            alert("Epochs must be between 1 and 50!");
            return;
        }
        
        continueTrainingBtn.disabled = true;
        continueTrainingStatus.textContent = "Starting training...";
        continueTrainingStatus.className = "retrain-status show info";
        
        try {
            const response = await fetch(`${API_BASE_URL}/continue-training?epochs=${epochs}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            continueTrainingStatus.textContent = `✅ ${data.message}`;
            continueTrainingStatus.className = "retrain-status show success";
            
            // Start polling for training status
            const pollInterval = setInterval(async () => {
                await checkModelStatus();
                await loadModelInfo();
                
                try {
                    const statusResponse = await fetch(`${API_BASE_URL}/model/status`);
                    const statusData = await statusResponse.json();
                    
                    if (!statusData.is_training) {
                        clearInterval(pollInterval);
                        continueTrainingBtn.disabled = false;
                        
                        if (statusData.training_status && statusData.training_status.status === 'error') {
                            continueTrainingStatus.textContent = `❌ Training Failed: ${statusData.training_status.message}`;
                            continueTrainingStatus.className = "retrain-status show error";
                        } else {
                            continueTrainingStatus.textContent = "✅ Training completed!";
                            continueTrainingStatus.className = "retrain-status show success";
                        }
                    } else {
                        // Update status during training
                        const progress = statusData.training_status.progress || 0;
                        const epoch = statusData.training_status.epoch || 0;
                        const totalEpochs = statusData.training_status.total_epochs || epochs;
                        continueTrainingStatus.textContent = `Training in progress... ${progress}% (Epoch ${epoch}/${totalEpochs})`;
                        continueTrainingStatus.className = "retrain-status show info";
                    }
                } catch (error) {
                    console.error("Error checking training status:", error);
                }
            }, 2000);
            
        } catch (error) {
            continueTrainingStatus.textContent = `❌ Training Failed: ${error.message}`;
            continueTrainingStatus.className = "retrain-status show error";
            continueTrainingBtn.disabled = false;
        }
    });
}

// Use Existing Dataset Button Event Listener
if (useExistingDatasetBtn) {
    useExistingDatasetBtn.addEventListener('click', async () => {
        useExistingDatasetBtn.disabled = true;
        existingDatasetStatus.textContent = "Starting retraining with existing datasets...";
        existingDatasetStatus.className = "retrain-status show info";
        
        try {
            const response = await fetch(`${API_BASE_URL}/retrain-existing`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            existingDatasetStatus.textContent = `✅ ${data.message}`;
            existingDatasetStatus.className = "retrain-status show success";
            
            // Update dataset info display
            if (data.safe_count !== undefined && data.danger_count !== undefined) {
                existingDatasetInfo.textContent = `${data.data_files} files (${data.safe_count} safe, ${data.danger_count} danger)`;
            }
            
            // Start polling for training status
            const pollInterval = setInterval(async () => {
                await checkModelStatus();
                await loadModelInfo();
                
                try {
                    const statusResponse = await fetch(`${API_BASE_URL}/model/status`);
                    const statusData = await statusResponse.json();
                    
                    if (!statusData.is_training) {
                        clearInterval(pollInterval);
                        useExistingDatasetBtn.disabled = false;
                        
                        if (statusData.training_status && statusData.training_status.status === 'error') {
                            existingDatasetStatus.textContent = `❌ Training Failed: ${statusData.training_status.message}`;
                            existingDatasetStatus.className = "retrain-status show error";
                        } else {
                            existingDatasetStatus.textContent = "✅ Retraining completed!";
                            existingDatasetStatus.className = "retrain-status show success";
                        }
                    } else {
                        // Update status during training
                        const progress = statusData.training_status.progress || 0;
                        const epoch = statusData.training_status.epoch || 0;
                        const totalEpochs = statusData.training_status.total_epochs || 3;
                        existingDatasetStatus.textContent = `Training in progress... ${progress}% (Epoch ${epoch}/${totalEpochs})`;
                        existingDatasetStatus.className = "retrain-status show info";
                    }
                } catch (error) {
                    console.error("Error checking training status:", error);
                }
            }, 2000);
            
        } catch (error) {
            existingDatasetStatus.textContent = `❌ Retraining Failed: ${error.message}`;
            existingDatasetStatus.className = "retrain-status show error";
            useExistingDatasetBtn.disabled = false;
        }
    });
}

// Update model info when model select changes
if (baseModelSelect) {
    baseModelSelect.addEventListener('change', () => {
        loadModelInfo();
    });
}

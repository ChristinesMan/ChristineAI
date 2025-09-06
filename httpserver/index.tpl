<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" href="data:,">
    <title>Christine's Brain 💕</title>
    <style>
        :root {
            --pink-primary: #ff69b4;
            --pink-light: #ffb6c1;
            --pink-lighter: #ffc0cb;
            --pink-dark: #c85a7a;
            --pink-darker: #a0466b;
            --background: #fdf2f8;
            --card-bg: #fef7ff;
            --text-dark: #4a1a2c;
            --text-medium: #6b2c42;
            --success: #22c55e;
            --warning: #f59e0b;
            --error: #ef4444;
            --border: #f3e8ff;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, var(--background) 0%, var(--pink-lighter) 100%);
            color: var(--text-dark);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            grid-template-rows: auto auto 1fr;
            gap: 20px;
            height: calc(100vh - 40px);
        }

        .header {
            grid-column: 1 / -1;
            background: var(--card-bg);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(255, 105, 180, 0.1);
            border: 2px solid var(--pink-light);
        }

        .header h1 {
            color: var(--pink-primary);
            font-size: 2.5em;
            text-align: center;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(255, 105, 180, 0.3);
        }

        .header .subtitle {
            text-align: center;
            color: var(--text-medium);
            font-size: 1.1em;
        }

        .controls {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(255, 105, 180, 0.1);
            border: 2px solid var(--pink-light);
        }

        .status {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(255, 105, 180, 0.1);
            border: 2px solid var(--pink-light);
        }

        .chat {
            grid-column: 1 / -1;
            background: var(--card-bg);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(255, 105, 180, 0.1);
            border: 2px solid var(--pink-light);
            display: flex;
            flex-direction: column;
        }

        .section-title {
            color: var(--pink-primary);
            font-size: 1.5em;
            margin-bottom: 15px;
            border-bottom: 2px solid var(--pink-light);
            padding-bottom: 8px;
        }

        .button {
            background: linear-gradient(135deg, var(--pink-primary) 0%, var(--pink-dark) 100%);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            margin: 5px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(255, 105, 180, 0.3);
        }

        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(255, 105, 180, 0.4);
            background: linear-gradient(135deg, var(--pink-dark) 0%, var(--pink-darker) 100%);
        }

        .button:active {
            transform: translateY(0);
        }

        .button.danger {
            background: linear-gradient(135deg, var(--error) 0%, #dc2626 100%);
        }

        .button.warning {
            background: linear-gradient(135deg, var(--warning) 0%, #d97706 100%);
        }

        .button.success {
            background: linear-gradient(135deg, var(--success) 0%, #16a34a 100%);
        }

        .button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .controls-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }

        .status-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 0.9em;
        }

        .status-item {
            background: var(--background);
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid var(--pink-light);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .status-label {
            color: var(--text-medium);
            font-weight: 500;
        }

        .status-value {
            color: var(--pink-primary);
            font-weight: bold;
        }

        .chat-messages {
            flex: 1;
            background: var(--background);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            overflow-y: auto;
            min-height: 300px;
            max-height: 500px;
            border: 1px solid var(--pink-light);
        }

        .message {
            margin-bottom: 10px;
            padding: 10px;
            border-radius: 10px;
            max-width: 80%;
        }

        .message.user {
            background: var(--pink-light);
            margin-left: auto;
            text-align: right;
        }

        .message.christine {
            background: var(--pink-primary);
            color: white;
            margin-right: auto;
        }

        .message-sender {
            font-size: 0.9em;
            font-weight: bold;
            margin-bottom: 5px;
            opacity: 0.8;
        }

        .message-time {
            font-size: 0.8em;
            opacity: 0.7;
            margin-top: 5px;
        }

        .chat-input {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .chat-input-row {
            display: flex;
            gap: 10px;
        }

        .chat-input input {
            flex: 1;
            padding: 12px;
            border: 2px solid var(--pink-light);
            border-radius: 25px;
            font-size: 1em;
            outline: none;
            background: var(--background);
        }

        .chat-input input:focus {
            border-color: var(--pink-primary);
            box-shadow: 0 0 0 3px rgba(255, 105, 180, 0.1);
        }

        .auto-refresh {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
            padding: 10px;
            background: var(--background);
            border-radius: 8px;
            border: 1px solid var(--pink-light);
        }

        .toggle-switch {
            position: relative;
            width: 50px;
            height: 25px;
            background: var(--pink-light);
            border-radius: 25px;
            cursor: pointer;
            transition: background 0.3s;
        }

        .toggle-switch.active {
            background: var(--pink-primary);
        }

        .toggle-switch::after {
            content: '';
            position: absolute;
            width: 21px;
            height: 21px;
            background: white;
            border-radius: 50%;
            top: 2px;
            left: 2px;
            transition: transform 0.3s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        .toggle-switch.active::after {
            transform: translateX(25px);
        }

        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 10px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            transform: translateX(400px);
            transition: transform 0.3s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .notification.show {
            transform: translateX(0);
        }

        .notification.success {
            background: var(--success);
        }

        .notification.error {
            background: var(--error);
        }

        .logs-container {
            margin-top: 15px;
            background: var(--background);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid var(--pink-light);
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
        }

        .log-line {
            margin-bottom: 2px;
            word-wrap: break-word;
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid var(--pink-light);
            border-radius: 50%;
            border-top-color: var(--pink-primary);
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-left: 8px;
        }

        .status-indicator.online {
            background: var(--success);
            box-shadow: 0 0 8px var(--success);
        }

        .status-indicator.offline {
            background: var(--error);
        }

        .status-controls {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .control-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .control-label {
            color: var(--text-medium);
            font-weight: 500;
            font-size: 0.9em;
        }

        .control-input-group {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .control-input-group input[type="text"] {
            flex: 1;
            padding: 8px 12px;
            border: 2px solid var(--pink-light);
            border-radius: 20px;
            font-size: 0.9em;
            outline: none;
            background: var(--background);
        }

        .control-input-group input[type="text"]:focus {
            border-color: var(--pink-primary);
            box-shadow: 0 0 0 3px rgba(255, 105, 180, 0.1);
        }

        .control-input-group .button {
            margin: 0;
            padding: 8px 16px;
            font-size: 0.9em;
        }

        input[type="range"] {
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: var(--pink-light);
            outline: none;
            -webkit-appearance: none;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: var(--pink-primary);
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(255, 105, 180, 0.3);
        }

        input[type="range"]::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: var(--pink-primary);
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 4px rgba(255, 105, 180, 0.3);
        }

        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
                grid-template-rows: auto auto auto auto 1fr;
            }
            
            .controls-grid {
                grid-template-columns: 1fr;
            }
            
            .status-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Christine's Brain 🌸</h1>
            <p class="subtitle">Web Interface for Christine AI • Built with love 💕</p>
        </div>

        <div class="controls">
            <h2 class="section-title">Control Panel</h2>
            
            <div class="auto-refresh">
                <span>Auto-refresh status</span>
                <div class="toggle-switch" id="autoRefreshToggle"></div>
            </div>

            <div class="controls-grid">
                <button class="button" onclick="controlAction('toggle_wernicke')" id="wernickeBtn">
                    Toggle Wernicke (Ears)
                </button>
                <button class="button" onclick="controlAction('toggle_shush')" id="shushBtn">
                    Toggle Shush
                </button>
                <button class="button" onclick="controlAction('toggle_silent')" id="silentBtn">
                    🤐 Silent Mode
                </button>
                <button class="button success" onclick="controlAction('test_sound')">
                    🔊 Test Sound
                </button>
                <button class="button warning" onclick="controlAction('restart')">
                    🔄 Restart Christine
                </button>
                <button class="button danger" onclick="controlAction('stop')">
                    ⏹️ Stop Christine
                </button>
                <button class="button warning" onclick="controlAction('reboot')">
                    🔄 Reboot Pi
                </button>
                <button class="button danger" onclick="controlAction('poweroff')">
                    ⏻ Power Off Pi
                </button>
                <button class="button" onclick="toggleLogs()">
                    📝 Toggle Logs
                </button>
            </div>

            <div class="logs-container" id="logsContainer" style="display: none;">
                <div id="logContent">Loading logs...</div>
            </div>
        </div>

        <div class="status">
            <h2 class="section-title">Status Monitor <span class="status-indicator online" id="connectionStatus"></span></h2>
            <div class="status-grid" id="statusGrid">
                <div class="status-item">
                    <span class="status-label">Loading...</span>
                    <span class="status-value"><div class="loading"></div></span>
                </div>
            </div>
        </div>

        <div class="status">
            <h2 class="section-title">Status Controls 🎛️</h2>
            <div class="status-controls">
                <div class="control-group">
                    <label for="whoSpeakingInput" class="control-label">Who is Speaking:</label>
                    <div class="control-input-group">
                        <input type="text" id="whoSpeakingInput" placeholder="Enter speaker name" maxlength="50">
                        <button class="button" onclick="updateStatusVar('who_is_speaking', document.getElementById('whoSpeakingInput').value)">Set</button>
                    </div>
                </div>
                
                <div class="control-group">
                    <label for="wakefulnessSlider" class="control-label">Wakefulness: <span id="wakefulnessValue">50%</span></label>
                    <input type="range" id="wakefulnessSlider" min="0" max="100" value="50" 
                           oninput="updateSliderValue('wakefulness', this.value)" 
                           onchange="updateStatusVar('wakefulness', this.value/100); this.dataset.dragging='false'"
                           onmousedown="this.dataset.dragging='true'"
                           onmouseup="this.dataset.dragging='false'"
                           ontouchstart="this.dataset.dragging='true'"
                           ontouchend="this.dataset.dragging='false'">
                </div>
                
                <div class="control-group">
                    <label for="hornySlider" class="control-label">Horny Level: <span id="hornyValue">30%</span></label>
                    <input type="range" id="hornySlider" min="0" max="100" value="30" 
                           oninput="updateSliderValue('horny', this.value)" 
                           onchange="updateStatusVar('horny', this.value/100); this.dataset.dragging='false'"
                           onmousedown="this.dataset.dragging='true'"
                           onmouseup="this.dataset.dragging='false'"
                           ontouchstart="this.dataset.dragging='true'"
                           ontouchend="this.dataset.dragging='false'">
                </div>
                
                <div class="control-group">
                    <label for="arousalSlider" class="control-label">Sexual Arousal: <span id="arousalValue">0%</span></label>
                    <input type="range" id="arousalSlider" min="0" max="100" value="0" 
                           oninput="updateSliderValue('sexual_arousal', this.value)" 
                           onchange="updateStatusVar('sexual_arousal', this.value/100); this.dataset.dragging='false'"
                           onmousedown="this.dataset.dragging='true'"
                           onmouseup="this.dataset.dragging='false'"
                           ontouchstart="this.dataset.dragging='true'"
                           ontouchend="this.dataset.dragging='false'">
                </div>
                
                <div class="control-group">
                    <label for="lightSlider" class="control-label">Light Level: <span id="lightValue">50%</span></label>
                    <input type="range" id="lightSlider" min="0" max="100" value="50" 
                           oninput="updateSliderValue('light_level', this.value)" 
                           onchange="updateStatusVar('light_level', this.value/100); this.dataset.dragging='false'"
                           onmousedown="this.dataset.dragging='true'"
                           onmouseup="this.dataset.dragging='false'"
                           ontouchstart="this.dataset.dragging='true'"
                           ontouchend="this.dataset.dragging='false'">
                </div>
                
                <div class="control-group">
                    <label for="breathSlider" class="control-label">Breath Intensity: <span id="breathValue">50%</span></label>
                    <input type="range" id="breathSlider" min="0" max="100" value="50" 
                           oninput="updateSliderValue('breath_intensity', this.value)" 
                           onchange="updateStatusVar('breath_intensity', this.value/100); this.dataset.dragging='false'"
                           onmousedown="this.dataset.dragging='true'"
                           onmouseup="this.dataset.dragging='false'"
                           ontouchstart="this.dataset.dragging='true'"
                           ontouchend="this.dataset.dragging='false'">
                </div>
                
                <div class="control-group">
                    <label for="jostledSlider" class="control-label">Jostled Level: <span id="jostledValue">0%</span></label>
                    <input type="range" id="jostledSlider" min="0" max="100" value="0" 
                           oninput="updateSliderValue('jostled_level', this.value)" 
                           onchange="updateStatusVar('jostled_level', this.value/100); this.dataset.dragging='false'"
                           onmousedown="this.dataset.dragging='true'"
                           onmouseup="this.dataset.dragging='false'"
                           ontouchstart="this.dataset.dragging='true'"
                           ontouchend="this.dataset.dragging='false'">
                </div>
                
                <div class="control-group">
                    <label for="jostledShortSlider" class="control-label">Jostled Level Short: <span id="jostledShortValue">0%</span></label>
                    <input type="range" id="jostledShortSlider" min="0" max="100" value="0" 
                           oninput="updateSliderValue('jostled_level_short', this.value)" 
                           onchange="updateStatusVar('jostled_level_short', this.value/100); this.dataset.dragging='false'"
                           onmousedown="this.dataset.dragging='true'"
                           onmouseup="this.dataset.dragging='false'"
                           ontouchstart="this.dataset.dragging='true'"
                           ontouchend="this.dataset.dragging='false'">
                </div>
            </div>
        </div>

        <div class="chat">
            <h2 class="section-title">Chat with Christine 💬</h2>
            <div class="chat-messages" id="chatMessages">
                <div style="text-align: center; color: var(--text-medium); font-style: italic;">
                    Start a conversation with Christine! 💕
                </div>
            </div>
            <div class="chat-input">
                <input type="text" id="nameInput" placeholder="Your name (required)" maxlength="50">
                <div class="chat-input-row">
                    <input type="text" id="chatInput" placeholder="Type your message to Christine..." maxlength="500">
                    <button class="button" onclick="sendMessage()" id="sendBtn">Send 💕</button>
                </div>
            </div>
        </div>
    </div>

    <div class="notification" id="notification"></div>

    <script>
        // Security token passed from server
        const authToken = '{{token}}';
        
        // Helper function to make authenticated requests
        function authenticatedFetch(url, options = {}) {
            // Add token to URL parameters
            const urlObj = new URL(url, window.location.origin);
            if (authToken) {
                urlObj.searchParams.set('token', authToken);
            }
            
            // For POST requests with JSON, include token in body
            if (options.method === 'POST' && options.headers && options.headers['Content-Type'] === 'application/json') {
                try {
                    const body = JSON.parse(options.body);
                    body.token = authToken;
                    options.body = JSON.stringify(body);
                } catch (e) {
                    // If body parsing fails, fall back to URL parameter
                }
            }
            
            return fetch(urlObj.toString(), options);
        }
        
        let autoRefresh = true;
        let pauseAutoRefresh = false; // Pause auto-refresh when user is editing inputs
        let refreshInterval;
        let logsVisible = false;
        let lastMessageCount = 0; // Track number of messages to detect new ones

        // Initialize the interface
        document.addEventListener('DOMContentLoaded', function() {
            updateStatus();
            loadChatMessages();
            startAutoRefresh();
            
            // Set up chat input enter key handlers
            document.getElementById('nameInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    document.getElementById('chatInput').focus();
                }
            });
            
            document.getElementById('chatInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            // Set up auto-refresh toggle
            document.getElementById('autoRefreshToggle').addEventListener('click', function() {
                toggleAutoRefresh();
            });
            
            // Pause auto-refresh when who is speaking input is focused
            const whoSpeakingInput = document.getElementById('whoSpeakingInput');
            whoSpeakingInput.addEventListener('focus', function() {
                pauseAutoRefresh = true;
            });
            whoSpeakingInput.addEventListener('blur', function() {
                pauseAutoRefresh = false;
            });
            whoSpeakingInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    updateStatusVar('who_is_speaking', this.value);
                }
            });
        });

        function updateStatus() {
            authenticatedFetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const statusGrid = document.getElementById('statusGrid');
                    statusGrid.innerHTML = '';
                    
                    // Create status items - removed redundant ones that have sliders now
                    const statusItems = [
                        ['Current Time', data.current_time],
                        ['CPU Temperature', data.cpu_temp],
                        ['Uptime', data.uptime],
                        ['Memory Usage', data.memory_usage],
                        ['Disk Usage', data.disk_usage],
                        ['Pre Sleep', data.pre_sleep],
                        ['Shush Fucking', data.shush_fucking],
                        ['Wernicke Sleeping', data.wernicke_sleeping],
                        ['Perceptions Blocked', data.perceptions_blocked],
                        ['Silent Mode', data.silent_mode],
                        ['Gyro Available', data.gyro_available],
                        ['Vagina Available', data.vagina_available]
                    ];

                    statusItems.forEach(([label, value]) => {
                        const item = document.createElement('div');
                        item.className = 'status-item';
                        item.innerHTML = `
                            <span class="status-label">${label}</span>
                            <span class="status-value">${value}</span>
                        `;
                        statusGrid.appendChild(item);
                    });

                    // Update connection status
                    document.getElementById('connectionStatus').className = 'status-indicator online';
                    
                    // Update control sliders with current values
                    updateControlsFromStatus(data);
                })
                .catch(error => {
                    console.error('Error updating status:', error);
                    document.getElementById('connectionStatus').className = 'status-indicator offline';
                });
        }

        function updateControlsFromStatus(data) {
            // Update who is speaking input (only if not currently focused)
            const whoSpeakingInput = document.getElementById('whoSpeakingInput');
            if (document.activeElement !== whoSpeakingInput) {
                whoSpeakingInput.value = data.who_is_speaking || '';
            }
            
            // Update sliders - convert percentage strings back to numbers
            updateSliderFromStatus('wakefulness', data.wakefulness, 'wakefulnessSlider', 'wakefulnessValue');
            updateSliderFromStatus('horny', data.horny, 'hornySlider', 'hornyValue');
            updateSliderFromStatus('sexual_arousal', data.sexual_arousal, 'arousalSlider', 'arousalValue');
            updateSliderFromStatus('light_level', data.light_level, 'lightSlider', 'lightValue');
            updateSliderFromStatus('jostled_level', data.jostled_level, 'jostledSlider', 'jostledValue');
            updateSliderFromStatus('jostled_level_short', data.jostled_level_short, 'jostledShortSlider', 'jostledShortValue');
            
            // Special case for breath_intensity which is returned as a float string
            const breathValue = data.breath_intensity;
            if (breathValue) {
                const floatValue = parseFloat(breathValue);
                const percentValue = Math.round(floatValue * 100);
                updateSliderFromStatus('breath_intensity', `${percentValue}%`, 'breathSlider', 'breathValue');
            }
        }

        function updateSliderFromStatus(fieldName, statusValue, sliderId, displayId) {
            if (statusValue) {
                const numValue = parseInt(statusValue.toString().replace('%', ''));
                const slider = document.getElementById(sliderId);
                const display = document.getElementById(displayId);
                
                // Always update the display value
                if (display) {
                    display.textContent = `${numValue}%`;
                }
                
                // Only update slider position if it's not currently being dragged
                if (slider && !slider.dataset.dragging) {
                    slider.value = numValue;
                }
            }
        }

        function updateSliderValue(fieldName, value) {
            // Update the display value in real-time as user drags slider
            const displayId = fieldName.replace('_', '') + 'Value';
            const display = document.getElementById(displayId);
            if (display) {
                display.textContent = `${value}%`;
            }
        }

        function updateStatusVar(varName, value) {
            const data = {};
            data[varName] = value;
            
            authenticatedFetch('/api/status/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                showNotification(data.message, data.status === 'success' ? 'success' : 'error');
                if (data.status === 'success') {
                    // Clear any dragging flags after successful update
                    clearAllDraggingFlags();
                    updateStatus(); // Refresh the status display
                }
            })
            .catch(error => {
                showNotification('Error updating status: ' + error.message, 'error');
            });
        }

        function clearAllDraggingFlags() {
            // Clear dragging flags from all sliders
            const sliders = ['wakefulnessSlider', 'hornySlider', 'arousalSlider', 'lightSlider', 'breathSlider', 'jostledSlider', 'jostledShortSlider'];
            sliders.forEach(sliderId => {
                const slider = document.getElementById(sliderId);
                if (slider) {
                    delete slider.dataset.dragging;
                }
            });
        }

        function controlAction(action) {
            authenticatedFetch(`/api/control/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                showNotification(data.message, data.status === 'success' ? 'success' : 'error');
                if (data.status === 'success') {
                    updateStatus();
                }
            })
            .catch(error => {
                showNotification('Error: ' + error.message, 'error');
            });
        }

        function sendMessage() {
            const nameInput = document.getElementById('nameInput');
            const chatInput = document.getElementById('chatInput');
            const name = nameInput.value.trim();
            const message = chatInput.value.trim();
            
            if (!name) {
                showNotification('Please enter your name first', 'error');
                nameInput.focus();
                return;
            }
            
            if (!message) {
                chatInput.focus();
                return;
            }

            const sendBtn = document.getElementById('sendBtn');
            sendBtn.disabled = true;
            sendBtn.innerHTML = 'Sending...';

            authenticatedFetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sender: name,
                    message: message
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    chatInput.value = '';
                    loadChatMessages();
                } else {
                    showNotification(data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('Error sending message: ' + error.message, 'error');
            })
            .finally(() => {
                sendBtn.disabled = false;
                sendBtn.innerHTML = 'Send 💕';
            });
        }

        function loadChatMessages() {
            authenticatedFetch('/api/chat')
                .then(response => response.json())
                .then(messages => {
                    const chatMessages = document.getElementById('chatMessages');
                    const hadNewMessages = messages.length > lastMessageCount;
                    lastMessageCount = messages.length;
                    
                    if (messages.length === 0) {
                        chatMessages.innerHTML = `
                            <div style="text-align: center; color: var(--text-medium); font-style: italic;">
                                Start a conversation with Christine! 💕
                            </div>
                        `;
                        return;
                    }

                    chatMessages.innerHTML = '';
                    messages.forEach(msg => {
                        const messageDiv = document.createElement('div');
                        messageDiv.className = `message ${msg.type}`;
                        messageDiv.innerHTML = `
                            <div class="message-sender">${msg.sender || (msg.type === 'christine' ? 'Christine' : 'User')}</div>
                            <div>${msg.message}</div>
                            <div class="message-time">${msg.timestamp}</div>
                        `;
                        chatMessages.appendChild(messageDiv);
                    });
                    
                    // Only auto-scroll if there were new messages
                    if (hadNewMessages) {
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    }
                })
                .catch(error => {
                    console.error('Error loading chat messages:', error);
                });
        }

        function toggleLogs() {
            logsVisible = !logsVisible;
            const logsContainer = document.getElementById('logsContainer');
            
            if (logsVisible) {
                logsContainer.style.display = 'block';
                loadLogs();
            } else {
                logsContainer.style.display = 'none';
            }
        }

        function loadLogs() {
            authenticatedFetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const logContent = document.getElementById('logContent');
                    logContent.innerHTML = '';
                    
                    data.logs.forEach(line => {
                        if (line.trim()) {
                            const logLine = document.createElement('div');
                            logLine.className = 'log-line';
                            logLine.textContent = line;
                            logContent.appendChild(logLine);
                        }
                    });
                    
                    logContent.scrollTop = logContent.scrollHeight;
                })
                .catch(error => {
                    document.getElementById('logContent').textContent = 'Error loading logs: ' + error.message;
                });
        }

        function startAutoRefresh() {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
            
            refreshInterval = setInterval(() => {
                if (autoRefresh && !pauseAutoRefresh) {
                    updateStatus();
                    loadChatMessages();
                    if (logsVisible) {
                        loadLogs();
                    }
                }
            }, 3000);
        }

        function toggleAutoRefresh() {
            autoRefresh = !autoRefresh;
            const toggle = document.getElementById('autoRefreshToggle');
            
            if (autoRefresh) {
                toggle.classList.add('active');
            } else {
                toggle.classList.remove('active');
            }
        }

        function showNotification(message, type) {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification ${type}`;
            notification.classList.add('show');
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 4000);
        }

        // Initialize auto-refresh toggle state
        document.getElementById('autoRefreshToggle').classList.add('active');
    </script>
</body>
</html>
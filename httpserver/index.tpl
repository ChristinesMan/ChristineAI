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
            height: calc(100vh - 40px);
            display: flex;
            flex-direction: column;
        }

        .header {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(255, 105, 180, 0.1);
            border: 2px solid var(--pink-light);
            margin-bottom: 20px;
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

        /* Tab Navigation */
        .tab-nav {
            display: flex;
            background: var(--card-bg);
            border-radius: 15px 15px 0 0;
            box-shadow: 0 4px 6px rgba(255, 105, 180, 0.1);
            border: 2px solid var(--pink-light);
            border-bottom: none;
            overflow: hidden;
        }

        .tab-button {
            flex: 1;
            padding: 15px 20px;
            background: linear-gradient(135deg, var(--pink-lighter) 0%, var(--pink-light) 100%);
            border: none;
            color: var(--text-dark);
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .tab-button:hover {
            background: linear-gradient(135deg, var(--pink-light) 0%, var(--pink-primary) 100%);
            color: white;
            transform: translateY(-2px);
        }

        .tab-button.active {
            background: linear-gradient(135deg, var(--pink-primary) 0%, var(--pink-dark) 100%);
            color: white;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
        }

        .tab-button:not(:last-child) {
            border-right: 1px solid var(--pink-light);
        }

        /* Tab Content */
        .tab-content {
            flex: 1;
            background: var(--card-bg);
            border-radius: 0 0 15px 15px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(255, 105, 180, 0.1);
            border: 2px solid var(--pink-light);
            border-top: none;
            overflow-y: auto;
        }

        .tab-pane {
            display: none;
            height: 100%;
        }

        .tab-pane.active {
            display: block;
        }

        /* Dashboard Layout */
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            height: 100%;
        }

        .dashboard-section {
            background: rgba(255, 255, 255, 0.5);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid var(--pink-light);
        }

        .controls {
            background: rgba(255, 255, 255, 0.5);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid var(--pink-light);
        }

        .status {
            background: rgba(255, 255, 255, 0.5);
            border-radius: 10px;
            padding: 15px;
            border: 1px solid var(--pink-light);
        }

        /* Settings Layout */
        .settings-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .setting-group {
            background: rgba(255, 255, 255, 0.5);
            border-radius: 10px;
            padding: 20px;
            border: 1px solid var(--pink-light);
        }

        .setting-group h3 {
            color: var(--pink-primary);
            margin-bottom: 15px;
            font-size: 1.3em;
        }

        .setting-item {
            margin-bottom: 15px;
        }

        .setting-item label {
            display: block;
            color: var(--text-dark);
            font-weight: bold;
            margin-bottom: 5px;
        }

        .setting-input {
            width: 100%;
            padding: 8px 12px;
            border: 2px solid var(--pink-light);
            border-radius: 8px;
            background: white;
            color: var(--text-dark);
        }

        .setting-range {
            width: 100%;
            margin: 8px 0;
        }

        /* Boolean settings. The template had no checkbox style before, because
           until the diarization switch there had never been a boolean setting. */
        .setting-toggle {
            width: 44px;
            height: 24px;
            margin: 8px 10px 8px 0;
            vertical-align: middle;
            accent-color: var(--pink-primary);
            cursor: pointer;
        }

        .setting-value {
            display: inline-block;
            background: var(--pink-primary);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            min-width: 50px;
            text-align: center;
        }

        .setting-help {
            display: inline-block;
            width: 18px;
            height: 18px;
            background: var(--pink-light);
            color: var(--text-dark);
            border-radius: 50%;
            text-align: center;
            line-height: 18px;
            font-size: 12px;
            font-weight: bold;
            cursor: pointer;
            margin-left: 8px;
            transition: all 0.3s ease;
        }

        .setting-help:hover {
            background: var(--pink-primary);
            color: white;
            transform: scale(1.1);
        }

        .tooltip {
            position: relative;
            display: inline-block;
        }

        .tooltip .tooltiptext {
            visibility: hidden;
            width: 320px;
            background: var(--text-dark);
            color: white;
            text-align: left;
            border-radius: 8px;
            padding: 12px;
            position: absolute;
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.9em;
            line-height: 1.4;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            /* Default position: below the button to prevent cutoff */
            top: 125%;
            left: 50%;
            margin-left: -160px;
        }

        .tooltip .tooltiptext::after {
            content: "";
            position: absolute;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            /* Default arrow: pointing up (tooltip below) */
            bottom: 100%;
            border-color: transparent transparent var(--text-dark) transparent;
        }

        /* Alternative positioning when tooltip would be cut off at bottom */
        .tooltip.flip-above .tooltiptext {
            top: auto;
            bottom: 125%;
        }

        .tooltip.flip-above .tooltiptext::after {
            bottom: auto;
            top: 100%;
            border-color: var(--text-dark) transparent transparent transparent;
        }

        /* Adjust horizontal position for tooltips near edges */
        .tooltip.align-left .tooltiptext {
            left: 0;
            margin-left: 0;
        }

        .tooltip.align-left .tooltiptext::after {
            left: 20px;
            margin-left: 0;
        }

        .tooltip.align-right .tooltiptext {
            left: auto;
            right: 0;
            margin-left: 0;
        }

        .tooltip.align-right .tooltiptext::after {
            left: auto;
            right: 20px;
            margin-left: 0;
        }

        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }

        .tooltip-default {
            display: block;
            margin-top: 6px;
            font-style: italic;
            color: var(--pink-primary);
            font-weight: bold;
        }

        /* Chat Layout */
        .chat {
            display: flex;
            flex-direction: column;
            height: 100%;
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

        /* Notification System */
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 300px;
            word-wrap: break-word;
        }

        .notification.show {
            transform: translateX(0);
        }

        .notification.success {
            background: linear-gradient(135deg, var(--success) 0%, #16a34a 100%);
        }

        .notification.error {
            background: linear-gradient(135deg, var(--error) 0%, #dc2626 100%);
        }

        .notification.info {
            background: linear-gradient(135deg, var(--pink-primary) 0%, var(--pink-dark) 100%);
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
            
            .settings-grid {
                grid-template-columns: 1fr;
            }
            
            .dashboard-grid {
                grid-template-columns: 1fr;
            }
            
            .tab-button {
                font-size: 0.9em;
                padding: 12px 15px;
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

        <!-- Tab Navigation -->
        <div class="tab-nav">
            <button class="tab-button active" onclick="showTab('dashboard')">
                🏠 Dashboard
            </button>
            <button class="tab-button" onclick="showTab('settings')">
                🎛️ Settings
            </button>
            <button class="tab-button" onclick="showTab('chat')">
                💬 Chat
            </button>
            <button class="tab-button" onclick="showTab('system')">
                🔧 System
            </button>
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
            <!-- Dashboard Tab -->
            <div id="dashboard" class="tab-pane active">
                <div class="dashboard-grid">
                    <div class="dashboard-section">
                        <h2 class="section-title">Status Monitor <span class="status-indicator online" id="connectionStatus"></span></h2>
                        <div class="auto-refresh">
                            <span>Auto-refresh status</span>
                            <div class="toggle-switch" id="autoRefreshToggle"></div>
                        </div>
                        <div class="status-grid" id="statusGrid">
                            <div class="status-item">
                                <span class="status-label">Loading...</span>
                                <span class="status-value"><div class="loading"></div></span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="dashboard-section">
                        <h2 class="section-title">Quick Controls</h2>
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
                        </div>
                        
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
                        </div>
                    </div>
                </div>
            </div>

            <!-- Settings Tab -->
            <div id="settings" class="tab-pane">
                <!-- Settings render themselves from STATE.user_configurable_vars
                     via /api/user-settings. Do NOT hand-write controls here:
                     this block used to hold 733 lines of hardcoded HTML and 34 of
                     84 registered settings were silently missing, because adding a
                     setting to status.py did nothing until someone also wrote the
                     matching markup. Add settings to the registry instead. -->
                <div class="settings-grid" id="settingsGrid">
                    <div style="text-align:center; color:var(--text-medium); font-style:italic; padding:20px;">
                        Loading settings…
                    </div>
                </div>
            </div>

            <!-- Chat Tab -->
            <div id="chat" class="tab-pane">
                <div class="chat">
                    <h2 class="section-title">Chat with Christine 💬</h2>
                    <div id="chatModeIndicator" style="text-align: center; margin-bottom: 10px; font-size: 0.9em; color: var(--text-medium);">
                        Checking chat mode...
                    </div>
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

            <!-- System Tab -->
            <div id="system" class="tab-pane">
                <div class="settings-grid">
                    <div class="setting-group">
                        <h3>🔧 System Controls</h3>
                        <div class="controls-grid">
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
                        </div>
                    </div>

                    <div class="setting-group">
                        <h3>📝 System Logs</h3>
                        <button class="button" onclick="toggleLogs()">
                            📝 Toggle Logs
                        </button>
                        <div class="logs-container" id="logsContainer" style="display: none;">
                            <div id="logContent">Loading logs...</div>
                        </div>
                    </div>
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

        // Tab Management
        function showTab(tabName) {
            // Hide all tab panes
            const panes = document.querySelectorAll('.tab-pane');
            panes.forEach(pane => pane.classList.remove('active'));
            
            // Remove active class from all tab buttons
            const buttons = document.querySelectorAll('.tab-button');
            buttons.forEach(button => button.classList.remove('active'));
            
            // Show the selected tab pane
            document.getElementById(tabName).classList.add('active');
            
            // Activate the clicked tab button
            event.target.classList.add('active');
            
            // Load settings if settings tab is opened
            if (tabName === 'settings') {
                loadUserSettings();
                // Reinitialize tooltips after settings are loaded
                setTimeout(setupTooltips, 100);
            }
        }

        // Settings Management
        let userSettings = {};

        function loadUserSettings() {
            authenticatedFetch('/api/user-settings')
                .then(response => response.json())
                .then(data => {
                    if (data.settings) {
                        userSettings = data.settings;
                        renderSettings();
                    }
                })
                .catch(error => {
                    console.error('Error loading user settings:', error);
                    const grid = document.getElementById('settingsGrid');
                    if (grid) {
                        grid.innerHTML = '<div style="text-align:center; color:var(--text-medium); padding:20px;">' +
                            'Could not load settings. Is she running?</div>';
                    }
                });
        }

        // Scale between stored value and slider value. The registry carries a
        // 'display' hint ({scale, unit}) so a setting stored in seconds can show
        // minutes without any per-setting JavaScript.
        function settingScale(config) {
            return (config.display && config.display.scale) ? config.display.scale : 1;
        }

        function settingUnit(config) {
            return (config.display && config.display.unit) ? config.display.unit : '';
        }

        function toSlider(config, stored) {
            const s = settingScale(config);
            if (s === 1) return stored;
            const v = stored / s;
            return (config.type === 'i' || s >= 60) ? Math.round(v) : v;
        }

        function toStored(config, slider) {
            const s = settingScale(config);
            const v = parseFloat(slider) * s;
            return config.type === 'i' ? Math.round(v) : v;
        }

        function formatSetting(config, sliderValue) {
            const unit = settingUnit(config);
            let n = parseFloat(sliderValue);
            // Sensitivity-style tiny floats need real precision to be readable.
            if (config.type === 'f' && Math.abs(config.max) <= 0.5) {
                return n.toFixed(4) + unit;
            }
            if (config.type === 'i' || settingScale(config) !== 1) {
                return Math.round(n) + unit;
            }
            return n + unit;
        }

        // A sensible step: integers step by 1, floats get ~200 increments across
        // their range, rounded to something human.
        function settingStep(config) {
            if (config.step) return config.step;
            if (config.type === 'i') return 1;
            const span = (config.max - config.min) / settingScale(config);
            if (span <= 0) return 0.01;
            const raw = span / 200;
            const mag = Math.pow(10, Math.floor(Math.log10(raw)));
            return Math.max(mag, 0.0001);
        }

        function escapeHtml(s) {
            return String(s).replace(/[&<>"']/g, c => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
            }[c]));
        }

        // Build the whole settings tab from the registry. Adding a setting to
        // STATE.user_configurable_vars is now all that is required for it to
        // appear here - no markup to hand-write, nothing to keep in sync.
        function renderSettings() {
            const grid = document.getElementById('settingsGrid');
            if (!grid) return;

            const groups = {};
            const order = [];
            for (const [name, config] of Object.entries(userSettings)) {
                const g = config.group || 'Advanced Settings';
                if (!groups[g]) { groups[g] = []; order.push(g); }
                groups[g].push([name, config]);
            }

            let html = '';
            for (const groupName of order) {
                const icon = groups[groupName][0][1].group_icon || '\u{1F527}';
                html += '<div class="setting-group">';
                html += '<h3>' + icon + ' ' + escapeHtml(groupName) + '</h3>';
                for (const [name, config] of groups[groupName]) {
                    const help = escapeHtml(config.help || '');
                    const desc = escapeHtml(config.desc || name);
                    const unit = settingUnit(config);
                    let defaultText = config.default;
                    if (config.type === 'b') {
                        defaultText = config.default ? 'on' : 'off';
                    } else if (settingScale(config) !== 1) {
                        defaultText = Math.round(config.default / settingScale(config)) + unit;
                    } else {
                        defaultText = String(config.default) + unit;
                    }

                    html += '<div class="setting-item">';
                    html += '<label>' + desc + ':';
                    if (help) {
                        html += '<div class="tooltip"><span class="setting-help">?</span>' +
                                '<span class="tooltiptext">' + help +
                                '<span class="tooltip-default">Default: ' +
                                escapeHtml(defaultText) + '</span></span></div>';
                    }
                    html += '</label>';

                    if (config.type === 'b') {
                        // Booleans get a real checkbox. The old hardcoded template
                        // had no checkbox markup at all, which is why the first
                        // boolean setting ever added was invisible.
                        html += '<input type="checkbox" class="setting-toggle" id="' + name + '"' +
                                (config.value ? ' checked' : '') + '>';
                        html += '<span class="setting-value" id="' + name + '_value">' +
                                (config.value ? 'On' : 'Off') + '</span>';
                    } else {
                        const min = config.min / settingScale(config);
                        const max = config.max / settingScale(config);
                        html += '<input type="range" class="setting-range" id="' + name + '"' +
                                ' min="' + min + '" max="' + max + '"' +
                                ' step="' + settingStep(config) + '"' +
                                ' value="' + toSlider(config, config.value) + '">';
                        html += '<span class="setting-value" id="' + name + '_value">' +
                                formatSetting(config, toSlider(config, config.value)) +
                                '</span>';
                    }
                    html += '</div>';
                }
                html += '</div>';
            }
            grid.innerHTML = html;
            wireSettings();
            setTimeout(setupTooltips, 100);
        }

        function wireSettings() {
            for (const [name, config] of Object.entries(userSettings)) {
                const el = document.getElementById(name);
                if (!el) continue;
                if (config.type === 'b') {
                    el.onchange = function() {
                        updateUserSetting(name, this.checked);
                        const d = document.getElementById(name + '_value');
                        if (d) d.textContent = this.checked ? 'On' : 'Off';
                    };
                } else {
                    el.onchange = function() {
                        updateUserSetting(name, toStored(config, this.value));
                    };
                    el.oninput = function() {
                        const d = document.getElementById(name + '_value');
                        if (d) d.textContent = formatSetting(config, this.value);
                    };
                }
            }
        }

        function updateUserSetting(settingName, actualValue) {
            const requestData = {
                value: actualValue,
                token: authToken
            };

            authenticatedFetch(`/api/user-settings/${settingName}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log(`✅ Updated ${settingName} to ${data.new_value}`);
                    showNotification(`Setting updated: ${settingName} = ${data.new_value}`, 'success');
                    if (userSettings[settingName]) {
                        userSettings[settingName].value = data.new_value;
                    }
                } else {
                    console.error(`❌ Failed to update ${settingName}:`, data.error);
                    showNotification(`Failed to update ${settingName}: ${data.error}`, 'error');
                }
            })
            .catch(error => {
                console.error('Error updating setting:', error);
                showNotification('Network error updating setting', 'error');
            });
        }

        // Notification System
        function showNotification(message, type = 'info') {
            const notification = document.getElementById('notification');
            notification.textContent = message;
            notification.className = `notification ${type} show`;
            
            setTimeout(() => {
                notification.classList.remove('show');
            }, 3000);
        }

        // Smart tooltip positioning
        function setupTooltips() {
            const tooltips = document.querySelectorAll('.tooltip');
            
            tooltips.forEach(tooltip => {
                const helpButton = tooltip.querySelector('.setting-help');
                const tooltipText = tooltip.querySelector('.tooltiptext');
                
                if (helpButton && tooltipText) {
                    helpButton.addEventListener('mouseenter', function() {
                        // Reset classes first
                        tooltip.classList.remove('flip-above', 'align-left', 'align-right');
                        
                        // Get viewport and element dimensions
                        const rect = helpButton.getBoundingClientRect();
                        const viewportHeight = window.innerHeight;
                        const viewportWidth = window.innerWidth;
                        
                        // Check if tooltip would be cut off at bottom (default is below now)
                        const spaceBelow = viewportHeight - rect.bottom;
                        const tooltipHeight = 120; // Estimated height
                        
                        if (spaceBelow < tooltipHeight + 20) {
                            tooltip.classList.add('flip-above');
                        }
                        
                        // Check horizontal positioning
                        const spaceLeft = rect.left;
                        const spaceRight = viewportWidth - rect.right;
                        const tooltipWidth = 320;
                        
                        if (spaceLeft < tooltipWidth/2 + 20) {
                            tooltip.classList.add('align-left');
                        } else if (spaceRight < tooltipWidth/2 + 20) {
                            tooltip.classList.add('align-right');
                        }
                    });
                }
            });
        }

        // Initialize the interface
        document.addEventListener('DOMContentLoaded', function() {
            updateStatus();
            loadChatMessages();
            loadUserSettings(); // Load settings on startup
            setupTooltips(); // Initialize smart tooltip positioning
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
                        ['Chat Mode', data.chat_mode],
                        ['Gyro Available', data.gyro_available],
                        ['Skin Available', data.skin_available]
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

            // Chat tab indicator: Christine enters/exits chat mode herself via her own executive
            // tools (enterChatMode()/exitChatMode()) - this is just reflecting her current state,
            // not a toggle. There's no button here on purpose.
            const chatModeIndicator = document.getElementById('chatModeIndicator');
            if (chatModeIndicator) {
                const inChatMode = String(data.chat_mode).toLowerCase() === 'true';
                if (inChatMode) {
                    chatModeIndicator.textContent = "💬 Christine is in chat mode right now - she'll see your message.";
                    chatModeIndicator.style.color = 'var(--accent-color, #d63384)';
                } else {
                    chatModeIndicator.textContent = "💤 Christine isn't in chat mode right now - she'll get a heads-up that a message is waiting, and will see it once she switches over.";
                    chatModeIndicator.style.color = 'var(--text-medium)';
                }
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
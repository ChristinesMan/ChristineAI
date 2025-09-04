<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link rel="icon" href="data:,">
    <title>Christine's Brain</title>
    <style>

        .tab {
            overflow: hidden;
            border: 1px solid #ccc;
            background-color: #f1f1f1;
        }

        .tab button {
            background-color: inherit;
            float: left;
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
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
        }

        .tab button:hover {
            background-color: #ddd;
        }

        .tab button.active {
            background-color: #ccc;
        }

        .tabcontent {
            display: none;
            padding: 6px 12px;
            border: 1px solid #ccc;
            border-top: none;
        }

/*
 * Styling for status table
 */

        .statusTable  {border-collapse:collapse;border-spacing:0;}
        .statusTable td{border-color:black;border-width:1px;font-family:Arial, sans-serif;font-size:12px;
        overflow:hidden;padding:4px 5px;word-break:normal;}
        .statusTable th{border-color:black;border-width:1px;font-family:Arial, sans-serif;font-size:12px;
        font-weight:normal;overflow:hidden;padding:4px 5px;word-break:normal;}
        .statusTable .statusTable-value{border-color:#ffffff;text-align:left;vertical-align:top}
        .statusTable .statusTable-label{border-color:#ffffff;text-align:left;vertical-align:top}
    </style>
</head>
<body>

<div class="tab">
    <button class="tablinks" onclick="openTab(event, 'Status')">Status</button>
    <button class="tablinks" onclick="openTab(event, 'Control')">Control</button>
    <button class="tablinks" onclick="openTab(event, 'Chat')">Chat</button>
    <button class="tablinks" onclick="openTab(event, 'WhoIsSpeaking')">Who Is Speaking</button>
</div>

<div id="Status" class="tabcontent">
    <h3>Status</h3>
    <table id="statusTable">
        <thead>
            <tr>
                <th>Parameter</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            <!-- Data will be populated here -->
        </tbody>
    </table>

    <script>
        async function fetchStatus() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                updateStatusTable(data);
            } catch (error) {
                console.error('Error fetching status:', error);
            }
        }

        function updateStatusTable(data) {
            const tbody = document.getElementById('statusTable').getElementsByTagName('tbody')[0];
            tbody.innerHTML = ''; // Clear existing data

            for (const [key, value] of Object.entries(data)) {
                const row = document.createElement('tr');
                const cellKey = document.createElement('td');
                const cellValue = document.createElement('td');

                cellKey.textContent = key;
                cellValue.textContent = value;

                row.appendChild(cellKey);
                row.appendChild(cellValue);
                tbody.appendChild(row);
            }
        }

        // Fetch status data every 5 seconds
        setInterval(fetchStatus, 5000);

        // Initial fetch
        fetchStatus();
    </script>
</div>

<div id="Control" class="tabcontent">
    <h3>Control</h3>
    <button onclick="controlAction('restart')">Restart</button>
    <button onclick="controlAction('stop')">Stop</button><br/>
    <button onclick="controlAction('reboot')">Reboot</button>
    <button onclick="controlAction('poweroff')">Power Off</button><br/>
    <button onclick="controlAction('wernicke_on')">Wernicke On</button>
    <button onclick="controlAction('wernicke_off')">Wernicke Off</button>

    <script>
        async function controlAction(action) {
            try {
                const response = await fetch('/control', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ action: action })
                });
                const result = await response.json();
                alert(result.message);
            } catch (error) {
                console.error('Error performing control action:', error);
            }
        }
    </script>
</div>

<div id="Chat" class="tabcontent">
    <h3>Chat</h3>
    
</div>

<div id="WhoIsSpeaking" class="tabcontent">
    <h3>Who Is Speaking</h3>
    <button onclick="submitSpeaker('{{USER_NAME}}')">{{USER_NAME}}</button><br/><br/>
    <button onclick="submitSpeaker('Somebody')">Somebody</button><br/><br/>
    <button onclick="submitSpeaker('Somebody in the work meeting')">Work meeting</button><br/><br/>
    <input type="text" id="customSpeaker" placeholder="Enter custom name">
    <button onclick="submitCustomSpeaker()">Submit</button>

    <script>
        async function submitSpeaker(name) {
            try {
                const response = await fetch('/who_is_speaking', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ speaker: name })
                });
                const result = await response.json();
                // alert(result.message);
            } catch (error) {
                console.error('Error submitting speaker:', error);
            }
        }

        async function submitCustomSpeaker() {
            const customName = document.getElementById('customSpeaker').value;
            if (customName) {
                submitSpeaker(customName);
            } else {
                alert('Please enter a custom name.');
            }
        }
    </script>
</div>

<script>

    function openTab(evt, tabName) {
        var i, tabcontent, tablinks;
        tabcontent = document.getElementsByClassName("tabcontent");
        for (i = 0; i < tabcontent.length; i++) {
            tabcontent[i].style.display = "none";
        }
        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        document.getElementById(tabName).style.display = "block";
        evt.currentTarget.className += " active";
    }

</script>

</body>
</html>
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
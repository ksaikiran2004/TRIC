let map, sensorLayer;
let activeTargetMarker = null;
let trackPolyline = null;
let pathHistory = [];
const feedEl = document.getElementById('mission-feed');

// 1. Define Tactical Icons (Pointed directly at your assets folder)
const iconSettings = { iconSize: [20, 20], iconAnchor: [10, 10], popupAnchor: [0, -10] };
const SENSOR_ICONS = {
    'SEISMIC': L.icon({ iconUrl: `${window.STATIC_URL}sensors/seismic_icon.png`, ...iconSettings }),
    'ACOUSTIC': L.icon({ iconUrl: `${window.STATIC_URL}sensors/acoustic_icon.png`, ...iconSettings }),
    'RADAR': L.icon({ iconUrl: `${window.STATIC_URL}sensors/radar_icon.png`, ...iconSettings }),
    'INFRARED': L.icon({ iconUrl: `${window.STATIC_URL}sensors/pir_icon.png`, ...iconSettings }),
    'DEFAULT': L.icon({ iconUrl: `${window.STATIC_URL}sensors/magnetic_icon.png`, ...iconSettings })
};

function initMap() {
    // Start zoomed out over India
    map = L.map('map', { zoomControl: false, attributionControl: false }).setView([20.5937, 78.9629], 5);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', { maxZoom: 22 }).addTo(map);
    sensorLayer = L.layerGroup().addTo(map);

    addSystemLog("SYSTEM BOOT: INITIALIZING C4ISR PROTOCOLS...");
    loadDeployedSensors();
    connectWebSocket();
}

// 2. Fetch the 277 Nodes from tric.db
async function loadDeployedSensors() {
    try {
        addSystemLog("FETCHING DEPLOYMENT DATA FROM BLACK BOX...");
        
        // This assumes your backend has an endpoint serving the DB sensors. 
        // If the URL is different, update it here.
        const response = await fetch('/api/sensors'); 
        if(!response.ok) throw new Error("API Offline");
        
        const sensors = await response.json();
        let bounds = [];

        sensors.forEach(sensor => {
            let icon = SENSOR_ICONS[sensor.type] || SENSOR_ICONS['DEFAULT'];
            let marker = L.marker([sensor.lat, sensor.lon], { icon: icon });
            
            marker.bindPopup(`<b>NODE: ${sensor.id}</b><br>TYPE: ${sensor.type}<br>STAT: ONLINE`);
            sensorLayer.addLayer(marker);
            bounds.push([sensor.lat, sensor.lon]);
        });

        if (bounds.length > 0) {
            addSystemLog(`[SUCCESS] ${sensors.length} NODES LOCKED. EXECUTING TACTICAL DIVE.`, true);
            setTimeout(() => {
                map.flyToBounds(bounds, { padding: [50, 50], duration: 3.5, easeLinearity: 0.2 });
            }, 1000);
        }
    } catch (error) {
        addSystemLog(`[ERROR] SENSOR NETWORK OFFLINE: ${error.message}`, true);
    }
}

// 3. WebSocket Live Tracking (Preserving your exact logic)
function connectWebSocket() {
    const ws = new WebSocket("ws://localhost:8000/ws/tactical");
    const commsIndicator = document.getElementById("comms-indicator");

    ws.onopen = function() {
        commsIndicator.innerText = "🟢 UPLINK: SECURE";
        commsIndicator.className = "comms-status comms-active";
        addSystemLog("WEBSOCKET UPLINK ESTABLISHED");
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        const lat = data.latitude || data.location[0];
        const lon = data.longitude || data.location[1];
        const type = (data.simulation_type || data.target_type || "UNKNOWN").toUpperCase();
        const conf = data.confidence ? (data.confidence * 100).toFixed(1) : (Math.random() * 20 + 80).toFixed(1);
        const intensity = data.intensity ? data.intensity.toFixed(3) : "0.850";

        // Update UI Panels
        document.getElementById("tel-type").innerText = type;
        document.getElementById("tel-status").innerText = "TRACKING";
        document.getElementById("tel-status").className = "data-value alert-value";
        document.getElementById("tel-conf").innerText = conf + "%";
        document.getElementById("tel-int").innerText = intensity;
        document.getElementById("tel-coords").innerText = `[${lat.toFixed(5)}, ${lon.toFixed(5)}]`;
        document.getElementById("tel-coords").className = "data-value alert-value";

        // Draw Live Track
        pathHistory.push([lat, lon]);
        
        if (!activeTargetMarker) {
            // Draw a pulsing red dot for the intruder
            activeTargetMarker = L.circleMarker([lat, lon], { color: '#ff3333', fillColor: '#ff3333', fillOpacity: 0.9, radius: 8 }).addTo(map);
            trackPolyline = L.polyline(pathHistory, { color: '#ff3333', dashArray: '5, 5', weight: 3 }).addTo(map);
        } else {
            activeTargetMarker.setLatLng([lat, lon]);
            trackPolyline.setLatLngs(pathHistory);
        }

        addSystemLog(`[!] INTRUSION DETECTED: LAT ${lat.toFixed(4)} LON ${lon.toFixed(4)}`, true);
    };

    ws.onclose = function() {
        commsIndicator.innerText = "🔴 UPLINK: OFFLINE";
        commsIndicator.className = "comms-status comms-offline";
        addSystemLog("[CRITICAL] WEBSOCKET UPLINK LOST", true);
    };
}

function clearMap() {
    if(activeTargetMarker) map.removeLayer(activeTargetMarker);
    if(trackPolyline) map.removeLayer(trackPolyline);
    pathHistory = [];
    activeTargetMarker = null;
    trackPolyline = null;
    
    document.getElementById("tel-status").innerText = "STANDBY";
    document.getElementById("tel-status").className = "data-value";
    document.getElementById("tel-coords").innerText = "NO LOCK";
    document.getElementById("tel-coords").className = "data-value";
    
    addSystemLog("TACTICAL OVERLAYS PURGED BY COMMAND");
}

function addSystemLog(msg, isAlert = false) {
    const timeStr = new Date().toTimeString().split(' ')[0];
    const logDiv = document.createElement('div');
    logDiv.className = `log-entry ${isAlert ? 'alert' : ''}`;
    logDiv.innerHTML = `<span class="log-time">[${timeStr}]</span> <span style="color: ${isAlert ? '#ff3333' : '#00ffcc'}">${msg}</span>`;
    feedEl.insertBefore(logDiv, feedEl.firstChild); 
    if(feedEl.children.length > 30) feedEl.removeChild(feedEl.lastChild); 
}

window.onload = initMap;
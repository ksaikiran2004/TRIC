let map, sensorLayer;
let activeTargetMarker = null;
let trackPolyline = null;
let pathHistory = [];
let deploymentBounds = null; 
const feedEl = document.getElementById('mission-feed');

// 3D Holotable Engine Instances
let holotableInstance = null;
let is3DModeActive = false;

const iconSettings = { iconSize: [20, 20], iconAnchor: [10, 10], popupAnchor: [0, -10] };
const SENSOR_ICONS = {
    'SEISMIC': L.icon({ iconUrl: `${window.STATIC_URL}sensors/seismic_icon.png`, ...iconSettings }),
    'ACOUSTIC': L.icon({ iconUrl: `${window.STATIC_URL}sensors/acoustic_icon.png`, ...iconSettings }),
    'RADAR': L.icon({ iconUrl: `${window.STATIC_URL}sensors/radar_icon.png`, ...iconSettings }),
    'INFRARED': L.icon({ iconUrl: `${window.STATIC_URL}sensors/pir_icon.png`, ...iconSettings }),
    'DEFAULT': L.icon({ iconUrl: `${window.STATIC_URL}sensors/magnetic_icon.png`, ...iconSettings })
};

function initMap() {
    map = L.map('map').setView([20.5937, 78.9629], 5);
    
    L.tileLayer('/offline_map/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: 'TRIC AIR-GAPPED NETWORK'
    }).addTo(map);

    sensorLayer = L.layerGroup().addTo(map);

    addSystemLog("SYSTEM BOOT: INITIALIZING OFFLINE PROTOCOLS...");
    loadDeployedSensors();
    connectWebSocket();

    const topoBtn = document.getElementById('topo-trigger-btn');
    const holoControls = document.getElementById('holotable-controls');
    const return2dBtn = document.getElementById('return-2d-btn');
    
    map.on('moveend', function() {
        if(is3DModeActive) return;
        let currentZoom = map.getZoom();
        let center = map.getCenter();
        let isKashmir = (center.lat > 33.8 && center.lat < 34.2 && center.lng > 73.8 && center.lng < 74.2);

        if (currentZoom >= 11 && isKashmir) {
            topoBtn.style.display = 'block';
        } else {
            topoBtn.style.display = 'none';
        }
    });

    // EXECUTE HANDSHAKE TO 3D HOLOTABLE
    topoBtn.addEventListener('click', function() {
        addSystemLog("WARNING: INITIALIZING WEBGL 3D HOLOTABLE...", true);
        is3DModeActive = true;
        topoBtn.style.display = 'none';
        document.getElementById('map').style.display = 'none';
        document.getElementById('holotable-canvas').style.display = 'block';
        holoControls.style.display = 'flex';

        // Spin up the WebGL engine context
        holotableInstance = new TacticalHolotable('holotable-canvas');
        
        pathHistory.forEach(coords => {
            holotableInstance.updateTargetPosition(coords[0], coords[1], deploymentBounds);
        });
    });

    // REVERT HANDSHAKE PROTOCOL
    return2dBtn.addEventListener('click', function() {
        addSystemLog("COLLAPSING 3D MESH: RETURNING TO 2D AIR-SPACE OVERLAY.");
        is3DModeActive = false;
        holoControls.style.display = 'none';
        document.getElementById('holotable-canvas').style.display = 'none';
        document.getElementById('map').style.display = 'block';
        
        if(holotableInstance) {
            holotableInstance.shutdown();
            holotableInstance = null;
        }
        map.invalidateSize();
    });
}

async function loadDeployedSensors() {
    try {
        const response = await fetch('/api/sensors'); 
        if(!response.ok) throw new Error("API Offline");
        
        const sensors = await response.json();
        let lats = [], lons = [];

        sensors.forEach(sensor => {
            let rawType = String(sensor.type).replace('SensorType.', '').toUpperCase().trim();
            let icon = SENSOR_ICONS[rawType] || SENSOR_ICONS['DEFAULT'];
            let marker = L.marker([sensor.lat, sensor.lon], { icon: icon });
            
            marker.bindPopup(`<b>NODE: ${sensor.id}</b><br>TYPE: ${rawType}<br>STAT: ONLINE`);
            sensorLayer.addLayer(marker);
            
            lats.push(sensor.lat);
            lons.push(sensor.lon);
        });

        if (lats.length > 0) {
            deploymentBounds = [
                [Math.min(...lats) - 0.05, Math.min(...lons) - 0.05],
                [Math.max(...lats) + 0.05, Math.max(...lons) + 0.05]
            ];
            
            addSystemLog(`[SUCCESS] ${sensors.length} NODES LOCKED. EXECUTING TACTICAL DIVE.`, false);
            setTimeout(() => {
                map.flyToBounds(deploymentBounds, { padding: [50, 50], duration: 4.0, easeLinearity: 0.25 });
            }, 1000);
        }
    } catch (error) {
        addSystemLog(`[ERROR] SENSOR NETWORK OFFLINE: ${error.message}`, true);
    }
}

function connectWebSocket() {
    const ws = new WebSocket("ws://localhost:8000/ws/tactical");
    const commsIndicator = document.getElementById("comms-indicator");

    ws.onopen = function() {
        commsIndicator.className = "comms-status online-text";
        commsIndicator.innerHTML = '<span id="comms-dot" class="status-dot online-dot"></span> UPLINK: SECURE';
        addSystemLog("WEBSOCKET UPLINK ESTABLISHED");
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        const lat = data.latitude || data.location[0];
        const lon = data.longitude || data.location[1];
        const type = (data.simulation_type || data.target_type || "UNKNOWN").toUpperCase();
        const conf = data.confidence ? (data.confidence * 100).toFixed(1) : (Math.random() * 20 + 80).toFixed(1);
        const intensity = data.intensity ? data.intensity.toFixed(3) : "0.850";
        
        document.getElementById("tel-type").innerText = type;
        document.getElementById("tel-status").innerText = "TRACKING";
        document.getElementById("tel-status").className = "data-value alert-value";
        document.getElementById("tel-conf").innerText = conf + "%";
        document.getElementById("tel-int").innerText = intensity;
        document.getElementById("tel-coords").innerText = `[${lat.toFixed(5)}, ${lon.toFixed(5)}]`;
        document.getElementById("tel-coords").className = "data-value alert-value";

        pathHistory.push([lat, lon]);
        
        if (is3DModeActive && holotableInstance) {
            holotableInstance.updateTargetPosition(lat, lon, deploymentBounds);
        }

        if (!activeTargetMarker) {
            activeTargetMarker = L.circleMarker([lat, lon], { color: '#ff3333', fillColor: '#ff3333', fillOpacity: 0.9, radius: 8 }).addTo(map);
            trackPolyline = L.polyline(pathHistory, { color: '#ff3333', dashArray: '5, 5', weight: 3 }).addTo(map);
        } else {
            activeTargetMarker.setLatLng([lat, lon]);
            trackPolyline.setLatLngs(pathHistory);
        }

        addSystemLog(`[!] INTRUSION DETECTED: LAT ${lat.toFixed(4)} LON ${lon.toFixed(4)}`, true);
    };

    ws.onclose = function() {
        commsIndicator.className = "comms-status offline-text";
        commsIndicator.innerHTML = '<span id="comms-dot" class="status-dot offline-dot"></span> UPLINK: OFFLINE';
        addSystemLog("[CRITICAL] WEBSOCKET UPLINK LOST", true);
    };
}

function setHoloMode(mode) {
    if(holotableInstance) {
        holotableInstance.setInteractionMode(mode);
    }
}

function clearMap() {
    if(activeTargetMarker) map.removeLayer(activeTargetMarker);
    if(trackPolyline) map.removeLayer(trackPolyline);
    pathHistory = [];
    activeTargetMarker = null;
    trackPolyline = null;
    
    if(holotableInstance) {
        holotableInstance.clearTrack();
    }
    
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
    logDiv.innerHTML = `<span class="log-time">[${timeStr}]</span> <span style="color: ${isAlert ? '#ff3333' : '#00ea4f'}">${msg}</span>`;
    feedEl.insertBefore(logDiv, feedEl.firstChild); 
    if(feedEl.children.length > 30) feedEl.removeChild(feedEl.lastChild); 
}

window.onload = initMap;
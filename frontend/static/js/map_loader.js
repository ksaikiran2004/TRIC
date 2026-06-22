// ==========================================
// AUTHENTICATION & BOOT SEQUENCE
// ==========================================
function verifyLogin() {
    const user = document.getElementById('auth-id').value;
    const pass = document.getElementById('auth-pass').value;
    if (user === "admin" && pass === "admin") {
        document.getElementById('login-view').style.display = 'none';
        document.getElementById('device-view').style.display = 'block';
    } else {
        document.getElementById('login-err').style.display = 'block';
    }
}

function bootSystem(mode) {
    document.getElementById('boot-screen').style.display = 'none';
    document.getElementById('main-dashboard').style.display = 'flex';
    
    if (mode === 'mobile') {
        document.body.classList.add('mobile-mode');
    }
    
    setTimeout(() => {
        initMap();
        initSplitter(); // Start the dynamic layout resizer
        initUAVDrag();  // Enable drone window dragging
        setTimeout(() => { if (map) map.invalidateSize(); }, 150);
    }, 250);
}

// ==========================================
// UI INTERACTION CONTROLLERS
// ==========================================
function toggleUAV() {
    const modal = document.getElementById('uav-modal');
    if (modal.style.display === 'none' || modal.style.display === '') {
        modal.style.display = 'flex'; // Flex is required so the image stretches
    } else {
        modal.style.display = 'none';
    }
}

function initSplitter() {
    const splitter = document.getElementById('splitter');
    const sidebar = document.getElementById('sidebar');
    let isResizing = false;

    splitter.addEventListener('mousedown', (e) => {
        isResizing = true;
        splitter.classList.add('active');
        document.body.style.cursor = 'col-resize';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        // Calculate new sidebar width
        let newWidth = window.innerWidth - e.clientX;
        if (newWidth >= 250 && newWidth <= 800) {
            sidebar.style.width = newWidth + 'px';
            
            // Aggressively resize maps to prevent tearing
            if (map && !is3DModeActive) map.invalidateSize();
            if (holotableInstance && is3DModeActive) holotableInstance.resize();
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            splitter.classList.remove('active');
            document.body.style.cursor = 'default';
        }
    });
}

function initUAVDrag() {
    const modal = document.getElementById('uav-modal');
    const header = modal.querySelector('.uav-header');
    let isDragging = false;
    let offsetX = 0, offsetY = 0;

    header.addEventListener('mousedown', (e) => {
        isDragging = true;
        offsetX = e.clientX - modal.offsetLeft;
        offsetY = e.clientY - modal.offsetTop;
    });

    document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        modal.style.left = (e.clientX - offsetX) + 'px';
        modal.style.top = (e.clientY - offsetY) + 'px';
    });

    document.addEventListener('mouseup', () => { isDragging = false; });
}

// ==========================================
// MAP & HOLOTABLE LOGIC
// ==========================================
let map, sensorLayer;
let activeTargetMarker = null;
let trackPolyline = null;
let pathHistory = [];
let deploymentBounds = null; 
let globalSensorData = []; 
const feedEl = document.getElementById('mission-feed');

let holotableInstance = null;
let is3DModeActive = false;

const LOC_COORDS = [
    [34.40, 73.80], [34.37, 73.83], [34.38, 73.88],
    [34.32, 73.94], [34.29, 74.02], [34.24, 74.08],
    [34.22, 74.15], [34.16, 74.22]
];

const createTacticalIcon = (color, label, isRadar = false) => {
    const animClass = isRadar ? 'radar-sweep' : 'sensorPulse';
    return L.divIcon({
        className: 'custom-tactical-icon',
        html: `<div style="border: 1px solid ${color}; background: rgba(0,0,0,0.8); color: ${color}; font-size: 11px; padding: 2px 6px; font-family: monospace; font-weight: bold; border-radius: 2px; box-shadow: 0 0 8px ${color}; display: flex; align-items: center; gap: 6px;">
                  <div style="width: 8px; height: 8px; background: ${color}; border-radius: 50%; display: inline-block; animation: ${animClass} 1.5s infinite;"></div>
                  ${label}
               </div>`,
        iconSize: [70, 24],
        iconAnchor: [35, 12],
        popupAnchor: [0, -15]
    });
};

const SENSOR_ICONS = {
    'SEISMIC': createTacticalIcon('#00ea4f', 'SEIS'),
    'ACOUSTIC': createTacticalIcon('#00a5ff', 'ACOU'),
    'INFRARED': createTacticalIcon('#ff9900', 'PIR'),
    'RADAR': createTacticalIcon('#ff3333', 'RDR', true)
};

function drawTacticalBorder() {
    L.polyline(LOC_COORDS, { color: '#ff1100', weight: 8, opacity: 0.3, dashArray: '15, 10' }).addTo(map);
    L.polyline(LOC_COORDS, { color: '#ffffff', weight: 2, opacity: 0.9, dashArray: '15, 10' }).addTo(map);
}

function initMap() {
    map = L.map('map').setView([34.28, 74.00], 10); 
    
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 18,
        className: 'tactical-map-filter',
        attribution: 'TRIC SATELLITE UPLINK'
    }).addTo(map);

    sensorLayer = L.layerGroup().addTo(map);

    addSystemLog("SYSTEM BOOT: INITIALIZING SATELLITE PROTOCOLS...");
    drawTacticalBorder();
    loadDeployedSensors();
    connectWebSocket();

    const topoBtn = document.getElementById('topo-trigger-btn');
    const holoControls = document.getElementById('holotable-controls');
    const return2dBtn = document.getElementById('return-2d-btn');
    const altimeterHud = document.getElementById('altimeter-hud'); 
    
    map.on('moveend', function() {
        if(is3DModeActive) return;
        let currentZoom = map.getZoom();
        if (currentZoom >= 10) {
            topoBtn.style.display = 'block';
        } else {
            topoBtn.style.display = 'none';
        }
    });

    topoBtn.addEventListener('click', function() {
        addSystemLog("WARNING: INITIALIZING WEBGL 3D HOLOTABLE...", true);
        is3DModeActive = true;
        topoBtn.style.display = 'none';
        document.getElementById('map').style.display = 'none';
        
        const canvasDiv = document.getElementById('holotable-canvas');
        canvasDiv.style.display = 'block';
        holoControls.style.display = 'flex';
        altimeterHud.style.display = 'block'; 

        setTimeout(() => {
            if (!holotableInstance) {
                holotableInstance = new TacticalHolotable('holotable-canvas');
            } else {
                holotableInstance.resize(); 
            }
            holotableInstance.loadSensors(globalSensorData, deploymentBounds, LOC_COORDS);
        }, 150);
    });

    return2dBtn.addEventListener('click', function() {
        addSystemLog("COLLAPSING 3D MESH: RETURNING TO 2D AIR-SPACE OVERLAY.");
        is3DModeActive = false;
        holoControls.style.display = 'none';
        altimeterHud.style.display = 'none'; 
        document.getElementById('holotable-canvas').style.display = 'none';
        document.getElementById('map').style.display = 'block';
        map.invalidateSize();
    });
}

async function loadDeployedSensors() {
    try {
        const response = await fetch('/api/sensors'); 
        if(!response.ok) throw new Error("API Offline");
        
        let sensors = await response.json();
        let lats = [], lons = [];
        let sIndex = 0;
        
        for (let i = 0; i < LOC_COORDS.length - 1; i++) {
            let start = LOC_COORDS[i];
            let end = LOC_COORDS[i+1];
            
            for(let j=0; j < 35; j++) {
                if(sIndex >= sensors.length) break;
                
                let fraction = j / 35;
                let baseLat = start[0] + (end[0] - start[0]) * fraction;
                let baseLon = start[1] + (end[1] - start[1]) * fraction;

                let s = sensors[sIndex];
                
                if (j % 4 === 0) {
                    s.tacticalType = 'RADAR';
                    s.lat = baseLat - 0.04; 
                    s.lon = baseLon - 0.04;
                } else if (j % 2 === 0) {
                    s.tacticalType = 'INFRARED';
                    s.lat = baseLat - 0.015;
                    s.lon = baseLon - 0.015;
                } else {
                    s.tacticalType = j % 3 === 0 ? 'ACOUSTIC' : 'SEISMIC';
                    s.lat = baseLat + (Math.random() * 0.002 - 0.001); 
                    s.lon = baseLon + (Math.random() * 0.002 - 0.001);
                }

                globalSensorData.push(s);

                let marker = L.marker([s.lat, s.lon], { icon: SENSOR_ICONS[s.tacticalType] });
                marker.bindPopup(`<b>NODE: ${s.id}</b><br>TYPE: ${s.tacticalType}<br>STAT: ONLINE`);
                sensorLayer.addLayer(marker);
                
                lats.push(s.lat);
                lons.push(s.lon);
                sIndex++;
            }
        }

        deploymentBounds = [ [Math.min(...lats) - 0.02, Math.min(...lons) - 0.02], [Math.max(...lats) + 0.02, Math.max(...lons) + 0.02] ];
        map.fitBounds(deploymentBounds);
        addSystemLog(`[SUCCESS] 3-TIER GRID DEPLOYED ALONG LoC.`, false);
        
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
        
        document.getElementById("tel-type").innerText = type;
        document.getElementById("tel-status").innerText = "TRACKING: INTRUDER";
        document.getElementById("tel-status").className = "data-value alert-value";
        document.getElementById("tel-conf").innerText = conf + "%";
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
        addSystemLog(`[!] INTRUDER DETECTED: LAT ${lat.toFixed(4)} LON ${lon.toFixed(4)}`, true);
    };
    ws.onclose = function() {
        commsIndicator.className = "comms-status offline-text";
        commsIndicator.innerHTML = '<span id="comms-dot" class="status-dot offline-dot"></span> UPLINK: OFFLINE';
    };
}

function clearMap() {
    if(activeTargetMarker) map.removeLayer(activeTargetMarker);
    if(trackPolyline) map.removeLayer(trackPolyline);
    pathHistory = [];
    activeTargetMarker = null;
    trackPolyline = null;
    if(holotableInstance) holotableInstance.clearTrack();
    
    document.getElementById("tel-status").innerText = "STANDBY";
    document.getElementById("tel-status").className = "data-value";
    document.getElementById("tel-coords").innerText = "NO LOCK";
    document.getElementById("tel-coords").className = "data-value";
}

function addSystemLog(msg, isAlert = false) {
    const timeStr = new Date().toTimeString().split(' ')[0];
    const logDiv = document.createElement('div');
    logDiv.className = `log-entry ${isAlert ? 'alert' : ''}`;
    logDiv.innerHTML = `<span class="log-time">[${timeStr}]</span> <span style="color: ${isAlert ? '#ff3333' : '#00ea4f'}">${msg}</span>`;
    feedEl.insertBefore(logDiv, feedEl.firstChild); 
    if(feedEl.children.length > 30) feedEl.removeChild(feedEl.lastChild); 
}
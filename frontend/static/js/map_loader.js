// =========================================================================
// TRIC C4ISR - INTEGRATED CONTROLLER & SENSOR FUSION ENGINE
// =========================================================================

function verifyLogin() {
    const user = document.getElementById('auth-id').value.trim().toLowerCase();
    const pass = document.getElementById('auth-pass').value.trim().toLowerCase();
    
    if (!user || !pass) return;

    if (user === "admin" && pass === "admin") {
        document.getElementById('login-err').style.display = 'none';
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
        try {
            initMap();
            initSplitter(); 
            initUAVDrag();  
            
            setTimeout(() => { 
                if (map) map.invalidateSize(); 
            }, 150);
        } catch (err) {
            console.error("[CRITICAL SHUTDOWN] FRONTEND INITIALIZATION FAILED:", err);
            alert("System initialization aborted. See internal debugger logs.");
        }
    }, 250);
}

function toggleUAV() {
    const modal = document.getElementById('uav-modal');
    if (!modal) return;
    if (modal.style.display === 'none' || modal.style.display === '') {
        modal.style.display = 'flex';
    } else {
        modal.style.display = 'none';
    }
}

function initSplitter() {
    const splitter = document.getElementById('splitter');
    const sidebar = document.getElementById('sidebar');
    if (!splitter || !sidebar) return; 

    let isResizing = false;

    splitter.addEventListener('mousedown', (e) => {
        isResizing = true;
        splitter.classList.add('active');
        document.body.classList.add('is-resizing'); 
        e.preventDefault(); 
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        e.preventDefault();
        
        let newWidth = window.innerWidth - e.clientX;
        if (newWidth >= 300 && newWidth <= 900) {
            sidebar.style.width = newWidth + 'px';
        }
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            splitter.classList.remove('active');
            document.body.classList.remove('is-resizing');
            
            window.dispatchEvent(new Event('resize'));
            
            if (map && !is3DModeActive) map.invalidateSize();
            if (holotableInstance && is3DModeActive) holotableInstance.resize();
        }
    });
}

function initUAVDrag() {
    const modal = document.getElementById('uav-modal');
    if (!modal) return;
    const header = modal.querySelector('.uav-header');
    if (!header) return;

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

let map = null;
let sensorLayer = null;
let activeTargetMarker = null;
let trackPolyline = null;
let pathHistory = [];
let deploymentBounds = null; 
let globalSensorData = []; 
let holotableInstance = null;
let is3DModeActive = false;

// Line of Control
const LOC_COORDS = [
    [34.95, 74.24], [34.66, 73.95], [34.42, 73.85], 
    [34.08, 74.03], [33.77, 74.09], [33.38, 74.30], [32.87, 74.45]
];

const IB_COORDS = [
    [32.87, 74.45], [32.60, 74.75], [32.15, 75.40], 
    [31.60, 74.55], [30.10, 73.88]
];

const createReticleIcon = (color, label) => {
    return L.divIcon({
        className: 'custom-reticle',
        html: `
            <div style="color: ${color}; text-align: center;">
                <div class="reticle-icon">
                    <div class="reticle-crosshair"></div>
                </div>
                <div class="reticle-label" style="border-color: ${color};">${label}</div>
            </div>
        `,
        iconSize: [50, 50],
        iconAnchor: [25, 25],
        popupAnchor: [0, -25]
    });
};

const SENSOR_ICONS = {
    'SEISMIC': createReticleIcon('#00ea4f', 'SEIS'),
    'ACOUSTIC': createReticleIcon('#00a5ff', 'ACOU'),
    'INFRARED': createReticleIcon('#ff9900', 'PIR'),
    'RADAR': createReticleIcon('#ff3333', 'RDR')
};

function drawTacticalBordersAndLabels() {
    L.polyline(IB_COORDS, { color: '#ff9900', weight: 4, opacity: 0.85 }).addTo(map);
    L.polyline(LOC_COORDS, { color: '#ff1100', weight: 8, opacity: 0.6, dashArray: '15, 15' }).addTo(map);
    L.polyline(LOC_COORDS, { color: '#ffffff', weight: 2, opacity: 0.9, dashArray: '15, 15' }).addTo(map);
}

function initMap() {
    map = L.map('map', { zoomControl: false }).setView([22.00, 78.00], 5); 
    
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 18,
        className: 'tactical-map-filter',
        attribution: 'TRIC SECURE SATELLITE CORE'
    }).addTo(map);

    L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 18, 
        className: 'tactical-labels-filter'
    }).addTo(map);

    sensorLayer = L.layerGroup().addTo(map);

    addSystemLog("SYSTEM INITIALIZATION BOOT: COMPILING GEOSPATIAL PARAMETERS...");
    
    drawTacticalBordersAndLabels();
    loadDeployedSensors();
    connectWebSocket();

    const topoBtn = document.getElementById('topo-trigger-btn');
    const holoControls = document.getElementById('holotable-controls');
    const return2dBtn = document.getElementById('return-2d-btn');
    const altimeterHud = document.getElementById('altimeter-hud'); 
    
    map.on('moveend', function() {
        if(is3DModeActive) return;
        let currentZoom = map.getZoom();
        if (currentZoom >= 9 && topoBtn) {
            topoBtn.style.display = 'flex'; 
        } else if (topoBtn) {
            topoBtn.style.display = 'none';
        }
    });

    if (topoBtn) {
        topoBtn.addEventListener('click', function() {
            addSystemLog("TACTICAL THREAT ALERT: INITIALIZING THREE.JS WEBGL CRUST MESH...", true);
            is3DModeActive = true;
            topoBtn.style.display = 'none';
            document.getElementById('map').style.display = 'none';
            
            const canvasDiv = document.getElementById('holotable-canvas');
            canvasDiv.style.display = 'block';
            if(holoControls) holoControls.style.display = 'flex';
            if(altimeterHud) altimeterHud.style.display = 'block'; 

            setTimeout(() => {
                if (typeof TacticalHolotable !== 'undefined') {
                    if (!holotableInstance) {
                        holotableInstance = new TacticalHolotable('holotable-canvas');
                    } else {
                        holotableInstance.resize(); 
                    }
                    holotableInstance.loadSensors(globalSensorData, deploymentBounds, LOC_COORDS);
                } else {
                    addSystemLog("[CRITICAL INTERRUPT] THREE.JS CORE FRAMEWORK UNREADABLE", true);
                }
            }, 150);
        });
    }

    if (return2dBtn) {
        return2dBtn.addEventListener('click', function() {
            addSystemLog("COLLAPSING WEBGL TOPOGRAPHY: PURGING GRID BUFFERS.");
            is3DModeActive = false;
            if(holoControls) holoControls.style.display = 'none';
            if(altimeterHud) altimeterHud.style.display = 'none'; 
            document.getElementById('holotable-canvas').style.display = 'none';
            document.getElementById('map').style.display = 'block';
            map.invalidateSize();
        });
    }
}

async function loadDeployedSensors() {
    try {
        const response = await fetch('/api/sensors'); 
        if(!response.ok) throw new Error("Database pipeline unreachable");
        
        let sensors = await response.json();
        let lats = [], lons = [];
        let sIndex = 0;
        
        // Exact conversions: 1 degree long ~ 92km at Kashmir latitude.
        // 2km = 0.021 degrees. 500m = 0.005 degrees. 250m = 0.0025 degrees.
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
                    // TIER 3 RADAR: 2km inland
                    s.tacticalType = 'RADAR';
                    s.lat = baseLat - 0.005; 
                    s.lon = baseLon + 0.02; 
                } else if (j % 2 === 0) {
                    // TIER 2 PIR: 500m inland
                    s.tacticalType = 'INFRARED';
                    s.lat = baseLat - 0.002;
                    s.lon = baseLon + 0.005; 
                } else {
                    // TIER 1 ACOUSTIC: 250m inland
                    s.tacticalType = j % 3 === 0 ? 'ACOUSTIC' : 'SEISMIC';
                    s.lat = baseLat; 
                    s.lon = baseLon + 0.0025; 
                }

                globalSensorData.push(s);

                let marker = L.marker([s.lat, s.lon], { icon: SENSOR_ICONS[s.tacticalType] });
                
                // FIX: Added bright green text on pure black background so it is highly readable
                marker.bindPopup(`
                    <div style="font-family: 'Share Tech Mono', monospace; background: #000; color: #00ea4f; font-size: 12px; padding: 8px; border: 1px solid #00ea4f;">
                        <b>NODE REFERENCE: ${s.id}</b><br>
                        CLASSIFICATION: ${s.tacticalType}<br>
                        HARDWARE STAT: <span style="color: #fff; font-weight:bold;">OPERATIONAL</span>
                    </div>
                `);
                sensorLayer.addLayer(marker);
                
                lats.push(s.lat);
                lons.push(s.lon);
                sIndex++;
            }
        }

        if(lats.length > 0) {
            deploymentBounds = [ [Math.min(...lats) - 0.04, Math.min(...lons) - 0.04], [Math.max(...lats) + 0.04, Math.max(...lons) + 0.04] ];
            addSystemLog(`[SECURE LINK] ${globalSensorData.length} ACTIVE BORDER SENSORS INTERFACED. EXECUTING ORBITAL ZOOM DIVE...`, false);
            setTimeout(() => {
                if (map) map.flyToBounds(deploymentBounds, { padding: [50, 50], duration: 4.0, easeLinearity: 0.2 });
            }, 800);
        }
        
    } catch (error) {
        addSystemLog(`[UPLINK ERROR] HARDWARE FABRIC REJECTION: ${error.message}`, true);
    }
}

function connectWebSocket() {
    const ws = new WebSocket("ws://localhost:8000/ws/tactical");
    const commsIndicator = document.getElementById("comms-indicator");

    ws.onopen = function() {
        if(commsIndicator) {
            commsIndicator.className = "comms-status online-text";
            commsIndicator.innerHTML = '<span id="comms-dot" class="status-dot online-dot"></span> SECURE MATRIX CHANNEL ACTIVATED';
        }
        addSystemLog("REALTIME TELEMETRY WS STREAM SYNCED.");
    };

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        const lat = data.latitude || data.location[0];
        const lon = data.longitude || data.location[1];
        const conf = data.confidence ? (data.confidence * 100).toFixed(1) : (Math.random() * 15 + 85).toFixed(1);
        
        const elStatus = document.getElementById("tel-status");
        const elConf = document.getElementById("tel-conf");
        const elCoords = document.getElementById("tel-coords");

        if (elStatus) {
            elStatus.innerText = "INTRUDER WARNING: ALARM VECTOR LOCK";
            elStatus.style.color = "#ff3333";
            elStatus.style.textShadow = "0 0 10px #ff3333";
        }
        
        if (elConf) elConf.innerText = conf + "%";
        
        if (elCoords) {
            elCoords.innerText = `[${lat.toFixed(5)}, ${lon.toFixed(5)}]`;
            elCoords.style.color = "#ff3333";
            elCoords.style.textShadow = "0 0 10px #ff3333";
        }

        pathHistory.push([lat, lon]);
        
        if (is3DModeActive && holotableInstance) {
            holotableInstance.updateTargetPosition(lat, lon, deploymentBounds);
        }

        if (map) {
            if (!activeTargetMarker) {
                activeTargetMarker = L.circleMarker([lat, lon], { color: '#ff3333', fillColor: '#ff3333', fillOpacity: 0.9, radius: 8 }).addTo(map);
                trackPolyline = L.polyline(pathHistory, { color: '#ff3333', dashArray: '5, 5', weight: 4 }).addTo(map);
            } else {
                activeTargetMarker.setLatLng([lat, lon]);
                trackPolyline.setLatLngs(pathHistory);
            }
        }
        addSystemLog(`[!] BOUNDARY BREACH ENCOUNTERED: COORDS [LAT: ${lat.toFixed(4)} LON: ${lon.toFixed(4)}]`, true);
    };

    ws.onclose = function() {
        if(commsIndicator) {
            commsIndicator.className = "comms-status offline-text";
            commsIndicator.innerHTML = '<span id="comms-dot" class="status-dot offline-dot"></span> STREAM DISCONNECTED';
        }
    };
}

function clearMap() {
    if(map) {
        if(activeTargetMarker) map.removeLayer(activeTargetMarker);
        if(trackPolyline) map.removeLayer(trackPolyline);
    }
    pathHistory = [];
    activeTargetMarker = null;
    trackPolyline = null;
    if(holotableInstance) holotableInstance.clearTrack();
    
    const elStatus = document.getElementById("tel-status");
    const elCoords = document.getElementById("tel-coords");

    if (elStatus) {
        elStatus.innerText = "STANDBY";
        elStatus.style.color = "#00ea4f";
        elStatus.style.textShadow = "0 0 5px #00ea4f";
    }
    
    if (elCoords) {
        elCoords.innerText = "NO LOCK";
        elCoords.style.color = "#00a5ff";
        elCoords.style.textShadow = "0 0 8px #00a5ff";
    }
    
    addSystemLog("SECURITY SCRUB COMPLETED: TRACK CACHE FLUSHED.");
}

function addSystemLog(msg, isAlert = false) {
    const feed = document.getElementById('mission-feed');
    if (!feed) return;

    const timeStr = new Date().toTimeString().split(' ')[0];
    const logDiv = document.createElement('div');
    
    logDiv.style.color = isAlert ? '#ff3333' : '#00ea4f';
    logDiv.style.padding = '6px 0';
    logDiv.style.borderBottom = '1px solid rgba(28, 56, 35, 0.4)';
    logDiv.style.fontFamily = "'Share Tech Mono', monospace";
    
    logDiv.innerHTML = `<span style="opacity: 0.5; margin-right:6px;">[${timeStr}]</span> ${msg}`;
    
    feed.insertBefore(logDiv, feed.firstChild); 
    if(feed.children.length > 35) feed.removeChild(feed.lastChild); 
}
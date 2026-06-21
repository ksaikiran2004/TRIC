# TRIC // TACTICAL ORCHESTRATOR
**Trinetra Rapid Interception Command (Air-Gapped C4ISR Prototype)**

![System Status](https://img.shields.io/badge/STATUS-OPERATIONAL-00ea4f?style=for-the-badge)
![Network](https://img.shields.io/badge/NETWORK-AIR--GAPPED-ff3333?style=for-the-badge)
![Vision](https://img.shields.io/badge/VISION-YOLOv8--SMALL-blue?style=for-the-badge)

## MISSION OVERVIEW
TRIC is a highly modular, locally-hosted Command, Control, Communications, Computers, Intelligence, Surveillance, and Reconnaissance (C4ISR) dashboard. It is engineered to fuse multi-node IoT sensor telemetry with live, AI-processed UAV optical feeds to track, classify, and intercept border intrusions in real-time.

The system is designed for **Strict Zero-Trust Air-Gapped Deployments**. Once dependencies and map matrices are secured, TRIC operates entirely offline, making it impervious to external network jamming or cloud-infrastructure latency.

---

## CORE ARCHITECTURE

The repository is structured using a strict MVC separation of concerns, balancing heavy Python backend mathematical routing with a lightweight, high-performance Vanilla JavaScript frontend.

### 1. The Brain // Backend Operations (`/backend`)
* **`vision_processor.py`**: The Optical Subsystem. Utilizes **OpenCV** and **YOLOv8 (Ultralytics)** for real-time edge-AI object detection, wrapping human and vehicle targets in tactical HUD telemetry.
* **`/orchestrator` & `/tracking`**: The Mathematical Core. Parses raw JSON payloads, calculates trajectory paths, and classifies target movement vectors.
* **`/simulation`**: The War-Game Engine. Generates synthetic sensor node deployments and simulates synchronized intrusion events across the topographical grid.
* **Data Storage (`/data`)**: Utilizes **SQLite** for asynchronous logging of system alerts, maintaining a historical black-box record of all tracked entities.

### 2. The Glass // Tactical Frontend (`/frontend`)
* **2D Macro Topography (`Leaflet.js`)**: An offline Slippy Map Tile engine pulling localized, high-resolution satellite imagery directly from the hard drive. 
* **3D WebGL Holotable (`Three.js`)**: A bespoke, localized 3D rendering engine. Upon reaching operational zoom thresholds, the dashboard collapses the 2D UI and boots a live mathematical wireframe mesh of the local terrain to visualize altitude and threat elevation.

---

## DEPLOYMENT PROTOCOL

### Phase 1: Environment Initialization
` ` `bash
# Install critical local dependencies
pip install flask opencv-python ultralytics requests numpy
` ` `

### Phase 2: Secure the Air-Gap (Map Acquisition)
*TRIC requires localized topographic matrices to operate offline.*
Execute the localized script to rip targeting coordinates from Esri's military-grade satellite servers.
` ` `bash
python map_fetcher.py
` ` `

### Phase 3: System Boot
Execute the core routing application. The system will bridge the OpenCV UAV feed, establish the SQLite connection, and host the dashboard on the local network.
` ` `bash
python app.py
` ` `
*Access the Tactical Glass at: `http://127.0.0.1:5000`*

---

## DATA FLOW & SYSTEM ARCHITECTURE
The following matrix illustrates the real-time telemetry and optical data pipelines within the TRIC edge-compute environment.

` ` `mermaid
graph LR
    %% Data Sources
    subgraph SENSORS [FIELD DEPLOYMENT]
        S1[Acoustic Nodes]
        S2[Seismic Nodes]
        S3[UAV Optical Feed]
    end

    %% Backend Processing
    subgraph BACKEND [PYTHON C4ISR CORE]
        WS[WebSocket Manager]
        YOLO{YOLOv8s Vision Engine}
        ORCH[Alert Orchestrator]
        DB[(SQLite Black Box)]
        FLASK[Flask HTTP Bridge]
    end

    %% Frontend UI
    subgraph FRONTEND [TACTICAL GLASS UI]
        DASH[Main Dashboard]
        MAP[2D Offline Map]
        HOLO[3D WebGL Holotable]
    end

    %% Connections
    S1 -. JSON Telemetry .-> WS
    S2 -. JSON Telemetry .-> WS
    S3 == Raw Frames ==> YOLO
    
    WS --> ORCH
    YOLO == Bounding Boxes & Threat Level ==> ORCH
    
    ORCH --> DB
    ORCH --> FLASK
    
    FLASK == HTTP/WS Uplink ==> DASH
    DASH --> MAP
    DASH --> HOLO
    
    %% Styling (Neon Aesthetic)
    style S1 fill:#1a1a1a,stroke:#00ea4f,stroke-width:2px,color:#fff
    style S2 fill:#1a1a1a,stroke:#00ea4f,stroke-width:2px,color:#fff
    style S3 fill:#1a1a1a,stroke:#ff3333,stroke-width:2px,color:#fff
    style YOLO fill:#2d1b1b,stroke:#ff3333,stroke-width:4px,color:#fff
    style HOLO fill:#15231b,stroke:#00ea4f,stroke-width:4px,color:#fff
    style DB fill:#1a1a1a,stroke:#00a5ff,color:#fff
` ` `

---

## LICENSE & CLASSIFICATION
**UNCLASSIFIED // FOR DEVELOPMENT PROTOTYPING ONLY**
This MVP architecture is designed for demonstration and structural validation. Production deployment requires transition from SQLite to TimescaleDB/Kafka, and WebRTC video pipelining.
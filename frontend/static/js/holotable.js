// TRIC C4ISR - LOCAL 3D HOLOTABLE ENGINE (VANILLA WEBGL)

class TacticalHolotable {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;
        
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.terrainMesh = null;
        this.targetMarker = null;
        this.pathLine = null;
        this.pathCoordinates = [];
        
        this.isAnimating = false;
        this.interactionMode = 'rotate'; // rotate, pan, zoom
        
        // Mouse Tracking state
        this.isDragging = false;
        this.previousMousePosition = { x: 0, y: 0 };
        
        this.init();
    }

    init() {
        // 1. Scene setup
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x050706);

        // 2. Camera Setup
        this.camera = new THREE.PerspectiveCamera(45, this.width / this.height, 1, 2000);
        this.camera.position.set(0, 150, 250);
        this.camera.lookAt(0, 0, 0);

        // 3. WebGL Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
        this.renderer.setSize(this.width, this.height);
        this.container.appendChild(this.renderer.domElement);

        // 4. Build Topographical Grid
        this.buildTerrainMesh();

        // 5. Tactical Lighting
        const ambientLight = new THREE.AmbientLight(0x113322);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0x00ea4f, 0.8);
        directionalLight.position.set(1, 1, 1).normalize();
        this.scene.add(directionalLight);

        // 6. Build Calibration Radar Rings
        this.buildRadarGrid();

        // 7. Setup Intercept Track Visualizers
        this.initTrackingLayers();

        // 8. Bind Control Hooks
        this.setupInputHandlers();
        
        // 9. Fire Render Loop
        this.isAnimating = true;
        this.animate();
    }

    buildTerrainMesh() {
        const gridSegments = 63; 
        const size = 200;
        
        const geometry = new THREE.PlaneGeometry(size, size, gridSegments, gridSegments);
        const positions = geometry.attributes.position;
        
        for (let i = 0; i < positions.count; i++) {
            const x = positions.getX(i);
            const y = positions.getY(i);
            
            let elevation = Math.sin(x * 0.05) * Math.cos(y * 0.05) * 20;
            elevation += Math.sin(x * 0.1) * 5;
            elevation += Math.cos(y * 0.15) * 3;
            
            if (Math.abs(x) < 30) {
                elevation *= 0.3; 
            }
            positions.setZ(i, elevation);
        }
        geometry.computeVertexNormals();

        const material = new THREE.MeshBasicMaterial({
            color: 0x384d3c,
            wireframe: true,
            transparent: true,
            opacity: 0.4
        });

        this.terrainMesh = new THREE.Mesh(geometry, material);
        this.terrainMesh.rotation.x = -Math.PI / 2;
        this.scene.add(this.terrainMesh);
    }

    buildRadarGrid() {
        const ringMaterial = new THREE.LineBasicMaterial({ color: 0x5b7a61, transparent: true, opacity: 0.3 });
        for (let r = 40; r <= 120; r += 40) {
            const ringGeom = new THREE.RingGeometry(r - 0.5, r + 0.5, 64);
            const ring = new THREE.LineLoop(ringGeom, ringMaterial);
            ring.rotation.x = Math.PI / 2;
            ring.position.y = -20;
            this.scene.add(ring);
        }
    }

    initTrackingLayers() {
        const dotGeom = new THREE.CylinderGeometry(3, 3, 15, 6);
        const dotMat = new THREE.MeshBasicMaterial({ color: 0xff3333, wireframe: true });
        this.targetMarker = new THREE.Mesh(dotGeom, dotMat);
        this.targetMarker.visible = false;
        this.scene.add(this.targetMarker);

        const pathMat = new THREE.LineBasicMaterial({ color: 0xff3333, linewidth: 2 });
        const maxPoints = 500;
        const positions = new Float32Array(maxPoints * 3);
        const pathGeom = new THREE.BufferGeometry();
        pathGeom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        
        this.pathLine = new THREE.Line(pathGeom, pathMat);
        this.scene.add(this.pathLine);
    }

    updateTargetPosition(lat, lon, originalBounds) {
        if (!originalBounds || originalBounds.length === 0) return;

        const minLat = originalBounds[0][0], maxLat = originalBounds[1][0];
        const minLon = originalBounds[0][1], maxLon = originalBounds[1][1];

        const pctX = (lon - minLon) / (maxLon - minLon || 1);
        const pctY = (lat - minLat) / (maxLat - minLat || 1);

        const x3d = (pctX - 0.5) * 180;
        const z3d = -(pctY - 0.5) * 180;

        let y3d = Math.sin(x3d * 0.05) * Math.cos(-z3d * 0.05) * 20; 

        this.targetMarker.position.set(x3d, y3d + 7.5, z3d);
        this.targetMarker.visible = true;

        this.pathCoordinates.push(new THREE.Vector3(x3d, y3d + 1, z3d));
        this.renderPathTrail();
    }

    renderPathTrail() {
        const positions = this.pathLine.geometry.attributes.position.array;
        let count = Math.min(this.pathCoordinates.length, 500);
        
        for (let i = 0; i < count; i++) {
            positions[i * 3] = this.pathCoordinates[i].x;
            positions[i * 3 + 1] = this.pathCoordinates[i].y;
            positions[i * 3 + 2] = this.pathCoordinates[i].z;
        }
        this.pathLine.geometry.setDrawRange(0, count);
        this.pathLine.geometry.attributes.position.needsUpdate = true;
    }

    setupInputHandlers() {
        this.container.addEventListener('mousedown', (e) => {
            this.isDragging = true;
            this.previousMousePosition = { x: e.clientX, y: e.clientY };
        });

        window.addEventListener('mouseup', () => { this.isDragging = false; });

        this.container.addEventListener('mousemove', (e) => {
            if (!this.isDragging) return;
            const deltaMove = { x: e.clientX - this.previousMousePosition.x, y: e.clientY - this.previousMousePosition.y };

            if (this.interactionMode === 'rotate') {
                this.terrainMesh.rotation.z += deltaMove.x * 0.005;
                this.terrainMesh.rotation.x += deltaMove.y * 0.005; 
            } else if (this.interactionMode === 'pan') {
                this.camera.position.x -= deltaMove.x * 0.5;
                this.camera.position.y += deltaMove.y * 0.5;
            }
            this.previousMousePosition = { x: e.clientX, y: e.clientY };
        });

        this.container.addEventListener('wheel', (e) => {
            e.preventDefault();
            this.camera.position.z += e.deltaY * 0.2;
            this.camera.position.z = Math.max(50, Math.min(this.camera.position.z, 600));
        });
    }

    setInteractionMode(mode) {
        this.interactionMode = mode;
    }

    clearTrack() {
        this.pathCoordinates = [];
        this.targetMarker.visible = false;
        this.pathLine.geometry.setDrawRange(0, 0);
        this.pathLine.geometry.attributes.position.needsUpdate = true;
    }

    resize() {
        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;
        this.camera.aspect = this.width / this.height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.width, this.height);
    }

    animate() {
        if (!this.isAnimating) return;
        requestAnimationFrame(() => this.animate());
        
        if (this.targetMarker.visible) {
            this.targetMarker.rotation.y += 0.02;
        }
        this.renderer.render(this.scene, this.camera);
    }

    shutdown() {
        this.isAnimating = false;
        if (this.renderer) {
            this.container.removeChild(this.renderer.domElement);
            this.renderer.dispose();
        }
    }
}
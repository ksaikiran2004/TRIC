// TRIC C4ISR - TACTICAL 3D HOLOTABLE (FRACTAL TERRAIN & COMPOSITE HARDWARE)

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
        this.sensorGroup = new THREE.Group();
        this.borderWallGroup = new THREE.Group();
        
        this.isAnimating = false;
        this.animatedSensors = []; 
        
        this.isDragging = false;
        this.previousMousePosition = { x: 0, y: 0 };
        this.altimeterEl = document.getElementById('alt-val');
        
        this.init();
    }

    init() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x050706);
        this.scene.fog = new THREE.FogExp2(0x050706, 0.0025); 

        this.camera = new THREE.PerspectiveCamera(45, this.width / this.height, 1, 2000);
        this.camera.position.set(0, 150, 200);
        this.camera.lookAt(0, 0, 0);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
        this.renderer.setSize(this.width, this.height);
        this.container.appendChild(this.renderer.domElement);

        this.scene.add(new THREE.AmbientLight(0x222222));
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1.5);
        directionalLight.position.set(100, 200, 50);
        this.scene.add(directionalLight);

        this.buildFractalTerrain();
        this.scene.add(this.borderWallGroup);
        this.scene.add(this.sensorGroup);
        this.initTrackingLayers();

        this.setupInputHandlers();
        this.isAnimating = true;
        this.animate();
        window.addEventListener('resize', () => this.resize());
    }

    // ==========================================
    // FRACTAL BROWNIAN MOTION (REALISTIC MOUNTAINS)
    // ==========================================
    buildFractalTerrain() {
        const gridSegments = 180; 
        const size = 400;
        
        const geometry = new THREE.PlaneGeometry(size, size, gridSegments, gridSegments);
        const positions = geometry.attributes.position;
        const colors = [];
        const colorObj = new THREE.Color();
        
        for (let i = 0; i < positions.count; i++) {
            const x = positions.getX(i);
            const y = positions.getY(i);
            
            // Layered frequencies to create chaotic, natural-looking mountains
            let elevation = 0;
            elevation += Math.sin(x * 0.015) * Math.cos(y * 0.015) * 40; // Base macro landscape
            elevation += Math.sin(x * 0.05 + y * 0.02) * 15;             // Mid-level ridges
            elevation += Math.cos(x * 0.1 - y * 0.08) * 5;               // High-frequency rocks
            elevation += Math.sin(x * 0.3) * Math.cos(y * 0.3) * 1.5;    // Micro-surface noise
            
            // Carve a jagged valley through the center for the border
            if (Math.abs(x) < 50) {
                elevation -= (50 - Math.abs(x)) * 0.5;
            }
            
            // Flatten the deep bottoms
            elevation = Math.max(elevation, Math.random() * 1.5);

            positions.setZ(i, elevation);

            // Tactical Topo Shading
            if (elevation < 5) colorObj.setHex(0x0a1a12);      
            else if (elevation < 20) colorObj.setHex(0x153320); 
            else if (elevation < 40) colorObj.setHex(0x384d3c); 
            else colorObj.setHex(0x5a7a60);                     
            
            colors.push(colorObj.r, colorObj.g, colorObj.b);
        }
        
        geometry.computeVertexNormals();
        geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

        const solidMaterial = new THREE.MeshPhongMaterial({ vertexColors: true, flatShading: true, shininess: 2 });
        const wireMaterial = new THREE.MeshBasicMaterial({ color: 0x00ea4f, wireframe: true, transparent: true, opacity: 0.08 });

        this.terrainMesh = new THREE.Mesh(geometry, solidMaterial);
        this.terrainMesh.add(new THREE.Mesh(geometry, wireMaterial)); 
        this.terrainMesh.rotation.x = -Math.PI / 2;
        this.scene.add(this.terrainMesh);
    }

    latLonTo3D(lat, lon, originalBounds) {
        const minLat = originalBounds[0][0], maxLat = originalBounds[1][0];
        const minLon = originalBounds[0][1], maxLon = originalBounds[1][1];

        const x3d = ((lon - minLon) / (maxLon - minLon || 1) - 0.5) * 350;
        const z3d = -((lat - minLat) / (maxLat - minLat || 1) - 0.5) * 350;
        
        // Exact same math as terrain generator to pin objects to the ground perfectly
        let y3d = 0;
        y3d += Math.sin(x3d * 0.015) * Math.cos(-z3d * 0.015) * 40;
        y3d += Math.sin(x3d * 0.05 + -z3d * 0.02) * 15;
        y3d += Math.cos(x3d * 0.1 - -z3d * 0.08) * 5;
        if (Math.abs(x3d) < 50) y3d -= (50 - Math.abs(x3d)) * 0.5;
        y3d = Math.max(y3d, 1.5);
        
        return new THREE.Vector3(x3d, y3d, z3d);
    }

    buildTacticalBorder(borderCoords, originalBounds) {
        while(this.borderWallGroup.children.length > 0){ this.borderWallGroup.remove(this.borderWallGroup.children[0]); }

        const wallMat = new THREE.MeshBasicMaterial({
            color: 0xff1100, transparent: true, opacity: 0.4, 
            blending: THREE.AdditiveBlending, side: THREE.DoubleSide, depthWrite: false
        });

        const points3D = borderCoords.map(coord => this.latLonTo3D(coord[0], coord[1], originalBounds));

        for (let i = 0; i < points3D.length - 1; i++) {
            const p1 = points3D[i], p2 = points3D[i + 1];
            const plane = new THREE.Mesh(new THREE.PlaneGeometry(p1.distanceTo(p2), 80), wallMat);
            plane.position.set((p1.x + p2.x) / 2, (p1.y + p2.y) / 2 + 30, (p1.z + p2.z) / 2);
            plane.lookAt(p1.x, plane.position.y, p1.z);
            plane.rotateY(Math.PI / 2);
            this.borderWallGroup.add(plane);
        }
    }

    // ==========================================
    // COMPOSITE MILITARY HARDWARE GENERATION
    // ==========================================
    buildRadarNode() {
        const group = new THREE.Group();
        const darkMat = new THREE.MeshPhongMaterial({ color: 0x222222, flatShading: true });
        const redMat = new THREE.MeshPhongMaterial({ color: 0xff3333, flatShading: true });

        // Base & Mast
        const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.8, 6, 8), darkMat);
        mast.position.y = 3;
        group.add(mast);

        // Spinning Dish
        const dishGroup = new THREE.Group();
        dishGroup.position.y = 6.5;
        
        const dish = new THREE.Mesh(new THREE.BoxGeometry(3, 1.5, 0.5), darkMat);
        dish.rotation.x = Math.PI / 6; // Angled to the sky
        const emitFace = new THREE.Mesh(new THREE.BoxGeometry(2.8, 1.3, 0.6), redMat);
        emitFace.rotation.x = Math.PI / 6;
        
        dishGroup.add(dish);
        dishGroup.add(emitFace);
        group.add(dishGroup);

        // Translucent Sweeping Cone
        const beamMat = new THREE.MeshBasicMaterial({ color: 0xff3333, transparent: true, opacity: 0.15, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false });
        const beam = new THREE.Mesh(new THREE.ConeGeometry(20, 40, 16, 1, true, 0, Math.PI / 3), beamMat);
        beam.rotation.x = -Math.PI / 2;
        beam.position.y = 6.5;
        group.add(beam);

        return { model: group, spinner: dishGroup, beam: beam };
    }

    buildInfraredNode() {
        const group = new THREE.Group();
        const darkMat = new THREE.MeshPhongMaterial({ color: 0x222222, flatShading: true });
        
        const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 8, 8), darkMat);
        mast.position.y = 4;
        group.add(mast);

        const housing = new THREE.Mesh(new THREE.BoxGeometry(1.5, 1.5, 2.5), darkMat);
        housing.position.set(0, 8, 0);
        group.add(housing);

        const lensMat = new THREE.MeshBasicMaterial({ color: 0xff9900 });
        const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 2.6, 16), lensMat);
        lens.rotation.x = Math.PI / 2;
        lens.position.set(0, 8, 0);
        group.add(lens);

        return { model: group, pulseObj: lens };
    }

    buildSeismicNode() {
        const group = new THREE.Group();
        // Heavy spike driven into the ground
        const spike = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 0, 3, 6), new THREE.MeshPhongMaterial({ color: 0x333333, flatShading: true }));
        spike.position.y = 1.5;
        group.add(spike);
        
        // Ground Ripple
        const ripMat = new THREE.MeshBasicMaterial({ color: 0x00ea4f, transparent: true, opacity: 0.8, side: THREE.DoubleSide, depthWrite: false });
        const ripple = new THREE.Mesh(new THREE.RingGeometry(0.5, 1.5, 32), ripMat);
        ripple.rotation.x = -Math.PI / 2;
        ripple.position.y = 0.5;
        group.add(ripple);

        return { model: group, pulseObj: ripple };
    }

    loadSensors(sensors, originalBounds, borderCoords2D) {
        while(this.sensorGroup.children.length > 0){ this.sensorGroup.remove(this.sensorGroup.children[0]); }
        this.animatedSensors = []; 

        if (!originalBounds) return;
        this.buildTacticalBorder(borderCoords2D, originalBounds);

        sensors.forEach(sensor => {
            const pos = this.latLonTo3D(sensor.lat, sensor.lon, originalBounds);
            let type = sensor.tacticalType;

            let node;
            if (type === 'RADAR') {
                node = this.buildRadarNode();
                this.animatedSensors.push({ obj: node.spinner, beam: node.beam, type: 'RADAR_SWEEP' });
            } else if (type === 'INFRARED') {
                node = this.buildInfraredNode();
                this.animatedSensors.push({ obj: node.pulseObj, type: 'GLOW', offset: Math.random() * 2 });
            } else { 
                node = this.buildSeismicNode(); // Acoustic and Seismic use ground ripples
                this.animatedSensors.push({ obj: node.pulseObj, type: 'RIPPLE', offset: Math.random() * 2 });
            }
            
            node.model.position.copy(pos);
            this.sensorGroup.add(node.model);
        });
    }

    initTrackingLayers() {
        // Precise Red Laser Beam for Target
        const targetMat = new THREE.MeshBasicMaterial({ color: 0xff1100 });
        this.targetMarker = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0, 50, 8), targetMat);
        this.targetMarker.visible = false;
        this.scene.add(this.targetMarker);

        const pathMat = new THREE.LineBasicMaterial({ color: 0xff1100, linewidth: 4 });
        this.pathLine = new THREE.Line(new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(new Float32Array(500 * 3), 3)), pathMat);
        this.scene.add(this.pathLine);
    }

    updateTargetPosition(lat, lon, originalBounds) {
        if (!originalBounds || originalBounds.length === 0) return;
        const pos = this.latLonTo3D(lat, lon, originalBounds);

        this.targetMarker.position.set(pos.x, pos.y + 25, pos.z); // Hover above ground
        this.targetMarker.visible = true;

        this.pathCoordinates.push(new THREE.Vector3(pos.x, pos.y + 1, pos.z));
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
            const deltaX = e.clientX - this.previousMousePosition.x;
            const deltaY = e.clientY - this.previousMousePosition.y;

            if (e.buttons === 1) { 
                // Left Click: Rotate
                this.scene.rotation.y += deltaX * 0.005;
            } else if (e.buttons === 2 || e.shiftKey) { 
                // Right Click or Shift+Left Click: Pan/Drag
                this.camera.translateX(-deltaX * 0.2);
                this.camera.translateY(deltaY * 0.2);
            }
            this.previousMousePosition = { x: e.clientX, y: e.clientY };
        });

        this.container.addEventListener('wheel', (e) => {
            e.preventDefault();
            const zoomDir = Math.sign(e.deltaY);
            
            // Fly forward and dive
            this.camera.translateZ(zoomDir * 15);
            this.camera.position.y += zoomDir * 5; 
            
            this.camera.position.y = Math.max(5, Math.min(this.camera.position.y, 500));
        });

        this.container.addEventListener('contextmenu', e => e.preventDefault());
    }

    animate() {
        if (!this.isAnimating) return;
        requestAnimationFrame(() => this.animate());
        
        const time = Date.now() * 0.003;

        // Update Altimeter HUD
        if(this.altimeterEl) {
            this.altimeterEl.innerText = Math.floor(this.camera.position.y);
        }

        // Hardware Animations
        this.animatedSensors.forEach(anim => {
            if (anim.type === 'RADAR_SWEEP') {
                anim.obj.rotation.y -= 0.08; 
                anim.beam.rotation.y -= 0.08;
            } else if (anim.type === 'GLOW') {
                anim.obj.material.color.setHSL(0.1, 1, 0.4 + Math.sin(time + anim.offset) * 0.3);
            } else if (anim.type === 'RIPPLE') {
                anim.obj.scale.x += 0.08;
                anim.obj.scale.y += 0.08;
                anim.obj.material.opacity -= 0.02;
                if (anim.obj.material.opacity <= 0) {
                    anim.obj.scale.set(1, 1, 1);
                    anim.obj.material.opacity = 0.8;
                }
            }
        });

        if (this.borderWallGroup) {
            const pulse = 0.3 + Math.abs(Math.sin(time * 0.5)) * 0.2;
            this.borderWallGroup.children.forEach(child => {
                if (child.isMesh) child.material.opacity = pulse;
            });
        }

        this.renderer.render(this.scene, this.camera);
    }
resize() {
        // Forces the engine to recalculate its boundaries
        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;
        if (this.renderer && this.width > 0 && this.height > 0) {
            this.renderer.setSize(this.width, this.height);
            this.camera.aspect = this.width / this.height;
            this.camera.updateProjectionMatrix();
        }
    }
    shutdown() {
        this.isAnimating = false;
        if (this.renderer) {
            this.container.removeChild(this.renderer.domElement);
            this.renderer.dispose();
        }
    }
}
// =========================================================================
// TRIC C4ISR - TACTICAL 3D HOLOTABLE TOPOGRAPHY ENGINE
// =========================================================================

class TacticalHolotable {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;
        
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(45, this.width / this.height, 1, 4000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
        
        this.sensorGroup = new THREE.Group();
        this.borderWallGroup = new THREE.Group();
        this.animatedSensors = []; 
        this.pathCoordinates = [];
        this.isAnimating = false;
        
        this.keys = { w: false, a: false, s: false, d: false };
        this.altimeterEl = document.getElementById('alt-val');
        
        this.init();
    }

    init() {
        this.scene.background = new THREE.Color(0x040705);
        this.scene.fog = new THREE.FogExp2(0x040705, 0.0018); 
        
        this.camera.position.set(0, 350, 450);
        this.camera.lookAt(0, 0, 0);

        this.renderer.setSize(this.width, this.height);
        this.container.appendChild(this.renderer.domElement);

        this.scene.add(new THREE.AmbientLight(0x28382d));
        const dirLight = new THREE.DirectionalLight(0xffffff, 1.4);
        dirLight.position.set(150, 400, 150);
        this.scene.add(dirLight);

        this.buildOrganicTerrain();
        this.scene.add(this.borderWallGroup);
        this.scene.add(this.sensorGroup);
        this.initTrackingLayers();

        this.setupInputHandlers();
        this.isAnimating = true;
        this.animate();
        
        window.addEventListener('resize', () => this.resize());
    }

    getElevationAt(px, py) {
        // Broad sweeping continental base
        let base = Math.sin(px * 0.003) * Math.cos(py * 0.003) * 120;
        
        // Large organic hills
        let hills = Math.sin(px * 0.01 + py * 0.015) * 60;
        let hills2 = Math.cos(px * 0.02 - py * 0.01) * 40;
        
        // Minor terrain variation (No Math.abs spikes)
        let detail = Math.sin(px * 0.05) * Math.cos(py * 0.05) * 10;
        
        let elevation = base + hills + hills2 + detail + 100;
        return Math.max(elevation, 5.0);
    }

    buildOrganicTerrain() {
        const gridSegments = 250;
        const size = 900;
        
        const geometry = new THREE.PlaneGeometry(size, size, gridSegments, gridSegments);
        const positions = geometry.attributes.position;
        const colors = [];
        const colorObj = new THREE.Color();
        
        for (let i = 0; i < positions.count; i++) {
            const x = positions.getX(i);
            const y = positions.getY(i);
            
            let elevation = this.getElevationAt(x, y);
            positions.setZ(i, elevation);

            // Shading representing operational topographic contours
            if (elevation < 30) colorObj.setHex(0x06140d);      
            else if (elevation < 80) colorObj.setHex(0x10301e); 
            else if (elevation < 140) colorObj.setHex(0x2d4233); 
            else colorObj.setHex(0x738a79); // Frozen tactical crests                    
            
            colors.push(colorObj.r, colorObj.g, colorObj.b);
        }
        
        geometry.computeVertexNormals();
        geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

        // FIX: flatShading: false removes the low-poly spiky look and creates smooth, massive mountains
        const solidMat = new THREE.MeshPhongMaterial({ vertexColors: true, flatShading: false, shininess: 3 });
        const wireMat = new THREE.MeshBasicMaterial({ color: 0x00ea4f, wireframe: true, transparent: true, opacity: 0.05 });

        this.terrainMesh = new THREE.Mesh(geometry, solidMat);
        this.terrainMesh.add(new THREE.Mesh(geometry, wireMat)); 
        this.terrainMesh.rotation.x = -Math.PI / 2;
        this.scene.add(this.terrainMesh);
    }

    latLonTo3D(lat, lon, originalBounds) {
        if (!originalBounds) return new THREE.Vector3(0,0,0);
        const minLat = originalBounds[0][0], maxLat = originalBounds[1][0];
        const minLon = originalBounds[0][1], maxLon = originalBounds[1][1];
        
        const x3d = ((lon - minLon) / (maxLon - minLon || 1) - 0.5) * 800;
        const z3d = -((lat - minLat) / (maxLat - minLat || 1) - 0.5) * 800;
        
        let y3d = this.getElevationAt(x3d, -z3d);
        return new THREE.Vector3(x3d, y3d, z3d);
    }

    buildTacticalBorder(borderCoords, originalBounds) {
        if (!borderCoords) return;
        while(this.borderWallGroup.children.length > 0) {
            this.borderWallGroup.remove(this.borderWallGroup.children[0]);
        }
        
        const wallMat = new THREE.MeshBasicMaterial({ 
            color: 0xff1100, transparent: true, opacity: 0.45, 
            blending: THREE.AdditiveBlending, side: THREE.DoubleSide, depthWrite: false 
        });
        
        const points3D = borderCoords.map(coord => this.latLonTo3D(coord[0], coord[1], originalBounds));

        for (let i = 0; i < points3D.length - 1; i++) {
            const p1 = points3D[i], p2 = points3D[i + 1];
            if (!p1 || !p2) continue;
            
            const plane = new THREE.Mesh(new THREE.PlaneGeometry(p1.distanceTo(p2), 300), wallMat); 
            plane.position.set((p1.x + p2.x) / 2, (p1.y + p2.y) / 2 + 75, (p1.z + p2.z) / 2);
            plane.lookAt(p1.x, plane.position.y, p1.z);
            plane.rotateY(Math.PI / 2);
            this.borderWallGroup.add(plane);
        }
    }

    buildRadarNode() {
        const group = new THREE.Group();
        const darkMat = new THREE.MeshPhongMaterial({ color: 0x181f1a, flatShading: true });
        
        const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 1.2, 14, 8), darkMat); 
        mast.position.y = 7; 
        group.add(mast);
        
        const spinnerGroup = new THREE.Group(); 
        spinnerGroup.position.y = 15;
        
        const dish = new THREE.Mesh(new THREE.BoxGeometry(5, 2.5, 0.6), darkMat); 
        dish.rotation.x = Math.PI / 6;
        
        const emitFace = new THREE.Mesh(new THREE.BoxGeometry(4.7, 2.2, 0.7), new THREE.MeshBasicMaterial({ color: 0xff2222 })); 
        emitFace.rotation.x = Math.PI / 6;
        
        const beam = new THREE.Mesh(new THREE.ConeGeometry(30, 60, 16, 1, true, 0, Math.PI / 3), new THREE.MeshBasicMaterial({ color: 0xff3333, transparent: true, opacity: 0.18, side: THREE.DoubleSide, blending: THREE.AdditiveBlending, depthWrite: false }));
        beam.rotation.x = -Math.PI / 2; 
        
        spinnerGroup.add(dish); 
        spinnerGroup.add(emitFace); 
        spinnerGroup.add(beam);
        group.add(spinnerGroup);
        
        return { model: group, spinner: spinnerGroup, type: 'RADAR_SWEEP' };
    }

    buildInfraredNode() {
        const group = new THREE.Group();
        const darkMat = new THREE.MeshPhongMaterial({ color: 0x1c211d, flatShading: true });
        
        const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 11, 8), darkMat); 
        mast.position.y = 5.5; 
        group.add(mast);
        
        const lens = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 1.0, 4, 16), new THREE.MeshBasicMaterial({ color: 0xff9900 })); 
        lens.rotation.x = Math.PI / 2; 
        lens.position.y = 11; 
        group.add(lens);
        
        return { model: group, pulseObj: lens };
    }

    buildSeismicNode() {
        const group = new THREE.Group();
        const spike = new THREE.Mesh(new THREE.CylinderGeometry(1.8, 0, 4, 6), new THREE.MeshPhongMaterial({ color: 0x2b332e, flatShading: true })); 
        spike.position.y = 2.0; 
        group.add(spike);
        
        const ripple = new THREE.Mesh(new THREE.RingGeometry(0.6, 3.0, 32), new THREE.MeshBasicMaterial({ color: 0x00ea4f, transparent: true, opacity: 0.85, side: THREE.DoubleSide, depthWrite: false })); 
        ripple.rotation.x = -Math.PI / 2; 
        ripple.position.y = 0.6; 
        group.add(ripple);
        
        return { model: group, pulseObj: ripple };
    }

    loadSensors(sensors, originalBounds, borderCoords2D) {
        while(this.sensorGroup.children.length > 0) {
            this.sensorGroup.remove(this.sensorGroup.children[0]);
        }
        this.animatedSensors = []; 
        if (!originalBounds) return;
        
        this.buildTacticalBorder(borderCoords2D, originalBounds);

        sensors.forEach(sensor => {
            const pos = this.latLonTo3D(sensor.lat, sensor.lon, originalBounds);
            let node;
            if (sensor.tacticalType === 'RADAR') { 
                node = this.buildRadarNode(); 
                this.animatedSensors.push({ obj: node.spinner, type: 'RADAR_SWEEP' }); 
            } else if (sensor.tacticalType === 'INFRARED') { 
                node = this.buildInfraredNode(); 
                this.animatedSensors.push({ obj: node.pulseObj, type: 'GLOW', offset: Math.random() * 2 }); 
            } else { 
                node = this.buildSeismicNode(); 
                this.animatedSensors.push({ obj: node.pulseObj, type: 'RIPPLE', offset: Math.random() * 2 }); 
            }
            node.model.position.copy(pos);
            this.sensorGroup.add(node.model);
        });
    }

    initTrackingLayers() {
        this.targetMarker = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0, 150, 8), new THREE.MeshBasicMaterial({ color: 0xff1100 }));
        this.targetMarker.visible = false; 
        this.scene.add(this.targetMarker);
        
        this.pathLine = new THREE.Line(new THREE.BufferGeometry().setAttribute('position', new THREE.BufferAttribute(new Float32Array(500 * 3), 3)), new THREE.LineBasicMaterial({ color: 0xff1100, linewidth: 5 }));
        this.scene.add(this.pathLine);
    }

    updateTargetPosition(lat, lon, originalBounds) {
        if (!originalBounds || originalBounds.length === 0) return;
        const pos = this.latLonTo3D(lat, lon, originalBounds);
        
        this.targetMarker.position.set(pos.x, pos.y + 75, pos.z); 
        this.targetMarker.visible = true;
        this.pathCoordinates.push(new THREE.Vector3(pos.x, pos.y + 2, pos.z));
        
        const positions = this.pathLine.geometry.attributes.position.array;
        let count = Math.min(this.pathCoordinates.length, 500);
        for (let i = 0; i < count; i++) { 
            positions[i*3] = this.pathCoordinates[i].x; 
            positions[i*3+1] = this.pathCoordinates[i].y; 
            positions[i*3+2] = this.pathCoordinates[i].z; 
        }
        this.pathLine.geometry.setDrawRange(0, count); 
        this.pathLine.geometry.attributes.position.needsUpdate = true;
    }

    setupInputHandlers() {
        let isDragging = false;
        let lastX = 0, lastY = 0;

        this.container.addEventListener('mousedown', (e) => {
            isDragging = true; 
            lastX = e.clientX; 
            lastY = e.clientY;
        });

        window.addEventListener('mouseup', () => { isDragging = false; });

        this.container.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            const deltaX = e.clientX - lastX;
            const deltaY = e.clientY - lastY;
            
            if (e.buttons === 1 && !e.shiftKey) {
                this.scene.rotation.y += deltaX * 0.005;
            } else {
                this.camera.position.x -= deltaX * 1.2;
                this.camera.position.z -= deltaY * 1.2;
            }
            
            lastX = e.clientX; 
            lastY = e.clientY;
        });

        this.container.addEventListener('wheel', (e) => {
            e.preventDefault();
            this.camera.translateZ(Math.sign(e.deltaY) * 25);
            this.camera.position.y = Math.max(10, Math.min(this.camera.position.y, 900));
        });

        window.addEventListener('keydown', (e) => {
            const code = e.key.toLowerCase();
            if (code === 'w' || code === 'arrowup') this.keys.w = true;
            if (code === 'a' || code === 'arrowleft') this.keys.a = true;
            if (code === 's' || code === 'arrowdown') this.keys.s = true;
            if (code === 'd' || code === 'arrowright') this.keys.d = true;
        });
        
        window.addEventListener('keyup', (e) => {
            const code = e.key.toLowerCase();
            if (code === 'w' || code === 'arrowup') this.keys.w = false;
            if (code === 'a' || code === 'arrowleft') this.keys.a = false;
            if (code === 's' || code === 'arrowdown') this.keys.s = false;
            if (code === 'd' || code === 'arrowright') this.keys.d = false;
        });

        this.container.addEventListener('contextmenu', e => e.preventDefault());
    }

    clearTrack() {
        this.pathCoordinates = [];
        this.targetMarker.visible = false;
        this.pathLine.geometry.setDrawRange(0, 0);
        this.pathLine.geometry.attributes.position.needsUpdate = true;
    }

    animate() {
        if (!this.isAnimating) return;
        requestAnimationFrame(() => this.animate());
        
        const stepRate = 6.0;
        if (this.keys.w) this.camera.position.z -= stepRate;
        if (this.keys.s) this.camera.position.z += stepRate;
        if (this.keys.a) this.camera.position.x -= stepRate;
        if (this.keys.d) this.camera.position.x += stepRate;

        if(this.altimeterEl) {
            this.altimeterEl.innerText = Math.floor(this.camera.position.y);
        }

        const tick = Date.now() * 0.003;
        
        this.animatedSensors.forEach(anim => {
            if (anim.type === 'RADAR_SWEEP') { 
                anim.obj.rotation.y -= 0.12; 
            } else if (anim.type === 'GLOW') { 
                anim.obj.material.color.setHSL(0.1, 1, 0.4 + Math.sin(tick + anim.offset) * 0.35); 
            } else if (anim.type === 'RIPPLE') {
                anim.obj.scale.x += 0.12; 
                anim.obj.scale.y += 0.12; 
                anim.obj.material.opacity -= 0.035;
                if (anim.obj.material.opacity <= 0) { 
                    anim.obj.scale.set(1, 1, 1); 
                    anim.obj.material.opacity = 0.85; 
                }
            }
        });

        if (this.borderWallGroup) {
            const baselinePulse = 0.25 + Math.abs(Math.sin(tick * 0.5)) * 0.35;
            this.borderWallGroup.children.forEach(child => {
                if(child.isMesh) child.material.opacity = baselinePulse;
            });
        }

        this.renderer.render(this.scene, this.camera);
    }

    resize() {
        if(!this.container) return;
        this.width = this.container.clientWidth; 
        this.height = this.container.clientHeight;
        if (this.renderer && this.width > 0) { 
            this.renderer.setSize(this.width, this.height); 
            this.camera.aspect = this.width / this.height; 
            this.camera.updateProjectionMatrix(); 
        }
    }
    
    shutdown() { 
        this.isAnimating = false; 
        if (this.renderer) { 
            if(this.container.contains(this.renderer.domElement)) {
                this.container.removeChild(this.renderer.domElement); 
            }
            this.renderer.dispose(); 
        } 
    }
}
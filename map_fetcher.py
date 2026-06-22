import os
import math
import requests
import time

def deg2num(lat_deg, lon_deg, zoom):
    """Converts GPS coordinates to slippy map tile X/Y math."""
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def download_tactical_tiles():
    print(">>> INITIATING SATELLITE UPLINK: DOWNLOADING OFFLINE MAP MATRIX...")
    
    # Target: Kashmir Border Region
    min_lat, max_lat = 33.5, 34.5
    min_lon, max_lon = 73.5, 74.5
    
    # Zoom levels: 5 (Macro India view) and 11 (Tactical trigger view)
    zoom_levels = [5, 6, 7, 10, 11] 
    
    # Using Esri World Imagery
    headers = {'User-Agent': 'TRIC-C4ISR-Node'}
    total_downloaded = 0
    
    for z in zoom_levels:
        x_min, y_max = deg2num(min_lat, min_lon, z)
        x_max, y_min = deg2num(max_lat, max_lon, z)
        
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                # Ensure directory exists
                tile_dir = os.path.join('data', 'offline_tiles', str(z), str(x))
                os.makedirs(tile_dir, exist_ok=True)
                
                filepath = os.path.join(tile_dir, f"{y}.png")
                
                # Skip if already downloaded
                if os.path.exists(filepath):
                    continue
                    
                # Esri Tile Format URL
                url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                
                try:
                    response = requests.get(url, headers=headers, timeout=5)
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        total_downloaded += 1
                        print(f"[+] Extracted Tile: Z:{z} X:{x} Y:{y}")
                    time.sleep(0.1) # Be polite to the server
                except Exception as e:
                    print(f"[-] Failed to download {url}")

    print(f"\n>>> SATELLITE ACQUISITION COMPLETE. {total_downloaded} NEW TILES SECURED IN AIR-GAP STORAGE.")

if __name__ == "__main__":
    download_tactical_tiles()
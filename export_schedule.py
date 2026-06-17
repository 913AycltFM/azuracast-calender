import json
import urllib.request
from datetime import datetime, timezone
import os

# --- CONFIGURATION ---
AZURACAST_URL = "https://radio.913aycltfm.com"

# Dictionary mapping your station IDs to their display names AND their public player links
STATIONS = {
    "91.3_ayclt_fm": {
        "name": "91.3_ayclt_fm",
        "public_url": f"{AZURACAST_URL}/public/91.3_ayclt_fm"
    },
    "91.3_ayclt_fm_hd2": {
        "name": "91.3_ayclt_fm_hd2",
        "public_url": f"{AZURACAST_URL}/public/91.3_ayclt_fm_hd2"
    },
    "91.3_ayclt_fm_hd3": {
        "name": "91.3_ayclt_fm_hd3",
        "public_url": f"{AZURACAST_URL}/public/91.3_ayclt_fm_hd3"
    }
}

OUTPUT_FILE = "azuracast_schedule.ics"  # Saving directly to root folder
# ---------------------

def fetch_schedule(station_id):
    url = f"{AZURACAST_URL}/api/station/{station_id}/schedule"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': '913AycltFM-iCal-Exporter'})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching station {station_id}: {e}")
        return []

def format_ical_date(timestamp):
    try:
        dt = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
        return dt.strftime("%Y%m%dT%H%M%SZ")
    except Exception:
        return None

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE) if os.path.dirname(OUTPUT_FILE) else '.', exist_ok=True)
    now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//91.3 Ayclt FM//Unified Schedule Exporter//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    event_count = 0
    
    for station_id, info in STATIONS.items():
        station_name = info["name"]
        public_url = info["public_url"]
        
        print(f"Fetching schedule for {station_name}...")
        schedule_data = fetch_schedule(station_id)
        
        for event in schedule_data:
            summary = event.get("name", "Scheduled Broadcast").strip()
            start_ts = event.get("start_timestamp")
            end_ts = event.get("end_timestamp")
            
            if not start_ts or not end_ts or not summary:
                continue
                
            start_str = format_ical_date(start_ts)
            end_str = format_ical_date(end_ts)
            
            if not start_str or not end_str:
                continue
                
            uid = f"ayclt-{station_id}-{event.get('id', start_ts)}@913aycltfm"
            tagged_summary = f"[{station_name}] {summary}"
            
            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_str}",
                f"DTSTART:{start_str}",
                f"DTEND:{end_str}",
                f"SUMMARY:{tagged_summary}",
                f"LOCATION:{public_url}",   # <--- Dynamically sets the specific station's player link
                "END:VEVENT"
            ])
            event_count += 1
            
    ics_lines.append("END:VCALENDAR")
    
    if event_count == 0:
        fallback_start = datetime.now(timezone.utc).strftime("%Y%m%dT%H%0000Z")
        fallback_end = datetime.now(timezone.utc).strftime("%Y%m%dT%H%0500Z")
        ics_lines.insert(-1, "BEGIN:VEVENT")
        ics_lines.insert(-1, f"UID:fallback-maintenance@913aycltfm")
        ics_lines.insert(-1, f"DTSTAMP:{now_str}")
        ics_lines.insert(-1, f"DTSTART:{fallback_start}")
        ics_lines.insert(-1, f"DTEND:{fallback_end}")
        ics_lines.insert(-1, "SUMMARY:[System] Schedule Sync Active")
        ics_lines.insert(-1, f"LOCATION:{AZURACAST_URL}/public")
        ics_lines.insert(-1, "END:VEVENT")
    
    print(f"Writing {max(event_count, 1)} events to the single iCalendar file...")
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(ics_lines))
        
    print(f"Successfully saved all stations to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

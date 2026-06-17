import json
import urllib.request
from datetime import datetime, timezone
import os

# --- CONFIGURATION ---
AZURACAST_URL = "https://radio.913aycltfm.com"

# Using your exact text short-codes as the keys instead of numeric IDs
STATIONS = {
    "91.3_ayclt_fm": "91.3_ayclt_fm",
    "91.3_ayclt_fm_hd2": "91.3_ayclt_fm_hd2",
    "91.3_ayclt_fm_hd3": "91.3_ayclt_fm_hd3"
}

OUTPUT_FILE = "docs/azuracast_schedule.ics"
# ---------------------

def fetch_schedule(station_id):
    # This now safely constructs URLs like /api/station/91.3_ayclt_fm/schedule
    url = f"{AZURACAST_URL}/api/station/{station_id}/schedule"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': '913AycltFM-iCal-Exporter'})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching station {station_id}: {e}")
        return []

def format_ical_date(timestamp):
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//91.3 Ayclt FM//Unified Schedule Exporter//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    for station_id, station_name in STATIONS.items():
        print(f"Fetching schedule for {station_name}...")
        schedule_data = fetch_schedule(station_id)
        
        for event in schedule_data:
            summary = event.get("name", "Scheduled Broadcast")
            start_ts = event.get("start_timestamp")
            end_ts = event.get("end_timestamp")
            
            # Generate a clean, unique ID using the shortcode text string
            uid = f"ayclt-{station_id}-{event.get('id', start_ts)}@913aycltfm"
            
            if not start_ts or not end_ts:
                continue
                
            start_str = format_ical_date(start_ts)
            end_str = format_ical_date(end_ts)
            
            tagged_summary = f"[{station_name}] {summary}"
            
            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_str}",
                f"DTSTART:{start_str}",
                f"DTEND:{end_str}",
                f"SUMMARY:{tagged_summary}",
                f"LOCATION:{AZURACAST_URL}", 
                "END:VEVENT"
            ])
            
    ics_lines.append("END:VCALENDAR")
    
    print("Writing all stations to the single iCalendar file...")
    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(ics_lines))
        
    print(f"Successfully saved all stations to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

import json
import urllib.request
from datetime import datetime, timezone
import os

# --- CONFIGURATION ---
# Your official AzuraCast base URL
AZURACAST_URL = "https://radio.913aycltfm.com"

# Dictionary linking your AzuraCast Station IDs to your exact database names
# Swap the numeric keys ("1", "2", "3") if your actual AzuraCast station IDs differ
STATIONS = {
    "1": "91.3_ayclt_fm",
    "2": "91.3_ayclt_fm_hd2",
    "3": "91.3_ayclt_fm_hd3"
}

OUTPUT_FILE = "docs/azuracast_schedule.ics"
# ---------------------

def fetch_schedule(station_id):
    url = f"{AZURACAST_URL}/api/station/{station_id}/schedule"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': '913AycltFM-iCal-Exporter'})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching station ID {station_id}: {e}")
        return []

def format_ical_date(timestamp):
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime("%Y%m%dT%H%M%SZ")

def main():
    # Ensure the GitHub Pages docs folder exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    
    # Initialize the iCalendar framework
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//91.3 Ayclt FM//Unified Schedule Exporter//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    # Loop through each station id configured above
    for station_id, station_name in STATIONS.items():
        print(f"Fetching schedule for {station_name} (ID: {station_id})...")
        schedule_data = fetch_schedule(station_id)
        
        for event in schedule_data:
            summary = event.get("name", "Scheduled Broadcast")
            start_ts = event.get("start_timestamp")
            end_ts = event.get("end_timestamp")
            
            # Formulate a unique ID incorporating the specific station to prevent overlapping conflicts
            uid = f"ayclt-st{station_id}-{event.get('id', start_ts)}@913aycltfm"
            
            if not start_ts or not end_ts:
                continue
                
            start_str = format_ical_date(start_ts)
            end_str = format_ical_date(end_ts)
            
            # Prefixes the show title so listeners on Discord see exactly which station it is on
            tagged_summary = f"[{station_name}] {summary}"
            
            ics_lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now_str}",
                f"DTSTART:{start_str}",
                f"DTEND:{end_str}",
                f"SUMMARY:{tagged_summary}",
                # Embeds your stream base URL as the event location in Discord
                f"LOCATION:{AZURACAST_URL}", 
                "END:VEVENT"
            ])
            
    ics_lines.append("END:VCALENDAR")
    
    # Commit the unified stream elements to a single file
    print("Writing all stations to the single iCalendar file...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(ics_lines))
        
    print(f"Successfully saved all stations to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
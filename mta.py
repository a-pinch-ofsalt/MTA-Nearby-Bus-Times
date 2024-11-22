import asyncio
import aiohttp
from datetime import datetime
import pytz
import sys
from dotenv import load_dotenv
import asyncio
import os
import json
from typing import Dict

load_dotenv()

def normalize_iso_datetime(iso_datetime):
    """Fix ISO format datetime to handle timezone offsets correctly."""
    if iso_datetime and iso_datetime != "N/A":
        if "-" in iso_datetime[-6:] or "+" in iso_datetime[-6:]:
            time_part, offset_part = iso_datetime[:-6], iso_datetime[-6:]
            offset_part = offset_part.replace(":", "")
            return time_part + offset_part
    return None

def format_time_difference(arrival_time):
    # Skip invalid or missing arrival times early
    if not arrival_time or arrival_time == "N/A":
        return "N/A"

    try:
        # Normalize ISO datetime format
        arrival_time = normalize_iso_datetime(arrival_time)
        if not arrival_time:
            return "N/A"

        arrival_dt = datetime.fromisoformat(arrival_time)

        # Convert current time to offset-aware in the same timezone as arrival_dt
        now = datetime.now(pytz.timezone('America/New_York'))

        delta = (arrival_dt - now).total_seconds() // 60
        if delta <= 2:
            return "arriving"
        return f"{int(delta)} min"
    except Exception as e:
        return "N/A"

async def fetch_stop_data(session, api_key, stop_id, stop_name):
    """Fetch bus data for a single stop asynchronously."""
    base_url = "https://bustime.mta.info/api/siri/stop-monitoring.json"
    params = {
        'key': api_key,
        'MonitoringRef': stop_id
    }
    async with session.get(base_url, params=params) as response:
        if response.status == 200:
            data = await response.json()
            visits = data.get('Siri', {}).get('ServiceDelivery', {}).get('StopMonitoringDelivery', [{}])[0].get('MonitoredStopVisit', [])
            bus_info = {}
            if not visits:
                return {stop_name: bus_info}

            for visit in visits:
                journey = visit.get('MonitoredVehicleJourney', {})
                line = journey.get('PublishedLineName', 'N/A')
                destination = journey.get('DestinationName', 'N/A')
                call = journey.get('MonitoredCall', {})
                arrival_time = call.get('ExpectedArrivalTime', 'N/A')
                arrival_in_minutes = format_time_difference(arrival_time)

                if arrival_in_minutes != "N/A":
                    if line not in bus_info:
                        bus_info[line] = []
                    bus_info[line].append({
                        "destination": destination,
                        "arrival": arrival_in_minutes
                    })
            return {stop_name: bus_info}
        else:
            print(f"Error fetching data for stop ID {stop_id}: {response.status}")
            return {stop_name: {}}

async def get_bus_times(api_key, stop_ids):
    """Fetch bus data for all stops asynchronously."""
    bus_data = {}
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_stop_data(session, api_key, stop_id, stop_name)
            for stop_id, stop_name in stop_ids
        ]
        results = await asyncio.gather(*tasks)
        for result in results:
            bus_data.update(result)
    return bus_data

async def get_stops_near_location(api_key, lat, lon, lat_span=0.005, lon_span=0.005):
    print(f"APIKEY IS ${api_key}")
    print(f"LAT=%{lat}")
    """Fetch nearby stops asynchronously."""
    if not api_key or lat is None or lon is None:
        raise ValueError("Invalid parameters: Ensure api_key, lat, lon, lat_span, and lon_span are provided.")

    stop_ids = []
    base_url = "https://bustime.mta.info/api/where/stops-for-location.json"
    params = {
        "key": api_key,
        "lat": lat,
        "lon": lon,
        "latSpan": lat_span,
        "lonSpan": lon_span
    }

    # Debug log the params
    print(f"Fetching stops with params: {params}")

    async with aiohttp.ClientSession() as session:
        async with session.get(base_url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                stops = data.get('data', {}).get('stops', [])
                for stop in stops:
                    stop_id = stop.get('id')
                    stop_name = stop.get('name')
                    if stop_id and stop_name:  # Ensure valid stop ID and name
                        stop_ids.append((stop_id, stop_name))
            else:
                raise ValueError(f"Error fetching stops: HTTP {response.status}")
    return stop_ids


"""async def main():
    api_key = os.getenv("MTA_API_KEY")
    latitude = 40.84634603880562
    longitude = -73.93382115690994

    stop_ids = await get_stops_near_location(api_key, latitude, longitude)
    bus_data = await get_bus_times(api_key, stop_ids)

    # Print the resulting dictionary
    print(json.dumps(bus_data, indent=2))"""

"""if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print(json.dumps({"error": "Please provide latitude and longitude as arguments."}))
        sys.exit(1)

    try:
        latitude = float(sys.argv[1])
        longitude = float(sys.argv[2])

        api_key = os.getenv('MTA_API_KEY')
        if not api_key:
            print(json.dumps({"error": "MTA_API_KEY environment variable not set."}))
            sys.exit(1)

        stop_ids = asyncio.run(get_stops_near_location(api_key, latitude, longitude))
        bus_data = asyncio.run(get_bus_times(api_key, stop_ids))

        # Print the resulting JSON to stdout
        print(json.dumps(bus_data, indent=2))
    except ValueError as e:
        print(json.dumps({"error": f"Value error: {str(e)}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected error: {str(e)}"}))
        sys.exit(1)"""



# Include your existing helper functions (e.g., get_stops_near_location, get_bus_times) here.

async def get_bus_data(api_key: str, latitude: float, longitude: float) -> Dict:
    """
    Main function to fetch bus data.
    """
    if not api_key:
        raise ValueError("MTA_API_KEY environment variable not set.")
    
    stop_ids = await get_stops_near_location(api_key, latitude, longitude)
    bus_data = await get_bus_times(api_key, stop_ids)
    return bus_data

# Remove the if __name__ == "__main__" block entirely





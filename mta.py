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
    """Ensure the ISO datetime string is in a format compatible with datetime.fromisoformat."""
    if iso_datetime and iso_datetime != "N/A":
        # Ensure there's a colon in the timezone offset (e.g., -05:00)
        if iso_datetime[-3] == ":" and (iso_datetime[-6] in ["-", "+"]):
            return iso_datetime  # Already valid
    return iso_datetime


def format_time_difference(arrival_time):
    print(f"Arrival time: {arrival_time}, Normalized: {normalize_iso_datetime(arrival_time)}")

    if not arrival_time or arrival_time == "N/A":
        return "N/A"

    try:
        arrival_time = normalize_iso_datetime(arrival_time)
        if not arrival_time:
            return "N/A"

        arrival_dt = datetime.fromisoformat(arrival_time)

        now = datetime.now(pytz.timezone('America/New_York'))
        print(f"Current time: {now}, Arrival datetime: {arrival_dt}")

        delta = (arrival_dt - now).total_seconds() // 60
        print(f"Time difference in minutes: {delta}")

        if delta <= 2:
            return "arriving"
        elif delta < 0:
            return "N/A"  # Arrival in the past
        return int(delta)
    except Exception as e:
        print(f"Error processing time difference: {e}")
        return "N/A"



async def fetch_stop_data(session, api_key, stop_id, stop_name, truncate=5):
    base_url = "https://bustime.mta.info/api/siri/stop-monitoring.json"
    params = {
        'key': api_key,
        'MonitoringRef': stop_id
    }
    async with session.get(base_url, params=params) as response:
        if response.status == 200:
            data = await response.json()

            # Debug: Log raw response
            print(f"Raw response for stop {stop_id} ({stop_name}): {json.dumps(data, indent=2)}")

            visits = data.get('Siri', {}).get('ServiceDelivery', {}).get('StopMonitoringDelivery', [{}])[0].get('MonitoredStopVisit', [])
            if not visits:
                print(f"No visits found for stop {stop_name}.")  # Debug
                return {stop_name: {}}


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

                print(f"Line: {line}, Destination: {destination}, Arrival: {arrival_in_minutes}")  # Debug

                if arrival_in_minutes != "N/A":
                    if line not in bus_info:
                        bus_info[line] = {}
                    if destination not in bus_info[line]:
                        bus_info[line][destination] = []
                    if len(bus_info[line][destination]) < truncate:
                        bus_info[line][destination].append(arrival_in_minutes)


            # Debug: Log bus info per stop
            print(f"Bus info for stop {stop_name}: {json.dumps(bus_info, indent=2)}")
            return {stop_name: bus_info}
        else:
            print(f"Error fetching data for stop ID {stop_id}: {response.status}")
            return {stop_name: {}}


async def get_bus_times(api_key, stop_ids, truncate=5):
    """Fetch bus data for all stops asynchronously and exclude empty stops."""
    bus_data = {}
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_stop_data(session, api_key, stop_id, stop_name, truncate)
            for stop_id, stop_name in stop_ids
        ]
        results = await asyncio.gather(*tasks)
        print("Hallo!")
        for result in results:
            for stop_name, buses in result.items():
                print("ITEMS = " + result.items)
                
                if buses:  # Only add stops with bus data
                    bus_data[stop_name] = buses
    return bus_data

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
            for stop_name, buses in result.items():
                print("OOGABOOGA")
                print(buses)
                
                if buses:  # Only add stops with bus data
                    bus_data[stop_name] = buses
                    bus_data.update(result)
                    print("HASIT")
                print("BRUH")
                print(result)
            
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
    print(f"Stop IDs: {stop_ids}")

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





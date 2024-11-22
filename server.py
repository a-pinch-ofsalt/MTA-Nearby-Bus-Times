from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import os
import asyncio
from mta import get_bus_data  # Import the refactored function from mta.py

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the MTA API! Use /get_bus_times with latitude and longitude parameters."}

@app.get("/get_bus_times")
async def get_bus_times(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude")):
    """
    Endpoint to fetch bus times directly using mta.py as a module.
    """
    try:
        api_key = os.getenv("MTA_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="MTA_API_KEY environment variable not set.")
        
        # Call the refactored mta.py function
        bus_data = await get_bus_data(api_key, lat, lon)
        return JSONResponse(content=bus_data)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

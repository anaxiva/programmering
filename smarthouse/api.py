import uvicorn
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

from smarthouse.persistence import SmartHouseRepository
from smarthouse.domain import Device, Measurement

# Database-tilkobling
def setup_database():
    project_dir = Path(__file__).parent.parent
    db_file = project_dir / "data" / "db.sql"
    return SmartHouseRepository(str(db_file.absolute()))

app = FastAPI()
repo = setup_database()
smarthouse = repo.load_smarthouse_deep()

# Statisk frontend (hvis du har www/)
if not (Path.cwd() / "www").exists():
    os.chdir(Path.cwd().parent)
if (Path.cwd() / "www").exists():
    app.mount("/static", StaticFiles(directory="www"), name="static")

@app.get("/")
def root():
    return RedirectResponse("/static/index.html")

@app.get("/hello")
def hello(name: str = "world"):
    return {"hello": name}

@app.get("/smarthouse")
def get_smarthouse_info():
    return {
        "no_rooms": len(smarthouse.get_rooms()),
        "no_floors": len(smarthouse.get_floors()),
        "registered_devices": len(smarthouse.get_devices()),
        "area": smarthouse.get_area()
    }

# Hjelpefunksjon
def serialize_device(device: Device):
    return {
        "id": device.id,
        "model_name": device.model_name,
        "supplier": device.supplier,
        "device_type": device.device_type,
        "room_name": device.room.room_name if device.room else None,
        "is_sensor": device.is_sensor(),
        "is_actuator": device.is_actuator()
    }

@app.get("/smarthouse/floor")
def get_floors():
    return [{"level": f.level, "room_count": len(f.rooms)} for f in smarthouse.get_floors()]

@app.get("/smarthouse/floor/{fid}")
def get_floor(fid: int):
    floor = next((f for f in smarthouse.get_floors() if f.level == fid), None)
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    return {"level": floor.level, "rooms": [r.room_name for r in floor.rooms]}

@app.get("/smarthouse/floor/{fid}/room")
def get_rooms(fid: int):
    floor = next((f for f in smarthouse.get_floors() if f.level == fid), None)
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    return [{"name": r.room_name, "size": r.room_size} for r in floor.rooms]

@app.get("/smarthouse/floor/{fid}/room/{rid}")
def get_room(fid: int, rid: int):
    floor = next((f for f in smarthouse.get_floors() if f.level == fid), None)
    if not floor or rid >= len(floor.rooms):
        raise HTTPException(status_code=404, detail="Room not found")
    room = floor.rooms[rid]
    return {
        "room_name": room.room_name,
        "room_size": room.room_size,
        "devices": [serialize_device(d) for d in room.devices]
    }

@app.get("/smarthouse/device")
def get_all_devices():
    return [serialize_device(d) for d in smarthouse.get_devices()]

@app.get("/smarthouse/device/{uuid}")
def get_device(uuid: str):
    device = smarthouse.get_device_by_id(uuid)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return serialize_device(device)

@app.get("/smarthouse/sensor/{uuid}/current")
def get_sensor_current(uuid: str):
    device = smarthouse.get_device_by_id(uuid)
    if not device or not device.is_sensor():
        raise HTTPException(status_code=404, detail="Sensor not found")
    m = repo.get_latest_reading(device)
    if not m:
        raise HTTPException(status_code=404, detail="No readings found")
    return vars(m)

class MeasurementIn(BaseModel):
    timestamp: str
    value: float
    unit: str

@app.post("/smarthouse/sensor/{uuid}/current")
def add_sensor_measurement(uuid: str, m: MeasurementIn):
    device = smarthouse.get_device_by_id(uuid)
    if not device or not device.is_sensor():
        raise HTTPException(status_code=404, detail="Sensor not found")
    c = repo.cursor()
    c.execute(
        "INSERT INTO measurements (ts, value, unit, device) VALUES (?, ?, ?, ?)",
        (m.timestamp, m.value, m.unit, uuid)
    )
    repo.conn.commit()
    c.close()
    return {"status": "Measurement added"}

@app.get("/smarthouse/sensor/{uuid}/values")
def get_sensor_values(uuid: str, limit: Optional[int] = Query(None)):
    device = smarthouse.get_device_by_id(uuid)
    if not device or not device.is_sensor():
        raise HTTPException(status_code=404, detail="Sensor not found")
    query = f"SELECT ts, value, unit FROM measurements WHERE device = ? ORDER BY ts DESC"
    if limit:
        query += f" LIMIT {limit}"
    c = repo.cursor()
    c.execute(query, (uuid,))
    result = [{"timestamp": row[0], "value": row[1], "unit": row[2]} for row in c.fetchall()]
    c.close()
    return result

@app.delete("/smarthouse/sensor/{uuid}/oldest")
def delete_oldest_measurement(uuid: str):
    device = smarthouse.get_device_by_id(uuid)
    if not device or not device.is_sensor():
        raise HTTPException(status_code=404, detail="Sensor not found")
    c = repo.cursor()
    c.execute("SELECT ts FROM measurements WHERE device = ? ORDER BY ts ASC LIMIT 1", (uuid,))
    row = c.fetchone()
    if row:
        c.execute("DELETE FROM measurements WHERE device = ? AND ts = ?", (uuid, row[0]))
        repo.conn.commit()
        c.close()
        return {"status": f"Oldest measurement from {row[0]} deleted"}
    else:
        c.close()
        raise HTTPException(status_code=404, detail="No measurements found")

@app.get("/smarthouse/actuator/{uuid}/current")
def get_actuator_state(uuid: str):
    device = smarthouse.get_device_by_id(uuid)
    if not device or not device.is_actuator():
        raise HTTPException(status_code=404, detail="Actuator not found")
    return {"state": device.state}

@app.put("/smarthouse/device/{uuid}")
def update_actuator_state(uuid: str, state: Optional[float] = None):
    device = smarthouse.get_device_by_id(uuid)
    if not device or not device.is_actuator():
        raise HTTPException(status_code=404, detail="Actuator not found")
    if state is not None:
        device.turn_on(state)
    else:
        device.turn_on()
    repo.update_actuator_state(device)
    return {"state": device.state}

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8000)

from fastapi import FastAPI
from pydantic import BaseModel

from Map.obstacle import Obstacle
from Settings.attributes import Direction
from Simulator.simulator import AlgoSimulator

import logging

logger = logging.getLogger("uvicorn")


app = FastAPI()


# Request body = raw string
class RunRequest(BaseModel):
    data: str


DIRECTION_MAP = {
    "T": Direction.TOP,
    "B": Direction.BOTTOM,
    "L": Direction.LEFT,
    "R": Direction.RIGHT,
}


def parse_obstacles(raw: str):
    obstacles = []

    if not raw.strip():
        return obstacles

    chunks = raw.split(";")

    for chunk in chunks:
        x, y, d, idx = chunk.split(",")

        obstacle = Obstacle(
            int(x),
            int(y),
            DIRECTION_MAP[d.upper()],
            int(idx),
        )

        obstacles.append(obstacle)

    return obstacles

@app.get("/")
async def health_check():
    return {"status": "ok", "message": "Simulator API running"}

@app.post("/run")
async def run_simulation(req: RunRequest):

    logger.info(f"Raw request data: {req.data}")

    obstacles = parse_obstacles(req.data)

    logger.info(f"Parsed obstacles: {obstacles}")

    sim = AlgoSimulator(obstacles)
    sim.init()
    sim.execute()

    return {"status": "simulation completed"}

from fastapi import FastAPI
from pydantic import BaseModel

from Map.obstacle import Obstacle
from Settings.attributes import Direction
from Simulator.simulator import AlgoSimulator

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


@app.post("/run")
async def run_simulation(req: RunRequest):

    obstacles = parse_obstacles(req.data)

    sim = AlgoSimulator(obstacles)
    sim.init()
    sim.execute()

    return {"status": "simulation completed"}

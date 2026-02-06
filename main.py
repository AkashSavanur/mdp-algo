from Map.obstacle import Obstacle
from Map.position import Position
from Settings.attributes import Direction
from Simulator.simulator import AlgoSimulator

def main():
    # Create test obstacles with adequate spacing
    # Format: Obstacle(x, y, direction, index)
    # x, y must be multiples of 10 with offset 5 (e.g., 5, 15, 25, 35, etc.)
    # direction: Direction.TOP, Direction.BOTTOM, Direction.LEFT, or Direction.RIGHT
    
    obstacles = [
        Obstacle(75, 25, Direction.TOP, 2),       # Bottom band, spaced from #1
        Obstacle(125, 75, Direction.LEFT, 3),     # Lower-middle right
        Obstacle(35, 145, Direction.TOP, 4),   # Mid-left vertical separation
        Obstacle(95, 155, Direction.RIGHT, 5),    # Upper-middle
        Obstacle(155, 115, Direction.TOP, 6),      # Mid-right
    ]
    
    app = AlgoSimulator(obstacles)
    app.init()
    app.execute()

if __name__ == "__main__":
    main()

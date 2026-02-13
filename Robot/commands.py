import math
from abc import ABC, abstractmethod
from Settings.config import *
from Settings.attributes import *
from Map.position import *


class Command(ABC):
    def __init__(self, time):
        self.time = time  # Time in seconds in which this command is carried out.
        self.ticks = math.ceil(time * FRAMES)  # Number of frame ticks that this command will take.
        self.total_ticks = self.ticks  # Keep track of original total ticks.

    def tick(self):
        self.ticks -= 1

    @abstractmethod
    def process_one_tick(self, robot):
        """
        Overriding method must call tick().
        """
        pass

    @abstractmethod
    def apply_on_pos(self, curr_pos):
        """
        Apply this command to a Position, such that its attributes will reflect the correct values
        after the command is done.

        This method should return itself.
        """
        pass

    @abstractmethod
    def convert_to_message(self):
        """
        Conversion to a message that is easy to send over the RPi.
        """
        pass


class ScanCommand(Command):
    def __init__(self, time, obj_index, obstacle=None, robot=None):
        super().__init__(time)
        self.obj_index = obj_index
        self.obstacle = obstacle
        self.robot = robot
        self.bullseye_found = False  # Flag to track if bullseye was found during scan
        self.scan_completed = False  # Flag to ensure we only process result once
        self.image_result = None  # Stores the RPi image recognition result

    def __str__(self):
        return f"ScanCommand(time={self.time, self.obj_index})"

    __repr__ = __str__

    def process_one_tick(self, robot):
        if self.total_ticks == 0:
            return

        self.tick()
        
        # When scan completes, process the image recognition result
        if self.ticks <= 0 and not self.scan_completed:
            self.scan_completed = True
            self._handle_scan_completion(robot)

    def _handle_scan_completion(self, robot):
        """
        Called when the scan completes. Requests image recognition from RPi
        and handles the result.
        """
        # Request image recognition from RPi
        self.image_result = self._request_image_recognition_from_rpi()
        
        # Check if bullseye was detected
        if self.image_result == "BULLSEYE":
            self.bullseye_found = True
            print(f"BULLSEYE DETECTED at obstacle {self.obj_index}!")
            # Interrupt current path and start scanning the 4 sides
            if self.robot and self.obstacle:
                self.robot.interrupt_path_and_scan_obstacle(self.obstacle)
        elif self.image_result:
            print(f"Image recognized at obstacle {self.obj_index}: {self.image_result}")

    def _request_image_recognition_from_rpi(self):
        """
        Sends a scan request to the RPi and gets the image recognition result.
        Returns the detected image type (e.g., "BULLSEYE", "TARGET_1", etc.)
        
        TODO: Connect this to actual RPi communication module.
        For now, this is a placeholder that should be implemented with your RPi interface.
        """
        # Placeholder - replace with actual RPi communication
        # Example: return rpi_interface.get_image_recognition()
        return None

    def apply_on_pos(self, curr_pos):
        pass

    def convert_to_message(self):
        return f"P___{self.obj_index}"


class ObstacleScanCommand(Command):
    """
    Command to traverse the 4 sides of an obstacle for image recognition.
    Goes around the obstacle in a square pattern (4 sides).
    Distance is the distance from the obstacle center to travel on each side.
    """
    def __init__(self, side_distance, obstacle, robot=None):
        """
        side_distance: Distance to travel on each side of the obstacle
        obstacle: The Obstacle object to scan around
        robot: Reference to the robot for calling handle_scan_result
        """
        # Time to traverse all 4 sides: 4 sides * 2 straight commands + 4 turns
        # Each side: straight + turn(90)
        straight_time = 4 * abs(side_distance / ROBOT_SPEED_PER_SECOND)
        turn_time = 4 * abs((math.radians(90) * ROBOT_LENGTH) / 
                           (ROBOT_SPEED_PER_SECOND * ROBOT_S_FACTOR))
        total_time = straight_time + turn_time
        
        super().__init__(total_time)
        self.side_distance = side_distance
        self.obstacle = obstacle
        self.robot = robot
        self.bullseye_found = False  # Flag to track if bullseye was found initially
        self.target_found = False  # Flag to track if target image was found
        self.scan_side = 0  # Which side we're currently scanning (0-3)
        self.sub_command = None  # Current sub-command being executed
        self.sub_commands = self._generate_scan_commands()
        self.check_interval = 10  # Check for image every 10 ticks
        self.ticks_since_last_check = 0

    def _generate_scan_commands(self):
        """Generate the sequence of commands to traverse all 4 sides."""
        commands = []
        # We'll generate straight + turn commands for each side
        for _ in range(4):
            commands.append(StraightCommand(self.side_distance))
            commands.append(TurnCommand(90, False))  # Turn left 90 degrees
        return commands

    def __str__(self):
        return f"ObstacleScanCommand(obstacle={self.obstacle.getIndex()}, side_dist={self.side_distance})"

    __repr__ = __str__

    def process_one_tick(self, robot):
        if self.total_ticks == 0:
            return

        self.tick()
        self.ticks_since_last_check += 1
        
        # Periodically check if target image was found during scanning
        if self.ticks_since_last_check >= self.check_interval and not self.target_found:
            self.ticks_since_last_check = 0
            image_result = self._request_image_recognition_from_rpi()
            
            if image_result and image_result != "BULLSEYE":
                self.target_found = True
                print(f"Target image found during obstacle scan at obstacle {self.obstacle.getIndex()}!")
                if self.robot:
                    self.robot.handle_scan_result_during_obstacle_scan(image_result)
                return
        
        # Execute sub-commands in sequence
        if self.sub_command is None or self.sub_command.ticks <= 0:
            if len(self.sub_commands) > 0:
                self.sub_command = self.sub_commands.pop(0)
            else:
                # Scanning complete without finding target
                print(f"Completed scanning all 4 sides of obstacle {self.obstacle.getIndex()}")
                return
        
        if self.sub_command:
            self.sub_command.process_one_tick(robot)

    def _request_image_recognition_from_rpi(self):
        """
        Requests image recognition result from the RPi.
        Returns the detected image type during obstacle scanning.
        
        TODO: Connect this to actual RPi communication module.
        """
        # Placeholder - replace with actual RPi communication
        # Example: return rpi_interface.get_image_recognition()
        return None

    def apply_on_pos(self, curr_pos):
        """Apply all the scanning movements to the position."""
        for cmd in self._generate_scan_commands():
            cmd.apply_on_pos(curr_pos)

    def convert_to_message(self):
        return f"SCAN_OBS_{self.obstacle.getIndex()}"

class StraightCommand(Command):
    def __init__(self, dist):
        """
        Specified distance is scaled. Do not divide the provided distance by the scaling factor!
        """
        # Calculate the time needed to travel the required distance.
        time = abs(dist / ROBOT_SPEED_PER_SECOND)
        super().__init__(time)

        self.dist = dist

    def __str__(self):
        return f"StraightCommand(dist={self.dist / SCALING_FACTOR}, {self.total_ticks} ticks)"

    __repr__ = __str__

    def process_one_tick(self, robot):
        if self.total_ticks == 0:
            return

        self.tick()
        distance = self.dist / self.total_ticks
        robot.straight(distance)

    def apply_on_pos(self, curr_pos: Position):
        """
        Apply this command onto a current Position object.
        """
        if curr_pos.direction == Direction.RIGHT:
            curr_pos.x += self.dist
        elif curr_pos.direction == Direction.TOP:
            curr_pos.y += self.dist
        elif curr_pos.direction == Direction.BOTTOM:
            curr_pos.y -= self.dist
        else:
            curr_pos.x -= self.dist

        return self

    def convert_to_message(self):

        # if descaled_distance < 0:
        #     return f"STM|BC{abs(descaled_distance):03}"
        # return f"STM|FC{descaled_distance:03}"
        if self.dist < 0:
            return f"SB{((abs(self.dist))//5):03}"
        return f"SF{((self.dist)//5):03}"


class TurnCommand(Command):
    def __init__(self, angle, rev):
        """
        Angle to turn and whether the turn is done in reverse or not. Note that this is in degrees.

        Note that negative angles will always result in the robot being rotated clockwise.
        """
        time = abs((math.radians(angle) * ROBOT_LENGTH) /
                   (ROBOT_SPEED_PER_SECOND * ROBOT_S_FACTOR))
        super().__init__(time)

        self.angle = angle
        self.rev = rev

    def __str__(self):
        return f"TurnCommand({self.angle:.2f}degrees, {self.total_ticks} ticks, rev={self.rev})"

    __repr__ = __str__

    def process_one_tick(self, robot):
        if self.total_ticks == 0:
            return

        self.tick()
        angle = self.angle / self.total_ticks
        robot.turn(angle, self.rev)

    def apply_on_pos(self, curr_pos: Position):
        """
        x_new = x + R(sin(∆θ + θ) - sin θ)
        y_new = y - R(cos(∆θ + θ) - cos θ)
        θ_new = θ + ∆θ
        R is the turning radius.

        Take note that:
            - +ve ∆θ -> rotate counter-clockwise
            - -ve ∆θ -> rotate clockwise

        Note that ∆θ is in radians.
        """
        assert isinstance(curr_pos, RobotPosition), print("Cannot apply turn command on non-robot positions!")

        # Get change in (x, y) coordinate.
        if curr_pos.direction == Direction.RIGHT or curr_pos.direction == Direction.LEFT:
            if not self.rev:
                ROBOT_TURN_RADIUS_X = ROBOT_TURN_RADIUS
                ROBOT_TURN_RADIUS_Y = ROBOT_TURN_RADIUS_DRIFT
            else:
                ROBOT_TURN_RADIUS_X = ROBOT_TURN_RADIUS_DRIFT
                ROBOT_TURN_RADIUS_Y = ROBOT_TURN_RADIUS
        else:
            if not self.rev:
                ROBOT_TURN_RADIUS_X = ROBOT_TURN_RADIUS_DRIFT
                ROBOT_TURN_RADIUS_Y = ROBOT_TURN_RADIUS
            else:
                ROBOT_TURN_RADIUS_X = ROBOT_TURN_RADIUS
                ROBOT_TURN_RADIUS_Y = ROBOT_TURN_RADIUS_DRIFT

        x_change = ROBOT_TURN_RADIUS_X * (math.sin(math.radians(curr_pos.angle + self.angle)) -
                                                math.sin(math.radians(curr_pos.angle)))
        y_change = ROBOT_TURN_RADIUS_Y * (math.cos(math.radians(curr_pos.angle + self.angle)) -
                                                math.cos(math.radians(curr_pos.angle)))

        if self.angle < 0 and not self.rev:  # Wheels to right moving forward.
            curr_pos.x -= x_change
            curr_pos.y += y_change
        elif (self.angle < 0 and self.rev) or (self.angle >= 0 and not self.rev):
            # (Wheels to left moving backwards) or (Wheels to left moving forwards).
            curr_pos.x += x_change
            curr_pos.y -= y_change
        else:  # Wheels to right moving backwards.
            curr_pos.x -= x_change
            curr_pos.y += y_change
        curr_pos.angle += self.angle

        if curr_pos.angle < -180:
            curr_pos.angle += 2 * 180
        elif curr_pos.angle >= 180:
            curr_pos.angle -= 2 * 180

        # Update the Position's direction.
        if 45 <= curr_pos.angle <= 3 * 45:
            curr_pos.direction = Direction.TOP
        elif -45 < curr_pos.angle < 45:
            curr_pos.direction = Direction.RIGHT
        elif -45 * 3 <= curr_pos.angle <= -45:
            curr_pos.direction = Direction.BOTTOM
        else:
            curr_pos.direction = Direction.LEFT
        return self

    def convert_to_message(self):
        if self.angle > 0 and not self.rev:
            # This is going forward left.
            return "LF090"
        elif self.angle > 0 and self.rev:
            # This is going backward right.
            return "RB090"
        elif self.angle < 0 and not self.rev:
            # This is going forward right.
            return "RF090"
        else:
            # This is going backward left.
            return "LB090"

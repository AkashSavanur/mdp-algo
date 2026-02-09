import pygame
import sys
import time
from abc import ABC, abstractmethod
from typing import List
from Map.obstacle import Obstacle
from Map.grid import Grid
from Settings.config import *
from Settings.colors import *
from Robot.robot import Robot
from GUI.button import Button


class LogBuffer:
    """Captures stdout from Robot/ and stores it for display in the GUI."""
    def __init__(self, original_stdout, max_lines: int = 20):
        self.original_stdout = original_stdout
        self.lines: List[str] = []
        self.max_lines = max_lines
        self._buffer = ""

    def write(self, text: str):
        self.original_stdout.write(text)  # Still print to console
        self._buffer += text
        while "\n" in self._buffer:
            line, _, self._buffer = self._buffer.partition("\n")
            self.lines.append(line.replace("\r", "").strip() or "")
            if len(self.lines) > self.max_lines:
                self.lines.pop(0)

    def flush(self):
        self.original_stdout.flush()
        if self._buffer.strip():
            self.lines.append(self._buffer.strip())
            self._buffer = ""
            if len(self.lines) > self.max_lines:
                self.lines.pop(0)


# Load button images
start_img = pygame.image.load("Assets/start_btn.png").convert_alpha()
exit_img = pygame.image.load("Assets/exit_btn.png").convert_alpha()

class AlgoApp(ABC):
    def __init__(self, obstacles: List[Obstacle]):
        self.grid = Grid(obstacles)
        self.robot = Robot(self.grid)
        
        self.start_button = Button(1400, 700, start_img, 0.25)
        self.exit_button = Button(1400, 850, exit_img, 0.35)
       # self.reset_button = Button(1000, 557, reset_img, 0.9)

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def execute(self):
        pass


class AlgoSimulator(AlgoApp):
    """
    Run the algorithm using a GUI simulator.
    """
    def __init__(self, obstacles: List[Obstacle]):
        super().__init__(obstacles)

        self.running = False
        self.size = self.width, self.height = WINDOW_SIZE
        self.screen = self.clock = None
        self.time_cal = False
        self.timer_start = None
        self.elapsed = 0
        self.log_buffer = None
        self._original_stdout = sys.stdout

    def init(self):
        """
        Set initial values for the app.
        """
        pygame.init()
        self.running = True

        self.log_buffer = LogBuffer(self._original_stdout, max_lines=18)
        sys.stdout = self.log_buffer

        self.screen = pygame.display.set_mode(self.size, pygame.FULLSCREEN)  # pygame.HWSURFACE | pygame.DOUBLEBUF pygame.RESIZABLE
        self.clock = pygame.time.Clock()

        # Inform user that it is finding path...
        pygame.display.set_caption("Calculating path...")
        font = pygame.font.SysFont("Helvetica", 35)
        text = font.render("Calculating path...", True, WHITE)
        text_rect = text.get_rect()
        text_rect.center = WINDOW_SIZE[0] / 2, WINDOW_SIZE[1] / 2
        self.screen.blit(text, text_rect)
        pygame.display.flip()

    def settle_events(self):
        """
        Process Pygame events.
        """
        for event in pygame.event.get():
            # On quit, stop the game loop. This will stop the app.
            if event.type == pygame.QUIT:
                self.running = False

    def do_updates(self):
        self.robot.update()

    def render(self):
        """
        Render the screen.
        """
        if self.timer_start is not None:
            self.elapsed = time.time() - self.timer_start

        rect_outer= pygame.Rect(0, 0, 1300, 1200)
        self.screen.fill(DARK_BLACK, rect=rect_outer)

        rect_grid = pygame.Rect(0, 0, 1000, 1000)
        self.screen.fill(MINT, rect=rect_grid)

        # Title 1
        font1 = pygame.font.SysFont("Helvetica", 26)
        text1 = font1.render("Algorithm Simulator", True, WHITE)
        text_rect1 = text1.get_rect()
        text_rect1 = 1000, 10
        self.screen.blit(text1, text_rect1)

        # Log panel (top right)
        if self.log_buffer:
            log_font = pygame.font.SysFont("Consolas", 14)
            log_area = pygame.Rect(1310, 45, 580, 200)
            pygame.draw.rect(self.screen, DARK_BLACK, log_area)
            pygame.draw.rect(self.screen, DARK_GREY, log_area, 1)
            line_height = 16
            max_visible = min(len(self.log_buffer.lines), log_area.height // line_height - 1)
            start_idx = max(0, len(self.log_buffer.lines) - max_visible)
            for i, line in enumerate(self.log_buffer.lines[start_idx:start_idx + max_visible]):
                if line:
                    truncated = line[:60] + "..." if len(line) > 60 else line
                    log_surface = log_font.render(truncated, True, WHITE)
                    self.screen.blit(log_surface, (log_area.x + 4, log_area.y + 4 + i * line_height))

        # Label 1
        font2 = pygame.font.SysFont("Helvetica", 24)
        text2 = font2.render("Image", True, DARK_YELLOW)
        text_rect2 = text2.get_rect()
        text_rect2 = 1040, 260
        self.screen.blit(text2, text_rect2)
        rect_label = pygame.Rect(1010, 264, 20, 20)
        self.screen.fill(DARK_YELLOW, rect=rect_label)

        # Label 2
        font4 = pygame.font.SysFont("Helvetica", 24)
        text4 = font4.render("Virtual obstacle border", True, RED)
        text_rect4 = text4.get_rect()
        text_rect4 = 1040, 310
        self.screen.blit(text4, text_rect4)
        rect_label2 = pygame.Rect(1010, 314, 20, 20)
        self.screen.fill(RED, rect=rect_label2)

        # Label 3
        font3 = pygame.font.SysFont("Helvetica", 24)
        text3 = font3.render("Forbidden", True, DARK_GREY)
        text_rect3 = text3.get_rect()
        text_rect3 = 1040, 360
        self.screen.blit(text3, text_rect3)
        rect_label3 = pygame.Rect(1010, 364, 20, 20)
        self.screen.fill(DARK_GREY, rect=rect_label3)

        # Label 4
        font5 = pygame.font.SysFont("Helvetica", 24)
        text5 = font5.render("Allowed", True, WHITE)
        text_rect5 = text5.get_rect()
        text_rect5 = 1040, 410
        self.screen.blit(text5, text_rect5)
        rect_label4 = pygame.Rect(1010, 414, 20, 20)
        self.screen.fill(WHITE, rect=rect_label4)

        self.grid.draw(self.screen)
        self.robot.draw(self.screen)

        # Draw start and exit buttons
        if self.start_button.draw():
            self.timer_start = time.time()
            # Calculate the path.
            start = time.time()
            self.robot.brain.plan_path()
            time_delta = str(time.time() - start)
            print(time_delta)

        if self.exit_button.draw():
            self.running = False

       # if self.reset_button.draw():
           # pass

        # Timer display
        # Timer display
        timer_font = pygame.font.SysFont("Helvetica", 32)

        mins = int(self.elapsed // 60)
        secs = int(self.elapsed % 60)
        millis = int((self.elapsed * 100) % 100)

        timer_text = f"{mins:02}:{secs:02}.{millis:02}"
        timer_surface = timer_font.render(timer_text, True, WHITE)

        timer_rect = timer_surface.get_rect()

        # Align vertically with buttons
        timer_rect.centerx = 1400   # same column as buttons
        timer_rect.y = 620          # slightly above start button

        timer_bg = pygame.Rect(1320, 600, 200, 60)
        self.screen.fill(DARK_BLACK, timer_bg)

        self.screen.blit(timer_surface, timer_rect)

        # Really render now.
        pygame.display.flip()

    def execute(self):
        """
        Initialise the app and start the game loop.
        """
        try:
            while self.running:
                # Check for Pygame events.
                self.settle_events()
                # Do required updates.
                self.do_updates()
                # Render the new frame.
                self.render()
        finally:
            sys.stdout = self._original_stdout


class AlgoMinimal(AlgoApp):
    """
    Minimal app to just calculate a path and then send the commands over.
    """
    def __init__(self, obstacles):
        super().__init__(obstacles)

    def init(self):
        pass

    def execute(self):
        print("Calculating path...")
        index_list = self.robot.brain.plan_path()
        return index_list
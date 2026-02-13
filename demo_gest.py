import pygame
import random

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 900, 600
PANEL_WIDTH = 200
SIM_WIDTH = WIDTH - PANEL_WIDTH

BG_COLOR = (30, 30, 30)
PANEL_COLOR = (45, 45, 45)
BOUNDARY_COLOR = (255, 255, 255)
SHAPE_COLOR = (0, 200, 255)

MAX_SHAPES = 5
SHAPE_SIZE = 30
SPEED = 5
# ---------------------------------------

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Simulation Panel")

clock = pygame.time.Clock()

# Shape class
class Shape:
    def __init__(self):
        self.x = random.randint(50, SIM_WIDTH - SHAPE_SIZE - 50)
        self.y = random.randint(50, HEIGHT - SHAPE_SIZE - 50)
        self.dx = 0
        self.dy = 0

    def move(self):
        self.x += self.dx
        self.y += self.dy

        # Boundary enforcement
        if self.x < 10:
            self.x = 10
        if self.x + SHAPE_SIZE > SIM_WIDTH - 10:
            self.x = SIM_WIDTH - SHAPE_SIZE - 10
        if self.y < 10:
            self.y = 10
        if self.y + SHAPE_SIZE > HEIGHT - 10:
            self.y = HEIGHT - SHAPE_SIZE - 10

    def draw(self):
        pygame.draw.rect(screen, SHAPE_COLOR,
                         (self.x, self.y, SHAPE_SIZE, SHAPE_SIZE))


shapes = []
selected_shape = None

running = True
while running:
    clock.tick(60)
    screen.fill(BG_COLOR)

    # -------- Simulation Boundary --------
    pygame.draw.rect(
        screen,
        BOUNDARY_COLOR,
        (10, 10, SIM_WIDTH - 20, HEIGHT - 20),
        2
    )

    # -------- Control Panel --------
    pygame.draw.rect(
        screen,
        PANEL_COLOR,
        (SIM_WIDTH, 0, PANEL_WIDTH, HEIGHT)
    )

    font = pygame.font.SysFont(None, 24)
    screen.blit(font.render("CONTROL PANEL", True, (255, 255, 255)),
                (SIM_WIDTH + 20, 20))

    screen.blit(font.render("A : Add Shape", True, (200, 200, 200)),
                (SIM_WIDTH + 20, 70))
    screen.blit(font.render("TAB : Select Shape", True, (200, 200, 200)),
                (SIM_WIDTH + 20, 100))
    screen.blit(font.render("Arrow Keys : Move", True, (200, 200, 200)),
                (SIM_WIDTH + 20, 130))
    screen.blit(font.render(f"Count: {len(shapes)}/{MAX_SHAPES}", True, (255, 150, 150)),
                (SIM_WIDTH + 20, 180))

    # -------- Events --------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # Add dummy shape
            if event.key == pygame.K_a:
                if len(shapes) < MAX_SHAPES:
                    shapes.append(Shape())
                    selected_shape = shapes[-1]

            # Select next shape
            if event.key == pygame.K_TAB and shapes:
                index = shapes.index(selected_shape) if selected_shape in shapes else -1
                selected_shape = shapes[(index + 1) % len(shapes)]

    keys = pygame.key.get_pressed()
    if selected_shape:
        selected_shape.dx = 0
        selected_shape.dy = 0

        if keys[pygame.K_LEFT]:
            selected_shape.dx = -SPEED
        if keys[pygame.K_RIGHT]:
            selected_shape.dx = SPEED
        if keys[pygame.K_UP]:
            selected_shape.dy = -SPEED
        if keys[pygame.K_DOWN]:
            selected_shape.dy = SPEED

    # -------- Update & Draw Shapes --------
    for shape in shapes:
        shape.move()
        shape.draw()

    pygame.display.flip()

pygame.quit()
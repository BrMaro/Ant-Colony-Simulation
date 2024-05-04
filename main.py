import pygame
import os
import math
import random

pygame.init()

WIDTH, HEIGHT = 1600, 900
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ant Colony Simulations")
FPS = 30

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
BROWN = (139, 69, 19)
DARK_BROWN = (101, 67, 33)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
AQUA = (100, 200, 200)
BLACK = (0, 0, 0)
GREY = (128, 128, 128)
WHITE = (255, 255, 255)
TURQUOISE = (64, 224, 208)

ANT_SIZE = (5, 5)
ANT = pygame.transform.scale(pygame.image.load(os.path.join('ant.png')), ANT_SIZE)
ANT_MAX_SPEED = 1
RED_PHEROMONE_DECAY_RATE = 0.993
BLUE_PHEROMONE_DECAY_RATE = 0.9995
ANTHILL_SENSE_RADIUS = 150 # pixels
CELL_SIZE = 5

EARTH = pygame.transform.scale(pygame.image.load(os.path.join("dirt.bmp")), (WIDTH, HEIGHT))

ANTHILL = pygame.image.load(os.path.join("anthill.bmp"))

# correct angle orientation when an ant faces an object
#   0 - image is looking to the right
#  90 - image is looking up
# 180 - image is looking to the left
# 270 - image is looking down
correction_angle = 90


class Ant:
    def __init__(self, ant_id, x, y):
        self.ant_id = ant_id
        self.x = x
        self.y = y
        self.type = "ant"
        self.velocity = [random.uniform(-ANT_MAX_SPEED, ANT_MAX_SPEED), random.uniform(-ANT_MAX_SPEED, ANT_MAX_SPEED)]
        self.max_speed = ANT_MAX_SPEED
        self.sense_radius = 250
        self.angle = 0
        self.inventory = []
        self.memory = []
        self.health = 100
        self.carrying_food = False
        self.state = ""         # exploring"/"delivery/"approach food
        # self.colony = None
        # self.age = 0
        # self.color = ANT_COLOR

    def sense_objects_and_react(self, objects, ants, pheromone_grid, anthill):
        sensed_objects = []
        if self.inventory:
            self.go_home(pheromone_grid, anthill, ants)
        else:
            for obj in objects:
                distance_to_obj = math.hypot(obj.x - self.x, obj.y - self.y)
                if distance_to_obj <= self.sense_radius:
                    sensed_objects.append(obj)
            if sensed_objects:
                for sensed_obj in sensed_objects:
                    if isinstance(sensed_obj, Food):
                        self.move_towards_target((sensed_obj.x, sensed_obj.y), ants)
                        distance_to_food = math.hypot(sensed_obj.x - self.x, sensed_obj.y - self.y)
                        if distance_to_food <= 2:
                            self.collect_food(sensed_obj)
            else:
                return None

    def collect_food(self, food_object):
        if isinstance(food_object, Food):
            if not self.inventory:
                self.inventory.append(food_object)
                self.carrying_food = True
                food_object.food_collected(1)

    def go_home(self, pheromone_grid, anthill, ants):
        self.state = "delivering"

        anthill_x, anthill_y = anthill.x,anthill.y
        distance_to_anthill = math.hypot(self.x - anthill_x, self.y - anthill_y)

        if distance_to_anthill <= 40:
            self.velocity = [0, 0]
            anthill.food_storage += 1
            self.inventory = []
            self.carrying_food = False
        elif distance_to_anthill <= ANTHILL_SENSE_RADIUS:
            self.move_towards_target((anthill_x,anthill_y), ants)
        else:
            if self.memory:
                # self.memory = list(dict.fromkeys(self.memory))
                next_cell = self.memory.pop()
                next_cell_coordinates = (next_cell[0]*CELL_SIZE,next_cell[1]*CELL_SIZE)

                self.move_towards_target(next_cell_coordinates, ants)
            else:
                # No memory, look for pheromone trails
                nearby_pheromones = self.check_nearby_pheromones(pheromone_grid)
                if nearby_pheromones:
                    # Follow the strongest pheromone trail
                    strongest_pheromone = max(nearby_pheromones, key=lambda p: p[1])
                    self.move_towards_target(strongest_pheromone[0], ants)
                else:
                    # No pheromone trails nearby, move randomly
                    self.move_randomly(ants, pheromone_grid)
    def check_nearby_pheromones(self, pheromone_grid):
        nearby_pheromones = []
        cell_x = int(self.x // CELL_SIZE)
        cell_y = int(self.y // CELL_SIZE)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                neighbor_x = cell_x + dx
                neighbor_y = cell_y + dy
                if (neighbor_x, neighbor_y) in pheromone_grid.red_drawn_cells:
                    pheromone_level = pheromone_grid.grid[neighbor_x][neighbor_y]
                    nearby_pheromones.append(((neighbor_x * CELL_SIZE + CELL_SIZE // 2, neighbor_y * CELL_SIZE + CELL_SIZE // 2), pheromone_level))
        return nearby_pheromones

    def move_towards_target(self, target, ants):
        target_x, target_y = target
        dx, dy = target_x - self.x, target_y - self.y
        distance_to_target = math.hypot(dx, dy)

        cell_x = int(self.x // CELL_SIZE)
        cell_y = int(self.y // CELL_SIZE)

        if self.state != "delivering":
            self.memory.append((cell_x, cell_y))
            # self.memory.append((self.x, self.y))

        if distance_to_target <= self.sense_radius:
            desired_velocity = [dx / distance_to_target, dy / distance_to_target]

            desired_velocity[0] *= self.max_speed
            desired_velocity[1] *= self.max_speed

            # steering force for moving towards target
            steering_force = [desired_velocity[0] - self.velocity[0], desired_velocity[1] - self.velocity[1]]

            # Update velocity
            self.velocity[0] += steering_force[0]
            self.velocity[1] += steering_force[1]

            self.avoid_collision(ants)

            # Update position
            self.x += self.velocity[0]
            self.y += self.velocity[1]

    def move_randomly(self, ants, pheromone_grid):
        cell_x = int(self.x // CELL_SIZE)
        cell_y = int(self.y // CELL_SIZE)

        if self.state != "delivering":
            self.memory.append((cell_x, cell_y))

        pheromone_grid.update_pheromones(cell_x, cell_y, 1,self.carrying_food)

        if random.random() < 0.01:
            current_angle = math.atan2(-self.velocity[1], self.velocity[0])  # Current angle in radians
            min_angle = current_angle - math.pi / 2  # 90 degrees turn to the left
            max_angle = current_angle + math.pi / 2  # 90 degrees turn to the right
            random_angle = random.uniform(min_angle, max_angle)

            random_velocity = [math.cos(random_angle), -math.sin(random_angle)]  # Reverse the sin component

            # Scale the random velocity to the ant's max speed
            random_velocity[0] *= self.max_speed
            random_velocity[1] *= self.max_speed

            # Update velocity and position for random movement
            self.velocity[0] = random_velocity[0]
            self.velocity[1] = random_velocity[1]

        # change direction when reaching screen boundaries
        if self.x >= WIDTH - 10 or self.x <= 10 or self.y >= HEIGHT - 10 or self.y <= 10:
            self.velocity[0] = -self.velocity[0] + random.uniform(0.1, 0.8)
            self.velocity[1] = -self.velocity[1] + random.uniform(0.1, 0.8)

        self.x += max(min(self.velocity[0], ANT_MAX_SPEED), -ANT_MAX_SPEED)
        self.y += max(min(self.velocity[1], ANT_MAX_SPEED), -ANT_MAX_SPEED)

        # calculate angle it should face. Make it face where it turns to
        angle = math.degrees(math.atan2(-self.velocity[1], self.velocity[0])) - correction_angle
        self.angle = angle

        self.avoid_collision(ants)

        # maintain ants within the screen
        self.x = max(0, min(self.x, WIDTH - 10))
        self.y = max(0, min(self.y, HEIGHT - 10))

    def avoid_collision(self, ants):
        for ant in ants:
            if ant != self:
                dx = ant.x - self.x
                dy = ant.y - self.y
                distance = math.hypot(dx, dy)

                if distance < ANT_SIZE[0]:  # Adjust this value as needed
                    avoidance_force = [dx / distance, dy / distance]
                    avoidance_force[0] *= self.max_speed
                    avoidance_force[1] *= self.max_speed

                    self.velocity[0] -= avoidance_force[0]
                    self.velocity[1] -= avoidance_force[1]

    def face_target(self, target):  # target is what the ants are facing
        # Calculate angle of rotation between target and ant
        target_x, target_y = target
        dx, dy = target_x - self.x, target_y - self.y
        angle = math.degrees(math.atan2(-dy, dx)) - correction_angle
        return angle

    def draw_ant(self, win):
        center_x, center_y = self.x, self.y
        angle = self.angle
        rotated_ant = pygame.transform.rotate(ANT, angle)
        rotated_rect = rotated_ant.get_rect(center=(center_x, center_y))
        win.blit(rotated_ant, rotated_rect.topleft)

        if self.carrying_food:
            circle_radius = 5  # Adjust size as needed
            offset_x = circle_radius * math.cos(math.radians(angle))
            offset_y = -circle_radius * math.sin(math.radians(angle))
            carrying_food_pos = (int(center_x + offset_x), int(center_y + offset_y))
            pygame.draw.circle(win, GREEN, carrying_food_pos, circle_radius)


class Anthill:
    def __init__(self, max_ants, initial_food, initial_ants, anthill_x, anthill_y):
        self.max_ants = max_ants
        self.ants = []
        self.food_storage = initial_food
        self.x = anthill_x
        self.y = anthill_y
        self.spawn_radius = 20
        self.initial_ants = initial_ants

        self.spawn_ants(initial_ants)

    def spawn_ants(self, num_ants):
        if len(self.ants) + num_ants <= self.max_ants:
            for ant_id in range(num_ants):
                rand_x = random.randint(self.x - self.spawn_radius, self.x + self.spawn_radius)
                rand_y = random.randint(self.y - self.spawn_radius, self.y + self.spawn_radius)

                new_ant = Ant(ant_id, rand_x, rand_y)
                self.ants.append(new_ant)
                yield new_ant

    def get_population(self):
        return len(self.ants)

    def check_for_food_surplus(self):
        return self.food_storage > len(self.ants)

    def draw_anthill(self, win):
        # win.blit(ANTHILL, (self.x, self.y))

        # Set center coordinates of the anthill
        center_x, center_y = WIDTH // 2, HEIGHT // 2

        # Define radii for the circles
        outer_radius = 50
        inner_radius = 15

        # Set thickness for the circles
        outer_thickness = 20
        inner_thickness = 10
        pygame.draw.circle(win, BROWN, (self.x, self.y), outer_radius, outer_thickness)

        # Draw inner circle
        pygame.draw.circle(win, DARK_BROWN, (self.x, self.y), inner_radius, inner_thickness)


class Food:
    def __init__(self, x, y, quantity):
        self.x = x
        self.y = y
        self.quantity = quantity
        self.offsets = [(random.randint(-5, 5), random.randint(-5, 5)) for _ in range(quantity // 10)]

    def food_collected(self, amount):
        self.quantity = max(0, self.quantity - amount)

    def draw_food(self, win):
        # Calculate the size of the large circle based on the quantity of food
        large_circle_radius = self.quantity

        # Draw the large circle
        pygame.draw.circle(win, GREEN, (self.x, self.y), large_circle_radius)

        # Draw individual circles for each unit of food
        for i in range(self.quantity):
            # Calculate the position of each individual food unit circle
            angle = i * (2 * math.pi / self.quantity)
            circle_radius = 10
            circle_x = self.x + int(large_circle_radius * math.cos(angle))
            circle_y = self.y + int(large_circle_radius * math.sin(angle))

            # Draw the individual food unit circle
            pygame.draw.circle(win, RED, (circle_x, circle_y), circle_radius)


class PheromoneGrid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(height)] for _ in range(width)]
        self.red_drawn_cells = []
        self.blue_drawn_cells = []
        self.pheromone_threshold = 2
        self.type = "RED"

    def update_pheromones(self, x, y, amount, carrying_food=False):
        self.grid[x][y] += amount
        if carrying_food:
            self.type = "BLUE"
            if (x,y) in self.red_drawn_cells:
                self.red_drawn_cells.remove((x,y))
            self.blue_drawn_cells.append((x, y))

        elif not carrying_food and self.grid[x][y] > self.pheromone_threshold:
            self.type = "RED"
            self.red_drawn_cells.append((x, y))

    def decay_pheromones(self, red_decay_rate,blue_decay_rate):
        for i, cell_coordinates in enumerate(self.red_drawn_cells):
            x, y = cell_coordinates
            self.grid[x][y] *= red_decay_rate
            if self.grid[x][y] <= self.pheromone_threshold:
                del self.red_drawn_cells[i]

        for i, cell_coordinates in enumerate(self.blue_drawn_cells):
            x, y = cell_coordinates
            self.grid[x][y] *= blue_decay_rate
            if self.grid[x][y] <= self.pheromone_threshold:
                del self.blue_drawn_cells[i]

    def draw_grid(self, win):
        for cell_coordinates in self.red_drawn_cells:
            x, y = cell_coordinates
            pheromone_level = self.grid[x][y]
            color = pygame.Color(255,0,0, min(round(pheromone_level), 255))

            # Calculate circle radius based on pheromone level
            radius = int(CELL_SIZE / 2 * pheromone_level / self.pheromone_threshold)

            # Ensure radius is within reasonable bounds
            radius = max(2, min(radius, CELL_SIZE // 2))

            # Calculate circle center coordinates
            center_x = x * CELL_SIZE + CELL_SIZE // 2
            center_y = y * CELL_SIZE + CELL_SIZE // 2

            pygame.draw.circle(win, color, (center_x, center_y), radius)

        for cell_coordinates in self.blue_drawn_cells:
            x, y = cell_coordinates
            pheromone_level = self.grid[x][y]
            color = pygame.Color(0,0,255, min(round(pheromone_level), 255))

            # Calculate circle radius based on pheromone level
            radius = int(CELL_SIZE / 2 * pheromone_level / self.pheromone_threshold)

            # Ensure radius is within reasonable bounds
            radius = max(2, min(radius, CELL_SIZE // 2))

            # Calculate circle center coordinates
            center_x = x * CELL_SIZE + CELL_SIZE // 2
            center_y = y * CELL_SIZE + CELL_SIZE // 2

            pygame.draw.circle(win, color, (center_x, center_y), radius)


def draw(win, ants, anthill, food, objects, pheromone_grid):
    # win.blit(EARTH,(0,0))
    win.fill(WHITE)
    anthill.draw_anthill(win)
    food.draw_food(win)
    pheromone_grid.decay_pheromones(RED_PHEROMONE_DECAY_RATE,BLUE_PHEROMONE_DECAY_RATE)
    pheromone_grid.draw_grid(win)
    for ant in ants:
        ant.move_randomly(ants, pheromone_grid)
        ant.sense_objects_and_react(objects, ants, pheromone_grid, anthill)
        ant.draw_ant(win)

    # Display food counter
    font = pygame.font.Font(None, 36)
    text_surface = font.render(f"Food Delivered: {anthill.food_storage}", True, BLACK)
    text_rect = text_surface.get_rect()
    text_rect.topleft = (10, 10)  # Top left corner
    win.blit(text_surface, text_rect)


def main():
    clock = pygame.time.Clock()
    run = True
    objects = []
    ants = []
    max_ants = 500
    initial_food = 30
    initial_ants = 100
    anthill_x, anthill_y = 500, 500

    food = Food(1100, 500, 100)
    anthill1 = Anthill(max_ants, initial_food, initial_ants, anthill_x, anthill_y)
    pheromone_grid = PheromoneGrid(WIDTH, HEIGHT)

    objects.append(food)
    for new_ant in anthill1.spawn_ants(anthill1.initial_ants):
        ants.append(new_ant)
        objects.append(new_ant)

    while run:
        clock.tick(FPS)
        # print(clock.get_fps())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        draw(WIN, ants, anthill1, food, objects, pheromone_grid)

        pygame.display.update()

    pygame.quit()


# import cProfile
# import pstats
#
# # Define your main function
# def main():
#     clock = pygame.time.Clock()
#     run = True
#     objects = []
#     ants = []
#     max_ants = 500
#     initial_food = 30
#     initial_ants = 20
#     anthill_x, anthill_y = 500, 500
#
#     food = Food(1500, 800, 100)
#     anthill1 = Anthill(max_ants, initial_food, initial_ants, anthill_x, anthill_y)
#     pheromone_grid = PheromoneGrid(WIDTH, HEIGHT)
#
#     objects.append(food)
#     for new_ant in anthill1.spawn_ants(anthill1.initial_ants):
#         ants.append(new_ant)
#         objects.append(new_ant)
#
#     while run:
#         clock.tick(FPS)
#         # Profile the draw function
#         with cProfile.Profile() as pr:
#             for event in pygame.event.get():
#                 if event.type == pygame.QUIT:
#                     run = False
#
#             draw(WIN, ants, anthill1, food, objects, pheromone_grid)
#
#         # Print profiling results
#         pr.print_stats()
#
#     pygame.quit()
#
# # Profile the main function
# if __name__ == "__main__":
#     profile_file = "profile_results.txt"
#     cProfile.run("main()", profile_file)
#
#     # Analyze the profiling results
#     with open(profile_file, "w") as f:
#         stats = pstats.Stats(profile_file, stream=f)
#         stats.sort_stats(pstats.SortKey.TIME)
#         stats.print_stats()


if __name__ == "__main__":
    main()

import pygame
import os
import math
import random
import time
import string
import cProfile

WIDTH, HEIGHT = 1920, 1080
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ant-Colony Simulation")
FPS = 45

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
ANT_MAX_SPEED = 1.5
RED_PHEROMONE_DECAY_RATE = 0.99
BLUE_PHEROMONE_DECAY_RATE = 0.9995
ANTHILL_SENSE_RADIUS = 150  # pixels
CELL_SIZE = 4
TURN_STRENGTH = 0.7

ANT = pygame.transform.scale(pygame.image.load(os.path.join('ant.png')), ANT_SIZE).convert()
# EARTH = pygame.transform.scale(pygame.image.load(os.path.join("dirt.bmp")), (WIDTH, HEIGHT))
# ANTHILL = pygame.image.load(os.path.join("anthill.bmp"))

# correct angle orientation when an ant faces an object
#   0 - image is looking to the right
#  90 - image is looking up
# 180 - image is looking to the left
# 270 - image is looking down
correction_angle = 90


class Ant:
    def __init__(self, ant_id, x, y, colony_id):
        self.ant_id = ant_id
        self.x = x
        self.y = y
        self.colony_id = colony_id
        self.velocity = [random.uniform(-ANT_MAX_SPEED, ANT_MAX_SPEED), random.uniform(-ANT_MAX_SPEED, ANT_MAX_SPEED)]
        self.max_speed = ANT_MAX_SPEED
        self.sense_radius = 250
        self.angle = 0
        self.inventory = []
        self.memory = []
        self.health = 100
        self.pheromone_sense_radius = 50
        self.carrying_food = False
        self.state = ""  # exploring"/"delivery/"approach food/fleeing/fighting
        self.returning_home = False
        self.turningAround = False
        self.turnAroundEndTime = 0
        self.turnAroundForce = [0, 0]
        self.pheromone_limit = 1500 + (ant_id * 5)
        # self.colony = None
        # self.age = 0
        # self.color = ANT_COLOR

    def sense_objects_and_react(self, objects, ants, pheromone_grid, anthill, food):
        cell_x = int(self.x // CELL_SIZE)
        cell_y = int(self.y // CELL_SIZE)

        # Sensed food but not yet collected
        distance_to_food = math.hypot(food.x - self.x, food.y - self.y)
        if distance_to_food <= self.sense_radius and not self.carrying_food:
            self.move_towards_target((food.x, food.y), ants)
            pheromone_grid.update_pheromones(cell_x, cell_y, 1, self.carrying_food)
            if distance_to_food <= food.quantity:
                self.collect_food(food)

        # if ant has collected food
        elif self.inventory:
            self.state = "delivering"
            self.go_home(pheromone_grid, anthill, ants)
            pheromone_grid.update_pheromones(cell_x, cell_y, 1, self.carrying_food)

        # Threshold returning flag
        elif self.returning_home:
            self.go_home(pheromone_grid, anthill, ants)
            distance_to_anthill = math.hypot(self.x - anthill.x, self.y - anthill.y)
            if len(self.memory) <= 30 and distance_to_anthill <= 30:
                self.returning_home = False

        # if ant is threshold returning
        elif len(self.memory) >= self.pheromone_limit and not self.carrying_food:
            self.state = "threshold return"
            self.returning_home = True

        # following pheromones
        else:
            self.state = "exploring"
            pheromone_trail = self.react_to_neighbour_pheromones(pheromone_grid, food)
            if pheromone_trail is not None:
                self.state="follow pheromones"
                self.move_towards_target(pheromone_trail, ants)
                pheromone_grid.update_pheromones(cell_x, cell_y, 1, self.carrying_food)
            else:
                self.move_randomly(ants, pheromone_grid)

    def collect_food(self, food_object):
        if isinstance(food_object, Food):
            if not self.inventory:
                self.inventory.append(food_object)
                self.carrying_food = True
                food_object.food_collected(1)

    def encounter_ant(self, other_ant):
        if self.colony_id != other_ant.colony_id:
            # Factors to consider
            # Nearness to their anthill
            # Their heatlh
            # Number of opponents
            # Presence of food
            pass

    def flee(self):
        pass

    def fight(self):
        pass

    def go_home(self, pheromone_grid, anthill, ants):
        anthill_x, anthill_y = anthill.x, anthill.y
        distance_to_anthill = math.hypot(self.x - anthill_x, self.y - anthill_y)

        # Dropping food into anthill
        if distance_to_anthill <= 30 and anthill.colony_id == self.colony_id and(self.state == "delivering" or self.state == "threshold return"):
            self.inventory = []
            self.memory = []
            self.state = "exploring"
            if self.carrying_food:
                self.velocity = [0, 0]
                anthill.food_storage += 1
                self.carrying_food = False

        # Moving to anthill if within sense radius
        elif distance_to_anthill <= ANTHILL_SENSE_RADIUS and anthill.colony_id == self.colony_id:
            self.move_towards_target((anthill_x, anthill_y), ants)

        else:
            if self.memory:
                next_cell = self.memory.pop()
                next_cell_coordinates = (next_cell[0] * CELL_SIZE, next_cell[1] * CELL_SIZE)
                self.move_towards_target(next_cell_coordinates, ants)
            else:
                self.move_randomly(ants, pheromone_grid)

    def react_to_neighbour_pheromones(self, pheromone_grid, food):
        nearest_pheromone = WIDTH
        nearest_pheromone_cell = None
        for cell in pheromone_grid.blue_drawn_cells:
            neighbour_x, neighbour_y = cell[0]*CELL_SIZE, cell[1]*CELL_SIZE

            if math.hypot(neighbour_x - self.x, neighbour_y - self.y) <= self.pheromone_sense_radius:
                distance_from_food = math.hypot(neighbour_x - food.x, neighbour_y - food.y)
                if distance_from_food < nearest_pheromone:
                    nearest_pheromone = distance_from_food
                    nearest_pheromone_cell = (neighbour_x, neighbour_y)
        return nearest_pheromone_cell

    def move_towards_target(self, target, ants):
        target_x, target_y = target
        dx, dy = target_x - self.x, target_y - self.y
        distance_to_target = math.hypot(dx, dy)

        cell_x = int(self.x // CELL_SIZE)
        cell_y = int(self.y // CELL_SIZE)

        if self.state != "delivering" and self.state != "threshold return":
            self.memory.append((cell_x, cell_y))

        if self.sense_radius >= distance_to_target > 0:
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

        pheromone_grid.update_pheromones(cell_x, cell_y, 1, self.carrying_food)

        if self.state != "delivering" and self.state != "threshold return":
            self.memory.append((cell_x, cell_y))

        if random.random() < 0.05:
            current_angle = math.atan2(-self.velocity[1], self.velocity[0])
            min_angle = current_angle - math.pi / 3  # 60 degrees possible turn to the left
            max_angle = current_angle + math.pi / 3  # 60 degrees possible turn to the right
            random_angle = random.uniform(min_angle, max_angle)

            random_velocity = [math.cos(random_angle), -math.sin(random_angle)]  # Reverse the sin component

            # Scale the random velocity to the ant's max speed
            random_velocity[0] *= self.max_speed
            random_velocity[1] *= self.max_speed

            # Update velocity and position for random movement
            self.velocity[0] = random_velocity[0]
            self.velocity[1] = random_velocity[1]

            self.start_turn_around(random_angle)

        # Change direction when reaching screen boundaries
        if self.x >= WIDTH - 20 or self.x <= 20 or self.y >= HEIGHT - 20 or self.y <= 20:
            self.velocity[0] = -self.velocity[1] + random.uniform(0.1, 0.8)
            self.velocity[1] = -self.velocity[0] + random.uniform(0.1, 0.8)
            self.turningAround = True

        self.x += max(min(self.velocity[0], ANT_MAX_SPEED), -ANT_MAX_SPEED)
        self.y += max(min(self.velocity[1], ANT_MAX_SPEED), -ANT_MAX_SPEED)

        # Calculate angle it should face. Make it face where it turns to
        angle = math.degrees(math.atan2(-self.velocity[1], self.velocity[0])) - correction_angle
        if angle < 0:
            angle = 360 + angle

        if self.turningAround:
            self.apply_smooth_turning()

        self.angle = angle

        # self.avoid_collision(ants)

        # Maintain ants within the screen
        self.x = max(0, min(self.x, WIDTH - 10))
        self.y = max(0, min(self.y, HEIGHT - 10))

    def start_turn_around(self, desired_angle):
        self.turningAround = True
        self.turnAroundEndTime = time.time() + random.uniform(1.5,3.5)

        # Calculate the turning force based on desired angle
        current_angle = math.radians(self.angle)
        perp_axis = [math.cos(current_angle + math.pi / 2), math.sin(current_angle + math.pi / 2)]
        self.turnAroundForce = [math.cos(desired_angle), math.sin(desired_angle)] + [
            perp_axis[i] * random.uniform(-0.5, 0.5) for i in range(2)]

    def apply_smooth_turning(self):
        if time.time() > self.turnAroundEndTime:
            self.turningAround = False
            return

        # Apply smooth turning force
        self.velocity[0] += self.turnAroundForce[0] * TURN_STRENGTH
        self.velocity[1] += self.turnAroundForce[1] * TURN_STRENGTH

    def avoid_collision(self, ants):
        for ant in ants:
            if ant != self:
                dx = ant.x - self.x
                dy = ant.y - self.y
                distance = math.hypot(dx, dy)

                if distance < ANT_SIZE[0]:  # Adjust this value as needed
                    # Calculate avoidance force
                    avoidance_force = [dx / distance, dy / distance]
                    avoidance_force[0] *= self.max_speed
                    avoidance_force[1] *= self.max_speed

                    # Apply avoidance force
                    self.velocity[0] -= avoidance_force[0]
                    self.velocity[1] -= avoidance_force[1]

                    # Smoothly steer away from the collision
                    desired_angle = math.atan2(self.velocity[1], self.velocity[0]) + math.pi / 6  # 90 degrees turn
                    self.start_turn_around(desired_angle)

    def face_target(self, target):
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
            circle_radius = 5
            offset_x = circle_radius * math.cos(math.radians(angle - correction_angle))
            offset_y = -circle_radius * math.sin(math.radians(angle - correction_angle))
            carrying_food_pos = (int(center_x + offset_x), int(center_y + offset_y))
            pygame.draw.circle(win, GREEN, carrying_food_pos, circle_radius)


class Anthill:
    def __init__(self, max_ants, initial_food, initial_ants, anthill_x, anthill_y, colony_id):
        self.max_ants = max_ants
        self.ants = []
        self.food_storage = initial_food
        self.x = anthill_x
        self.y = anthill_y
        self.colony_id = colony_id
        self.spawn_radius = 20
        self.initial_ants = initial_ants

        self.spawn_ants(initial_ants)

    def spawn_ants(self, num_ants):
        if len(self.ants) + num_ants <= self.max_ants:
            for ant_id in range(num_ants):
                rand_x = random.randint(self.x - self.spawn_radius, self.x + self.spawn_radius)
                rand_y = random.randint(self.y - self.spawn_radius, self.y + self.spawn_radius)

                new_ant = Ant(ant_id, rand_x, rand_y, self.colony_id)
                self.ants.append(new_ant)
                yield new_ant

    def draw_anthill(self, win):
        # win.blit(ANTHILL, (self.x, self.y))

        # Set center coordinates of the anthill
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        outer_radius = 50
        inner_radius = 15
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
        large_circle_radius = self.quantity
        pygame.draw.circle(win, GREEN, (self.x, self.y), large_circle_radius)

        if self.quantity <= 0:
            del self


class PheromoneGrid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = {(x,y): 0 for x in range(width) for y in range(height)}
        self.red_drawn_cells = {}
        self.blue_drawn_cells = {}
        self.pheromone_threshold = 0.01
        self.type = "RED"
    def update_pheromones(self, x, y, amount, carrying_food=False):
        self.grid[(x, y)] += amount
        if carrying_food:
            self.type = "BLUE"
            self.red_drawn_cells.pop((x, y), None)
            self.blue_drawn_cells[(x, y)] = True
        elif not carrying_food and self.grid[(x, y)] > self.pheromone_threshold:
            self.type = "RED"
            self.red_drawn_cells[(x, y)] = True

    def decay_pheromones(self, red_decay_rate, blue_decay_rate):
        self.red_drawn_cells = {cell: True for cell in self.red_drawn_cells if
                                self.grid[cell] > self.pheromone_threshold}
        self.blue_drawn_cells = {cell: True for cell in self.blue_drawn_cells if
                                 self.grid[cell] > self.pheromone_threshold}

        for cell in self.red_drawn_cells:
            self.grid[cell] *= red_decay_rate

        for cell in self.blue_drawn_cells:
            self.grid[cell] *= blue_decay_rate

    def draw_grid(self, win, shape="circle"):
        for cell in self.red_drawn_cells:
            x, y = cell
            pheromone_level = self.grid[cell]
            color = pygame.Color(255, 0, 0, min(round(pheromone_level), 255))

            if shape == "circle":
                radius = int(CELL_SIZE / 2 * pheromone_level / self.pheromone_threshold)
                radius = max(2, min(radius, CELL_SIZE // 2))

                center_x = x * CELL_SIZE + CELL_SIZE // 2
                center_y = y * CELL_SIZE + CELL_SIZE // 2

                pygame.draw.circle(win, color, (center_x, center_y), radius)

            elif shape == "square":
                side_length = int(CELL_SIZE * pheromone_level / self.pheromone_threshold)
                side_length = max(2, min(side_length, CELL_SIZE))

                top_left_x = x * CELL_SIZE + (CELL_SIZE - side_length) // 2
                top_left_y = y * CELL_SIZE + (CELL_SIZE - side_length) // 2

                pygame.draw.rect(win, color, (top_left_x, top_left_y, side_length, side_length))

        for cell in self.blue_drawn_cells:
            x, y = cell
            pheromone_level = self.grid[cell]
            color = pygame.Color(0, 0, 255, min(round(pheromone_level), 255))
            if shape == "circle":
                radius = int(CELL_SIZE / 2 * pheromone_level / self.pheromone_threshold)
                radius = max(2, min(radius, CELL_SIZE // 2))

                center_x = x * CELL_SIZE + CELL_SIZE // 2
                center_y = y * CELL_SIZE + CELL_SIZE // 2

                pygame.draw.circle(win, color, (center_x, center_y), radius)

            elif shape == "square":
                side_length = int(CELL_SIZE * pheromone_level / self.pheromone_threshold)

                side_length = max(2, min(side_length, CELL_SIZE))

                top_left_x = x * CELL_SIZE + (CELL_SIZE - side_length) // 2
                top_left_y = y * CELL_SIZE + (CELL_SIZE - side_length) // 2

                pygame.draw.rect(win, color, (top_left_x, top_left_y, side_length, side_length))


def display_properties(ant, win):
    ant_properties = [
        f"Ant ID: {ant.ant_id}",
        f"Colony:{ant.colony_id}",
        f"Position: ({round(ant.x,2), round(ant.y,2)})",
        f"Velocity: ({round(ant.velocity[0],2)}, {round(ant.velocity[1],2)})",
        f"Carrying Food: {ant.carrying_food}",
        f"State: {ant.state}",
        f"Health: {ant.health}"
    ]

    font = pygame.font.Font(None, 24)
    text_height = 40
    for prop in ant_properties:
        text_surface = font.render(prop, True, WHITE)
        win.blit(text_surface, (40, text_height))
        text_height += 20


def find_nearest_ant(mouse_pos, ants, max_distance=30):
    nearest_ant = None
    min_distance = float('inf')

    for ant in ants:
        distance = math.hypot(mouse_pos[0] - ant.x, mouse_pos[1] - ant.y)
        if distance < min_distance and distance <= max_distance:
            min_distance = distance
            nearest_ant = ant

    return nearest_ant


def generate_anthills_and_ants(initial_ants, distance_from_food, num_colonies, max_ants, initial_food,food):
    anthills = []
    ants = []
    objects = []

    food_x, food_y = food.x, food.y

    radius = distance_from_food


    # Calculate circumference of the circle
    circumference = 2 * math.pi * radius

    # Determine the portion of the circumference within the screen
    if circumference > WIDTH:
        visible_circumference = WIDTH
    else:
        visible_circumference = circumference

    angle_increment = 2 * math.pi / num_colonies

    # Place anthills around the food
    for i in range(num_colonies):
        angle = i * angle_increment
        anthill_x = int(food_x + radius * math.cos(angle))
        anthill_y = int(food_y + radius * math.sin(angle))

        # Ensure anthills are within the screen and at least 50 pixels away from the boundaries
        anthill_x = max(min(anthill_x, WIDTH - 50), 50)
        anthill_y = max(min(anthill_y, HEIGHT - 50), 50)

        anthill = Anthill(max_ants, initial_food, initial_ants, anthill_x, anthill_y, string.ascii_uppercase[i])
        anthills.append(anthill)

        # Spawn ants for each anthill
        for new_ant in anthill.spawn_ants(initial_ants):
            ants.append(new_ant)
            objects.append(new_ant)

    return ants, anthills, objects


text_cache = {}
display_ant_properties = False
current_ant = None


def draw(win, ants, anthills, food, objects, pheromone_grid, frames_per_second):
    global display_ant_properties, current_ant

    win.fill(BLACK)
    food.draw_food(win)
    pheromone_grid.decay_pheromones(RED_PHEROMONE_DECAY_RATE, BLUE_PHEROMONE_DECAY_RATE)
    pheromone_grid.draw_grid(win,)

    for anthill in anthills:
        anthill.draw_anthill(win)
        for ant in ants:
            ant.sense_objects_and_react(objects, ants, pheromone_grid, anthill, food)
            ant.draw_ant(win)

    if display_ant_properties:
        display_properties(current_ant, win)

    if pygame.mouse.get_pressed()[0]:
        mouse_pos = pygame.mouse.get_pos()
        nearest_ant = find_nearest_ant(mouse_pos, ants)
        if nearest_ant is not None:
            display_ant_properties = True
            current_ant = nearest_ant

    # Display food counter
    font = pygame.font.Font(None, 36)
    text = f"Anthill 1: {anthills[0].food_storage}         FPS: {round(frames_per_second)}"

    if text not in text_cache:
        text_surface = font.render(text, True, WHITE)
        text_cache[text] = text_surface
    else:
        text_surface = text_cache[text]

    text_rect = text_surface.get_rect()
    text_rect.topleft = (10, 5)  # Top left corner
    win.blit(text_surface, text_rect)


def main():
    clock = pygame.time.Clock()
    run = True
    objects = []
    ants = []
    max_ants = 500
    initial_food = 30
    initial_ants = 50
    distance_from_food = 800
    num_colonies = 1  # Adjust as needed
    pheromone_grid = PheromoneGrid(WIDTH, HEIGHT)
    food = Food(WIDTH//2, HEIGHT//2, 100)
    ants, anthills, objects = generate_anthills_and_ants(initial_ants, distance_from_food, num_colonies, max_ants,initial_food,food)

    # objects.append(food)

    while run:

        clock.tick(FPS)
        frames_per_second = clock.get_fps()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        draw(WIN, ants, anthills, food, objects, pheromone_grid, frames_per_second)
        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    pygame.init()
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        main()
    except KeyboardInterrupt:
        # Disable the profiler and print the results
        profiler.disable()
        profiler.print_stats()

    pygame.quit()
import pygame
import os
import math
import random
import time

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
ANT_MAX_SPEED = 1.5
RED_PHEROMONE_DECAY_RATE = 0.995
BLUE_PHEROMONE_DECAY_RATE = 0.99999
ANTHILL_SENSE_RADIUS = 150  # pixels
CELL_SIZE = 1
TURN_STRENGTH = 0.4

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
        self.state = ""  # exploring"/"delivery/"approach food
        self.returning_home = False
        self.turningAround = False
        self.turnAroundEndTime = 0
        self.turnAroundForce = [0, 0]
        self.pheromone_limit = 1000
        # self.colony = None
        # self.age = 0
        # self.color = ANT_COLOR

    def sense_objects_and_react(self, objects, ants, pheromone_grid, anthill, food ):
        cell_x = int(self.x // CELL_SIZE)
        cell_y = int(self.y // CELL_SIZE)
        sensed_objects = []

        if self.inventory:
            self.state = "delivering"
            self.go_home(pheromone_grid, anthill, ants)
            pheromone_grid.update_pheromones(cell_x, cell_y, 1, self.carrying_food)

        elif self.returning_home:
            self.go_home(pheromone_grid, anthill, ants)

            distance_to_anthill = math.hypot(self.x - anthill.x, self.y - anthill.y)

            if len(self.memory) <= 30 or distance_to_anthill <= 30:
                self.returning_home = False

        elif len(self.memory) >= self.pheromone_limit and not self.carrying_food:
            self.state = "threshold return"
            self.returning_home = True

        else:
            self.state = "exploring"
            pheromone_trail = self.react_to_neighbour_pheromones(pheromone_grid,food)
            if pheromone_trail is not None:
                pheromone_exact_coordinates = (pheromone_trail[0] * CELL_SIZE, pheromone_trail[1] * CELL_SIZE)
                self.move_towards_target(pheromone_exact_coordinates, ants)
                pheromone_grid.update_pheromones(cell_x, cell_y, 1, self.carrying_food)
            else:
                self.move_randomly(ants, pheromone_grid)

            for obj in objects:
                if obj != self:
                    distance_to_obj = math.hypot(obj.x - self.x, obj.y - self.y)
                    if distance_to_obj <= self.sense_radius:
                        sensed_objects.append(obj)

            if sensed_objects:
                for sensed_obj in sensed_objects:
                    if isinstance(sensed_obj, Food):
                        self.move_towards_target((sensed_obj.x, sensed_obj.y), ants)
                        distance_to_food = math.hypot(sensed_obj.x - self.x, sensed_obj.y - self.y)
                        if distance_to_food <= 10:
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
        anthill_x, anthill_y = anthill.x, anthill.y
        distance_to_anthill = math.hypot(self.x - anthill_x, self.y - anthill_y)

        # Dropping food
        if distance_to_anthill <= 30 and (self.state == "delivering" or self.state == "threshold return"):
            self.velocity = [0, 0]
            self.inventory = []
            self.memory = []
            self.state = "exploring"
            if self.carrying_food:
                anthill.food_storage += 1
                self.carrying_food = False

        # Moving to anthill if within sense radius
        elif distance_to_anthill <= ANTHILL_SENSE_RADIUS:
            self.move_towards_target((anthill_x, anthill_y), ants)

        else:
            if self.memory:
                next_cell = self.memory.pop()
                next_cell_coordinates = (next_cell[0] * CELL_SIZE, next_cell[1] * CELL_SIZE)
                self.move_towards_target(next_cell_coordinates, ants)
            else:
                self.move_randomly(ants, pheromone_grid)

    # new approach: try sampling pheromones as we move
    def react_to_neighbour_pheromones(self, pheromone_grid, food):
        # # Define directions: forward, left, and right based on the ant's current orientation
        # if 22.5 <= self.angle <= 67.5:
        #     forward_direction = (-1, -1)
        #     left_direction = (-1, 0)
        #     right_direction = (0, -1)
        # elif 67.5 <= self.angle <= 112.5:
        #     forward_direction = (-1, 0)
        #     left_direction = (-1, 1)
        #     right_direction = (-1, -1)
        # elif 112.5 <= self.angle <= 157.5:
        #     forward_direction = (-1, 1)
        #     left_direction = (0, 1)
        #     right_direction = (-1, 0)
        # elif 157.5 <= self.angle <= 202.5:
        #     forward_direction = (0, 1)
        #     left_direction = (1, 1)
        #     right_direction = (-1, 1)
        # elif 202.5 <= self.angle <= 247.5:
        #     forward_direction = (1, 1)
        #     left_direction = (1, 0)
        #     right_direction = (0, -1)
        # elif 247.5 <= self.angle <= 292.5:
        #     forward_direction = (1, 0)
        #     left_direction = (1, -1)
        #     right_direction = (1, 1)
        # elif 292.5 <= self.angle <= 337.5:
        #     forward_direction = (1, -1)
        #     left_direction = (0, -1)
        #     right_direction = (1, 0)
        # else:
        #     forward_direction = (0, -1)
        #     left_direction = (-1, -1)
        #     right_direction = (1, -1)
        #
        # directions = [forward_direction, left_direction, right_direction]
        # min_pheromone = float('inf')
        #
        # best_direction = None
        #
        # for dx, dy in directions:
        #     cell_x, cell_y = int(self.x / CELL_SIZE) + dx, int(self.y / CELL_SIZE) + dy
        #     # Check if the neighbour cell is within the grid
        #     if 0 <= cell_x < pheromone_grid.width and 0 <= cell_y < pheromone_grid.height:
        #         pheromone_level = pheromone_grid.grid[cell_x][cell_y]
        #         if type == "blue":
        #             if pheromone_level < min_pheromone and (cell_x, cell_y) in pheromone_grid.blue_drawn_cells:
        #                 min_pheromone = pheromone_level
        #                 best_direction = (cell_x, cell_y)
        # return best_direction
        nearby_cells = []

        cell_x = int(self.x // CELL_SIZE)
        cell_y = int(self.y // CELL_SIZE)

        sense_radius = 30
        min_pheromone = float('inf')
        min_coordinates = None
        #
        for dx in range(-sense_radius, sense_radius + 1):
            for dy in range(-sense_radius, sense_radius + 1):
                # Calculate the coordinates of the current cell
                neighbour_x = cell_x + dx
                neighbour_y = cell_y + dy
                nearby_cells.append((neighbour_x, neighbour_y))

        for (neighbour_x,neighbour_y) in nearby_cells:
            # Check if the cell coordinates are within the grid boundaries
            if 0 <= neighbour_x < pheromone_grid.width and 0 <= neighbour_y < pheromone_grid.height:
                distance_to_cell = math.hypot((neighbour_x + 0.5) * CELL_SIZE - self.x,
                                              (neighbour_y + 0.5) * CELL_SIZE - self.y)

                if distance_to_cell <= sense_radius:
                    if (neighbour_x, neighbour_y) in pheromone_grid.blue_drawn_cells:
                        distance_from_food = math.hypot(neighbour_x-food.x,neighbour_y-food.y)
                        if distance_from_food < min_pheromone:
                            min_pheromone = distance_from_food
                            min_coordinates = (neighbour_x,neighbour_y)
        return min_coordinates

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

        # Code for appending memory and other logic...
        pheromone_grid.update_pheromones(cell_x, cell_y, 1, self.carrying_food)
        if self.state != "delivering" and self.state != "threshold return":
            self.memory.append((cell_x, cell_y))

        if random.random() < 0.01:
            current_angle = math.atan2(-self.velocity[1], self.velocity[0])  # Current angle in radians
            min_angle = current_angle - math.pi / 3  # 60 degrees turn to the left
            max_angle = current_angle + math.pi / 3  # 60 degrees turn to the right
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
        if self.x >= WIDTH - 10 or self.x <= 10 or self.y >= HEIGHT - 10 or self.y <= 10:
            self.velocity[0] = -self.velocity[0] + random.uniform(0.1, 0.8)
            self.velocity[1] = -self.velocity[1] + random.uniform(0.1, 0.8)

        self.x += max(min(self.velocity[0], ANT_MAX_SPEED), -ANT_MAX_SPEED)
        self.y += max(min(self.velocity[1], ANT_MAX_SPEED), -ANT_MAX_SPEED)

        # Calculate angle it should face. Make it face where it turns to
        angle = math.degrees(math.atan2(-self.velocity[1], self.velocity[0])) - correction_angle
        if angle < 0:
            angle = 360 + angle

        if self.turningAround:
            self.apply_smooth_turning()

        self.angle = angle

        self.avoid_collision(ants)

        # Maintain ants within the screen
        self.x = max(0, min(self.x, WIDTH - 10))
        self.y = max(0, min(self.y, HEIGHT - 10))

    def start_turn_around(self, desired_angle):
        self.turningAround = True
        self.turnAroundEndTime = time.time() + 1.5  # Example duration for turn around
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
            offset_x = circle_radius * math.cos(math.radians(angle + correction_angle))
            offset_y = -circle_radius * math.sin(math.radians(angle + correction_angle))
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
        self.pheromone_threshold = 0.01
        self.type = "RED"

    def update_pheromones(self, x, y, amount, carrying_food=False):
        self.grid[x][y] += amount
        if carrying_food:
            self.type = "BLUE"
            if (x, y) in self.red_drawn_cells:
                self.red_drawn_cells.remove((x, y))
            self.blue_drawn_cells.append((x, y))

        elif not carrying_food and self.grid[x][y] > self.pheromone_threshold:
            self.type = "RED"
            self.red_drawn_cells.append((x,y))

    def decay_pheromones(self, red_decay_rate, blue_decay_rate):
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

    def draw_grid(self, win, shape="circle"):
        for cell_coordinates in self.red_drawn_cells:
            x, y = cell_coordinates
            pheromone_level = self.grid[x][y]
            color = pygame.Color(255, 0, 0, min(round(pheromone_level), 255))

            # Calculate shape based on the provided option
            if shape == "circle":
                # Calculate circle radius based on pheromone level
                radius = int(CELL_SIZE / 2 * pheromone_level / self.pheromone_threshold)

                radius = max(2, min(radius, CELL_SIZE // 2))

                center_x = x * CELL_SIZE + CELL_SIZE // 2
                center_y = y * CELL_SIZE + CELL_SIZE // 2

                pygame.draw.circle(win, color, (center_x, center_y), radius)
            elif shape == "square":
                # Calculate square side length based on pheromone level
                side_length = int(CELL_SIZE * pheromone_level / self.pheromone_threshold)

                side_length = max(2, min(side_length, CELL_SIZE))

                top_left_x = x * CELL_SIZE + (CELL_SIZE - side_length) // 2
                top_left_y = y * CELL_SIZE + (CELL_SIZE - side_length) // 2

                pygame.draw.rect(win, color, (top_left_x, top_left_y, side_length, side_length))

        for cell_coordinates in self.blue_drawn_cells:
            x, y = cell_coordinates
            pheromone_level = self.grid[x][y]
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


def draw(win, ants, anthill, food, objects, pheromone_grid):
    # win.blit(EARTH,(0,0))
    win.fill(GREY)
    anthill.draw_anthill(win)
    food.draw_food(win)
    pheromone_grid.decay_pheromones(RED_PHEROMONE_DECAY_RATE, BLUE_PHEROMONE_DECAY_RATE)
    pheromone_grid.draw_grid(win)
    for ant in ants:
        ant.sense_objects_and_react(objects, ants, pheromone_grid, anthill,food)
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
    initial_ants = 5
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
        print(clock.get_fps())
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        draw(WIN, ants, anthill1, food, objects, pheromone_grid)

        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()




import pygame
import os
import math
import random

WIDTH, HEIGHT = 1800, 960
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ant Colony Simulations")
FPS = 120

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
BROWN = (165, 42, 42)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
AQUA = (100, 200, 200)
BLACK = (0, 0, 0)
GREY = (128, 128, 128)
WHITE = (255, 255, 255)
TURQUOISE = (64, 224, 208)
EARTH = (163, 137, 104)

ANT_SIZE = (10, 10)
ANT = pygame.transform.scale(pygame.image.load(os.path.join('ant.png')), ANT_SIZE)
ANT_MAX_SPEED = .75

ANTHILL = pygame.image.load(os.path.join("earth.PNG"))
# ANTHILL = pygame.draw.circle(WIN,BLACK,)


#   0 - image is looking to the right
#  90 - image is looking up
# 180 - image is looking to the left
# 270 - image is looking down
correction_angle = 90


class Ant:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.type = "ant"
        self.velocity = [random.uniform(-ANT_MAX_SPEED, ANT_MAX_SPEED), random.uniform(-ANT_MAX_SPEED, ANT_MAX_SPEED)]
        self.max_speed = ANT_MAX_SPEED
        self.sense_radius = 250

        # self.state = "exploring"/"delivery"/"sustenance"
        # self.colony = None
        # self.health = 100
        # self.age = 0
        # self.inventory = {}
        # self.color = ANT_COLOR

    def get_angle(self):
        # Calculate angle of rotation between mouse pointer and ant
        mousex, mousey = pygame.mouse.get_pos()
        dx, dy = mousex - self.x, mousey - self.y
        angle = math.degrees(math.atan2(-dy, dx)) - correction_angle
        return angle

    def sense_objects(self, objects):
        sensed_objects = []
        for obj in objects:
            distance_to_obj = math.hypot(obj.x - self.x, obj.y - self.y)
            if distance_to_obj <= self.sense_radius:
                sensed_objects.append(obj)
        if sensed_objects:
            return [obj.type for obj in sensed_objects]
        else:
            return None

    def get_velocity(self):
        return self.velocity

    def avoid_collision(self, ants):
        for ant in ants:
            if ant != self:
                dx = ant.x - self.x
                dy = ant.y - self.y
                distance = math.hypot(dx, dy)

                if distance < ANT_SIZE[0]:  # Adjust this value as needed
                    # There's a potential collision, so we adjust the ant's velocity
                    avoidance_force = [dx / distance, dy / distance]
                    avoidance_force[0] *= self.max_speed
                    avoidance_force[1] *= self.max_speed

                    self.velocity[0] -= avoidance_force[0]
                    self.velocity[1] -= avoidance_force[1]

    def move_towards_mouse(self, ants):
        target_x, target_y = pygame.mouse.get_pos()
        dx, dy = target_x - self.x, target_y - self.y
        distance_to_mouse = math.hypot(dx, dy)

        if distance_to_mouse <= self.sense_radius:
            desired_velocity = [dx / distance_to_mouse, dy / distance_to_mouse]

            desired_velocity[0] *= self.max_speed
            desired_velocity[1] *= self.max_speed

            # Calculate steering force
            steering_force = [desired_velocity[0] - self.velocity[0], desired_velocity[1] - self.velocity[1]]

            # Update velocity
            self.velocity[0] += steering_force[0]
            self.velocity[1] += steering_force[1]

            self.avoid_collision(ants)

            # Update position
            self.x += self.velocity[0]
            self.y += self.velocity[1]

    def get_position(self):
        return self.x, self.y

    def draw_ant(self, win):
        # bind image within a rectangle
        center_x, center_y = self.x, self.y
        angle = self.get_angle()
        rotated_ant = pygame.transform.rotate(ANT, angle)
        rotated_rect = rotated_ant.get_rect(center=(center_x, center_y))
        win.blit(rotated_ant, rotated_rect.topleft)


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
            for _ in range(num_ants):
                rand_x = random.randint(self.x - self.spawn_radius, self.x + self.spawn_radius)
                rand_y = random.randint(self.y - self.spawn_radius, self.y + self.spawn_radius)

                new_ant = Ant(rand_x, rand_y)
                self.ants.append(new_ant)
                yield new_ant

    def get_population(self):
        return len(self.ants)

    def check_for_food_surplus(self):
        return self.food_storage > len(self.ants)
    def draw_anthill(self,win):
        win.blit(ANTHILL,(self.x,self.y))


def generate_first_round_ants(number):
    ants = []
    for _ in range(number):
        x = random.randint(0, WIDTH)  # Generate a random x-coordinate between 0 and 1000
        y = random.randint(0, HEIGHT)  # Generate a random y-coordinate between 0 and 700
        new_ant = Ant(x, y)  # Create a new ant at the random location
        ants.append(new_ant)
    return ants


def draw(win, ants,anthill):
    win.fill(GREY)
    anthill.draw_anthill(win)
    for ant in ants:
        ant.move_towards_mouse(ants)
        ant.draw_ant(win)

    pygame.display.update()


def main():
    clock = pygame.time.Clock()
    run = True
    objects = []
    ants = []
    anthill1 = Anthill(500,30,20,500,500)
    for new_ant in anthill1.spawn_ants(anthill1.initial_ants):
        ants.append(new_ant)
    # ants = generate_first_round_ants(1300)
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        draw(WIN, ants,anthill1)

        pygame.display.update()

    pygame.quit()


main()

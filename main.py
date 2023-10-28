import pygame
import os
import math
import random

WIDTH, HEIGHT = 1280, 720
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ant Colony Simulations")
FPS = 120


AQUA = (100, 200, 200)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
WHITE = (255, 255, 255)

ANT_SIZE = (25, 25)
ANT = pygame.transform.scale(pygame.image.load(os.path.join('ant.png')), ANT_SIZE)
ANT_MAX_SPEED = 3


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
        # self.state = "exploring"
        # self.colony = None
        # self.health = 100
        # self.age = 0
        self.sense_radius = 200
        # self.inventory = {}
        # self.color = ANT_COLOR
        self.max_speed = ANT_MAX_SPEED

    def get_angle(self):
        # Calculate angle of rotation between mouse pointer and ant
        mousex, mousey = pygame.mouse.get_pos()
        dx, dy = mousex - self.x, mousey - self.y
        angle = math.degrees(math.atan2(-dy, dx)) - correction_angle
        return angle

    def sense_objects(self,objects):
        sensed_objects = []
        for obj in objects:
            distance_to_obj = math.hypot(obj.x - self.x,obj.y - self.y)
            if distance_to_obj<=self.sense_radius:
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

                if distance < 2 * ANT_SIZE[0]:  # Adjust this value as needed
                    # There's a potential collision, so we adjust the ant's velocity
                    avoidance_force = [dx / distance, dy / distance]
                    avoidance_force[0] *= self.max_speed
                    avoidance_force[1] *= self.max_speed

                    self.velocity[0] -= avoidance_force[0]
                    self.velocity[1] -= avoidance_force[1]
    def move_towards_mouse(self,ants):
        target_x,target_y = pygame.mouse.get_pos()
        dx, dy = target_x - self.x, target_y - self.y
        distance_to_mouse = math.hypot(dx, dy)

        if distance_to_mouse <= self.sense_radius:
            desired_velocity = [dx/distance_to_mouse,dy/distance_to_mouse]

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
        return self.x,self.y

    def draw_ant(self,win):
        # bind image within a rectangle
        center_x, center_y = self.x, self.y
        angle = self.get_angle()
        rotated_ant = pygame.transform.rotate(ANT, angle)
        rotated_rect = rotated_ant.get_rect(center=(center_x, center_y))
        win.blit(rotated_ant, rotated_rect.topleft)


def draw(win, ants):

    win.fill(WHITE)
    objects = []
    objects = objects + ants
    for ant in ants:
        print(ant.get_velocity())
        ant.move_towards_mouse(ants)
        ant.draw_ant(win)

    pygame.display.update()


def main():
    clock = pygame.time.Clock()
    run = True
    ants = [Ant(500, 500),Ant(500,300),Ant(600,400),Ant(600,100)]
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        draw(WIN, ants)

        pygame.display.update()

    pygame.quit()


main()

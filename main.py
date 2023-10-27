import pygame
import os
import math

WIDTH, HEIGHT = 1280, 720
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ant Simulations")
FPS = 120
ant_speed = 2

AQUA = (100, 200, 200)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
WHITE = (255, 255, 255)

#   0 - image is looking to the right
#  90 - image is looking up
# 180 - image is looking to the left
# 270 - image is looking down
correction_angle = 90




def get_angle(centre_x,centre_y):
    #Calculate angle of rotation between mouse pointer and ant
    mousex, mousey = pygame.mouse.get_pos()
    dx, dy = mousex - centre_x, mousey - centre_y
    angle = math.degrees(math.atan2(-dy, dx)) - correction_angle
    return angle


def draw(win, ant_position):
    #bind image within a rectangle
    ANT = pygame.transform.scale(pygame.image.load(os.path.join('ant.png')), (60, 60))
    rect = ANT.get_rect()
    center_x, center_y = ant_position  #should be relative to the entire window
    angle = get_angle(center_x, center_y)
    rotated_ant = pygame.transform.rotate(ANT, angle)
    rotated_rect = rotated_ant.get_rect(center=ant_position)

    win.fill(WHITE)
    win.blit(rotated_ant, rotated_rect.topleft)

    pygame.display.update()


def main():
    clock = pygame.time.Clock()
    run = True
    start_pos = WIN.get_rect().center
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        draw(WIN,start_pos)


        pygame.display.update()

    pygame.quit()

main()
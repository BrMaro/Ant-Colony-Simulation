from ast import And
import pygame
import os
import math

WIDTH, HEIGHT = 1280, 720
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ant Simulations")
FPS = 60
ant_speed = 2

AQUA = (100, 200, 200)
BLACK = (0, 0, 0)
GREY = (200, 200, 200)
WHITE = (255, 255, 255)



def antrotation(antx, anty):
    rotationangle = 0
    mousex, mousey = pygame.mouse.get_pos()
    if mousex < antx and mousey < anty:
        rotationangle = math.degrees(math.atan(mousey / mousex))
    if mousex < antx and mousey > anty:
        rotationangle = 180 - math.degrees(math.atan(mousey / mousex))
    if mousex > antx and mousey > anty:
        rotationangle = 180 + math.degrees(math.atan(mousey / mousex))
    if mousex > antx and mousey < anty:
        rotationangle = 360 - math.degrees(math.atan(mousey / mousex))
    print(mousex, mousey, rotationangle)
    return rotationangle



def ant_origin_rotations(antx, anty, image):
    rotationangle = 0
    mousex, mousey = pygame.mouse.get_pos()

    # Calculate the position with the rotated image size
    rotated_image = pygame.transform.rotate(image, rotationangle)
    x = antx - rotated_image.get_width() // 2
    y = anty - rotated_image.get_height() // 2

    # Calculate the angle from the mouse position to the image center
    dx = mousex - antx
    dy = mousey - anty
    rotationangle = math.degrees(math.atan2(dy, dx))

    print(mousex, mousey, rotationangle)
    return rotationangle

def antmovement(antx, anty):
    mousex, mousey = pygame.mouse.get_pos()
    if mousex < antx:
        antx -= ant_speed
    else:
        antx += ant_speed

    if mousey < anty:
        anty -= ant_speed
    else:
        anty += ant_speed
    return antx, anty


def main():
    clock = pygame.time.Clock()
    rotation_angle = 0
    run = True
    antx, anty = (WIDTH // 2, HEIGHT // 2)
    while run:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        WIN.fill(WHITE)
        SHOWN_ANT = pygame.transform.rotate(pygame.transform.scale(pygame.image.load(os.path.join('ant.png')), (20, 20)),rotation_angle)
        antx, anty = antmovement(antx, anty)
        WIN.blit(SHOWN_ANT, (antx, anty))
        rotation_angle = ant_origin_rotations(antx,anty,SHOWN_ANT)



        pygame.display.update()

    pygame.quit()


main()
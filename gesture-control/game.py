import pygame

pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gesture-Controlled Game")

# Game variables
player = pygame.Rect(100, 300, 50, 50)  # Example player (a rectangle)
running = True

# Main game loop
while running:
    screen.fill((0, 0, 0))  # Clear screen

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Detect key presses (simulated by WebSocket client)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.y -= 50  # Jump
            elif event.key == pygame.K_UP:
                player.y -= 30  # Move up

    # Draw player
    pygame.draw.rect(screen, (0, 255, 0), player)

    pygame.display.flip()
    pygame.time.delay(30)

pygame.quit()

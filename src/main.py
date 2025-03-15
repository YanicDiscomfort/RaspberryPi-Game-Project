import time
import pygame
import random

import RPi.GPIO as GPIO
import smbus2


GPIO.setmode(GPIO.BCM)

# Farben für die verschiedenen Tetris-Steine
colors = [
    (0, 0, 0),  # Hintergrundfarbe (schwarz)
    (120, 37, 179),
    (100, 179, 179),
    (80, 34, 22),
    (80, 134, 22),
    (180, 34, 22),
    (180, 34, 122),
]

class Figure:
    x = 0
    y = 0

    # Verschiedene Formen der Tetris-Steine
    figures = [
        [[1, 5, 9, 13], [4, 5, 6, 7]],  # Form 1 (T)
        [[4, 5, 9, 10], [2, 6, 5, 9]],  # Form 2 (S)
        [[6, 7, 9, 10], [1, 5, 6, 10]],  # Form 3 (Z)
        [[1, 2, 5, 9], [0, 4, 5, 6], [1, 5, 9, 8], [4, 5, 6, 10]],  # Form 4 (L)
        [[1, 2, 6, 10], [5, 6, 7, 9], [2, 6, 10, 11], [3, 5, 6, 7]],  # Form 5 (J)
        [[1, 4, 5, 6], [1, 4, 5, 9], [4, 5, 6, 9], [1, 5, 6, 9]],  # Form 6 (O)
        [[1, 2, 5, 6]],  # Form 7 (I)
    ]

    def __init__(self, x, y):
        self.x = x  # X-Position des Steins
        self.y = y  # Y-Position des Steins
        self.type = random.randint(0, len(self.figures) - 1)  # Zufällige Auswahl der Steinform
        self.color = random.randint(1, len(colors) - 1)  # Zufällige Farbe des Steins
        self.rotation = 0  # Anfangsrotation ist 0 (keine Drehung)

    def image(self):
        # Gibt die aktuelle Darstellung des Steins basierend auf der Rotation zurück
        return self.figures[self.type][self.rotation]

    def rotate(self):
        # Dreht den Stein im Uhrzeigersinn
        self.rotation = (self.rotation - 1) % len(self.figures[self.type])

class Tetris:
    def __init__(self, height, width):
        self.level = 2  # Schwierigkeitsgrad (Level)
        self.score = 0  # Spielergebnis
        self.lives = 3  # Anzahl der Leben des Spielers
        self.state = "start"  # Aktueller Spielzustand
        self.field = []  # Spielfeld
        self.height = height  # Höhe des Spielfelds
        self.width = width  # Breite des Spielfelds
        self.x = 100  # X-Offset für das Zeichnen des Spielfelds
        self.y = 60  # Y-Offset für das Zeichnen des Spielfelds
        self.zoom = 20  # Größe eines Blocks
        self.figure = None  # Der aktuelle Tetris-Stein

        # Initialisiere das Spielfeld mit Nullen (leere Felder)
        self.field = [[0 for _ in range(width)] for _ in range(height)]

    def new_figure(self):
        # Erzeugt einen neuen Tetris-Stein
        self.figure = Figure(3, 0)

    def intersects(self):
        # Prüft, ob der aktuelle Stein mit anderen Blöcken oder den Rändern des Spielfelds kollidiert
        intersection = False
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    if i + self.figure.y > self.height - 1 or \
                            j + self.figure.x > self.width - 1 or \
                            j + self.figure.x < 0 or \
                            self.field[i + self.figure.y][j + self.figure.x] > 0:
                        intersection = True
        return intersection

    def break_lines(self):
        # Überprüft, ob eine Reihe vollständig ausgefüllt ist und entfernt diese
        lines = 0
        for i in range(1, self.height):
            zeros = 0
            for j in range(self.width):
                if self.field[i][j] == 0:
                    zeros += 1
            if zeros == 0:  # Eine komplette Reihe
                lines += 1
                for i1 in range(i, 1, -1):
                    for j in range(self.width):
                        self.field[i1][j] = self.field[i1 - 1][j]
        self.score += lines ** 2  # Punkte basierend auf der Anzahl der entfernten Reihen

    def go_space(self):
        # Der Stein fällt, bis er auf ein Hindernis trifft
        while not self.intersects():
            self.figure.y += 1
        self.figure.y -= 1
        self.freeze()

    def go_down(self):
        # Der Stein bewegt sich um eine Reihe nach unten
        self.figure.y += 1
        if self.intersects():
            self.figure.y -= 1
            self.freeze()

    def freeze(self):
        # "Einfrieren" des Steins (wenn er auf einem anderen Stein oder dem Spielfeldboden landet)
        for i in range(4):
            for j in range(4):
                if i * 4 + j in self.figure.image():
                    self.field[i + self.figure.y][j + self.figure.x] = self.figure.color
        self.break_lines()  # Überprüfe, ob Reihen entfernt werden können
        self.new_figure()  # Erzeuge einen neuen Stein
        if self.intersects():
            # Wenn nach dem Erzeugen des neuen Steins eine Kollision vorliegt, hat der Spieler verloren
            self.lives -= 1  # Ein Leben abziehen
            if self.lives <= 0:
                self.state = "gameover"  # Das Spiel ist vorbei, keine Leben mehr
            else:
                self.reset_game()  # Zurücksetzen des Spiels, aber mit verbleibenden Leben

    def go_side(self, dx):
        # Der Stein bewegt sich nach links (-1) oder rechts (+1)
        old_x = self.figure.x
        self.figure.x += dx
        if self.intersects():
            self.figure.x = old_x

    def rotate(self):
        # Der Stein wird rotiert
        old_rotation = self.figure.rotation
        self.figure.rotate()
        if self.intersects():
            self.figure.rotation = old_rotation  # Rückgängig machen, wenn die Rotation nicht möglich ist

    def reset_game(self):
        # Setzt das Spielfeld zurück und beginnt mit einem neuen Spiel
        self.field = [[0 for _ in range(self.width)] for _ in range(self.height)]  # Spielfeld zurücksetzen
        self.score = 0  # Punkte zurücksetzen
        self.new_figure()  # Erzeuge einen neuen Tetris-Stein


class Rpi:
    def __init__(self):
        GPIO.setup(14, GPIO.IN)
        GPIO.setup(17, GPIO.OUT)
        GPIO.setup(27, GPIO.OUT)
        GPIO.setup(22, GPIO.OUT)

        self.bus = smbus2.SMBus(1)
        self.address = 0x48
        self.last_joystick_action = time.time()
        self.joystick_delay = 0.2  # Delay in seconds between joystick actions
        self.last_button_action = time.time()
        self.button_delay = 0.3  # Delay in seconds between button actions

    def read_joystick_x(self):
        try:
            self.bus.write_byte(self.address, 0)  # Channel 0 for X-axis
            self.bus.read_byte(self.address)  # Dummy read to start conversion
            return self.bus.read_byte(self.address)
        except OSError as e:
            print(f"I2C communication error: {e}")
            return None

    def read_joystick_y(self):
        try:
            self.bus.write_byte(self.address, 1)  # Channel 1 for Y-axis
            self.bus.read_byte(self.address)  # Dummy read to start conversion
            return self.bus.read_byte(self.address)
        except OSError as e:
            print(f"I2C communication error: {e}")
            return None

    def get_button(self):
        if GPIO.input(14) == 0:
            return True
        return False

    def process_button(self, game):
        current_time = time.time()
        if current_time - self.last_button_action >= self.button_delay:
            if self.get_button():
                game.rotate()  # Rotate the figure
                self.last_button_action = current_time
                return True
        return False

    def process_joystick(self, game):
        current_time = time.time()
        if current_time - self.last_joystick_action >= self.joystick_delay:
            # Read X-axis for left/right movement
            joystick_x = self.read_joystick_x()
            if joystick_x is not None:
                if joystick_x < 100:
                    game.go_side(1)  # Move right
                    self.last_joystick_action = current_time
                elif joystick_x > 225:
                    game.go_side(-1)  # Move left
                    self.last_joystick_action = current_time

            # Read Y-axis for down movement
            joystick_y = self.read_joystick_y()
            if joystick_y is not None:
                if joystick_y < 100:  # Joystick pushed down
                    game.go_down()  # Move block down
                    self.last_joystick_action = current_time

    def reset_game(self):
        GPIO.output(17, GPIO.HIGH)
        GPIO.output(27, GPIO.HIGH)
        GPIO.output(22, GPIO.HIGH)

    def remove_life(self, lives):
        if lives > 0:
            lives -= 1
            if lives == 2:
                GPIO.output(17, GPIO.LOW)
            elif lives == 1:
                GPIO.output(27, GPIO.LOW)
            elif lives == 0:
                GPIO.output(22, GPIO.LOW)

# Initialisiere das Spiel mit pygame
pygame.init()
rpi = Rpi()
rpi.reset_game()

# Farben für das Spiel
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)

# Fenstergröße
size = (400, 500)
screen = pygame.display.set_mode(size)

pygame.display.set_caption("Tetris")

# Hauptspielschleife
done = False
clock = pygame.time.Clock()
fps = 25  # Frames pro Sekunde
game = Tetris(20, 10)  # Erstelle ein Tetris-Spiel mit einem Spielfeld von 20x10
counter = 0

previous_lives = game.lives  # Track lives to detect changes

pressing_down = False  # Wird verwendet, um festzustellen, ob der Spieler die Pfeiltaste nach unten gedrückt hält

while not done:
    if game.figure is None:
        game.new_figure()  # Erzeuge einen neuen Tetris-Stein, wenn keiner vorhanden ist
    counter += 1
    if counter > 100000:
        counter = 0

    # Check if player lost a life
    if previous_lives > game.lives:
        rpi.remove_life(previous_lives)
        previous_lives = game.lives

    # Das Spiel bewegt den Stein nach unten, wenn genügend Zeit vergangen ist oder der Spieler nach unten drückt
    if counter % (fps // game.level // 2) == 0 or pressing_down:
        if game.state == "start":
            game.go_down()

    rpi.process_joystick(game)

    rpi.process_button(game)

    # Verarbeite Tasteneingaben
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                game.rotate()
                pressing_down = False
            if event.key == pygame.K_DOWN:
                pressing_down = True
            if event.key == pygame.K_LEFT:
                game.go_side(-1)
                pressing_down = False
            if event.key == pygame.K_RIGHT:
                game.go_side(1)
                pressing_down = False
            if event.key == pygame.K_SPACE:
                game.go_space()
                pressing_down = False
            if event.key == pygame.K_ESCAPE:
                game.__init__(20, 10)  # Das Spiel zurücksetzen
                rpi.reset_game()
                previous_lives = game.lives  # Reset the life counter

    # Wenn die nach unten-Taste losgelassen wird, stoppe das Fallen
    if event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                pressing_down = False

    # Bildschirm zeichnen
    screen.fill(BLACK)

    # Zeichne das Spielfeld
    for i in range(game.height):
        for j in range(game.width):
            pygame.draw.rect(screen, GRAY, [game.x + game.zoom * j, game.y + game.zoom * i, game.zoom, game.zoom], 1)
            if game.field[i][j] > 0:
                pygame.draw.rect(screen, colors[game.field[i][j]], 
                                 [game.x + game.zoom * j + 1, game.y + game.zoom * i + 1, game.zoom - 2, game.zoom - 1])

    # Zeichne den aktuellen Stein
    if game.figure is not None:
        for i in range(4):
            for j in range(4):
                p = i * 4 + j
                if p in game.figure.image():
                    pygame.draw.rect(screen, colors[game.figure.color], 
                                     [game.x + game.zoom * (j + game.figure.x) + 1,
                                      game.y + game.zoom * (i + game.figure.y) + 1,
                                      game.zoom - 2, game.zoom - 2])

    # Anzeige von Punkten und Leben
    font = pygame.font.SysFont('Calibri', 25, True, False)
    font1 = pygame.font.SysFont('Calibri', 65, True, False)
    text = font.render("Score: " + str(game.score), True, WHITE)
    lives_text = font.render("Lives: " + str(game.lives), True, WHITE)  # Anzeige der Leben
    text_game_over = font1.render("Game Over", True, (255, 125, 0))
    text_game_over1 = font1.render("Press ESC", True, (255, 215, 0))

    # Positionierung der Textanzeigen
    screen.blit(text, [0, 0])
    screen.blit(lives_text, [0, 30])  # Anzeige der verbleibenden Leben
    if game.state == "gameover":
        screen.blit(text_game_over, [20, 200])
        screen.blit(text_game_over1, [25, 265])

    pygame.display.flip()  # Bildschirm aktualisieren
    clock.tick(fps)  # Framerate einhalten

pygame.quit()  # Beende pygame

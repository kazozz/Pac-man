import pygame
import random
import sys
import math

# Инициализация Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

# Константы
WINDOW_WIDTH = 780
WINDOW_HEIGHT = 650
CELL_SIZE = 30
FPS = 60

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (255, 192, 203)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
DARK_BLUE = (0, 0, 150)
HEART_RED = (255, 50, 50)

# Направления
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# ЗВУКИ
def create_sound(frequency, duration, volume=0.3):
    try:
        sample_rate = 22050
        n_samples = int(sample_rate * duration)
        sound_bytes = bytearray()
        for i in range(n_samples):
            value = int(32767 * volume * math.sin(2 * math.pi * frequency * i / sample_rate))
            sound_bytes.append(value & 0xFF)
            sound_bytes.append((value >> 8) & 0xFF)
        return pygame.mixer.Sound(buffer=bytes(sound_bytes))
    except:
        return None

SOUND_POWER = create_sound(440, 0.3, 0.3)
SOUND_DEATH = create_sound(200, 0.5, 0.4)
SOUND_EAT_GHOST = create_sound(1200, 0.1, 0.3)
SOUND_START = create_sound(523, 0.2, 0.3)
SOUND_COUNTDOWN = create_sound(660, 0.15, 0.25)

def play_sound(sound):
    if sound:
        sound.play()

def play_win():
    notes = [523, 587, 659, 698, 784, 880, 987, 1046]
    for note in notes:
        s = create_sound(note, 0.12, 0.3)
        if s:
            s.play()
            pygame.time.wait(130)

def play_lose():
    notes = [523, 493, 440, 392, 349, 329, 293, 261]
    for note in notes:
        s = create_sound(note, 0.15, 0.3)
        if s:
            s.play()
            pygame.time.wait(160)

class Pacman:
    def __init__(self, x, y, player_num):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.speed = 3
        self.radius = CELL_SIZE // 2 - 2
        self.lives = 3
        self.score = 0
        self.invincible_timer = 90
        self.player_num = player_num
        
    def update(self, walls):
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        
        new_x = self.x + self.next_direction[0] * self.speed
        new_y = self.y + self.next_direction[1] * self.speed
        new_rect = pygame.Rect(new_x - self.radius, new_y - self.radius, 
                                self.radius * 2, self.radius * 2)
        
        collision = False
        for wall in walls:
            if new_rect.colliderect(wall):
                collision = True
                break
        
        if not collision:
            self.direction = self.next_direction
            self.x = new_x
            self.y = new_y
        
        new_x = self.x + self.direction[0] * self.speed
        new_y = self.y + self.direction[1] * self.speed
        new_rect = pygame.Rect(new_x - self.radius, new_y - self.radius, 
                                self.radius * 2, self.radius * 2)
        
        collision = False
        for wall in walls:
            if new_rect.colliderect(wall):
                collision = True
                break
        
        if not collision:
            self.x = new_x
            self.y = new_y
        
        if self.x < 0:
            self.x = WINDOW_WIDTH
        elif self.x > WINDOW_WIDTH:
            self.x = 0
        if self.y < 0:
            self.y = WINDOW_HEIGHT - 50
        elif self.y > WINDOW_HEIGHT - 50:
            self.y = 0
    
    def draw(self, screen):
        if self.invincible_timer > 0 and (pygame.time.get_ticks() // 100 % 2 == 0):
            return
        color = YELLOW if self.player_num == 1 else GREEN
        angle = 0
        if self.direction == RIGHT:
            angle = 0
        elif self.direction == LEFT:
            angle = 180
        elif self.direction == UP:
            angle = 90
        elif self.direction == DOWN:
            angle = 270
        mouth_angle = 30 + (pygame.time.get_ticks() // 100 % 10) * 3
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.arc(screen, BLACK, 
                       (self.x - self.radius, self.y - self.radius, 
                        self.radius * 2, self.radius * 2),
                       (angle - mouth_angle) * 3.14159 / 180,
                       (angle + mouth_angle) * 3.14159 / 180, 3)
    
    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.invincible_timer = 90

class Ghost:
    def __init__(self, x, y, color, name):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.color = color
        self.name = name
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.speed = 2
        self.radius = CELL_SIZE // 2 - 2
        self.frightened_mode = False
        self.frightened_timer = 0
        self.respawn_timer = 0
        
    def update(self, walls, pacman_x, pacman_y, difficulty):
        if self.respawn_timer > 0:
            self.respawn_timer -= 1
            return
        if difficulty == 1:
            current_speed = 1.5
        elif difficulty == 2:
            current_speed = 2.0
        else:
            current_speed = 2.8
        if self.frightened_mode:
            current_speed = 1.2
            if random.random() < 0.03:
                self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        else:
            if self.name == "Blinky":
                self.chase_pacman(pacman_x, pacman_y)
            elif self.name == "Pinky":
                target_x = pacman_x + 80
                target_y = pacman_y + 80
                self.move_towards_target(target_x, target_y)
            elif self.name == "Inky":
                if random.random() < 0.05:
                    self.chase_pacman(pacman_x, pacman_y)
                elif random.random() < 0.03:
                    self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        new_x = self.x + self.direction[0] * current_speed
        new_y = self.y + self.direction[1] * current_speed
        new_rect = pygame.Rect(new_x - self.radius, new_y - self.radius,
                                self.radius * 2, self.radius * 2)
        collision = False
        for wall in walls:
            if new_rect.colliderect(wall):
                collision = True
                break
        if collision:
            possible_dirs = [UP, DOWN, LEFT, RIGHT]
            random.shuffle(possible_dirs)
            for new_dir in possible_dirs:
                test_x = self.x + new_dir[0] * current_speed
                test_y = self.y + new_dir[1] * current_speed
                test_rect = pygame.Rect(test_x - self.radius, test_y - self.radius,
                                        self.radius * 2, self.radius * 2)
                collision = False
                for wall in walls:
                    if test_rect.colliderect(wall):
                        collision = True
                        break
                if not collision:
                    self.direction = new_dir
                    break
        else:
            self.x = new_x
            self.y = new_y
        if self.frightened_mode:
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.frightened_mode = False
    
    def chase_pacman(self, pacman_x, pacman_y):
        dx = pacman_x - self.x
        dy = pacman_y - self.y
        if abs(dx) > abs(dy):
            if dx > 0:
                self.direction = RIGHT
            else:
                self.direction = LEFT
        else:
            if dy > 0:
                self.direction = DOWN
            else:
                self.direction = UP
    
    def move_towards_target(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        if abs(dx) > abs(dy):
            if dx > 0:
                self.direction = RIGHT
            else:
                self.direction = LEFT
        else:
            if dy > 0:
                self.direction = DOWN
            else:
                self.direction = UP
    
    def draw(self, screen):
        if self.respawn_timer > 0:
            return
        if self.frightened_mode:
            color = BLUE if (pygame.time.get_ticks() // 100) % 2 == 0 else PURPLE
        else:
            color = self.color
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.rect(screen, color, 
                        (int(self.x - self.radius), int(self.y), 
                         self.radius * 2, self.radius // 2))
        pygame.draw.circle(screen, WHITE, (int(self.x - 7), int(self.y - 5)), 5)
        pygame.draw.circle(screen, WHITE, (int(self.x + 7), int(self.y - 5)), 5)
        pygame.draw.circle(screen, BLACK, (int(self.x - 7), int(self.y - 5)), 2)
        pygame.draw.circle(screen, BLACK, (int(self.x + 7), int(self.y - 5)), 2)
    
    def reset(self):
        self.x = self.start_x
        self.y = self.start_y
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.frightened_mode = False
        self.respawn_timer = 40

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Пакман - Учебная практика")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        self.medium_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 24)
        self.running = True
        self.difficulty = 1
        self.game_mode = "menu"
        self.current_player = 1
        self.winner_score = 0
        self.winner_name = ""
        self.player1_lives = 3
        self.player2_lives = 3
        self.player1_score = 0
        self.player2_score = 0
        self.setup_game()
    
    def draw_heart(self, screen, x, y, size=20):
        heart_pixels = [
            [0, 1, 0, 1, 0],
            [1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1],
            [0, 1, 1, 1, 0],
            [0, 0, 1, 0, 0]
        ]
        pixel_size = max(1, size // 5)
        for row in range(5):
            for col in range(5):
                if heart_pixels[row][col] == 1:
                    pygame.draw.rect(screen, HEART_RED, 
                                   (x + col * pixel_size, y + row * pixel_size, 
                                    pixel_size, pixel_size))
    
    def draw_hearts(self, screen, x, y, count, size=20):
        heart_width = size + 5
        for i in range(count):
            self.draw_heart(screen, x + i * heart_width, y, size)
    
    def get_score_to_win(self):
        if self.difficulty == 1:
            return 800
        elif self.difficulty == 2:
            return 1000
        else:
            return 1200
        
    def setup_game(self):
        self.walls = []
        self.pellets = []
        self.power_pellets = []
        self.total_pellets = 0
        
        self.maze = [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,2,1,1,1,2,1,1,1,2,1,2,1,1,1,2,1,1,1,2,1,1,1,2,2,1],
            [1,2,1,2,2,2,1,2,2,2,2,2,1,2,2,2,2,2,1,2,2,2,1,2,2,1],
            [1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,2,1],
            [1,2,2,2,1,2,2,2,1,2,2,2,2,2,1,2,2,2,1,2,2,2,2,2,2,1],
            [1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,2,1],
            [1,2,1,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,2,2,1,2,2,2,2,1],
            [1,2,1,1,1,2,1,2,1,1,1,2,1,1,1,2,1,2,1,2,1,2,1,2,2,1],
            [1,2,2,2,2,2,1,2,2,2,2,2,1,2,2,2,2,2,1,2,2,2,2,2,2,1],
            [1,2,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,1,2,2,1],
            [1,2,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,2,2,2,2,1],
            [1,2,1,1,1,2,1,2,1,1,1,2,1,2,1,2,1,2,1,2,1,2,1,2,2,1],
            [1,2,2,2,2,2,1,2,2,2,2,2,1,2,2,2,2,2,1,2,2,2,2,2,2,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        ]
        
        for row in range(len(self.maze)):
            for col in range(len(self.maze[row])):
                x = col * CELL_SIZE + CELL_SIZE // 2
                y = row * CELL_SIZE + CELL_SIZE // 2
                if self.maze[row][col] == 1:
                    wall_rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    self.walls.append(wall_rect)
                elif self.maze[row][col] == 2:
                    if (row == 1 and col == 1) or (row == 1 and col == 24) or \
                       (row == 13 and col == 1) or (row == 13 and col == 24):
                        self.power_pellets.append((x, y))
                        self.total_pellets += 1
                    else:
                        self.pellets.append((x, y))
                        self.total_pellets += 1
        
        start_x = 13 * CELL_SIZE + CELL_SIZE // 2
        start_y = 13 * CELL_SIZE + CELL_SIZE // 2
        self.player1 = Pacman(start_x, start_y, 1)
        self.player2 = Pacman(start_x, start_y, 2)
        self.current_pacman = self.player1
        self.current_player = 1
        
        if self.game_mode == "two_player":
            self.player1_lives = 3
            self.player2_lives = 3
            self.player1_score = 0
            self.player2_score = 0
            self.player1.lives = 3
            self.player2.lives = 3
            self.player1.score = 0
            self.player2.score = 0
        else:
            self.player1_lives = 3
            self.player1_score = 0
            self.player1.lives = 3
            self.player1.score = 0
        
        self.ghosts = [
            Ghost(5 * CELL_SIZE + CELL_SIZE // 2, 5 * CELL_SIZE + CELL_SIZE // 2, RED, "Blinky"),
            Ghost(20 * CELL_SIZE + CELL_SIZE // 2, 5 * CELL_SIZE + CELL_SIZE // 2, PINK, "Pinky"),
            Ghost(5 * CELL_SIZE + CELL_SIZE // 2, 10 * CELL_SIZE + CELL_SIZE // 2, ORANGE, "Inky"),
        ]
        
        self.frightened_mode_active = False
        self.frightened_timer = 0
        self.start_delay = 120
    
    def start_countdown(self):
        for i in range(3, 0, -1):
            self.draw_game_only()
            count_text = self.big_font.render(str(i), True, YELLOW)
            text_rect = count_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 100))
            self.screen.blit(count_text, text_rect)
            pygame.display.flip()
            play_sound(SOUND_COUNTDOWN)
            pygame.time.wait(800)
    
    def draw_game_only(self):
        self.screen.fill(BLACK)
        for wall in self.walls:
            pygame.draw.rect(self.screen, DARK_BLUE, wall)
            pygame.draw.rect(self.screen, BLUE, wall, 2)
        for pellet in self.pellets:
            pygame.draw.circle(self.screen, WHITE, pellet, 3)
        for power_pellet in self.power_pellets:
            pygame.draw.circle(self.screen, YELLOW, power_pellet, 12)
            pygame.draw.circle(self.screen, WHITE, power_pellet, 6)
        for ghost in self.ghosts:
            ghost.draw(self.screen)
        self.current_pacman.draw(self.screen)
    
    def show_instructions(self):
        self.screen.fill(BLACK)
        title = self.big_font.render("ИНСТРУКЦИЯ", True, YELLOW)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 40))
        self.screen.blit(title, title_rect)
        score_to_win = self.get_score_to_win()
        instructions = [
            ("ЦЕЛЬ ИГРЫ:", 100),
            (f"Собери {score_to_win} очков, избегая призраков!", 135),
            ("", 165),
            ("УПРАВЛЕНИЕ:", 195),
            ("Стрелки - игрок 1", 230),
            ("Клавиши W,A,S,D - игрок 2", 265),
            ("", 295),
            ("УСИЛЕНИЯ:", 325),
            ("Большие желтые точки дают", 360),
            ("временную возможность есть призраков!", 390),
            ("", 420),
            ("СЛОЖНОСТЬ:", 450),
            ("Легкая - 800 очков, призраки медленнее", 480),
            ("Средняя - 1000 очков", 510),
            ("Сложная - 1200 очков, призраки быстрее", 540),
            ("", 580),
            ("Нажми ESC для возврата в меню", 610)
        ]
        for text, y in instructions:
            if text:
                color = GREEN if ":" in text else WHITE
                inst_text = self.small_font.render(text, True, color)
                rect = inst_text.get_rect(center=(WINDOW_WIDTH//2, y))
                self.screen.blit(inst_text, rect)
        pygame.display.flip()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    waiting = False
                elif event.type == pygame.KEYDOWN:
                    waiting = False
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        if self.game_mode == "menu" or self.start_delay > 0:
            return
        
        # ПРЯМАЯ ПРОВЕРКА КЛАВИШ - БЕЗ УСЛОВИЙ!
        # Игрок 1 (всегда можно управлять в сингл режиме)
        if self.game_mode == "single":
            if keys[pygame.K_UP]:
                self.current_pacman.next_direction = UP
            if keys[pygame.K_DOWN]:
                self.current_pacman.next_direction = DOWN
            if keys[pygame.K_LEFT]:
                self.current_pacman.next_direction = LEFT
            if keys[pygame.K_RIGHT]:
                self.current_pacman.next_direction = RIGHT
        
        # Режим двух игроков
        if self.game_mode == "two_player":
            if self.current_player == 1:
                # Игрок 1 - стрелки
                if keys[pygame.K_UP]:
                    self.current_pacman.next_direction = UP
                if keys[pygame.K_DOWN]:
                    self.current_pacman.next_direction = DOWN
                if keys[pygame.K_LEFT]:
                    self.current_pacman.next_direction = LEFT
                if keys[pygame.K_RIGHT]:
                    self.current_pacman.next_direction = RIGHT
            else:
                # Игрок 2 - WASD
                if keys[pygame.K_w]:
                    self.current_pacman.next_direction = UP
                if keys[pygame.K_s]:
                    self.current_pacman.next_direction = DOWN
                if keys[pygame.K_a]:
                    self.current_pacman.next_direction = LEFT
                if keys[pygame.K_d]:
                    self.current_pacman.next_direction = RIGHT
    
    def update(self):
        if self.game_mode not in ["single", "two_player"]:
            return
        
        if self.start_delay > 0:
            self.start_delay -= 1
            if self.start_delay == 0:
                self.start_countdown()
            return
        
        self.current_pacman.update(self.walls)
        
        for pellet in self.pellets[:]:
            dist = ((self.current_pacman.x - pellet[0])**2 + 
                   (self.current_pacman.y - pellet[1])**2)**0.5
            if dist < self.current_pacman.radius + 4:
                self.pellets.remove(pellet)
                self.current_pacman.score += 10
                if self.game_mode == "two_player":
                    if self.current_player == 1:
                        self.player1_score = self.current_pacman.score
                    else:
                        self.player2_score = self.current_pacman.score
        
        for power_pellet in self.power_pellets[:]:
            dist = ((self.current_pacman.x - power_pellet[0])**2 + 
                   (self.current_pacman.y - power_pellet[1])**2)**0.5
            if dist < self.current_pacman.radius + 12:
                self.power_pellets.remove(power_pellet)
                self.current_pacman.score += 50
                play_sound(SOUND_POWER)
                if self.game_mode == "two_player":
                    if self.current_player == 1:
                        self.player1_score = self.current_pacman.score
                    else:
                        self.player2_score = self.current_pacman.score
                self.frightened_mode_active = True
                self.frightened_timer = 300
                for ghost in self.ghosts:
                    ghost.frightened_mode = True
                    ghost.frightened_timer = 300
        
        if self.frightened_mode_active:
            self.frightened_timer -= 1
            if self.frightened_timer <= 0:
                self.frightened_mode_active = False
                for ghost in self.ghosts:
                    ghost.frightened_mode = False
        
        for ghost in self.ghosts:
            ghost.update(self.walls, self.current_pacman.x, self.current_pacman.y, self.difficulty)
            
            if self.current_pacman.invincible_timer <= 0:
                dist = ((ghost.x - self.current_pacman.x)**2 + 
                       (ghost.y - self.current_pacman.y)**2)**0.5
                if dist < ghost.radius + self.current_pacman.radius:
                    if ghost.frightened_mode:
                        ghost.reset()
                        self.current_pacman.score += 200
                        play_sound(SOUND_EAT_GHOST)
                        if self.game_mode == "two_player":
                            if self.current_player == 1:
                                self.player1_score = self.current_pacman.score
                            else:
                                self.player2_score = self.current_pacman.score
                    else:
                        self.current_pacman.lives -= 1
                        play_sound(SOUND_DEATH)
                        if self.game_mode == "two_player":
                            if self.current_player == 1:
                                self.player1_lives = self.current_pacman.lives
                            else:
                                self.player2_lives = self.current_pacman.lives
                        
                        if self.current_pacman.lives > 0:
                            self.reset_positions()
                            self.start_delay = 60
                        else:
                            if self.game_mode == "two_player":
                                if self.current_player == 1 and self.player2_lives > 0:
                                    self.current_player = 2
                                    self.current_pacman = self.player2
                                    self.reset_positions()
                                    self.start_delay = 60
                                elif self.current_player == 2 and self.player1_lives > 0:
                                    self.current_player = 1
                                    self.current_pacman = self.player1
                                    self.reset_positions()
                                    self.start_delay = 60
                                else:
                                    if self.player1_score > self.player2_score:
                                        self.winner_name = "Игрок 1 победил!"
                                        self.winner_score = self.player1_score
                                    elif self.player2_score > self.player1_score:
                                        self.winner_name = "Игрок 2 победил!"
                                        self.winner_score = self.player2_score
                                    else:
                                        self.winner_name = "Ничья!"
                                        self.winner_score = self.player1_score
                                    self.game_mode = "game_over"
                                    play_lose()
                            else:
                                self.winner_score = self.current_pacman.score
                                self.winner_name = "Ты проиграл"
                                self.game_mode = "game_over"
                                play_lose()
        
        score_to_win = self.get_score_to_win()
        if self.current_pacman.score >= score_to_win:
            if self.game_mode == "single":
                self.winner_name = "Ты победил!"
                self.winner_score = self.current_pacman.score
                self.game_mode = "win"
                play_win()
            else:
                self.winner_name = f"Игрок {self.current_player} победил!"
                self.winner_score = self.current_pacman.score
                self.game_mode = "win"
                play_win()
    
    def reset_positions(self):
        self.current_pacman.reset()
        for ghost in self.ghosts:
            ghost.reset()
    
    def draw(self):
        self.draw_game_only()
        info_y_start = 470
        info_panel = pygame.Rect(0, 450, WINDOW_WIDTH, 200)
        pygame.draw.rect(self.screen, DARK_GRAY, info_panel)
        pygame.draw.rect(self.screen, GRAY, info_panel, 3)
        score_to_win = self.get_score_to_win()
        if self.game_mode == "single":
            score_text = self.font.render(f"СЧЕТ: {self.current_pacman.score} / {score_to_win}", True, YELLOW)
            self.screen.blit(score_text, (WINDOW_WIDTH//2 - score_text.get_width()//2, info_y_start))
            hearts_x = WINDOW_WIDTH//2 - (self.current_pacman.lives * 25)//2
            self.draw_hearts(self.screen, hearts_x, info_y_start + 35, self.current_pacman.lives, 20)
        else:
            score_text = self.font.render(f"ИГРОК 1: {self.player1_score}     ИГРОК 2: {self.player2_score}", True, YELLOW)
            self.screen.blit(score_text, (WINDOW_WIDTH//2 - score_text.get_width()//2, info_y_start))
            hearts1_x = WINDOW_WIDTH//2 - 100
            self.draw_hearts(self.screen, hearts1_x, info_y_start + 35, self.player1_lives, 18)
            p1_text = self.small_font.render("Игрок 1", True, YELLOW)
            self.screen.blit(p1_text, (hearts1_x + 5, info_y_start + 60))
            hearts2_x = WINDOW_WIDTH//2 + 40
            self.draw_hearts(self.screen, hearts2_x, info_y_start + 35, self.player2_lives, 18)
            p2_text = self.small_font.render("Игрок 2", True, YELLOW)
            self.screen.blit(p2_text, (hearts2_x + 5, info_y_start + 60))
            player_text = self.font.render(f"ХОДИТ: ИГРОК {self.current_player}", True, GREEN)
            self.screen.blit(player_text, (WINDOW_WIDTH//2 - player_text.get_width()//2, info_y_start + 100))
        diff_names = {1: "ЛЕГКИЙ (800)", 2: "СРЕДНИЙ (1000)", 3: "СЛОЖНЫЙ (1200)"}
        diff_text = self.small_font.render(diff_names[self.difficulty], True, WHITE)
        self.screen.blit(diff_text, (WINDOW_WIDTH - 150, info_y_start))
        if self.frightened_mode_active:
            fear_text = self.font.render("РЕЖИМ СТРАХА!", True, PURPLE)
            self.screen.blit(fear_text, (WINDOW_WIDTH//2 - fear_text.get_width()//2, info_y_start + 140))
    
    def draw_menu(self):
        self.screen.fill(BLACK)
        title = self.big_font.render("ПАКМАН", True, YELLOW)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, 80))
        self.screen.blit(title, title_rect)
        menu_options = [
            ("1. ОДИН ИГРОК", 220),
            ("2. ДВА ИГРОКА", 270),
            ("3. ИНСТРУКЦИЯ", 320),
            ("4. СЛОЖНОСТЬ", 370),
            ("ESC - ВЫХОД", 500)
        ]
        for text, y in menu_options:
            color = WHITE
            if text.startswith("4. СЛОЖНОСТЬ"):
                diff_names = {1: "ЛЕГКИЙ (800)", 2: "СРЕДНИЙ (1000)", 3: "СЛОЖНЫЙ (1200)"}
                text = f"4. СЛОЖНОСТЬ: {diff_names[self.difficulty]}"
                if self.difficulty == 1:
                    color = GREEN
                elif self.difficulty == 2:
                    color = YELLOW
                else:
                    color = RED
            option_text = self.font.render(text, True, color)
            rect = option_text.get_rect(center=(WINDOW_WIDTH//2, y))
            self.screen.blit(option_text, rect)
        self.draw_heart(self.screen, 700, 60, 30)
        pygame.draw.circle(self.screen, YELLOW, (150, 80), 30)
        pygame.draw.arc(self.screen, BLACK, (120, 50, 60, 60), 0.2, 1.0, 4)
    
    def draw_game_over_screen(self):
        self.screen.fill(BLACK)
        is_win = (self.game_mode == "win")
        if is_win:
            title = self.big_font.render("ПОБЕДА!", True, GREEN)
            if pygame.time.get_ticks() // 100 % 2 == 0:
                for _ in range(20):
                    x = random.randint(0, WINDOW_WIDTH)
                    y = random.randint(0, WINDOW_HEIGHT // 2)
                    color = random.choice([RED, GREEN, BLUE, YELLOW, PINK])
                    pygame.draw.circle(self.screen, color, (x, y), 3)
        else:
            title = self.big_font.render("ИГРА ОКОНЧЕНА", True, RED)
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 100))
        self.screen.blit(title, title_rect)
        name_text = self.medium_font.render(self.winner_name, True, YELLOW)
        name_rect = name_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 30))
        self.screen.blit(name_text, name_rect)
        score_text = self.medium_font.render(f"СЧЕТ: {self.winner_score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 20))
        self.screen.blit(score_text, score_rect)
        esc_text = self.font.render("Нажми ESC для возврата в меню", True, GREEN)
        esc_rect = esc_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 130))
        self.screen.blit(esc_text, esc_rect)
    
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.game_mode in ["single", "two_player", "game_over", "win"]:
                            self.game_mode = "menu"
                            self.setup_game()
                        elif self.game_mode == "menu":
                            self.running = False
                    elif self.game_mode == "menu":
                        if event.key == pygame.K_1:
                            self.game_mode = "single"
                            self.current_player = 1
                            self.setup_game()
                            play_sound(SOUND_START)
                        elif event.key == pygame.K_2:
                            self.game_mode = "two_player"
                            self.current_player = 1
                            self.setup_game()
                            play_sound(SOUND_START)
                        elif event.key == pygame.K_3:
                            self.show_instructions()
                        elif event.key == pygame.K_4:
                            self.difficulty = (self.difficulty % 3) + 1
            
            if self.game_mode == "menu":
                self.draw_menu()
            elif self.game_mode in ["single", "two_player"]:
                self.handle_input()
                self.update()
                self.draw()
            elif self.game_mode in ["game_over", "win"]:
                self.draw_game_over_screen()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("ДОБРО ПОЖАЛОВАТЬ В ПАКМАН!")
    print("Управление: стрелки - игрок 1, WASD - игрок 2")
    print("ESC - выход в меню")
    game = Game()
    game.run()

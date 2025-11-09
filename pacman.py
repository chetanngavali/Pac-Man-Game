import pygame
import random
import math
import numpy as np
from enum import Enum

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 700
CELL_SIZE = 30
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
DARK_BLUE = (0, 0, 100)
NAVY = (0, 0, 128)
YELLOW = (255, 255, 0)
GOLD = (255, 215, 0)
ORANGE = (255, 165, 0)
RED = (255, 0, 0)
DARK_RED = (139, 0, 0)
PINK = (255, 182, 193)
HOT_PINK = (255, 105, 180)
CYAN = (0, 255, 255)
DARK_CYAN = (0, 139, 139)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 100, 0)
PURPLE = (128, 0, 128)
DARK_PURPLE = (75, 0, 130)
GRAY = (128, 128, 128)
DARK_GRAY = (30, 30, 30)
LIGHT_GRAY = (200, 200, 200)

# Game speeds
PACMAN_SPEED = 2.5
GHOST_SPEED = 1.5
FRIGHTENED_SPEED = 1.0

# Directions
class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    NONE = (0, 0)

# Game states
class GameState(Enum):
    LOADING = 0
    MAIN_MENU = 1
    LEVEL_SELECT = 2
    SETTINGS = 3
    PLAYING = 4
    PAUSED = 5


class SoundManager:
    """Generate and manage game sounds"""
    def __init__(self):
        self.sounds = {}
        self.music_playing = False
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        
        # Generate sounds
        self.generate_sounds()
    
    def generate_tone(self, frequency, duration, volume=0.5):
        """Generate a simple tone"""
        sample_rate = 22050
        n_samples = int(duration * sample_rate)
        
        # Generate sine wave
        t = np.linspace(0, duration, n_samples, False)
        wave = np.sin(frequency * 2 * np.pi * t)
        
        # Apply envelope (fade in/out)
        envelope = np.ones(n_samples)
        fade_samples = int(0.01 * sample_rate)  # 10ms fade
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        wave = wave * envelope * volume
        
        # Convert to 16-bit
        wave = np.int16(wave * 32767)
        
        # Stereo
        stereo_wave = np.column_stack((wave, wave))
        
        return pygame.sndarray.make_sound(stereo_wave)
    
    def generate_sounds(self):
        """Generate all game sound effects"""
        try:
            # Eating pellet sound (short beep)
            self.sounds['eat'] = self.generate_tone(880, 0.05, 0.3)
            
            # Power pellet sound (lower, longer)
            self.sounds['power'] = self.generate_tone(440, 0.2, 0.4)
            
            # Eating ghost sound (ascending tones)
            self.sounds['eat_ghost'] = self.generate_tone(660, 0.15, 0.5)
            
            # Death sound (descending)
            self.sounds['death'] = self.generate_tone(220, 0.3, 0.6)
            
            # Level complete sound (ascending arpeggio)
            self.sounds['win'] = self.generate_tone(1000, 0.4, 0.5)
            
            # Menu click sound
            self.sounds['click'] = self.generate_tone(600, 0.05, 0.3)
            
            print("✓ Sound effects generated successfully!")
        except Exception as e:
            print(f"⚠ Warning: Could not generate sounds - {e}")
            # Create dummy sounds
            for key in ['eat', 'power', 'eat_ghost', 'death', 'win', 'click']:
                self.sounds[key] = None
    
    def play_sound(self, sound_name):
        """Play a sound effect"""
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.sounds[sound_name].set_volume(self.sfx_volume)
                self.sounds[sound_name].play()
            except:
                pass
    
    def start_background_music(self):
        """Start simple background music loop"""
        if not self.music_playing:
            try:
                # Generate simple background music (just a loop for now)
                music = self.generate_tone(440, 2.0, 0.2)
                music.set_volume(self.music_volume)
                music.play(loops=-1)  # Loop forever
                self.music_playing = True
                print("✓ Background music started")
            except Exception as e:
                print(f"⚠ Warning: Could not start music - {e}")
    
    def stop_background_music(self):
        """Stop background music"""
        try:
            pygame.mixer.stop()
            self.music_playing = False
        except:
            pass
    
    def set_music_volume(self, volume):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        try:
            pygame.mixer.music.set_volume(self.music_volume)
        except:
            pass
    
    def set_sfx_volume(self, volume):
        """Set SFX volume (0.0 to 1.0)"""
        self.sfx_volume = max(0.0, min(1.0, volume))


class Particle:
    """Particle effects system"""
    def __init__(self, x, y, color, velocity, lifetime=30):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.velocity = list(velocity)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 5)
        
    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.velocity[0] *= 0.95
        self.velocity[1] += 0.2
        self.lifetime -= 1
        
    def is_alive(self):
        return self.lifetime > 0
        
    def draw(self, screen):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            size = max(1, int(self.size * (self.lifetime / self.max_lifetime)))
            
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (size, size), size)
            screen.blit(surf, (int(self.x - size), int(self.y - size)))


class SpriteRenderer:
    """Centralized sprite rendering system"""
    
    @staticmethod
    def draw_pacman(surface, size, mouth_angle, direction):
        """Draw Pac-Man sprite"""
        center = size // 2
        
        for radius in range(center, 0, -1):
            intensity = int(255 * (radius / center))
            color = (intensity, intensity, 0)
            pygame.draw.circle(surface, color, (center, center), radius)
        
        if mouth_angle > 5:
            mouth_points = [(center, center)]
            
            if direction == Direction.RIGHT:
                start_angle = math.radians(mouth_angle)
                end_angle = math.radians(360 - mouth_angle)
            elif direction == Direction.LEFT:
                start_angle = math.radians(180 - mouth_angle)
                end_angle = math.radians(180 + mouth_angle)
            elif direction == Direction.UP:
                start_angle = math.radians(270 - mouth_angle)
                end_angle = math.radians(270 + mouth_angle)
            elif direction == Direction.DOWN:
                start_angle = math.radians(90 - mouth_angle)
                end_angle = math.radians(90 + mouth_angle)
            else:
                start_angle = math.radians(mouth_angle)
                end_angle = math.radians(360 - mouth_angle)
            
            p1 = (center + int(center * math.cos(start_angle)), 
                  center + int(center * math.sin(start_angle)))
            p2 = (center + int(center * math.cos(end_angle)), 
                  center + int(center * math.sin(end_angle)))
            
            mouth_points.extend([p1, p2])
            pygame.draw.polygon(surface, BLACK, mouth_points)
        
        eye_x = center + (center // 3 if direction != Direction.LEFT else -center // 3)
        eye_y = center - center // 4
        pygame.draw.circle(surface, BLACK, (eye_x, eye_y), max(2, center // 6))
    
    @staticmethod
    def draw_ghost(surface, size, color, frightened=False, blink=False):
        """Draw ghost sprite"""
        center = size // 2
        
        if frightened:
            ghost_color = WHITE if blink else BLUE
        else:
            ghost_color = color
        
        pygame.draw.circle(surface, ghost_color, (center, center - 2), center - 2)
        pygame.draw.rect(surface, ghost_color, (2, center - 2, size - 4, center))
        
        wave_points = [(2, center + center // 2)]
        for i in range(5):
            x = 2 + i * (size - 4) // 4
            y = size - 2 if i % 2 == 0 else size - 8
            wave_points.append((x, y))
        wave_points.append((size - 2, center + center // 2))
        pygame.draw.polygon(surface, ghost_color, wave_points)
        
        if not frightened:
            eye_size = center // 3
            pygame.draw.circle(surface, WHITE, (center - center // 3, center - center // 4), eye_size)
            pygame.draw.circle(surface, WHITE, (center + center // 3, center - center // 4), eye_size)
            
            pupil_size = eye_size // 2
            pygame.draw.circle(surface, BLACK, (center - center // 3 + 2, center - center // 4), pupil_size)
            pygame.draw.circle(surface, BLACK, (center + center // 3 + 2, center - center // 4), pupil_size)
        else:
            pygame.draw.line(surface, (255, 200, 200), 
                           (center - 8, center - 5), (center - 4, center - 2), 2)
            pygame.draw.line(surface, (255, 200, 200), 
                           (center + 4, center - 5), (center + 8, center - 2), 2)
    
    @staticmethod
    def draw_power_pellet(surface, size, pulse_factor):
        """Draw animated power pellet"""
        center = size // 2
        radius = int((center - 2) * pulse_factor)
        
        for r in range(radius + 10, radius, -1):
            alpha = int(80 * ((r - radius) / 10))
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 100, alpha), (center, center), r)
            surface.blit(surf, (0, 0))
        
        pygame.draw.circle(surface, WHITE, (center, center), radius)
        pygame.draw.circle(surface, YELLOW, (center, center), max(2, radius - 2))


class PacMan:
    """Pac-Man character with graphics"""
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.start_x = float(x)
        self.start_y = float(y)
        self.direction = Direction.RIGHT
        self.next_direction = Direction.NONE
        self.speed = PACMAN_SPEED
        self.radius = CELL_SIZE // 2 - 5
        
        self.mouth_angle = 0
        self.mouth_open = True
        self.animation_frame = 0
        
        self.particles = []
        
        self.size = CELL_SIZE - 4
        self.sprite = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
    
    def update(self, maze):
        self.animation_frame += 1
        if self.animation_frame % 5 == 0:
            if self.mouth_open:
                self.mouth_angle = min(45, self.mouth_angle + 5)
                if self.mouth_angle >= 45:
                    self.mouth_open = False
            else:
                self.mouth_angle = max(0, self.mouth_angle - 5)
                if self.mouth_angle <= 0:
                    self.mouth_open = True
        
        if self.next_direction != Direction.NONE:
            new_x = self.x + self.next_direction.value[0] * self.speed
            new_y = self.y + self.next_direction.value[1] * self.speed
            if not self.check_collision(new_x, new_y, maze):
                self.direction = self.next_direction
        
        if self.direction != Direction.NONE:
            new_x = self.x + self.direction.value[0] * self.speed
            new_y = self.y + self.direction.value[1] * self.speed
            if not self.check_collision(new_x, new_y, maze):
                if self.animation_frame % 4 == 0:
                    vel = (-self.direction.value[0] * random.uniform(0.5, 1.5),
                          -self.direction.value[1] * random.uniform(0.5, 1.5))
                    self.particles.append(Particle(self.x, self.y, YELLOW, vel, 15))
                
                self.x = new_x
                self.y = new_y
        
        if self.x < 0:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = 0
        
        for particle in self.particles:
            particle.update()
        self.particles = [p for p in self.particles if p.is_alive()]
        
        self.sprite.fill((0, 0, 0, 0))
        SpriteRenderer.draw_pacman(self.sprite, self.size, self.mouth_angle, self.direction)
    
    def check_collision(self, x, y, maze):
        margin = 4
        corners = [
            (x - self.radius + margin, y - self.radius + margin),
            (x + self.radius - margin, y - self.radius + margin),
            (x - self.radius + margin, y + self.radius - margin),
            (x + self.radius - margin, y + self.radius - margin),
        ]
        
        for cx, cy in corners:
            mx = int(cx // CELL_SIZE)
            my = int(cy // CELL_SIZE)
            if 0 <= my < len(maze) and 0 <= mx < len(maze[0]):
                if maze[my][mx] == 1:
                    return True
        return False
    
    def create_eat_effect(self):
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            vel = (math.cos(angle) * speed, math.sin(angle) * speed)
            color = random.choice([WHITE, YELLOW, GOLD])
            self.particles.append(Particle(self.x, self.y, color, vel, 20))
    
    def reset_position(self):
        self.x = self.start_x
        self.y = self.start_y
        self.direction = Direction.NONE
        self.particles = []
    
    def draw(self, screen):
        for particle in self.particles:
            particle.draw(screen)
        
        sprite_x = int(self.x - self.size // 2)
        sprite_y = int(self.y - self.size // 2)
        screen.blit(self.sprite, (sprite_x, sprite_y))


class Ghost:
    """Ghost character with graphics"""
    def __init__(self, x, y, color, name):
        self.x = float(x)
        self.y = float(y)
        self.start_x = float(x)
        self.start_y = float(y)
        self.color = color
        self.name = name
        self.direction = Direction.RIGHT
        self.speed = GHOST_SPEED
        self.radius = CELL_SIZE // 2 - 2
        
        self.frightened = False
        self.frightened_timer = 0
        self.blink = False
        
        self.animation_frame = 0
        
        self.size = CELL_SIZE - 4
        self.sprite = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.update_sprite()
    
    def update(self, maze, pacman):
        self.animation_frame += 1
        
        if self.frightened:
            self.frightened_timer -= 1
            self.blink = self.frightened_timer < 120 and (self.frightened_timer // 10) % 2 == 0
            
            if self.frightened_timer <= 0:
                self.frightened = False
                self.speed = GHOST_SPEED
        
        if not self.frightened:
            self.chase_pacman(maze, pacman)
        else:
            self.flee_from_pacman(maze, pacman)
        
        new_x = self.x + self.direction.value[0] * self.speed
        new_y = self.y + self.direction.value[1] * self.speed
        
        if not self.check_collision(new_x, new_y, maze):
            self.x = new_x
            self.y = new_y
        else:
            self.choose_random_direction(maze)
        
        if self.x < 0:
            self.x = SCREEN_WIDTH
        elif self.x > SCREEN_WIDTH:
            self.x = 0
        
        if self.animation_frame % 10 == 0:
            self.update_sprite()
    
    def update_sprite(self):
        self.sprite.fill((0, 0, 0, 0))
        SpriteRenderer.draw_ghost(self.sprite, self.size, self.color, 
                                  self.frightened, self.blink)
    
    def chase_pacman(self, maze, pacman):
        dx = pacman.x - self.x
        dy = pacman.y - self.y
        
        if abs(dx) > abs(dy):
            new_dir = Direction.RIGHT if dx > 0 else Direction.LEFT
        else:
            new_dir = Direction.DOWN if dy > 0 else Direction.UP
        
        test_x = self.x + new_dir.value[0] * self.speed * 5
        test_y = self.y + new_dir.value[1] * self.speed * 5
        
        if not self.check_collision(test_x, test_y, maze):
            self.direction = new_dir
    
    def flee_from_pacman(self, maze, pacman):
        dx = self.x - pacman.x
        dy = self.y - pacman.y
        
        if abs(dx) > abs(dy):
            new_dir = Direction.RIGHT if dx > 0 else Direction.LEFT
        else:
            new_dir = Direction.DOWN if dy > 0 else Direction.UP
        
        test_x = self.x + new_dir.value[0] * self.speed * 5
        test_y = self.y + new_dir.value[1] * self.speed * 5
        
        if not self.check_collision(test_x, test_y, maze):
            self.direction = new_dir
    
    def choose_random_direction(self, maze):
        directions = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
        random.shuffle(directions)
        
        for direction in directions:
            test_x = self.x + direction.value[0] * self.speed * 5
            test_y = self.y + direction.value[1] * self.speed * 5
            if not self.check_collision(test_x, test_y, maze):
                self.direction = direction
                break
    
    def check_collision(self, x, y, maze):
        mx = int(x // CELL_SIZE)
        my = int(y // CELL_SIZE)
        
        if 0 <= my < len(maze) and 0 <= mx < len(maze[0]):
            return maze[my][mx] == 1
        return True
    
    def set_frightened(self, duration):
        self.frightened = True
        self.frightened_timer = duration
        self.speed = FRIGHTENED_SPEED
        self.update_sprite()
    
    def reset_position(self):
        self.x = self.start_x
        self.y = self.start_y
        self.frightened = False
        self.update_sprite()
    
    def draw(self, screen):
        sprite_x = int(self.x - self.size // 2)
        sprite_y = int(self.y - self.size // 2)
        screen.blit(self.sprite, (sprite_x, sprite_y))


class Button:
    """Button with hover effects"""
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.pulse = 0
    
    def draw(self, screen, font):
        self.pulse = (self.pulse + 1) % 60
        
        color = self.hover_color if self.is_hovered else self.color
        offset = int(2 * math.sin(self.pulse / 10)) if self.is_hovered else 0
        
        rect = pygame.Rect(self.rect.x, self.rect.y + offset, 
                          self.rect.width, self.rect.height)
        pygame.draw.rect(screen, color, rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, rect, 2, border_radius=10)
        
        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
    
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click


class Slider:
    """Volume slider - FIXED VERSION"""
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.dragging = False
        self.handle_radius = 12
        self.handle_x = self.value_to_x(initial_val)
    
    def value_to_x(self, value):
        ratio = (value - self.min_val) / (self.max_val - self.min_val)
        return self.rect.x + int(ratio * self.rect.width)
    
    def x_to_value(self, x):
        x = max(self.rect.x, min(x, self.rect.x + self.rect.width))
        ratio = (x - self.rect.x) / self.rect.width
        return self.min_val + ratio * (self.max_val - self.min_val)
    
    def draw(self, screen):
        # Track background
        pygame.draw.rect(screen, DARK_GRAY, self.rect, border_radius=5)
        
        # Filled portion (green)
        filled_width = int(self.handle_x - self.rect.x)
        if filled_width > 0:
            filled = pygame.Rect(self.rect.x, self.rect.y, filled_width, self.rect.height)
            pygame.draw.rect(screen, GREEN, filled, border_radius=5)
        
        # Border
        pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=5)
        
        # Handle (yellow circle)
        pygame.draw.circle(screen, YELLOW, (int(self.handle_x), self.rect.centery), 
                          self.handle_radius)
        pygame.draw.circle(screen, WHITE, (int(self.handle_x), self.rect.centery), 
                          self.handle_radius, 2)
    
    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            dist = math.sqrt((mouse_pos[0] - self.handle_x)**2 + 
                           (mouse_pos[1] - self.rect.centery)**2)
            if dist <= self.handle_radius + 5:  # Slightly larger hit area
                self.dragging = True
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.handle_x = max(self.rect.x, min(mouse_pos[0], self.rect.x + self.rect.width))
            self.value = self.x_to_value(self.handle_x)
            return True
        return False


# Level data
LEVELS = [
    {
        "name": "Level 1 - Easy",
        "difficulty": "Easy",
        "ghost_count": 2,
        "speed_multiplier": 1.0,
        "maze": [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 3, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 2, 1, 1, 3, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 1, 2, 2, 2, 1, 1, 2, 2, 2, 1, 2, 2, 2, 2, 1],
            [1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 2, 1, 2, 1, 1, 0, 0, 1, 1, 2, 1, 2, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 1, 0, 0, 0, 0, 1, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1],
            [1, 2, 2, 2, 2, 1, 2, 2, 2, 1, 1, 2, 2, 2, 1, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1],
            [1, 3, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 3, 1],
            [1, 1, 2, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 2, 1, 1],
            [1, 2, 2, 2, 2, 1, 2, 2, 2, 1, 1, 2, 2, 2, 1, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]
    },
    {
        "name": "Level 2 - Medium",
        "difficulty": "Medium",
        "ghost_count": 3,
        "speed_multiplier": 1.3,
        "maze": [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 1],
            [1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1],
            [1, 2, 1, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 1],
            [1, 2, 1, 2, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 1, 2, 1],
            [1, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 1],
            [1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1],
            [1, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 1],
            [1, 2, 1, 2, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 2, 1, 2, 1],
            [1, 2, 1, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 1],
            [1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1],
            [1, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 1],
            [1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]
    },
    {
        "name": "Level 3 - Hard",
        "difficulty": "Hard",
        "ghost_count": 4,
        "speed_multiplier": 1.6,
        "maze": [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 3, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 3, 1],
            [1, 2, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 2, 1],
            [1, 2, 1, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 1],
            [1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1],
            [1, 2, 2, 2, 1, 2, 2, 2, 2, 0, 0, 2, 2, 2, 2, 1, 2, 2, 2, 1],
            [1, 2, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 2, 1],
            [1, 2, 1, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 1, 2, 1],
            [1, 2, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1],
            [1, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]
    }
]


class Game:
    """Main game class with sound"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pac-Man - Complete Edition with Sound")
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.title_font = pygame.font.Font(None, 72)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.tiny_font = pygame.font.Font(None, 18)
        
        # State
        self.state = GameState.LOADING
        self.selected_level = 0
        self.score = 0
        self.high_score = 0
        self.lives = 3
        self.game_over = False
        self.win = False
        
        # Sound Manager
        self.sound_manager = SoundManager()
        
        # Loading
        self.loading_progress = 0
        
        # Sprites
        self.wall_sprite = self.create_wall_sprite()
        self.pellet_sprite = self.create_pellet_sprite()
        
        # Background particles
        self.bg_particles = []
        for _ in range(30):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            vel = (random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3))
            color = random.choice([BLUE, CYAN, PURPLE])
            self.bg_particles.append(Particle(x, y, color, vel, 100))
        
        self.setup_buttons()
        self.setup_sliders()
    
    def create_wall_sprite(self):
        surf = pygame.Surface((CELL_SIZE, CELL_SIZE))
        surf.fill(DARK_BLUE)
        pygame.draw.rect(surf, BLUE, (0, 0, CELL_SIZE, CELL_SIZE), 2)
        pygame.draw.line(surf, NAVY, (2, 2), (CELL_SIZE-2, 2), 1)
        return surf
    
    def create_pellet_sprite(self):
        surf = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(surf, WHITE, (4, 4), 2)
        return surf
    
    def setup_buttons(self):
        cx = SCREEN_WIDTH // 2
        
        self.play_button = Button(cx - 100, 250, 200, 50, "PLAY", BLUE, CYAN)
        self.level_select_button = Button(cx - 100, 320, 200, 50, "SELECT LEVEL", BLUE, CYAN)
        self.settings_button = Button(cx - 100, 390, 200, 50, "SETTINGS", BLUE, CYAN)
        self.quit_button = Button(cx - 100, 460, 200, 50, "QUIT", RED, ORANGE)
        
        self.level_buttons = []
        for i in range(len(LEVELS)):
            btn = Button(cx - 150, 200 + i * 80, 300, 60, 
                        LEVELS[i]["name"], GREEN, CYAN)
            self.level_buttons.append(btn)
        
        self.back_button = Button(cx - 100, 580, 200, 50, "BACK", ORANGE, RED)
        
        self.resume_button = Button(cx - 100, 250, 200, 50, "RESUME", GREEN, CYAN)
        self.restart_button = Button(cx - 100, 320, 200, 50, "RESTART", ORANGE, YELLOW)
        self.menu_button = Button(cx - 100, 390, 200, 50, "MAIN MENU", BLUE, CYAN)
    
    def setup_sliders(self):
        # Create sliders with proper positioning - FIXED
        slider_width = 250
        slider_height = 15
        slider_x = (SCREEN_WIDTH - slider_width) // 2
        
        self.music_slider = Slider(slider_x, 250, slider_width, slider_height, 
                                   0, 1, self.sound_manager.music_volume, "Music")
        self.sfx_slider = Slider(slider_x, 370, slider_width, slider_height, 
                                0, 1, self.sound_manager.sfx_volume, "SFX")
    
    def load_game(self):
        for i in range(101):
            self.loading_progress = i
            self.draw_loading_screen()
            pygame.time.delay(8)
        pygame.time.delay(200)
        
        # Start background music
        self.sound_manager.start_background_music()
        
        self.state = GameState.MAIN_MENU
    
    def draw_loading_screen(self):
        self.screen.fill(BLACK)
        
        # Title
        for offset in [(3, 3), (-3, 3), (3, -3), (-3, -3)]:
            glow = self.title_font.render("PAC-MAN", True, ORANGE)
            rect = glow.get_rect(center=(SCREEN_WIDTH // 2 + offset[0], 150 + offset[1]))
            self.screen.blit(glow, rect)
        
        title = self.title_font.render("PAC-MAN", True, YELLOW)
        rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, rect)
        
        # Loading bar
        bar_w, bar_h = 400, 30
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = 400
        
        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=15)
        
        progress_w = int((self.loading_progress / 100) * (bar_w - 4))
        if progress_w > 0:
            pygame.draw.rect(self.screen, GREEN, (bar_x + 2, bar_y + 2, progress_w, bar_h - 4), 
                           border_radius=13)
        
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=15)
        
        text = self.font.render(f"Loading... {self.loading_progress}%", True, WHITE)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, 470))
        self.screen.blit(text, text_rect)
        
        # Loading sound systems
        if self.loading_progress > 50:
            sound_text = self.small_font.render("Generating sound effects...", True, CYAN)
            sound_rect = sound_text.get_rect(center=(SCREEN_WIDTH // 2, 550))
            self.screen.blit(sound_text, sound_rect)
        
        pygame.display.flip()
    
    def draw_main_menu(self):
        self.screen.fill(BLACK)
        
        for p in self.bg_particles:
            p.update()
            if p.x < 0 or p.x > SCREEN_WIDTH:
                p.velocity[0] *= -1
            if p.y < 0 or p.y > SCREEN_HEIGHT:
                p.velocity[1] *= -1
            p.draw(self.screen)
        
        for offset in [(4, 4), (-4, 4), (4, -4), (-4, -4)]:
            glow = self.title_font.render("PAC-MAN", True, ORANGE)
            rect = glow.get_rect(center=(SCREEN_WIDTH // 2 + offset[0], 120 + offset[1]))
            self.screen.blit(glow, rect)
        
        title = self.title_font.render("PAC-MAN", True, YELLOW)
        rect = title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.screen.blit(title, rect)
        
        subtitle = self.small_font.render("With Sound Effects", True, CYAN)
        rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 180))
        self.screen.blit(subtitle, rect)
        
        mouse_pos = pygame.mouse.get_pos()
        for btn in [self.play_button, self.level_select_button, 
                   self.settings_button, self.quit_button]:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen, self.font if btn != self.level_select_button else self.small_font)
        
        if self.high_score > 0:
            text = self.small_font.render(f"High Score: {self.high_score}", True, GOLD)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, 600))
            self.screen.blit(text, rect)
        
        pygame.display.flip()
    
    def draw_level_select(self):
        self.screen.fill(BLACK)
        
        title = self.title_font.render("SELECT LEVEL", True, YELLOW)
        rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, rect)
        
        mouse_pos = pygame.mouse.get_pos()
        for i, btn in enumerate(self.level_buttons):
            btn.check_hover(mouse_pos)
            btn.draw(self.screen, self.font)
            
            diff = self.small_font.render(f"Difficulty: {LEVELS[i]['difficulty']}", True, WHITE)
            ghosts = self.small_font.render(f"Ghosts: {LEVELS[i]['ghost_count']}", True, LIGHT_GRAY)
            self.screen.blit(diff, (SCREEN_WIDTH // 2 - 110, btn.rect.y + 70))
            self.screen.blit(ghosts, (SCREEN_WIDTH // 2 + 30, btn.rect.y + 70))
        
        self.back_button.check_hover(mouse_pos)
        self.back_button.draw(self.screen, self.font)
        
        pygame.display.flip()
    
    def draw_settings(self):
        """FIXED SETTINGS PAGE"""
        self.screen.fill(BLACK)
        
        # Title
        title = self.title_font.render("SETTINGS", True, YELLOW)
        rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, rect)
        
        # Music Volume Section
        music_label = self.font.render("Music Volume", True, WHITE)
        music_rect = music_label.get_rect(center=(SCREEN_WIDTH // 2, 210))
        self.screen.blit(music_label, music_rect)
        
        # Music slider
        self.music_slider.draw(self.screen)
        
        # Music percentage
        music_pct = self.small_font.render(f"{int(self.sound_manager.music_volume * 100)}%", True, CYAN)
        music_pct_rect = music_pct.get_rect(center=(SCREEN_WIDTH // 2, 285))
        self.screen.blit(music_pct, music_pct_rect)
        
        # SFX Volume Section
        sfx_label = self.font.render("SFX Volume", True, WHITE)
        sfx_rect = sfx_label.get_rect(center=(SCREEN_WIDTH // 2, 330))
        self.screen.blit(sfx_label, sfx_rect)
        
        # SFX slider
        self.sfx_slider.draw(self.screen)
        
        # SFX percentage
        sfx_pct = self.small_font.render(f"{int(self.sound_manager.sfx_volume * 100)}%", True, CYAN)
        sfx_pct_rect = sfx_pct.get_rect(center=(SCREEN_WIDTH // 2, 405))
        self.screen.blit(sfx_pct, sfx_pct_rect)
        
        # Controls Section
        controls_label = self.font.render("Controls", True, YELLOW)
        controls_rect = controls_label.get_rect(center=(SCREEN_WIDTH // 2, 460))
        self.screen.blit(controls_label, controls_rect)
        
        controls = [
            "Arrow Keys / WASD - Move",
            "ESC - Pause",
            "R - Restart"
        ]
        
        y = 500
        for ctrl in controls:
            text = self.small_font.render(ctrl, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self.screen.blit(text, text_rect)
            y += 30
        
        # Back button
        mouse_pos = pygame.mouse.get_pos()
        self.back_button.check_hover(mouse_pos)
        self.back_button.draw(self.screen, self.font)
        
        pygame.display.flip()
    
    def setup_level(self, level_idx):
        self.selected_level = level_idx
        level = LEVELS[level_idx]
        
        self.maze = [row[:] for row in level["maze"]]
        
        spawn_x, spawn_y = self.find_spawn()
        self.pacman = PacMan(spawn_x, spawn_y)
        
        colors = [(RED, "Blinky"), (PINK, "Pinky"), (CYAN, "Inky"), (ORANGE, "Clyde")]
        self.ghosts = []
        for i in range(level["ghost_count"]):
            color, name = colors[i]
            ghost = Ghost(CELL_SIZE * (9 + i), CELL_SIZE * 9, color, name)
            ghost.speed = GHOST_SPEED * level["speed_multiplier"]
            self.ghosts.append(ghost)
        
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.win = False
        self.pellets_remaining = sum(row.count(2) + row.count(3) for row in self.maze)
        self.pellets_total = self.pellets_remaining
        self.power_pulse = 0
        
        self.state = GameState.PLAYING
    
    def find_spawn(self):
        for y in range(len(self.maze) // 2, len(self.maze)):
            for x in range(len(self.maze[0])):
                if self.maze[y][x] in [0, 2, 3]:
                    return (x * CELL_SIZE + CELL_SIZE // 2, y * CELL_SIZE + CELL_SIZE // 2)
        return (300.0, 450.0)
    
    def handle_input(self, event):
        if self.state in [GameState.MAIN_MENU, GameState.LEVEL_SELECT, GameState.SETTINGS]:
            return self.handle_menu_input(event)
        elif self.state == GameState.PLAYING:
            self.handle_game_input(event)
        elif self.state == GameState.PAUSED:
            self.handle_pause_input(event)
        return True
    
    def handle_menu_input(self, event):
        mouse_pos = pygame.mouse.get_pos()
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == GameState.MAIN_MENU:
                if self.play_button.is_clicked(mouse_pos, True):
                    self.sound_manager.play_sound('click')
                    self.setup_level(0)
                elif self.level_select_button.is_clicked(mouse_pos, True):
                    self.sound_manager.play_sound('click')
                    self.state = GameState.LEVEL_SELECT
                elif self.settings_button.is_clicked(mouse_pos, True):
                    self.sound_manager.play_sound('click')
                    self.state = GameState.SETTINGS
                elif self.quit_button.is_clicked(mouse_pos, True):
                    return False
            elif self.state == GameState.LEVEL_SELECT:
                for i, btn in enumerate(self.level_buttons):
                    if btn.is_clicked(mouse_pos, True):
                        self.sound_manager.play_sound('click')
                        self.setup_level(i)
                        break
                if self.back_button.is_clicked(mouse_pos, True):
                    self.sound_manager.play_sound('click')
                    self.state = GameState.MAIN_MENU
            elif self.state == GameState.SETTINGS:
                if self.back_button.is_clicked(mouse_pos, True):
                    self.sound_manager.play_sound('click')
                    self.state = GameState.MAIN_MENU
        
        # Handle sliders in settings
        if self.state == GameState.SETTINGS:
            if self.music_slider.handle_event(event, mouse_pos):
                self.sound_manager.set_music_volume(self.music_slider.value)
            if self.sfx_slider.handle_event(event, mouse_pos):
                self.sound_manager.set_sfx_volume(self.sfx_slider.value)
        
        return True
    
    def handle_game_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.game_over or self.win:
                if event.key == pygame.K_r:
                    self.setup_level(self.selected_level)
                elif event.key == pygame.K_ESCAPE:
                    self.state = GameState.MAIN_MENU
                elif self.win and event.key == pygame.K_RETURN:
                    next_idx = (self.selected_level + 1) % len(LEVELS)
                    self.setup_level(next_idx)
            else:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.PAUSED
                elif event.key in [pygame.K_UP, pygame.K_w]:
                    self.pacman.next_direction = Direction.UP
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    self.pacman.next_direction = Direction.DOWN
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    self.pacman.next_direction = Direction.LEFT
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    self.pacman.next_direction = Direction.RIGHT
    
    def handle_pause_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.resume_button.is_clicked(mouse_pos, True):
                self.sound_manager.play_sound('click')
                self.state = GameState.PLAYING
            elif self.restart_button.is_clicked(mouse_pos, True):
                self.sound_manager.play_sound('click')
                self.setup_level(self.selected_level)
            elif self.menu_button.is_clicked(mouse_pos, True):
                self.sound_manager.play_sound('click')
                self.state = GameState.MAIN_MENU
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
    
    def update_game(self):
        if self.game_over or self.win:
            return
        
        self.pacman.update(self.maze)
        
        mx = int(self.pacman.x // CELL_SIZE)
        my = int(self.pacman.y // CELL_SIZE)
        
        if 0 <= my < len(self.maze) and 0 <= mx < len(self.maze[0]):
            if self.maze[my][mx] == 2:
                self.maze[my][mx] = 0
                self.score += 10
                self.pellets_remaining -= 1
                self.pacman.create_eat_effect()
                self.sound_manager.play_sound('eat')
            elif self.maze[my][mx] == 3:
                self.maze[my][mx] = 0
                self.score += 50
                self.pellets_remaining -= 1
                self.pacman.create_eat_effect()
                self.sound_manager.play_sound('power')
                for ghost in self.ghosts:
                    ghost.set_frightened(300)
        
        if self.pellets_remaining == 0:
            self.win = True
            self.sound_manager.play_sound('win')
            if self.score > self.high_score:
                self.high_score = self.score
        
        for ghost in self.ghosts:
            ghost.update(self.maze, self.pacman)
            
            dist = math.sqrt((self.pacman.x - ghost.x)**2 + (self.pacman.y - ghost.y)**2)
            if dist < CELL_SIZE * 0.7:
                if ghost.frightened:
                    self.score += 200
                    self.sound_manager.play_sound('eat_ghost')
                    ghost.reset_position()
                    for _ in range(15):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(2, 4)
                        vel = (math.cos(angle) * speed, math.sin(angle) * speed)
                        self.pacman.particles.append(Particle(ghost.x, ghost.y, BLUE, vel, 25))
                else:
                    self.lives -= 1
                    self.sound_manager.play_sound('death')
                    if self.lives <= 0:
                        self.game_over = True
                        if self.score > self.high_score:
                            self.high_score = self.score
                    else:
                        self.pacman.reset_position()
                        for g in self.ghosts:
                            g.reset_position()
    
    def draw_game(self):
        self.screen.fill(BLACK)
        
        self.power_pulse = (self.power_pulse + 1) % 60
        pulse = 0.8 + 0.2 * abs(math.sin(self.power_pulse / 10))
        
        for y, row in enumerate(self.maze):
            for x, cell in enumerate(row):
                cx, cy = x * CELL_SIZE, y * CELL_SIZE
                
                if cell == 1:
                    self.screen.blit(self.wall_sprite, (cx, cy))
                elif cell == 2:
                    px = cx + CELL_SIZE // 2 - 4
                    py = cy + CELL_SIZE // 2 - 4
                    self.screen.blit(self.pellet_sprite, (px, py))
                elif cell == 3:
                    surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    SpriteRenderer.draw_power_pellet(surf, CELL_SIZE, pulse)
                    self.screen.blit(surf, (cx, cy))
        
        for ghost in self.ghosts:
            ghost.draw(self.screen)
        self.pacman.draw(self.screen)
        
        ui_y = SCREEN_HEIGHT - 95
        
        score = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score, (10, ui_y))
        
        level = self.font.render(f"Level: {self.selected_level + 1}", True, WHITE)
        self.screen.blit(level, (SCREEN_WIDTH // 2 - 60, ui_y))
        
        # Progress indicator
        if hasattr(self, "pellets_total") and self.pellets_total > 0:
            progress_pct = int(100 * (self.pellets_total - self.pellets_remaining) / max(1, self.pellets_total))
            progress_text = self.font.render(f"Progress: {progress_pct}%", True, WHITE)
            self.screen.blit(progress_text, (SCREEN_WIDTH // 2 - 60, ui_y + 30))
        
        lives = self.font.render("Lives:", True, WHITE)
        self.screen.blit(lives, (SCREEN_WIDTH - 180, ui_y))
        for i in range(self.lives):
            surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            SpriteRenderer.draw_pacman(surf, 20, 30, Direction.RIGHT)
            self.screen.blit(surf, (SCREEN_WIDTH - 90 + i * 28, ui_y + 5))
        
        if self.game_over or self.win:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            text = self.title_font.render("GAME OVER!" if self.game_over else "YOU WIN!", 
                                         True, RED if self.game_over else GREEN)
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, 250))
            self.screen.blit(text, rect)
            
            score = self.font.render(f"Final Score: {self.score}", True, WHITE)
            rect = score.get_rect(center=(SCREEN_WIDTH // 2, 330))
            self.screen.blit(score, rect)
            
            hint1 = self.small_font.render("Press R to Restart", True, CYAN)
            hint2 = self.small_font.render("Press ESC for Menu", True, CYAN)
            self.screen.blit(hint1, (SCREEN_WIDTH // 2 - 100, 400))
            self.screen.blit(hint2, (SCREEN_WIDTH // 2 - 110, 440))
            
            if self.win:
                hint3 = self.small_font.render("Press Enter for Next Level", True, CYAN)
                self.screen.blit(hint3, (SCREEN_WIDTH // 2 - 130, 480))
        
        pygame.display.flip()
    
    def draw_pause_menu(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        title = self.title_font.render("PAUSED", True, YELLOW)
        rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.screen.blit(title, rect)
        
        mouse_pos = pygame.mouse.get_pos()
        for btn in [self.resume_button, self.restart_button, self.menu_button]:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen, self.font)
        
        pygame.display.flip()
    
    def run(self):
        running = True
        
        if self.state == GameState.LOADING:
            self.load_game()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    running = self.handle_input(event)
            
            if self.state == GameState.MAIN_MENU:
                self.draw_main_menu()
            elif self.state == GameState.LEVEL_SELECT:
                self.draw_level_select()
            elif self.state == GameState.SETTINGS:
                self.draw_settings()
            elif self.state == GameState.PLAYING:
                self.update_game()
                self.draw_game()
            elif self.state == GameState.PAUSED:
                self.draw_pause_menu()
            
            self.clock.tick(FPS)
        
        pygame.quit()


if __name__ == "__main__":
    print("🎮 Starting Pac-Man with Sound Effects...")
    print("📢 Make sure your volume is on!")
    game = Game()
    game.run()

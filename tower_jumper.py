import pygame
import random
import math
import sys
import os
from enum import Enum

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.5
JUMP_FORCE = -12
PLAYER_SPEED = 5
PLATFORM_SPEED = 2
SCROLL_THRESHOLD = 200
PLATFORM_GAP_MIN = 60
PLATFORM_GAP_MAX = 120
QUAKE_INTERVAL_MIN = 10  # seconds
QUAKE_INTERVAL_MAX = 15  # seconds
QUAKE_DURATION = 2  # seconds
WIND_FORCE = 1.5
WIND_DURATION = 5  # seconds
WIND_INTERVAL_MIN = 8  # seconds
WIND_INTERVAL_MAX = 20  # seconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
PLATFORM_COLOR = (100, 200, 100)
BREAKING_PLATFORM_COLOR = (200, 100, 100)
BOUNCE_PLATFORM_COLOR = (100, 100, 200)
MOVING_PLATFORM_COLOR = (200, 200, 100)
BG_COLOR = (135, 206, 235)  # Sky blue
MENU_BG_COLOR = (25, 25, 112)  # Midnight Blue

# Game states
class GameState(Enum):
    MENU = 0
    PLAYING = 1
    PAUSED = 2
    GAME_OVER = 3
    
# Difficulty levels
class Difficulty(Enum):
    EASY = 0
    NORMAL = 1
    HARD = 2

# Platform types
class PlatformType(Enum):
    STATIC = 1
    MOVING = 2
    BREAKING = 3
    BOUNCE = 4

# Powerup types
class PowerupType(Enum):
    WINGS = 1
    DOUBLE_JUMP = 2
    MAGNET = 3
    SLOW_TIME = 4

# Button class for menu
class Button:
    def __init__(self, x, y, width, height, text, color=BLUE, hover_color=GREEN, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        
    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)  # Border
        
        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered
        
    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 50
        self.vel_x = 0
        self.vel_y = 0
        self.is_jumping = False
        self.can_double_jump = False
        self.has_wings = False
        self.wings_timer = 0
        self.slow_time = False
        self.slow_time_timer = 0
        self.magnet = False
        self.magnet_timer = 0
        self.score = 0
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.facing_right = True
        
        # Create simple character sprite frames
        self.create_sprite_frames()
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 5  # frames between animation updates
        
    def create_sprite_frames(self):
        # Create simple character sprite
        self.frames_right = []
        self.frames_left = []
        
        # Standing frame
        standing_right = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Body
        pygame.draw.rect(standing_right, BLUE, (5, 10, 20, 30))
        # Head
        pygame.draw.circle(standing_right, (70, 70, 220), (15, 10), 10)
        # Legs
        pygame.draw.rect(standing_right, (50, 50, 180), (8, 40, 6, 10))
        pygame.draw.rect(standing_right, (50, 50, 180), (16, 40, 6, 10))
        
        # Walking frame 1
        walking1_right = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Body
        pygame.draw.rect(walking1_right, BLUE, (5, 10, 20, 30))
        # Head
        pygame.draw.circle(walking1_right, (70, 70, 220), (15, 10), 10)
        # Legs (walking position)
        pygame.draw.rect(walking1_right, (50, 50, 180), (8, 40, 6, 10))
        pygame.draw.rect(walking1_right, (50, 50, 180), (18, 38, 6, 12))
        
        # Walking frame 2
        walking2_right = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Body
        pygame.draw.rect(walking2_right, BLUE, (5, 10, 20, 30))
        # Head
        pygame.draw.circle(walking2_right, (70, 70, 220), (15, 10), 10)
        # Legs (walking position)
        pygame.draw.rect(walking2_right, (50, 50, 180), (6, 38, 6, 12))
        pygame.draw.rect(walking2_right, (50, 50, 180), (16, 40, 6, 10))
        
        # Jumping frame
        jumping_right = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Body
        pygame.draw.rect(jumping_right, BLUE, (5, 10, 20, 30))
        # Head
        pygame.draw.circle(jumping_right, (70, 70, 220), (15, 10), 10)
        # Legs (jumping position)
        pygame.draw.rect(jumping_right, (50, 50, 180), (10, 40, 5, 8))
        pygame.draw.rect(jumping_right, (50, 50, 180), (15, 40, 5, 8))
        
        # Add frames to right-facing list
        self.frames_right = [standing_right, walking1_right, walking2_right, jumping_right]
        
        # Create left-facing frames by flipping the right-facing ones
        for frame in self.frames_right:
            self.frames_left.append(pygame.transform.flip(frame, True, False))
        
    def update(self, platforms, wind_force=0, time_factor=1.0):
        # Apply gravity
        self.vel_y += GRAVITY * time_factor
        
        # Apply wind force
        self.vel_x += wind_force * time_factor
        
        # Apply friction
        self.vel_x *= 0.9
        
        # Update position
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Update facing direction
        if self.vel_x > 0.5:
            self.facing_right = True
        elif self.vel_x < -0.5:
            self.facing_right = False
        
        # Update animation
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            if abs(self.vel_x) > 0.5:  # If moving horizontally
                self.current_frame = (self.current_frame + 1) % 3  # Cycle through standing and walking frames
            else:
                self.current_frame = 0  # Standing frame
                
        # If jumping, use jumping frame
        if self.is_jumping:
            self.current_frame = 3
        
        # Screen boundaries
        if self.x < 0:
            self.x = 0
            self.vel_x = 0
        elif self.x > SCREEN_WIDTH - self.width:
            self.x = SCREEN_WIDTH - self.width
            self.vel_x = 0
            
        # Update rectangle for collision detection
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
        # Check for platform collisions
        self.check_platform_collisions(platforms)
        
        # Update powerup timers
        if self.has_wings:
            self.wings_timer -= time_factor
            if self.wings_timer <= 0:
                self.has_wings = False
                
        if self.slow_time:
            self.slow_time_timer -= time_factor
            if self.slow_time_timer <= 0:
                self.slow_time = False
                
        if self.magnet:
            self.magnet_timer -= time_factor
            if self.magnet_timer <= 0:
                self.magnet = False
    
    def check_platform_collisions(self, platforms):
        if self.vel_y > 0:  # Only check when falling
            for platform in platforms:
                if (self.rect.bottom >= platform.rect.top and
                    self.rect.bottom <= platform.rect.top + self.vel_y + 10 and
                    self.rect.right > platform.rect.left and
                    self.rect.left < platform.rect.right):
                    
                    # Land on platform
                    self.rect.bottom = platform.rect.top
                    self.y = self.rect.y
                    self.vel_y = 0
                    self.is_jumping = False
                    self.can_double_jump = True
                    
                    # Handle platform types
                    if platform.platform_type == PlatformType.BREAKING:
                        platform.breaking = True
                    elif platform.platform_type == PlatformType.BOUNCE:
                        self.vel_y = JUMP_FORCE * 1.5
                        self.is_jumping = True
    
    def jump(self):
        if not self.is_jumping:
            self.vel_y = JUMP_FORCE
            self.is_jumping = True
        elif self.can_double_jump:
            self.vel_y = JUMP_FORCE
            self.can_double_jump = False
    
    def draw(self, screen, camera_y):
        # Draw player sprite at camera-adjusted position
        frames = self.frames_right if self.facing_right else self.frames_left
        screen.blit(frames[self.current_frame], (self.x, self.y - camera_y))
        
        # Draw powerup indicators
        if self.has_wings:
            # Draw wing indicators
            wing_color = (220, 220, 255)
            wing_x = self.x - 8 if self.facing_right else self.x + self.width - 2
            pygame.draw.polygon(screen, wing_color, [
                (wing_x, self.y - camera_y + 15),
                (wing_x - 10 if self.facing_right else wing_x + 10, self.y - camera_y + 25),
                (wing_x, self.y - camera_y + 35)
            ])
        
        if self.slow_time:
            # Draw clock indicator above head
            pygame.draw.circle(screen, YELLOW, (int(self.x + self.width/2), int(self.y - camera_y - 10)), 5)
            pygame.draw.line(screen, BLACK, 
                            (int(self.x + self.width/2), int(self.y - camera_y - 10)),
                            (int(self.x + self.width/2), int(self.y - camera_y - 15)), 2)
            pygame.draw.line(screen, BLACK, 
                            (int(self.x + self.width/2), int(self.y - camera_y - 10)),
                            (int(self.x + self.width/2 + 3), int(self.y - camera_y - 8)), 2)
            
        if self.magnet:
            # Draw magnet indicator
            magnet_color = (200, 50, 50)
            pygame.draw.rect(screen, magnet_color, (self.x + 5, self.y - camera_y - 5, self.width - 10, 5))
            pygame.draw.rect(screen, magnet_color, (self.x + self.width//2 - 2, self.y - camera_y - 10, 4, 5))

class Platform:
    def __init__(self, x, y, width, platform_type=PlatformType.STATIC):
        self.x = x
        self.y = y
        self.width = width
        self.height = 15
        self.platform_type = platform_type
        self.rect = pygame.Rect(x, y, width, self.height)
        self.breaking = False
        self.break_timer = 30  # frames before disappearing
        self.direction = 1  # For moving platforms
        self.move_distance = 100  # For moving platforms
        self.original_x = x  # For moving platforms
        
    def update(self):
        if self.platform_type == PlatformType.MOVING:
            self.x += PLATFORM_SPEED * self.direction
            
            # Change direction if reached movement limit
            if self.x > self.original_x + self.move_distance:
                self.direction = -1
            elif self.x < self.original_x - self.move_distance:
                self.direction = 1
                
            self.rect.x = int(self.x)
            
        if self.breaking:
            self.break_timer -= 1
    
    def draw(self, screen, camera_y):
        if self.breaking and self.break_timer <= 0:
            return
            
        color = PLATFORM_COLOR
        if self.platform_type == PlatformType.MOVING:
            color = MOVING_PLATFORM_COLOR
        elif self.platform_type == PlatformType.BREAKING:
            color = BREAKING_PLATFORM_COLOR
            if self.breaking:
                # Make platform flash when breaking
                if self.break_timer % 5 == 0:
                    color = RED
        elif self.platform_type == PlatformType.BOUNCE:
            color = BOUNCE_PLATFORM_COLOR
            
        pygame.draw.rect(screen, color, (self.x, self.y - camera_y, self.width, self.height))

class Powerup:
    def __init__(self, x, y, powerup_type):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.powerup_type = powerup_type
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.collected = False
        
    def draw(self, screen, camera_y):
        if self.collected:
            return
            
        color = WHITE
        if self.powerup_type == PowerupType.WINGS:
            color = WHITE
        elif self.powerup_type == PowerupType.DOUBLE_JUMP:
            color = GREEN
        elif self.powerup_type == PowerupType.MAGNET:
            color = RED
        elif self.powerup_type == PowerupType.SLOW_TIME:
            color = YELLOW
            
        pygame.draw.rect(screen, color, (self.x, self.y - camera_y, self.width, self.height))

class Hazard:
    def __init__(self, x, y, hazard_type, speed=2):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 30
        self.hazard_type = hazard_type  # "spike", "bird", "rock"
        self.speed = speed
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
    def update(self, time_factor=1.0):
        if self.hazard_type == "bird":
            self.x += self.speed * time_factor
            if self.x > SCREEN_WIDTH:
                self.x = -self.width
        elif self.hazard_type == "rock":
            self.y += self.speed * time_factor
            
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
    def draw(self, screen, camera_y):
        pygame.draw.rect(screen, RED, (self.x, self.y - camera_y, self.width, self.height))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tower Jumper")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.running = True
        self.game_over = False
        self.score = 0
        self.high_score = 0
        
        # Game objects
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.platforms = []
        self.powerups = []
        self.hazards = []
        
        # Camera
        self.camera_y = 0
        
        # Tower effects
        self.quake_timer = FPS * random.randint(QUAKE_INTERVAL_MIN, QUAKE_INTERVAL_MAX)
        self.quake_active = False
        self.quake_duration = 0
        self.quake_intensity = 0
        self.rotation_angle = 0
        
        # Wind effects
        self.wind_timer = FPS * random.randint(WIND_INTERVAL_MIN, WIND_INTERVAL_MAX)
        self.wind_active = False
        self.wind_duration = 0
        self.wind_force = 0
        
        # Initialize platforms
        self.generate_initial_platforms()
        
    def generate_initial_platforms(self):
        # Starting platform
        self.platforms.append(Platform(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 50, 100))
        
        # Generate initial set of platforms
        current_y = SCREEN_HEIGHT - 150
        while current_y > -1000:  # Generate some platforms above the screen
            current_y -= random.randint(PLATFORM_GAP_MIN, PLATFORM_GAP_MAX)
            platform_width = random.randint(60, 150)
            platform_x = random.randint(0, SCREEN_WIDTH - platform_width)
            
            # Determine platform type
            platform_type = PlatformType.STATIC
            platform_chance = random.random()
            
            if platform_chance < 0.1:
                platform_type = PlatformType.BOUNCE
            elif platform_chance < 0.3:
                platform_type = PlatformType.MOVING
            elif platform_chance < 0.4:
                platform_type = PlatformType.BREAKING
                
            self.platforms.append(Platform(platform_x, current_y, platform_width, platform_type))
            
            # Chance to add powerup above platform
            if random.random() < 0.1:
                powerup_type = random.choice(list(PowerupType))
                self.powerups.append(Powerup(platform_x + platform_width//2 - 10, 
                                            current_y - 30, powerup_type))
                                            
            # Chance to add hazard
            if random.random() < 0.05 and current_y < SCREEN_HEIGHT - 300:  # No hazards near start
                if random.random() < 0.5:
                    # Spike on platform
                    self.hazards.append(Hazard(platform_x + random.randint(10, platform_width-40), 
                                              current_y - 15, "spike"))
                else:
                    # Flying bird
                    bird_y = current_y - random.randint(50, 100)
                    bird_speed = random.choice([-3, 3])
                    bird_x = 0 if bird_speed > 0 else SCREEN_WIDTH
                    self.hazards.append(Hazard(bird_x, bird_y, "bird", bird_speed))
    
    def generate_platforms_above(self):
        # Generate new platforms as player climbs
        highest_platform = min(platform.y for platform in self.platforms)
        
        while highest_platform > self.camera_y - SCREEN_HEIGHT:
            new_y = highest_platform - random.randint(PLATFORM_GAP_MIN, PLATFORM_GAP_MAX)
            platform_width = random.randint(60, 150)
            platform_x = random.randint(0, SCREEN_WIDTH - platform_width)
            
            # Determine platform type - higher up means more difficult platforms
            platform_type = PlatformType.STATIC
            platform_chance = random.random()
            height_factor = min(0.7, abs(new_y) / 10000)  # Increases with height
            
            if platform_chance < 0.1 + height_factor * 0.1:
                platform_type = PlatformType.BOUNCE
            elif platform_chance < 0.3 + height_factor * 0.2:
                platform_type = PlatformType.MOVING
            elif platform_chance < 0.4 + height_factor * 0.3:
                platform_type = PlatformType.BREAKING
                
            self.platforms.append(Platform(platform_x, new_y, platform_width, platform_type))
            highest_platform = new_y
            
            # Chance to add powerup above platform
            if random.random() < 0.1:
                powerup_type = random.choice(list(PowerupType))
                self.powerups.append(Powerup(platform_x + platform_width//2 - 10, 
                                            new_y - 30, powerup_type))
                                            
            # Chance to add hazard
            if random.random() < 0.05 + height_factor * 0.1:
                hazard_chance = random.random()
                if hazard_chance < 0.4:
                    # Spike on platform
                    self.hazards.append(Hazard(platform_x + random.randint(10, platform_width-40), 
                                              new_y - 15, "spike"))
                elif hazard_chance < 0.8:
                    # Flying bird
                    bird_y = new_y - random.randint(50, 100)
                    bird_speed = random.choice([-3, 3])
                    bird_x = 0 if bird_speed > 0 else SCREEN_WIDTH
                    self.hazards.append(Hazard(bird_x, bird_y, "bird", bird_speed))
                else:
                    # Falling rock
                    rock_x = random.randint(0, SCREEN_WIDTH - 30)
                    rock_y = new_y - random.randint(100, 200)
                    self.hazards.append(Hazard(rock_x, rock_y, "rock", 3))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_over = not self.game_over  # Toggle pause
                elif event.key == pygame.K_SPACE or event.key == pygame.K_UP or event.key == pygame.K_w:
                    if not self.game_over:
                        self.player.jump()
                elif event.key == pygame.K_r and self.game_over:
                    self.reset_game()
    
    def handle_input(self):
        if self.game_over:
            return
            
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.vel_x = -PLAYER_SPEED
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.vel_x = PLAYER_SPEED
        else:
            self.player.vel_x *= 0.9  # Friction
    
    def update(self):
        if self.game_over:
            return
            
        # Calculate time factor for slow time powerup
        time_factor = 0.5 if self.player.slow_time else 1.0
        
        # Update tower effects
        self.update_tower_effects(time_factor)
        
        # Update player
        self.player.update(self.platforms, self.wind_force if self.wind_active else 0, time_factor)
        
        # Update camera to follow player
        if self.player.y < self.camera_y + SCROLL_THRESHOLD:
            self.camera_y = self.player.y - SCROLL_THRESHOLD
        
        # Update platforms
        for platform in self.platforms[:]:
            platform.update()
            if platform.breaking and platform.break_timer <= 0:
                self.platforms.remove(platform)
            elif platform.y > self.camera_y + SCREEN_HEIGHT + 100:
                self.platforms.remove(platform)
        
        # Generate new platforms as needed
        self.generate_platforms_above()
        
        # Update powerups and check collection
        for powerup in self.powerups[:]:
            if powerup.y > self.camera_y + SCREEN_HEIGHT + 100:
                self.powerups.remove(powerup)
            elif not powerup.collected and self.player.rect.colliderect(powerup.rect):
                self.apply_powerup(powerup)
                powerup.collected = True
                self.powerups.remove(powerup)
        
        # Update hazards
        for hazard in self.hazards[:]:
            hazard.update(time_factor)
            if hazard.y > self.camera_y + SCREEN_HEIGHT + 100:
                self.hazards.remove(hazard)
            elif self.player.rect.colliderect(hazard.rect):
                self.game_over = True
        
        # Update score based on height
        height_score = max(0, int((self.player.score - self.player.y) / 10))
        if height_score > self.score:
            self.score = height_score
        
        # Check for game over
        if self.player.y > self.camera_y + SCREEN_HEIGHT:
            self.game_over = True
            if self.score > self.high_score:
                self.high_score = self.score
    
    def update_tower_effects(self, time_factor):
        # Tower quake effect
        if not self.quake_active:
            self.quake_timer -= time_factor
            if self.quake_timer <= 0:
                self.quake_active = True
                self.quake_duration = FPS * QUAKE_DURATION
                self.quake_intensity = random.uniform(2, 5)
                self.rotation_angle = random.uniform(-5, 5)
                
                # Shift platforms during quake
                for platform in self.platforms:
                    platform.x += random.randint(-30, 30)
                    if platform.x < 0:
                        platform.x = 0
                    elif platform.x > SCREEN_WIDTH - platform.width:
                        platform.x = SCREEN_WIDTH - platform.width
                    platform.rect.x = int(platform.x)
                    
                    if platform.platform_type == PlatformType.MOVING:
                        platform.original_x = platform.x
        else:
            self.quake_duration -= time_factor
            if self.quake_duration <= 0:
                self.quake_active = False
                self.quake_timer = FPS * random.randint(QUAKE_INTERVAL_MIN, QUAKE_INTERVAL_MAX)
                self.rotation_angle = 0
        
        # Wind effect
        if not self.wind_active:
            self.wind_timer -= time_factor
            if self.wind_timer <= 0:
                self.wind_active = True
                self.wind_duration = FPS * WIND_DURATION
                self.wind_force = random.choice([-WIND_FORCE, WIND_FORCE])
        else:
            self.wind_duration -= time_factor
            if self.wind_duration <= 0:
                self.wind_active = False
                self.wind_timer = FPS * random.randint(WIND_INTERVAL_MIN, WIND_INTERVAL_MAX)
                self.wind_force = 0
    
    def apply_powerup(self, powerup):
        if powerup.powerup_type == PowerupType.WINGS:
            self.player.has_wings = True
            self.player.wings_timer = 5 * FPS  # 5 seconds
        elif powerup.powerup_type == PowerupType.DOUBLE_JUMP:
            self.player.can_double_jump = True
        elif powerup.powerup_type == PowerupType.MAGNET:
            self.player.magnet = True
            self.player.magnet_timer = 7 * FPS  # 7 seconds
        elif powerup.powerup_type == PowerupType.SLOW_TIME:
            self.player.slow_time = True
            self.player.slow_time_timer = 3 * FPS  # 3 seconds
    
    def draw(self):
        self.screen.fill(BG_COLOR)
        
        # Apply tower quake effect
        if self.quake_active:
            quake_offset_x = random.uniform(-self.quake_intensity, self.quake_intensity)
            quake_offset_y = random.uniform(-self.quake_intensity, self.quake_intensity)
        else:
            quake_offset_x = 0
            quake_offset_y = 0
        
        # Draw platforms
        for platform in self.platforms:
            platform.draw(self.screen, self.camera_y)
        
        # Draw powerups
        for powerup in self.powerups:
            powerup.draw(self.screen, self.camera_y)
        
        # Draw hazards
        for hazard in self.hazards:
            hazard.draw(self.screen, self.camera_y)
        
        # Draw player
        self.player.draw(self.screen, self.camera_y)
        
        # Draw wind effect indicator
        if self.wind_active:
            wind_start = 0 if self.wind_force > 0 else SCREEN_WIDTH
            wind_end = SCREEN_WIDTH if self.wind_force > 0 else 0
            for i in range(5):
                y_pos = 100 + i * 100
                pygame.draw.line(self.screen, (200, 200, 255, 128), 
                                (wind_start, y_pos), 
                                (wind_end, y_pos), 
                                3)
        
        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 20))
        
        # Draw height
        height_text = self.font.render(f"Height: {abs(int(self.player.y))}", True, WHITE)
        self.screen.blit(height_text, (20, 60))
        
        # Draw game over screen
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.font.render("GAME OVER", True, WHITE)
            score_text = self.font.render(f"Score: {self.score}", True, WHITE)
            high_score_text = self.font.render(f"High Score: {self.high_score}", True, WHITE)
            restart_text = self.font.render("Press R to Restart", True, WHITE)
            
            self.screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 80))
            self.screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2 - 30))
            self.screen.blit(high_score_text, (SCREEN_WIDTH//2 - high_score_text.get_width()//2, SCREEN_HEIGHT//2 + 10))
            self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 60))
        
        pygame.display.flip()
    
    def reset_game(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.platforms = []
        self.powerups = []
        self.hazards = []
        self.camera_y = 0
        self.score = 0
        self.game_over = False
        self.quake_timer = FPS * random.randint(QUAKE_INTERVAL_MIN, QUAKE_INTERVAL_MAX)
        self.quake_active = False
        self.wind_timer = FPS * random.randint(WIND_INTERVAL_MIN, WIND_INTERVAL_MAX)
        self.wind_active = False
        self.generate_initial_platforms()
    
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.handle_input()
            self.update()
            self.draw()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()

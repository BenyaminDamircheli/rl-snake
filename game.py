import pygame
import random
import time
from enum import Enum
import numpy as np


class Direction(Enum):
    RIGHT = 0
    LEFT = 1
    UP = 2
    DOWN = 3


class SnakeGame:
    def __init__(self, width=640, height=480, grid_size=20, render=True):
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.grid_width = self.width // self.grid_size
        self.grid_height = self.height // self.grid_size
        self.render = render

        # initialize pygame rendering if enabled
        if self.render:
            pygame.init()
            self.display = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Snake")
            self.clock = pygame.time.Clock()

        # initialize game state
        self.reset()


    def reset(self):
        """
        Reset the game state and return the initial observation
        """
         # Initial direction
        self.snake_direction = Direction.RIGHT
        
        # Initial snake position (head at center, body to the left)
        self.head = [self.grid_width // 2, self.grid_height // 2]
        
        # snake is a list of positions, starting with the head
        self.snake = [
            self.head.copy(),
            [self.head[0] - 1, self.head[1]],
            [self.head[0] - 2, self.head[1]]
        ]
        
        # Initial score and food
        self.score = 0
        self.food = None
        self._place_food()
        
        # Initial game over state
        self.game_over = False
        
        # Frame iteration (can be used to limit game length)
        self.frame_iteration = 0
        
        return self._get_state()
    
    def _place_food(self):
        """
        Place a new food item at a random position on the grid not occupied by the snake
        """
        while True:
            x = random.randint(0, self.grid_width - 1)
            y = random.randint(0, self.grid_height - 1)
            self.food = [x, y]
            if self.food not in self.snake:
                break


    def debug_print(self):
        """
        Print the current game state for debugging purposes as ASCII
        """
        board = [["." for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        if self.food:
            board[self.food[1]][self.food[0]] = "F"
        
        for i, seg in enumerate(self.snake):
            if i == 0:
                board[seg[1]][seg[0]] = "H"
            else:
                board[seg[1]][seg[0]] = "X"
        
        # Print the board with borders
        print('+' + '-' * self.grid_width + '+')
        for row in board:
            print('|' + ''.join(row) + '|')
        print('+' + '-' * self.grid_width + '+')
        print(f"Score: {self.score}, Length: {len(self.snake)}, Direction: {self.snake_direction.name}")
    
    def step(self, action):
        """
        Update the game state based on the provided action.
        
        Args:
            action (int): 0 = RIGHT, 1 = DOWN, 2 = LEFT, 3 = UP
        
        Returns:
            state (np.array): The new state
            reward (float): The reward for this step
            done (bool): Whether the game is over
            info (dict): Additional information (score)
        """
        # Update frame iteration
        self.frame_iteration += 1
        
        # Process game events (allows for window closing)
        if self.render:
            # Process only QUIT events, keep other events for main loop
            for event in pygame.event.get(pygame.QUIT):
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
            pygame.event.pump()
        
        # Move snake based on the action
        self._move(action)
        self.snake.insert(0, self.head.copy())
        
        # Initialize reward
        reward = 0
        done = False
        
        # Check if game over (collision or timeout)
        if self._is_collision() or self.frame_iteration > 100 * len(self.snake):
            done = True
            reward = -10
            return self._get_state(), reward, done, {'score': self.score}
        
        # Check if snake ate food
        if self.head == self.food:
            self.score += 1
            reward = 10
            self._place_food()
        else:
            # Remove the last segment of the snake (unless it just ate)
            self.snake.pop()
        
        # Update UI if rendering is enabled
        if self.render:
            self._update_ui()
            self.clock.tick(30)  # Adjust speed here
        
        # Small negative reward to encourage efficiency
        if reward == 0:
            reward = -0.01
        
        return self._get_state(), reward, done, {'score': self.score}
    
    def _is_collision(self):
        """Check if the snake has collided with a wall or itself."""
        # Hit boundary
        if (
            self.head[0] >= self.grid_width or self.head[0] < 0 or
            self.head[1] >= self.grid_height or self.head[1] < 0
        ):
            return True
        
        # Hit itself (check if head position is in the rest of the body)
        if self.head in self.snake[1:]:
            return True
        
        return False
    
    def _update_ui(self):
        """Update the game display."""
        if not self.render:
            return
            
        self.display.fill((0, 0, 0))  # Black background
        
        # Draw snake
        for pt in self.snake:
            pygame.draw.rect(
                self.display, (0, 255, 0),  # Green snake
                pygame.Rect(
                    pt[0] * self.grid_size, pt[1] * self.grid_size,
                    self.grid_size, self.grid_size
                )
            )
            
            # Draw a darker green border around snake segments
            pygame.draw.rect(
                self.display, (0, 200, 0),  # Darker green
                pygame.Rect(
                    pt[0] * self.grid_size, pt[1] * self.grid_size,
                    self.grid_size, self.grid_size
                ), 1  # Width=1 for just the border
            )
        
        # Draw food
        pygame.draw.rect(
            self.display, (255, 0, 0),  # Red food
            pygame.Rect(
                self.food[0] * self.grid_size, self.food[1] * self.grid_size,
                self.grid_size, self.grid_size
            )
        )
        
        # Display score
        font = pygame.font.SysFont('arial', 25)
        text = font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.display.blit(text, [0, 0])
        
        pygame.display.flip()
    
    def _draw_game_over(self):
        """Draw the game over overlay."""
        if not self.render:
            return
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)) # Black with some transparency
        self.display.blit(overlay, (0, 0))
        
        # Game Over Text
        font = pygame.font.SysFont('arial', 50)
        text = font.render("GAME OVER", True, (255, 0, 0)) # Red
        text_rect = text.get_rect(center=(self.width / 2, self.height / 2 - 50))
        self.display.blit(text, text_rect)
        
        # Final Score Text
        font = pygame.font.SysFont('arial', 30)
        score_text = font.render(f"Final Score: {self.score}", True, (255, 255, 255)) # White
        score_rect = score_text.get_rect(center=(self.width / 2, self.height / 2))
        self.display.blit(score_text, score_rect)

        # Restart Text
        font = pygame.font.SysFont('arial', 25)
        restart_text = font.render("Press 'R' to Restart", True, (255, 255, 255)) # White
        restart_rect = restart_text.get_rect(center=(self.width / 2, self.height / 2 + 50))
        self.display.blit(restart_text, restart_rect)
        
        pygame.display.flip()
    
    def _move(self, action):
        """
        Update the snake's direction and head position based on the action.
        
        Args:
            action (int): 0 = RIGHT, 1 = LEFT, 2 = UP, 3 = DOWN
        """
        # Map actions to Directions and define opposites
        # Action: 0=RIGHT, 1=LEFT, 2=UP, 3=DOWN
        directions = [Direction.RIGHT, Direction.LEFT, Direction.UP, Direction.DOWN]
        opposites = { 
            Direction.RIGHT: Direction.LEFT,
            Direction.LEFT: Direction.RIGHT,
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP
        }
        
        if 0 <= action <= 3:
            new_direction = directions[action]
            current_direction = self.snake_direction
            
            # Prevent 180-degree turns
            if new_direction != opposites[current_direction]:
                self.snake_direction = new_direction

        # Update head position based on the potentially updated direction
        x, y = self.head
        if self.snake_direction == Direction.RIGHT:
            x += 1
        elif self.snake_direction == Direction.LEFT:
            x -= 1
        elif self.snake_direction == Direction.DOWN:
            y += 1
        elif self.snake_direction == Direction.UP:
            y -= 1
        
        self.head = [x, y]
    
    def _get_state(self):
        """
        Get the state representation for the RL agent.
        
        Returns:
            np.array: The state representation (12 binary values)
        """
        head_x, head_y = self.head
        
        # Create points for checking danger
        points_relative = [
            [1, 0],   # Right
            [0, 1],   # Down
            [-1, 0],  # Left
            [0, -1]   # Up
        ]
        
        danger = [False, False, False, False]  # Danger in each direction
        
        # Check for danger in each direction
        for i, (dx, dy) in enumerate(points_relative):
            point = [head_x + dx, head_y + dy]
            # Check if point is out of bounds
            if (
                point[0] >= self.grid_width or point[0] < 0 or
                point[1] >= self.grid_height or point[1] < 0
            ):
                danger[i] = True
            # Check if point is on snake body
            elif point in self.snake[1:]:
                danger[i] = True
        
        # Current direction as a one-hot encoding
        dir_one_hot = [0, 0, 0, 0]
        dir_one_hot[self.snake_direction.value] = 1
        
        # Food direction
        food_dir = [
            self.food[0] > head_x,  # Food is to the right
            self.food[1] > head_y,  # Food is down
            self.food[0] < head_x,  # Food is to the left
            self.food[1] < head_y   # Food is up
        ]
        
        # Combine all state features
        state = danger + dir_one_hot + food_dir
        
        return np.array(state, dtype=int)

    def get_action_space(self):
        """
        Returns the action space information.
        
        Returns:
            dict: Information about the action space
        """
        return {
            'n': 4,  # Number of possible actions
            'actions': {
                0: 'RIGHT',
                1: 'DOWN',
                2: 'LEFT',
                3: 'UP'
            }
        }
    
    def get_state_space(self):
        """
        Returns the state space information.
        
        Returns:
            dict: Information about the state space
        """
        return {
            'shape': (12,),  # 4 danger values + 4 direction values + 4 food direction values
            'features': {
                'danger': 'Binary values indicating danger in RIGHT, DOWN, LEFT, UP directions',
                'direction': 'One-hot encoding of current direction (RIGHT, DOWN, LEFT, UP)',
                'food_direction': 'Binary values indicating if food is in RIGHT, DOWN, LEFT, UP directions'
            }
        }

class SnakeEnv:
    """
    A wrapper for the SnakeGameAI that follows the Gym-like interface.
    This makes it easier to use with RL libraries.
    """
    def __init__(self, width=640, height=480, grid_size=20, render=True):
        self.game = SnakeGame(width, height, grid_size, render)
        self.action_space = self.game.get_action_space()
        self.observation_space = self.game.get_state_space()
    
    def reset(self):
        """
        Reset the game and return the initial observation
        """
        return self.game.reset()
    
    def step(self, action):
        """
        Take a step in the game
        
        Args:
            action (int): The action to take
        
        Returns:
            tuple: (observation, reward, done, info)
        """
        return self.game.step(action)
    
    def render(self):
        """
        Render the game
        """
        if self.game.render:
            self.game._update_ui()
    
    def close(self):
        """
        Close the game
        """
        if self.game.render:
            pygame.quit()
    

# Example of usage
def main():
    human_mode = True  # Set to False for AI mode
    game = SnakeGame(render=True)
    
    # Print information about the state and action spaces
    print(f"Action Space: {game.get_action_space()}")
    print(f"State Space: {game.get_state_space()}")
    
    # Game loop
    done = False
    while True:
        # Handle quit and restart events
        restart_game = False
        action = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if done and event.key == pygame.K_r:
                    restart_game = True
                elif not done and human_mode:
                    if event.key == pygame.K_a:
                        action = 1
                    elif event.key == pygame.K_d:
                        action = 0
                    elif event.key == pygame.K_w:
                        action = 2
                    elif event.key == pygame.K_s:
                        action = 3
        if restart_game:
            game.reset()
            done = False
            continue

        # Game logic
        if not done:
            state = game._get_state()
            if human_mode:
                if action is None:
                    action = game.snake_direction.value
            else:
                action = random.randint(0, 3)

            # Advance game
            next_state, reward, done, info = game.step(action)
            time.sleep(0.1)

            if not human_mode:
                print(f"State: {state}")
                print(f"Action: {action}")
                print(f"Reward: {reward}")
                print(f"Score: {info['score']}")
                time.sleep(1)

            if done:
                print(f"Game Over! Final Score: {info['score']}")
        else:
            # Draw game over and wait for restart
            game._draw_game_over()
            game.clock.tick(15)

if __name__ == "__main__":
    main()
        
    
    
    


        

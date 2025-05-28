import pygame
import random
import copy
from collections import deque
import time 

# Constants
GRID_SIZE   = 9
CELL_SIZE   = 60
BOARD_PIX   = GRID_SIZE * CELL_SIZE
BUTTON_AREA = 60
WIDTH       = BOARD_PIX
HEIGHT      = BOARD_PIX + BUTTON_AREA

WHITE       = (255, 255, 255)
BLACK       = (  0,   0,   0)
GRAY        = (200, 200, 200)
BLUE        = (100, 100, 255)
GREEN       = (  0, 200,   0)
RED         = (200,   0,   0)
ORANGE      = (255, 140, 0)
HOVER_COLOR = (255, 180, 0) 
CLICK_COLOR = (200, 100, 0) 
POPUP_BG_COLOR = (150, 150, 150, 180)
POPUP_TEXT_COLOR = (255, 255, 255)
NUM_DELAY   = 50  
POPUP_DURATION = 3

# Game States
MENU        = 0
PLAYING     = 1

# Music file path
MUSIC_FILE  = 'kids-game-gaming-background-music-295075.mp3' 
COUNT_SOUND_FILE = 'bubble-pop-2-293341.mp3'

# Generate Random Sudoku
def fill_diagonal_boxes(grid):
    def fill_box(r, c):
        nums = list(range(1, 10))
        random.shuffle(nums)
        for i in range(3):
            for j in range(3):
                grid[r+i][c+j] = nums.pop()
    for start in (0, 3, 6):
        fill_box(start, start)

def is_valid(grid, r, c, n):
    if any(grid[r][j] == n for j in range(9)): return False
    if any(grid[i][c] == n for i in range(9)): return False
    
    br, bc = (r//3)*3, (c//3)*3
    for i in range(br, br+3):
        for j in range(bc, bc+3):
            if grid[i][j] == n: return False
    return True

def backtrack_fill(grid):
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                for n in range(1, 10):
                    if is_valid(grid, i, j, n):
                        grid[i][j] = n
                        if backtrack_fill(grid):
                            return True
                        grid[i][j] = 0
                return False
    return True

def generate_puzzle(holes=40):
    grid = [[0]*9 for _ in range(9)]
    fill_diagonal_boxes(grid)
    backtrack_fill(grid)
    positions = [(i,j) for i in range(9) for j in range(9)]
    random.shuffle(positions)
    for _ in range(holes):
        i, j = positions.pop()
        grid[i][j] = 0
    return grid

def find_empty(grid):
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                return i, j
    return None

# Pygame Setup
pygame.init()
pygame.mixer.init() 

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sudoku Solver")
font         = pygame.font.SysFont(None, 40)
button_font  = pygame.font.SysFont(None, 32)
title_font   = pygame.font.SysFont(None, 72) 
clock        = pygame.time.Clock()

dfs_btn      = pygame.Rect(40,  BOARD_PIX + 10, 100, 40)
bfs_btn      = pygame.Rect(160, BOARD_PIX + 10, 100, 40)
reset_btn    = pygame.Rect(280, BOARD_PIX + 10, 100, 40)
gen_btn      = pygame.Rect(400, BOARD_PIX + 10, 100, 40)

# Menu Buttons
play_btn     = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 - 30, 150, 60)
exit_btn     = pygame.Rect(WIDTH // 2 - 75, HEIGHT // 2 + 50, 150, 60)

# Load Music
try:
    pygame.mixer.music.load(MUSIC_FILE)
    pygame.mixer.music.set_volume(0.5) 
except pygame.error as e:
    print(f"Could not load music file: {e}")

# Load Count Sound Effect
count_sound = None
try:
    count_sound = pygame.mixer.Sound(COUNT_SOUND_FILE)
    count_sound.set_volume(0.7) 
except pygame.error as e:
    print(f"Could not load count sound file: {e}")

# Draw Functions
def draw_grid(g, highlight=None):
    screen.fill(WHITE)

    for i in range(9):
        for j in range(9):
            x, y = j*CELL_SIZE, i*CELL_SIZE
            if highlight == (i, j):
                pygame.draw.rect(screen, BLUE, (x, y, CELL_SIZE, CELL_SIZE))
            n = g[i][j]
            if n != 0:
                txt = font.render(str(n), True, BLACK)
                screen.blit(txt, (x+20, y+10))
    
    for i in range(10):
        w = 3 if i%3==0 else 1
        pygame.draw.line(screen, BLACK, (0, i*CELL_SIZE), (BOARD_PIX, i*CELL_SIZE), w)
        pygame.draw.line(screen, BLACK, (i*CELL_SIZE, 0), (i*CELL_SIZE, BOARD_PIX), w)

def draw_buttons(mouse_pos, mouse_click):
    # DFS Button
    color_dfs = ORANGE
    if dfs_btn.collidepoint(mouse_pos):
        color_dfs = HOVER_COLOR
        if mouse_click[0]: 
            color_dfs = CLICK_COLOR
    pygame.draw.rect(screen, color_dfs, dfs_btn)
    screen.blit(button_font.render("DFS", True, WHITE), (dfs_btn.x+25, dfs_btn.y+10))

    # BFS Button
    color_bfs = ORANGE
    if bfs_btn.collidepoint(mouse_pos):
        color_bfs = HOVER_COLOR
        if mouse_click[0]:
            color_bfs = CLICK_COLOR
    pygame.draw.rect(screen, color_bfs, bfs_btn)
    screen.blit(button_font.render("BFS", True, WHITE), (bfs_btn.x+25, bfs_btn.y+10))

    # Reset Button
    color_reset = RED
    if reset_btn.collidepoint(mouse_pos):
        color_reset = (255, 100, 100) 
        if mouse_click[0]:
            color_reset = (200, 0, 0) 
    pygame.draw.rect(screen, color_reset, reset_btn)
    screen.blit(button_font.render("Reset", True, WHITE), (reset_btn.x+20, reset_btn.y+10))

    # New Button
    color_gen = GREEN
    if gen_btn.collidepoint(mouse_pos):
        color_gen = (100, 255, 100) 
        if mouse_click[0]:
            color_gen = (0, 150, 0) 
    pygame.draw.rect(screen, color_gen, gen_btn)
    screen.blit(button_font.render("New", True, WHITE), (gen_btn.x+30, gen_btn.y+10))

def draw_menu(mouse_pos, mouse_click):
    screen.fill(GRAY) 

    # Draw Title
    title_text = title_font.render("Sudoku Solver", True, BLACK)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
    screen.blit(title_text, title_rect)

    # Play Button
    color_play = GREEN
    if play_btn.collidepoint(mouse_pos):
        color_play = (100, 255, 100) 
        if mouse_click[0]:
            color_play = (0, 150, 0) 
    pygame.draw.rect(screen, color_play, play_btn)
    play_text = button_font.render("Play", True, WHITE)
    play_text_rect = play_text.get_rect(center=play_btn.center)
    screen.blit(play_text, play_text_rect)

    # Exit Button
    color_exit = RED
    if exit_btn.collidepoint(mouse_pos):
        color_exit = (255, 100, 100) 
        if mouse_click[0]:
            color_exit = (200, 0, 0) 
    pygame.draw.rect(screen, color_exit, exit_btn)
    exit_text = button_font.render("Exit", True, WHITE)
    exit_text_rect = exit_text.get_rect(center=exit_btn.center)
    screen.blit(exit_text, exit_text_rect)

# Draw Pop-up function
def draw_popup(message):
    popup_surface = pygame.Surface((WIDTH * 0.7, HEIGHT * 0.2), pygame.SRCALPHA)
    popup_surface.fill(POPUP_BG_COLOR)

    popup_text = font.render(message, True, POPUP_TEXT_COLOR)
    text_rect = popup_text.get_rect(center=(popup_surface.get_width() // 2, popup_surface.get_height() // 2))
    popup_surface.blit(popup_text, text_rect)

    popup_rect = popup_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(popup_surface, popup_rect)

# Solve with DFS
def solve_dfs(grid):
    empty = find_empty(grid)
    if not empty:
        return True
    r, c = empty
    for n in range(1, 10):
        if is_valid(grid, r, c, n):
            grid[r][c] = n
            if count_sound: 
                count_sound.play()
            draw_grid(grid, highlight=(r,c))
            draw_buttons(pygame.mouse.get_pos(), pygame.mouse.get_pressed()) 
            pygame.display.flip()
            pygame.time.delay(NUM_DELAY)
            if solve_dfs(grid):
                return True
            # backtrack
            grid[r][c] = 0
            if count_sound: 
                count_sound.play() 
            draw_grid(grid, highlight=(r,c))
            draw_buttons(pygame.mouse.get_pos(), pygame.mouse.get_pressed()) 
            pygame.display.flip()
            pygame.time.delay(NUM_DELAY)
    return False

# Solve with BFS 
def solve_bfs(initial):
    queue = deque([initial])
    visited = set()
    
    while queue:
        current_grid = queue.popleft()
        
        grid_key = tuple(tuple(row) for row in current_grid)
        if grid_key in visited:
            continue
        visited.add(grid_key)
        
        if not find_empty(current_grid):
            return current_grid
            
        empty_cells = []
        for i in range(9):
            for j in range(9):
                if current_grid[i][j] == 0:
                    empty_cells.append((i, j))
        
        if empty_cells:
            r, c = empty_cells[0]
            for n in range(1, 10):
                if is_valid(current_grid, r, c, n):
                    new_grid = copy.deepcopy(current_grid)
                    new_grid[r][c] = n
                    queue.append(new_grid)
    
    return None

# Animate Solution
def animate_solution(grid, solution):
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0 and solution[i][j] != 0:
                grid[i][j] = solution[i][j]
                if count_sound: 
                    count_sound.play()
                draw_grid(grid, highlight=(i,j))
                draw_buttons(pygame.mouse.get_pos(), pygame.mouse.get_pressed()) 
                pygame.display.flip()
                pygame.time.delay(NUM_DELAY)
                
# Main Loop
original = generate_puzzle(holes=40)
grid     = [row[:] for row in original]
solving  = False
solved   = False
method   = None
running  = True
game_state = MENU 
start_time = 0.0 
solve_duration = 0.0 

# Pop-up variables
popup_active = False
popup_message = ""
popup_end_time = 0.0

# Play music when entering the menu state
if game_state == MENU and pygame.mixer.music.get_busy() == False:
    try:
        pygame.mixer.music.play(-1) 
    except pygame.error as e:
        print(f"Could not play music: {e}")


while running:
    mouse_pos   = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed() 

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if game_state == MENU:
                if play_btn.collidepoint(e.pos):
                    game_state = PLAYING
                    pygame.mixer.music.stop() 
                    original = generate_puzzle(holes=40)
                    grid     = [row[:] for row in original]
                    solving  = solved = False
                    solve_duration = 0.0 
                    popup_active = False
                elif exit_btn.collidepoint(e.pos):
                    running = False
            elif game_state == PLAYING:
                if popup_active and e.button == 1: 
                    popup_active = False

                if dfs_btn.collidepoint(e.pos) and not solving:
                    method  = "DFS"
                    solving = True
                    start_time = time.perf_counter() 
                    solved = False 
                    solve_duration = 0.0
                    popup_active = False 
                elif bfs_btn.collidepoint(e.pos) and not solving:
                    method  = "BFS"
                    solving = True
                    start_time = time.perf_counter() 
                    solved = False 
                    solve_duration = 0.0
                    popup_active = False 
                elif reset_btn.collidepoint(e.pos):
                    grid    = [row[:] for row in original]
                    solving = solved = False
                    solve_duration = 0.0 
                    popup_active = False 
                elif gen_btn.collidepoint(e.pos):
                    original = generate_puzzle(holes=40)
                    grid     = [row[:] for row in original]
                    solving  = solved = False
                    solve_duration = 0.0 
                    popup_active = False 

    if game_state == MENU:
        draw_menu(mouse_pos, mouse_click)
        if not pygame.mixer.music.get_busy():
            try:
                pygame.mixer.music.play(-1) 
            except pygame.error as e:
                print(f"Could not play music: {e}")
    elif game_state == PLAYING:
        draw_grid(grid)
        draw_buttons(mouse_pos, mouse_click)
        
        if solving and not solved:
            if method == "DFS":
                solved = solve_dfs(grid)
            elif method == "BFS":
                solution = solve_bfs(grid) 
                if solution:
                    animate_solution(grid, solution)
                    solved = True
            
            if solved: 
                end_time = time.perf_counter()
                solve_duration = end_time - start_time
                popup_message = f"Solved in: {solve_duration:.4f}s"
                popup_active = True
                popup_end_time = time.time() + POPUP_DURATION
                    
            solving = False
        
        if popup_active:
            draw_popup(popup_message)
            if time.time() > popup_end_time:
                popup_active = False


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
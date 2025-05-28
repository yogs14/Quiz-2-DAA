import pygame
import random
import copy
from collections import deque

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
NUM_DELAY   = 50  

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
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sudoku Solver")
font         = pygame.font.SysFont(None, 40)
button_font  = pygame.font.SysFont(None, 32)
clock        = pygame.time.Clock()

dfs_btn      = pygame.Rect(40,  BOARD_PIX + 10, 100, 40)
bfs_btn      = pygame.Rect(160, BOARD_PIX + 10, 100, 40)
reset_btn    = pygame.Rect(280, BOARD_PIX + 10, 100, 40)
gen_btn      = pygame.Rect(400, BOARD_PIX + 10, 100, 40)

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

def draw_buttons():
    pygame.draw.rect(screen, ORANGE, dfs_btn)
    pygame.draw.rect(screen, ORANGE, bfs_btn)
    pygame.draw.rect(screen, RED,   reset_btn)
    pygame.draw.rect(screen, GREEN, gen_btn)
    screen.blit(button_font.render("DFS", True, WHITE), (dfs_btn.x+25, dfs_btn.y+10))
    screen.blit(button_font.render("BFS", True, WHITE), (bfs_btn.x+25, bfs_btn.y+10))
    screen.blit(button_font.render("Reset", True, WHITE), (reset_btn.x+20, reset_btn.y+10))
    screen.blit(button_font.render("New", True, WHITE), (gen_btn.x+30, gen_btn.y+10))

# Solve with DFS
def solve_dfs(grid):
    empty = find_empty(grid)
    if not empty:
        return True
    r, c = empty
    for n in range(1, 10):
        if is_valid(grid, r, c, n):
            grid[r][c] = n
            draw_grid(grid, highlight=(r,c))
            draw_buttons()
            pygame.display.flip()
            pygame.time.delay(NUM_DELAY)
            if solve_dfs(grid):
                return True
            
            grid[r][c] = 0
            draw_grid(grid, highlight=(r,c))
            draw_buttons()
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
                draw_grid(grid, highlight=(i,j))
                draw_buttons()
                pygame.display.flip()
                pygame.time.delay(NUM_DELAY)
                
# Main Loop
original = generate_puzzle(holes=40)
grid     = [row[:] for row in original]
solving  = False
solved   = False
method   = None
running  = True

while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if dfs_btn.collidepoint(e.pos) and not solving:
                method  = "DFS"
                solving = True
            elif bfs_btn.collidepoint(e.pos) and not solving:
                method  = "BFS"
                solving = True
            elif reset_btn.collidepoint(e.pos):
                grid    = [row[:] for row in original]
                solving = solved = False
            elif gen_btn.collidepoint(e.pos):
                original = generate_puzzle(holes=40)
                grid     = [row[:] for row in original]
                solving  = solved = False

    draw_grid(grid)
    draw_buttons()
    pygame.display.flip()

    if solving and not solved:
        if method == "DFS":
            solved = solve_dfs(grid)
        elif method == "BFS":
            solution = solve_bfs(grid)
            if solution:
                animate_solution(grid, solution)
                solved = True
                
        solving = False

    clock.tick(60)

pygame.quit()

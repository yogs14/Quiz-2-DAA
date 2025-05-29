import pygame
import random
import copy
from collections import deque
import time

# Constants
GRID_SIZE    = 9
CELL_SIZE    = 60
BOARD_PIX    = GRID_SIZE * CELL_SIZE

# --- Layout For Side-by-Side Tree View ---
TREE_AREA_WIDTH = 400  # Width for the tree visualization area
TOTAL_WIDTH     = BOARD_PIX + TREE_AREA_WIDTH # Grid + Tree
BUTTON_AREA     = 60 # Height for the button panel below grid/tree
SCREEN_HEIGHT   = BOARD_PIX + BUTTON_AREA # Main content area (grid/tree) is BOARD_PIX high

GRID_RECT = pygame.Rect(0, 0, BOARD_PIX, BOARD_PIX)
TREE_DISPLAY_RECT = pygame.Rect(BOARD_PIX, 0, TREE_AREA_WIDTH, BOARD_PIX) # Tree beside grid
# --- End Layout Constants ---


WHITE        = (255, 255, 255)
BLACK        = (  0,   0,   0)
GRAY         = (200, 200, 200)
BLUE         = (100, 100, 255) # Color for nodes being tried
GREEN        = (  0, 200,   0) # Color for main buttons
RED          = (200,   0,   0) # Color for reset and backtracked nodes
ORANGE       = (255, 140,   0)
HOVER_COLOR  = (255, 180,   0)
CLICK_COLOR  = (200, 100,   0)
POPUP_BG_COLOR = (150, 150, 150, 180)
POPUP_TEXT_COLOR = (255, 255, 255)
NUM_DELAY    = 50 
POPUP_DURATION = 3

# --- Tree Visualization Constants (adapted for live view) ---
LIVE_TREE_NODE_RADIUS = 12 # Smaller nodes for denser tree
LIVE_TREE_X_SPACING = 70
LIVE_TREE_Y_SPACING = 55
LIVE_TREE_NODE_COLOR_TRYING = BLUE # (100, 180, 250)
LIVE_TREE_NODE_COLOR_SOLUTION = (60, 220, 60) # Bright Green for solution path
LIVE_TREE_NODE_COLOR_BACKTRACKED = RED # (250, 100, 100)
LIVE_TREE_LINE_COLOR = (200, 200, 200)
LIVE_TREE_LABEL_COLOR = BLACK
# --- End Tree Visualization Constants ---

# Game States
MENU         = 0
PLAYING      = 1
# TREE_VIEW state is removed

# Music file path
MUSIC_FILE   = 'kids-game-gaming-background-music-295075.mp3'
COUNT_SOUND_FILE = 'bubble-pop-2-293341.mp3'

# --- Global variables for live DFS tree ---
live_tree_nodes = []
_live_node_id_counter = 0
final_solution_node_ids = set() # Set of node IDs on the final solution path for DFS
# --- End Global live tree vars ---

# Generate Random Sudoku (functions remain the same)
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

def backtrack_fill(grid): # Used for initial puzzle generation
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                for n in range(1, 10):
                    if is_valid(grid, i, j, n):
                        grid[i][j] = n
                        if backtrack_fill(grid): return True
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
            if grid[i][j] == 0: return i, j
    return None

# Pygame Setup
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((TOTAL_WIDTH, SCREEN_HEIGHT)) # Adjusted width
pygame.display.set_caption("Sudoku Solver with Live DFS Tree")
font         = pygame.font.SysFont(None, 40)
button_font  = pygame.font.SysFont(None, 30)
title_font   = pygame.font.SysFont(None, 72)
live_tree_font = pygame.font.SysFont(None, 18) # Smaller font for tree nodes
clock        = pygame.time.Clock()

# Button Rectangles (Adjusted for new TOTAL_WIDTH if needed, placed under GRID_RECT)
BTN_WIDTH = 100
BTN_GAP = 15
# Buttons will be placed relative to (0, BOARD_PIX)
dfs_btn      = pygame.Rect(BTN_GAP,  BOARD_PIX + 10, BTN_WIDTH, 40)
bfs_btn      = pygame.Rect(dfs_btn.right + BTN_GAP, BOARD_PIX + 10, BTN_WIDTH, 40)
reset_btn    = pygame.Rect(bfs_btn.right + BTN_GAP, BOARD_PIX + 10, BTN_WIDTH, 40)
gen_btn      = pygame.Rect(reset_btn.right + BTN_GAP, BOARD_PIX + 10, BTN_WIDTH, 40)
# No separate "View Tree" button as it's live

# Menu Buttons
play_btn     = pygame.Rect(TOTAL_WIDTH // 2 - 75, SCREEN_HEIGHT // 2 - 30, 150, 60)
exit_btn     = pygame.Rect(TOTAL_WIDTH // 2 - 75, SCREEN_HEIGHT // 2 + 50, 150, 60)


# Load Music & Sounds (remains the same)
try:
    pygame.mixer.music.load(MUSIC_FILE)
    pygame.mixer.music.set_volume(0.5)
except pygame.error as e:
    print(f"Could not load music file: {e}")
count_sound = None
try:
    count_sound = pygame.mixer.Sound(COUNT_SOUND_FILE)
    count_sound.set_volume(0.7)
except pygame.error as e:
    print(f"Could not load count sound file: {e}")


# --- Live Tree Node ID Generator ---
def get_new_live_node_id():
    global _live_node_id_counter
    _live_node_id_counter += 1
    return _live_node_id_counter
# --- End ID Generator ---


# --- Drawing Functions ---
def draw_grid_in_area(grid_data, highlight_cell, area_rect):
    # Erase previous grid area - done by redraw_entire_solving_screen
    # pygame.draw.rect(screen, WHITE, area_rect) # Fill grid background
    for i in range(9):
        for j in range(9):
            x_abs = area_rect.left + j * CELL_SIZE
            y_abs = area_rect.top + i * CELL_SIZE
            
            # Draw cell background (e.g., if part of highlight)
            if highlight_cell == (i, j):
                pygame.draw.rect(screen, BLUE, (x_abs, y_abs, CELL_SIZE, CELL_SIZE))
            
            num = grid_data[i][j]
            if num != 0:
                txt_surf = font.render(str(num), True, BLACK)
                screen.blit(txt_surf, (x_abs + 20, y_abs + 10))
    
    for i in range(10): # Draw grid lines
        line_width = 3 if i % 3 == 0 else 1
        # Horizontal lines
        pygame.draw.line(screen, BLACK, (area_rect.left, area_rect.top + i * CELL_SIZE), \
                         (area_rect.right, area_rect.top + i * CELL_SIZE), line_width)
        # Vertical lines
        pygame.draw.line(screen, BLACK, (area_rect.left + i * CELL_SIZE, area_rect.top), \
                         (area_rect.left + i * CELL_SIZE, area_rect.bottom), line_width)

def draw_live_tree(tree_nodes_list, display_rect, solved_node_ids):
    # Erase previous tree area - done by redraw_entire_solving_screen
    # pygame.draw.rect(screen, GRAY, display_rect) # Fill tree background

    if not tree_nodes_list: return

    nodes_by_id = {node['id']: node for node in tree_nodes_list}
    
    # Calculate positions dynamically (simple layered, might need improvement for many nodes)
    nodes_at_depth = {}
    max_depth_in_tree = 0
    for node in tree_nodes_list:
        d = node['depth']
        max_depth_in_tree = max(max_depth_in_tree, d)
        if d not in nodes_at_depth: nodes_at_depth[d] = []
        nodes_at_depth[d].append(node['id'])

    for depth, ids_at_this_depth in nodes_at_depth.items():
        num_nodes = len(ids_at_this_depth)
        y_pos_abs = display_rect.top + LIVE_TREE_Y_SPACING + (depth * LIVE_TREE_Y_SPACING)
        if y_pos_abs > display_rect.bottom - LIVE_TREE_NODE_RADIUS: # Prune if too deep for display
            continue

        for i, node_id in enumerate(ids_at_this_depth):
            node = nodes_by_id[node_id]
            x_pos_abs = display_rect.left + (i + 1) * (display_rect.width / (num_nodes + 1))
            node['pos'] = (int(x_pos_abs), int(y_pos_abs))

    # Draw lines
    for node in tree_nodes_list:
        if node.get('parent_id') is not None and node['parent_id'] in nodes_by_id:
            parent_node = nodes_by_id[node['parent_id']]
            if 'pos' in node and 'pos' in parent_node:
                 # Ensure nodes are within drawable Y range
                if node['pos'][1] <= display_rect.bottom - LIVE_TREE_NODE_RADIUS and \
                   parent_node['pos'][1] <= display_rect.bottom - LIVE_TREE_NODE_RADIUS:
                    pygame.draw.line(screen, LIVE_TREE_LINE_COLOR, node['pos'], parent_node['pos'], 1)
    
    # Draw nodes and labels
    for node in tree_nodes_list:
        if 'pos' in node and node['pos'][1] <= display_rect.bottom - LIVE_TREE_NODE_RADIUS: # Check Y bound
            color = LIVE_TREE_NODE_COLOR_TRYING
            if node['id'] in solved_node_ids:
                color = LIVE_TREE_NODE_COLOR_SOLUTION
            elif node.get('status') == 'backtracked':
                color = LIVE_TREE_NODE_COLOR_BACKTRACKED
            elif node.get('status') == 'root':
                color = GRAY
            
            pygame.draw.circle(screen, color, node['pos'], LIVE_TREE_NODE_RADIUS)
            pygame.draw.circle(screen, BLACK, node['pos'], LIVE_TREE_NODE_RADIUS, 1) # Border
            
            label_surf = live_tree_font.render(node['label'], True, LIVE_TREE_LABEL_COLOR)
            label_rect = label_surf.get_rect(center=node['pos'])
            screen.blit(label_surf, label_rect)


def draw_main_buttons(mouse_pos, mouse_click_state): # For buttons under grid/tree
    # DFS Button
    color_dfs = ORANGE
    if dfs_btn.collidepoint(mouse_pos): color_dfs = HOVER_COLOR
    if dfs_btn.collidepoint(mouse_pos) and mouse_click_state[0]: color_dfs = CLICK_COLOR
    pygame.draw.rect(screen, color_dfs, dfs_btn)
    screen.blit(button_font.render("DFS", True, WHITE), (dfs_btn.x + BTN_WIDTH//2 - 20, dfs_btn.y + 10))

    # BFS Button
    color_bfs = ORANGE
    if bfs_btn.collidepoint(mouse_pos): color_bfs = HOVER_COLOR
    if bfs_btn.collidepoint(mouse_pos) and mouse_click_state[0]: color_bfs = CLICK_COLOR
    pygame.draw.rect(screen, color_bfs, bfs_btn)
    screen.blit(button_font.render("BFS", True, WHITE), (bfs_btn.x + BTN_WIDTH//2 - 20, bfs_btn.y + 10))

    # Reset Button
    color_reset = RED
    if reset_btn.collidepoint(mouse_pos): color_reset = (255,100,100)
    if reset_btn.collidepoint(mouse_pos) and mouse_click_state[0]: color_reset = (180,0,0)
    pygame.draw.rect(screen, color_reset, reset_btn)
    screen.blit(button_font.render("Reset", True, WHITE), (reset_btn.x + BTN_WIDTH//2 - 28, reset_btn.y + 10))

    # New Button
    color_gen = GREEN
    if gen_btn.collidepoint(mouse_pos): color_gen = (100,255,100)
    if gen_btn.collidepoint(mouse_pos) and mouse_click_state[0]: color_gen = (0,150,0)
    pygame.draw.rect(screen, color_gen, gen_btn)
    screen.blit(button_font.render("New", True, WHITE), (gen_btn.x + BTN_WIDTH//2 - 22, gen_btn.y + 10))

def draw_menu_screen(mouse_pos, mouse_click_state): # Adjusted for new screen size
    screen.fill(GRAY)
    title_text = title_font.render("Sudoku Solver", True, BLACK)
    title_rect = title_text.get_rect(center=(TOTAL_WIDTH // 2, SCREEN_HEIGHT // 2 - 150))
    screen.blit(title_text, title_rect)
    # Play Button
    color_play = GREEN
    if play_btn.collidepoint(mouse_pos): color_play = (100,255,100)
    if play_btn.collidepoint(mouse_pos) and mouse_click_state[0]: color_play = (0,150,0)
    pygame.draw.rect(screen, color_play, play_btn)
    play_text = button_font.render("Play", True, WHITE)
    screen.blit(play_text, play_text.get_rect(center=play_btn.center))
    # Exit Button
    color_exit = RED
    if exit_btn.collidepoint(mouse_pos): color_exit = (255,100,100)
    if exit_btn.collidepoint(mouse_pos) and mouse_click_state[0]: color_exit = (180,0,0)
    pygame.draw.rect(screen, color_exit, exit_btn)
    exit_text = button_font.render("Exit", True, WHITE)
    screen.blit(exit_text, exit_text.get_rect(center=exit_btn.center))

def draw_popup_message(message_str): # Standard popup
    popup_surf = pygame.Surface((TOTAL_WIDTH * 0.5, SCREEN_HEIGHT * 0.2), pygame.SRCALPHA)
    popup_surf.fill(POPUP_BG_COLOR)
    popup_text_surf = font.render(message_str, True, POPUP_TEXT_COLOR)
    text_rect = popup_text_surf.get_rect(center=(popup_surf.get_width()//2, popup_surf.get_height()//2))
    popup_surf.blit(popup_text_surf, text_rect)
    screen.blit(popup_surf, popup_surf.get_rect(center=(TOTAL_WIDTH//2, SCREEN_HEIGHT//2)))


# --- Central Drawing Function for Solving Screen (Grid + Tree + Buttons) ---
def redraw_entire_solving_screen(current_grid, highlight_coord, tree_data, solved_nodes, mouse_pos, mouse_clicks):
    screen.fill(WHITE) # Background for the whole solving area (grid + tree)
    pygame.draw.rect(screen, (230,230,250), TREE_DISPLAY_RECT) # Light background for tree area

    draw_grid_in_area(current_grid, highlight_coord, GRID_RECT)
    draw_live_tree(tree_data, TREE_DISPLAY_RECT, solved_nodes)
    draw_main_buttons(mouse_pos, mouse_clicks) # Buttons drawn last, on top of everything if they overlap BOARD_PIX level
    # Note: Buttons are drawn in their own area below BOARD_PIX based on current rects.
    # If they were to overlap, this order matters.
# --- End Central Drawing ---


# --- DFS Solver with Integrated Live Tree Building & Drawing ---
def solve_dfs_with_live_tree(current_grid, parent_tree_node_id, depth, solved_node_ids_set):
    global live_tree_nodes, _live_node_id_counter # Use globals

    # Handle pygame events to keep window responsive & allow quit
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit() # Exit gracefully

    empty_cell = find_empty(current_grid)
    if not empty_cell: # Solved
        return True

    r, c = empty_cell
    original_val = current_grid[r][c] # Should be 0

    # Add this exploration level (cell (r,c)) as a conceptual parent if not already represented
    # For simplicity, each number tried will be a child of 'parent_tree_node_id'

    for n in range(1, 10):
        if is_valid(current_grid, r, c, n):
            current_grid[r][c] = n
            if count_sound: count_sound.play()

            node_id = get_new_live_node_id()
            live_tree_nodes.append({
                'id': node_id, 'parent_id': parent_tree_node_id,
                'label': f'({r},{c})={n}', 'depth': depth,
                'status': 'trying', # Will be updated
            })
            
            # Redraw everything
            redraw_entire_solving_screen(current_grid, (r,c), live_tree_nodes, solved_node_ids_set, pygame.mouse.get_pos(), pygame.mouse.get_pressed())
            pygame.display.flip()
            pygame.time.delay(NUM_DELAY)

            if solve_dfs_with_live_tree(current_grid, node_id, depth + 1, solved_node_ids_set):
                solved_node_ids_set.add(node_id) # This node is on solution path
                # Find and update status in list (less efficient but ok for few nodes)
                for node_obj in live_tree_nodes:
                    if node_obj['id'] == node_id: node_obj['status'] = 'solution'; break
                return True # Propagate success up

            # Backtrack
            current_grid[r][c] = original_val # Reset cell
            if count_sound: count_sound.play()
            # Update node status to backtracked
            for node_obj in live_tree_nodes:
                if node_obj['id'] == node_id: node_obj['status'] = 'backtracked'; break
            
            # Redraw after backtrack
            redraw_entire_solving_screen(current_grid, (r,c), live_tree_nodes, solved_node_ids_set, pygame.mouse.get_pos(), pygame.mouse.get_pressed())
            pygame.display.flip()
            pygame.time.delay(NUM_DELAY)
            
    return False # No number worked for this cell (r,c)
# --- End DFS Solver ---


# BFS Solver (remains mostly for animation, no live tree for BFS yet)
def solve_bfs_for_animation(initial_grid_state):
    queue = deque([initial_grid_state])
    visited_bfs_solve = {tuple(map(tuple, initial_grid_state))}

    while queue:
        current_grid_bfs = queue.popleft()
        empty_cell = find_empty(current_grid_bfs)
        if not empty_cell: return current_grid_bfs
        r, c = empty_cell
        for n in range(1, 10):
            if is_valid(current_grid_bfs, r, c, n):
                new_grid_bfs = copy.deepcopy(current_grid_bfs)
                new_grid_bfs[r][c] = n
                new_grid_key = tuple(map(tuple, new_grid_bfs))
                if new_grid_key not in visited_bfs_solve:
                    visited_bfs_solve.add(new_grid_key)
                    queue.append(new_grid_bfs)
    return None

def animate_bfs_solution(grid_to_animate_on, solution_grid): # For BFS
    # For BFS, tree is not shown live. Grid animation only.
    for i in range(9):
        for j in range(9):
            if grid_to_animate_on[i][j] == 0 and solution_grid[i][j] != 0:
                grid_to_animate_on[i][j] = solution_grid[i][j]
                if count_sound: count_sound.play()
                
                # Redraw only grid and buttons for BFS animation
                screen.fill(WHITE) # Clear screen
                draw_grid_in_area(grid_to_animate_on, (i,j), GRID_RECT)
                # Optionally, draw a placeholder or message in TREE_DISPLAY_RECT for BFS
                bfs_msg_surf = font.render("BFS Solving (No Live Tree)", True, BLACK)
                screen.blit(bfs_msg_surf, bfs_msg_surf.get_rect(center=TREE_DISPLAY_RECT.center))
                draw_main_buttons(pygame.mouse.get_pos(), pygame.mouse.get_pressed())
                pygame.display.flip()
                pygame.time.delay(NUM_DELAY)


# Main Loop
original_puzzle = generate_puzzle(holes=40)
current_grid_state = [row[:] for row in original_puzzle]
is_solving = False
is_solved = False
solve_method = None # "DFS" or "BFS"
game_running = True
current_game_state = MENU
timer_start_time = 0.0
solve_time_duration = 0.0

popup_active_flag = False
popup_message_text = ""
popup_disappear_time = 0.0

if current_game_state == MENU and not pygame.mixer.music.get_busy():
    try: pygame.mixer.music.play(-1)
    except pygame.error as e: print(f"Music error: {e}")

while game_running:
    current_mouse_pos = pygame.mouse.get_pos()
    current_mouse_clicks = pygame.mouse.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                if current_game_state == MENU:
                    if play_btn.collidepoint(event.pos):
                        current_game_state = PLAYING
                        pygame.mixer.music.stop()
                        original_puzzle = generate_puzzle(holes=40)
                        current_grid_state = [row[:] for row in original_puzzle]
                        is_solving = is_solved = False
                        popup_active_flag = False
                    elif exit_btn.collidepoint(event.pos):
                        game_running = False
                elif current_game_state == PLAYING:
                    if popup_active_flag: # Click dismisses popup
                        popup_active_flag = False
                    
                    if not is_solving: # Process buttons only if not already solving
                        if dfs_btn.collidepoint(event.pos):
                            solve_method = "DFS"
                            is_solving = True # This will now trigger the live solve in main draw loop
                            is_solved = False
                            timer_start_time = time.perf_counter()
                            current_grid_state = [row[:] for row in original_puzzle] # Solve on a fresh copy

                            # Initialize DFS live tree
                            live_tree_nodes = []
                            _live_node_id_counter = 0
                            final_solution_node_ids = set()
                            root_node_id = get_new_live_node_id()
                            live_tree_nodes.append({'id': root_node_id, 'parent_id': None, 
                                                    'label': 'DFS Root', 'depth': 0, 'status': 'root'})
                            
                            # The actual solving and drawing is now driven by solve_dfs_with_live_tree
                            # This call will block until solved or fully explored by the function
                            solution_was_found_dfs = solve_dfs_with_live_tree(current_grid_state, root_node_id, 1, final_solution_node_ids)
                            is_solved = solution_was_found_dfs
                            if solution_was_found_dfs:
                                final_solution_node_ids.add(root_node_id) # Add root to solution path

                            is_solving = False # Mark as finished solving
                            solve_time_duration = time.perf_counter() - timer_start_time
                            popup_message_text = f"DFS: {'Solved' if is_solved else 'No Solution'} in {solve_time_duration:.3f}s"
                            popup_active_flag = True
                            popup_disappear_time = time.time() + POPUP_DURATION

                        elif bfs_btn.collidepoint(event.pos):
                            solve_method = "BFS"
                            is_solving = True # Regular BFS animation will run
                            is_solved = False
                            timer_start_time = time.perf_counter()
                            current_grid_state = [row[:] for row in original_puzzle] # Fresh copy
                            
                            # BFS does not use the live tree in this version
                            live_tree_nodes = [] # Clear any DFS tree
                            final_solution_node_ids = set()

                            solution_grid_bfs = solve_bfs_for_animation(copy.deepcopy(current_grid_state))
                            if solution_grid_bfs:
                                animate_bfs_solution(current_grid_state, solution_grid_bfs)
                                is_solved = True
                            
                            is_solving = False
                            solve_time_duration = time.perf_counter() - timer_start_time
                            popup_message_text = f"BFS: {'Solved' if is_solved else 'No Solution'} in {solve_time_duration:.3f}s"
                            popup_active_flag = True
                            popup_disappear_time = time.time() + POPUP_DURATION

                        elif reset_btn.collidepoint(event.pos):
                            current_grid_state = [row[:] for row in original_puzzle]
                            is_solving = is_solved = False
                            popup_active_flag = False
                            live_tree_nodes = [] # Clear tree
                        elif gen_btn.collidepoint(event.pos):
                            original_puzzle = generate_puzzle(holes=40)
                            current_grid_state = [row[:] for row in original_puzzle]
                            is_solving = is_solved = False
                            popup_active_flag = False
                            live_tree_nodes = [] # Clear tree

    # --- Main Drawing Logic ---
    if current_game_state == MENU:
        draw_menu_screen(current_mouse_pos, current_mouse_clicks)
        if not pygame.mixer.music.get_busy():
            try: pygame.mixer.music.play(-1)
            except pygame.error as e: print(f"Music error: {e}")
    elif current_game_state == PLAYING:
        if not is_solving: # If not actively in a blocking solve call (like DFS live)
            # This redraws the static state (e.g., after BFS animation or before any solve)
            redraw_entire_solving_screen(current_grid_state, None, live_tree_nodes, final_solution_node_ids, current_mouse_pos, current_mouse_clicks)
        # If is_solving is true for DFS, drawing is handled inside solve_dfs_with_live_tree.
        # If is_solving is true for BFS, drawing is handled inside animate_bfs_solution.

        if popup_active_flag:
            draw_popup_message(popup_message_text)
            if time.time() > popup_disappear_time:
                popup_active_flag = False
    
    if game_running : #only flip if not quit
        pygame.display.flip()
    clock.tick(60)

pygame.quit()
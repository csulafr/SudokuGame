import pygame, sys, time, random, copy, os

# -------------------------
# Configuration
# -------------------------
CELL = 60
GRID_SIZE = CELL * 9
SIDEBAR_WIDTH = 280
WINDOW_W = GRID_SIZE + SIDEBAR_WIDTH + 60
WINDOW_H = GRID_SIZE + 100
FPS = 60
ANIM_DELAY = 0.015

# Aesthetic Color Palette - Calm & Minimal
BG_COLOR = (250, 251, 252)
GRID_COLOR = (220, 225, 232)
GRID_BOLD = (130, 145, 165)
CELL_BG = (255, 255, 255)
CELL_PREFILLED = (242, 246, 252)
CELL_SELECTED = (254, 249, 241)
CELL_HOVER = (248, 250, 252)
CELL_WRONG = (254, 240, 240)
CELL_CORRECT = (240, 253, 244)
TEXT_PRIMARY = (30, 41, 59)
TEXT_SECONDARY = (100, 116, 139)
TEXT_PREFILLED = (71, 85, 105)
ACCENT_BLUE = (99, 102, 241)
ACCENT_GREEN = (34, 197, 94)
ACCENT_RED = (239, 68, 68)
ACCENT_PURPLE = (168, 85, 247)

# -------------------------
# File Utils
# -------------------------
def read_sudoku_file(path):
    grid = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            row = [int(x) for x in line.split()]
            grid.append(row)
    if len(grid) != 9 or any(len(r) != 9 for r in grid):
        raise ValueError("File must contain 9x9 grid")
    return grid

def validate_sudoku_file(path):
    try:
        grid = []
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    row = [int(x) for x in line.split()]
                    if len(row) != 9:
                        return False, "Each row must have 9 columns"
                    if any(x < 0 or x > 9 for x in row):
                        return False, "Numbers must be 0-9"
                    grid.append(row)
                except ValueError:
                    return False, "File contains non-numeric characters"
        if len(grid) != 9:
            return False, f"File must have 9 rows (found {len(grid)})"
        return True, grid
    except Exception as e:
        return False, str(e)

def write_grid_file(grid, path):
    with open(path, "w") as f:
        for r in grid:
            f.write(" ".join(str(x) for x in r) + "\n")

def open_file_dialog():
    """Open file dialog without Tkinter - using pygame's event system"""
    # This will be handled by drag-and-drop
    return None

# -------------------------
# Sudoku Logic
# -------------------------
def valid(grid, r, c, val):
    if val in grid[r]: return False
    for i in range(9):
        if grid[i][c] == val: return False
    sr, sc = 3*(r//3), 3*(c//3)
    for i in range(sr, sr+3):
        for j in range(sc, sc+3):
            if grid[i][j] == val: return False
    return True

def find_empty(grid):
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                return (i,j)
    return None

def solve_backtracking_nonvisual(puzzle, timeout=30.0):
    g = copy.deepcopy(puzzle)
    start = time.perf_counter()
    timed_out = False
    def rec():
        nonlocal timed_out
        if timeout and (time.perf_counter()-start) > timeout:
            timed_out = True
            return False
        e = find_empty(g)
        if not e: return True
        r,c = e
        for v in range(1,10):
            if valid(g, r, c, v):
                g[r][c] = v
                if rec(): return True
                g[r][c] = 0
        return False
    ok = rec()
    elapsed = (time.perf_counter()-start)*1000.0
    return (ok and not timed_out, (copy.deepcopy(g) if ok else None), elapsed)

def domain(grid, r, c):
    if grid[r][c] != 0: return []
    s = set(range(1,10))
    s -= set(grid[r])
    s -= {grid[i][c] for i in range(9)}
    sr, sc = 3*(r//3), 3*(c//3)
    for i in range(sr, sr+3):
        for j in range(sc, sc+3):
            s.discard(grid[i][j])
    return list(s)

def solve_backtracking_mrv_nonvisual(puzzle, timeout=30.0):
    g = copy.deepcopy(puzzle)
    start = time.perf_counter()
    timed_out = False
    def rec():
        nonlocal timed_out
        if timeout and (time.perf_counter()-start) > timeout:
            timed_out = True
            return False
        empties = [(r,c) for r in range(9) for c in range(9) if g[r][c]==0]
        if not empties: return True
        best = None; best_dom = None
        for (r,c) in empties:
            dom = domain(g,r,c)
            if len(dom)==0: return False
            if best is None or len(dom) < len(best_dom):
                best = (r,c); best_dom = dom
        r,c = best
        for v in best_dom:
            g[r][c] = v
            if rec(): return True
            g[r][c] = 0
        return False
    ok = rec()
    elapsed = (time.perf_counter()-start)*1000.0
    return (ok and not timed_out, (copy.deepcopy(g) if ok else None), elapsed)

def count_solutions(grid, limit=2, timeout=1.0):
    g = copy.deepcopy(grid)
    cnt = 0
    start = time.perf_counter()
    def rec():
        nonlocal cnt
        if (time.perf_counter()-start) > timeout or cnt >= limit:
            return
        e = find_empty(g)
        if not e:
            cnt += 1
            return
        r,c = e
        for v in range(1,10):
            if valid(g,r,c,v):
                g[r][c] = v
                rec()
                g[r][c] = 0
                if cnt >= limit: return
    rec()
    return cnt

def generate_full_grid():
    grid = [[0]*9 for _ in range(9)]
    nums = list(range(1,10))
    def rec(pos=0):
        if pos==81: return True
        r,c = divmod(pos,9)
        if grid[r][c] != 0:
            return rec(pos+1)
        random.shuffle(nums)
        for v in nums:
            if valid(grid,r,c,v):
                grid[r][c] = v
                if rec(pos+1): return True
                grid[r][c] = 0
        return False
    rec()
    return grid

def generate_puzzle(difficulty="medium"):
    full = generate_full_grid()
    puzzle = copy.deepcopy(full)
    if difficulty=="easy":
        remove_target = random.randint(30, 36)
    elif difficulty=="hard":
        remove_target = random.randint(50, 56)
    else:
        remove_target = random.randint(40, 48)
    cells = [(r,c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    removed = 0
    attempts = 0
    for (r,c) in cells:
        if removed >= remove_target or attempts > 300:
            break
        attempts += 1
        backup = puzzle[r][c]
        puzzle[r][c] = 0
        solcount = count_solutions(puzzle, limit=2, timeout=0.5)
        if solcount != 1:
            puzzle[r][c] = backup
        else:
            removed += 1
    return puzzle, full

# -------------------------
# Pygame Setup
# -------------------------
pygame.init()
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
pygame.display.set_caption("Sudoku")
clock = pygame.time.Clock()

# Fonts - Clean & Modern
FONT_TITLE = pygame.font.SysFont("Arial", 28, bold=True)
FONT_CELL = pygame.font.SysFont("Arial", 32, bold=True)
FONT_BTN = pygame.font.SysFont("Arial", 15, bold=True)
FONT_SMALL = pygame.font.SysFont("Arial", 13)
FONT_TINY = pygame.font.SysFont("Arial", 11)

# -------------------------
# UI Components
# -------------------------
def draw_text(text, x, y, font, color=TEXT_PRIMARY, center=False):
    surf = font.render(text, True, color)
    if center:
        rect = surf.get_rect(center=(x, y))
    else:
        rect = surf.get_rect(topleft=(x, y))
    screen.blit(surf, rect)
    return rect

def draw_rounded_rect(surface, color, rect, radius=8):
    """Draw rounded rectangle"""
    x, y, w, h = rect
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def draw_button(text, x, y, w, h, color, hover_color=None, icon=None):
    mouse_pos = pygame.mouse.get_pos()
    is_hover = x <= mouse_pos[0] <= x+w and y <= mouse_pos[1] <= y+h
    
    btn_color = hover_color if (is_hover and hover_color) else color
    if is_hover and not hover_color:
        btn_color = tuple(min(c + 15, 255) for c in color)
    
    # Shadow
    shadow = pygame.Rect(x+2, y+2, w, h)
    draw_rounded_rect(screen, (0,0,0,20), shadow, 8)
    
    # Button
    draw_rounded_rect(screen, btn_color, (x, y, w, h), 8)
    
    # Text with icon
    text_x = x + w//2
    if icon:
        # Draw icon on the left
        icon_surf = FONT_BTN.render(icon, True, (255,255,255))
        icon_rect = icon_surf.get_rect(center=(x + 20, y + h//2))
        screen.blit(icon_surf, icon_rect)
        # Draw text shifted to the right
        text_surf = FONT_BTN.render(text, True, (255,255,255))
        text_rect = text_surf.get_rect(center=(x + w//2 + 10, y + h//2))
        screen.blit(text_surf, text_rect)
    else:
        draw_text(text, text_x, y + h//2, FONT_BTN, (255,255,255), center=True)
    
    return pygame.Rect(x, y, w, h)

def format_time(seconds):
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

# -------------------------
# Main Game Class
# -------------------------
class SudokuGame:
    def __init__(self):
        self.puzzle = [[0]*9 for _ in range(9)]
        self.solution = [[0]*9 for _ in range(9)]
        self.user_grid = [[0]*9 for _ in range(9)]
        self.prefilled = set()
        self.selected = None
        self.hover = None
        self.wrong_cells = set()
        self.correct_cells = set()
        self.start_time = time.time()
        self.elapsed = 0
        self.solving = False
        self.solved_time = None
        self.message = None
        self.message_time = 0
        self.difficulty = "file"
        self.drag_hover = False
        self.timer_paused = False
        self.pause_start = 0
        self.current_puzzle_name = "SudokuTest.txt"
        self.current_solution_name = "SolusiSudoku.txt"
        self.generate_counter = 0
        self.drop_counter = 0
        
        # Load from SudokuTest.txt first
        self.load_default_file()
    
    def load_default_file(self):
        """Load SudokuTest.txt on startup"""
        if os.path.exists("SudokuTest.txt"):
            try:
                self.puzzle = read_sudoku_file("SudokuTest.txt")
                self.user_grid = copy.deepcopy(self.puzzle)
                self.prefilled = {(r,c) for r in range(9) for c in range(9) if self.puzzle[r][c] != 0}
                self.selected = None
                self.wrong_cells.clear()
                self.correct_cells.clear()
                self.start_time = time.time()
                self.solving = False
                self.solved_time = None
                self.timer_paused = False
                self.difficulty = "file"
                self.current_puzzle_name = "SudokuTest.txt"
                self.current_solution_name = "SolusiSudoku.txt"
                
                # Try to solve to get solution
                ok, sol, _ = solve_backtracking_mrv_nonvisual(self.puzzle, timeout=10.0)
                if ok and sol:
                    self.solution = sol
                    self.show_message("Loaded SudokuTest.txt", ACCENT_GREEN)
                else:
                    self.show_message("Loaded file (no solution)", ACCENT_BLUE)
            except:
                # If file doesn't exist or error, generate puzzle
                self.new_puzzle("medium")
        else:
            # Generate default puzzle if file not found
            self.new_puzzle("medium")
    
    def get_next_generate_number(self):
        """Get next available generate number"""
        self.generate_counter += 1
        while os.path.exists(f"SudokuTest_generate({self.generate_counter}).txt"):
            self.generate_counter += 1
        return self.generate_counter
    
    def get_next_drop_number(self):
        """Get next available drop number"""
        self.drop_counter += 1
        while os.path.exists(f"SudokuTest_drop({self.drop_counter}).txt"):
            self.drop_counter += 1
        return self.drop_counter
    
    def new_puzzle(self, difficulty):
        self.difficulty = difficulty
        self.puzzle, self.solution = generate_puzzle(difficulty)
        self.user_grid = copy.deepcopy(self.puzzle)
        self.prefilled = {(r,c) for r in range(9) for c in range(9) if self.puzzle[r][c] != 0}
        self.selected = None
        self.wrong_cells.clear()
        self.correct_cells.clear()
        self.start_time = time.time()
        self.elapsed = 0
        self.solving = False
        self.solved_time = None
        self.timer_paused = False
        
        # Set file names for generated puzzle
        num = self.get_next_generate_number()
        self.current_puzzle_name = f"SudokuTest_generate({num}).txt"
        self.current_solution_name = f"SolusiSudoku_generate({num}).txt"
        
        # Save the generated puzzle
        write_grid_file(self.puzzle, self.current_puzzle_name)
        
        self.show_message(f"New {difficulty} puzzle!", ACCENT_GREEN)
    
    def load_from_file(self, filepath):
        try:
            is_valid, result = validate_sudoku_file(filepath)
            if is_valid:
                self.puzzle = result
                self.user_grid = copy.deepcopy(self.puzzle)
                self.prefilled = {(r,c) for r in range(9) for c in range(9) if self.puzzle[r][c] != 0}
                self.selected = None
                self.wrong_cells.clear()
                self.correct_cells.clear()
                self.start_time = time.time()
                self.solving = False
                self.solved_time = None
                self.timer_paused = False
                self.difficulty = "file"
                
                # Set file names for dropped file
                num = self.get_next_drop_number()
                self.current_puzzle_name = f"SudokuTest_drop({num}).txt"
                self.current_solution_name = f"SolusiSudoku_drop({num}).txt"
                
                # Save the dropped puzzle with new name
                write_grid_file(self.puzzle, self.current_puzzle_name)
                
                # Try to solve to get solution
                ok, sol, _ = solve_backtracking_mrv_nonvisual(self.puzzle, timeout=10.0)
                if ok and sol:
                    self.solution = sol
                    self.show_message(f"Loaded as drop({num})", ACCENT_GREEN)
                else:
                    self.show_message("Warning: Could not verify solution", ACCENT_RED)
                return True
            else:
                self.show_message(f"Invalid file: {result}", ACCENT_RED)
                return False
        except Exception as e:
            self.show_message(f"Error: {str(e)}", ACCENT_RED)
            return False
    
    def show_message(self, text, color=ACCENT_BLUE):
        self.message = (text, color)
        self.message_time = time.time()
    
    def check_answer(self):
        self.wrong_cells.clear()
        self.correct_cells.clear()
        all_correct = True
        
        for r in range(9):
            for c in range(9):
                if self.user_grid[r][c] != 0 and (r,c) not in self.prefilled:
                    if self.user_grid[r][c] != self.solution[r][c]:
                        self.wrong_cells.add((r,c))
                        all_correct = False
                    else:
                        self.correct_cells.add((r,c))
        
        is_complete = all(self.user_grid[r][c] != 0 for r in range(9) for c in range(9))
        
        if all_correct and is_complete:
            self.elapsed = time.time() - self.start_time
            self.solved_time = self.elapsed
            
            # Save solution when manually solved completely
            write_grid_file(self.user_grid, self.current_solution_name)
            
            self.show_message(f"Perfect! Solved in {format_time(self.elapsed)}", ACCENT_GREEN)
        elif self.wrong_cells:
            self.show_message(f"{len(self.wrong_cells)} mistakes found", ACCENT_RED)
        else:
            self.show_message("Correct so far! Keep going", ACCENT_BLUE)
    
    def solve_with_algo(self, algo="mrv"):
        # Pause timer
        if not self.timer_paused and not self.solved_time:
            self.timer_paused = True
            self.pause_start = time.time()
            self.elapsed = self.pause_start - self.start_time
        
        self.solving = True
        if algo == "backtracking":
            ok, sol, t = solve_backtracking_nonvisual(self.puzzle, timeout=30.0)
            algo_name = "Backtracking"
        else:
            ok, sol, t = solve_backtracking_mrv_nonvisual(self.puzzle, timeout=30.0)
            algo_name = "Backtracking+MRV"
        
        if ok and sol:
            self.user_grid = copy.deepcopy(sol)
            self.wrong_cells.clear()
            self.correct_cells.clear()
            
            # Save solution to file (only when solved successfully)
            write_grid_file(sol, self.current_solution_name)
            
            self.solved_time = self.elapsed
            self.show_message(f"Solved with {algo_name} in {t:.1f}ms | Saved!", ACCENT_GREEN)
        else:
            self.show_message("Failed to solve (timeout)", ACCENT_RED)
        
        self.solving = False
    
    def clear_inputs(self):
        for r in range(9):
            for c in range(9):
                if (r,c) not in self.prefilled:
                    self.user_grid[r][c] = 0
        self.wrong_cells.clear()
        self.correct_cells.clear()
        self.show_message("Cleared all inputs", ACCENT_BLUE)
    
    def draw_grid(self):
        """Draw the sudoku grid"""
        board_x = 30
        board_y = 50
        
        # Get mouse position for hover effect
        mx, my = pygame.mouse.get_pos()
        
        # Draw cells
        for r in range(9):
            for c in range(9):
                x = board_x + c * CELL
                y = board_y + r * CELL
                rect = pygame.Rect(x, y, CELL, CELL)
                
                # Determine cell color
                cell_color = CELL_BG
                if self.selected == (r,c):
                    cell_color = CELL_SELECTED
                elif rect.collidepoint(mx, my) and (r,c) not in self.prefilled:
                    cell_color = CELL_HOVER
                elif (r,c) in self.prefilled:
                    cell_color = CELL_PREFILLED
                elif (r,c) in self.wrong_cells:
                    cell_color = CELL_WRONG
                elif (r,c) in self.correct_cells:
                    cell_color = CELL_CORRECT
                
                pygame.draw.rect(screen, cell_color, rect)
                
                # Draw number
                val = self.user_grid[r][c]
                if val != 0:
                    color = TEXT_PREFILLED if (r,c) in self.prefilled else TEXT_PRIMARY
                    draw_text(str(val), x + CELL//2, y + CELL//2, FONT_CELL, color, center=True)
        
        # Draw grid lines
        for i in range(10):
            lw = 3 if i % 3 == 0 else 1
            color = GRID_BOLD if i % 3 == 0 else GRID_COLOR
            # Horizontal
            pygame.draw.line(screen, color, 
                           (board_x, board_y + i*CELL), 
                           (board_x + GRID_SIZE, board_y + i*CELL), lw)
            # Vertical
            pygame.draw.line(screen, color, 
                           (board_x + i*CELL, board_y), 
                           (board_x + i*CELL, board_y + GRID_SIZE), lw)
        
        return (board_x, board_y, GRID_SIZE, GRID_SIZE)
    
    def draw_sidebar(self):
        """Draw control panel"""
        sidebar_x = GRID_SIZE + 60
        y = 50
        
        # Title
        draw_text("SUDOKU", sidebar_x, y, FONT_TITLE, TEXT_PRIMARY)
        y += 45
        
        # Timer
        if not self.solved_time:
            if self.timer_paused:
                current_time = self.elapsed
            else:
                current_time = time.time() - self.start_time
        else:
            current_time = self.solved_time
        
        timer_text = format_time(current_time)
        timer_color = TEXT_SECONDARY if self.timer_paused else ACCENT_BLUE
        draw_text(timer_text, sidebar_x, y, FONT_TITLE, timer_color)
        if self.timer_paused:
            draw_text("PAUSED", sidebar_x + 100, y + 8, FONT_TINY, ACCENT_RED)
        y += 50
        
        # Difficulty buttons
        draw_text("New Puzzle", sidebar_x, y, FONT_SMALL, TEXT_SECONDARY)
        y += 25
        
        btn_w = 80
        btn_h = 32
        easy_color = ACCENT_GREEN if self.difficulty == "easy" else GRID_COLOR
        med_color = ACCENT_BLUE if self.difficulty == "medium" else GRID_COLOR
        hard_color = ACCENT_RED if self.difficulty == "hard" else GRID_COLOR
        
        easy_btn = draw_button("Easy", sidebar_x, y, btn_w, btn_h, easy_color)
        med_btn = draw_button("Med", sidebar_x + 90, y, btn_w, btn_h, med_color)
        hard_btn = draw_button("Hard", sidebar_x + 180, y, btn_w, btn_h, hard_color)
        y += 50
        
        # Action buttons
        check_btn = draw_button("Check", sidebar_x, y, 125, 40, ACCENT_GREEN)
        clear_btn = draw_button("Clear", sidebar_x + 135, y, 125, 40, ACCENT_RED)
        y += 55
        
        # Drag & Drop Zone
        drop_zone = pygame.Rect(sidebar_x, y, 260, 60)
        drop_color = ACCENT_PURPLE if not self.drag_hover else tuple(min(c + 30, 255) for c in ACCENT_PURPLE)
        
        # Drop zone background with dashed border effect
        pygame.draw.rect(screen, (255, 255, 255), drop_zone, border_radius=10)
        
        # Dashed border
        dash_length = 10
        gap_length = 5
        border_color = drop_color
        
        # Top border
        x_pos = drop_zone.left
        while x_pos < drop_zone.right:
            pygame.draw.line(screen, border_color, (x_pos, drop_zone.top), 
                           (min(x_pos + dash_length, drop_zone.right), drop_zone.top), 3)
            x_pos += dash_length + gap_length
        
        # Bottom border
        x_pos = drop_zone.left
        while x_pos < drop_zone.right:
            pygame.draw.line(screen, border_color, (x_pos, drop_zone.bottom), 
                           (min(x_pos + dash_length, drop_zone.right), drop_zone.bottom), 3)
            x_pos += dash_length + gap_length
        
        # Left border
        y_pos = drop_zone.top
        while y_pos < drop_zone.bottom:
            pygame.draw.line(screen, border_color, (drop_zone.left, y_pos), 
                           (drop_zone.left, min(y_pos + dash_length, drop_zone.bottom)), 3)
            y_pos += dash_length + gap_length
        
        # Right border
        y_pos = drop_zone.top
        while y_pos < drop_zone.bottom:
            pygame.draw.line(screen, border_color, (drop_zone.right, y_pos), 
                           (drop_zone.right, min(y_pos + dash_length, drop_zone.bottom)), 3)
            y_pos += dash_length + gap_length
        
        # Icon and text
        icon_y = drop_zone.centery - 15
        draw_text("📁", drop_zone.centerx, icon_y, FONT_TITLE, drop_color, center=True)
        draw_text("Drop .txt file here", drop_zone.centerx, icon_y + 30, FONT_TINY, TEXT_SECONDARY, center=True)
        
        y += 75
        
        # Solve buttons
        draw_text("Auto Solve", sidebar_x, y, FONT_SMALL, TEXT_SECONDARY)
        y += 25
        solve_bt = draw_button("Backtracking", sidebar_x, y, 125, 40, ACCENT_BLUE)
        solve_mrv = draw_button("Backtracking+MRV", sidebar_x + 135, y, 140, 40, ACCENT_BLUE)
        y += 55
        
        # Quit button
        quit_btn = draw_button("Quit Game", sidebar_x, y, 260, 40, ACCENT_RED)
        y += 55
        
        # Message display
        if self.message and (time.time() - self.message_time) < 3.0:
            text, color = self.message
            # Wrap text if too long
            if len(text) > 25:
                words = text.split()
                line1 = " ".join(words[:len(words)//2])
                line2 = " ".join(words[len(words)//2:])
                draw_text(line1, sidebar_x, y, FONT_TINY, color)
                draw_text(line2, sidebar_x, y + 15, FONT_TINY, color)
            else:
                draw_text(text, sidebar_x, y, FONT_SMALL, color)
        
        return {
            "easy": easy_btn,
            "medium": med_btn,
            "hard": hard_btn,
            "check": check_btn,
            "clear": clear_btn,
            "drop_zone": drop_zone,
            "solve_bt": solve_bt,
            "solve_mrv": solve_mrv,
            "quit": quit_btn
        }
    
    def draw(self):
        screen.fill(BG_COLOR)
        board_rect = self.draw_grid()
        buttons = self.draw_sidebar()
        
        # Instructions at bottom
        draw_text("Drag & drop .txt file to purple zone | Click cell & type 1-9 | Arrow keys to move", 
                 WINDOW_W//2, WINDOW_H - 20, FONT_TINY, TEXT_SECONDARY, center=True)
        
        return board_rect, buttons
    
    def handle_click(self, pos, board_rect, buttons):
        bx, by, bw, bh = board_rect
        mx, my = pos
        
        # Check grid click
        if bx <= mx <= bx+bw and by <= my <= by+bh:
            col = (mx - bx) // CELL
            row = (my - by) // CELL
            if (row, col) not in self.prefilled:
                self.selected = (row, col)
            else:
                self.selected = None
            return
        
        # Check buttons
        if buttons["easy"].collidepoint(pos):
            self.new_puzzle("easy")
        elif buttons["medium"].collidepoint(pos):
            self.new_puzzle("medium")
        elif buttons["hard"].collidepoint(pos):
            self.new_puzzle("hard")
        elif buttons["check"].collidepoint(pos):
            self.check_answer()
        elif buttons["clear"].collidepoint(pos):
            self.clear_inputs()
        elif buttons["solve_bt"].collidepoint(pos):
            self.solve_with_algo("backtracking")
        elif buttons["solve_mrv"].collidepoint(pos):
            self.solve_with_algo("mrv")
        elif buttons["quit"].collidepoint(pos):
            pygame.quit()
            sys.exit()
    
    def handle_key(self, key):
        if not self.selected:
            return
        
        r, c = self.selected
        
        # Number input
        if pygame.K_1 <= key <= pygame.K_9:
            val = key - pygame.K_0
            self.user_grid[r][c] = val
            self.wrong_cells.discard((r,c))
            self.correct_cells.discard((r,c))
        elif key in [pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_0]:
            self.user_grid[r][c] = 0
            self.wrong_cells.discard((r,c))
            self.correct_cells.discard((r,c))
        
        # Arrow keys
        elif key == pygame.K_UP and r > 0:
            nr = r - 1
            while nr >= 0 and (nr,c) in self.prefilled:
                nr -= 1
            if nr >= 0:
                self.selected = (nr, c)
        elif key == pygame.K_DOWN and r < 8:
            nr = r + 1
            while nr < 9 and (nr,c) in self.prefilled:
                nr += 1
            if nr < 9:
                self.selected = (nr, c)
        elif key == pygame.K_LEFT and c > 0:
            nc = c - 1
            while nc >= 0 and (r,nc) in self.prefilled:
                nc -= 1
            if nc >= 0:
                self.selected = (r, nc)
        elif key == pygame.K_RIGHT and c < 8:
            nc = c + 1
            while nc < 9 and (r,nc) in self.prefilled:
                nc += 1
            if nc < 9:
                self.selected = (r, nc)
    
    def handle_file_drop(self, filepath):
        """Handle dropped file"""
        self.load_from_file(filepath)

# -------------------------
# Main Loop
# -------------------------
def main():
    game = SudokuGame()
    
    # Enable file drop
    pygame.event.set_allowed([pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN, pygame.DROPFILE])
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.DROPFILE:
                # Handle file drop
                filepath = event.file
                game.handle_file_drop(filepath)
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                board_rect, buttons = game.draw()
                game.handle_click(event.pos, board_rect, buttons)
            
            elif event.type == pygame.KEYDOWN:
                game.handle_key(event.key)
        
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        pygame.quit()
        print("Error:", e)
        import traceback
        traceback.print_exc()
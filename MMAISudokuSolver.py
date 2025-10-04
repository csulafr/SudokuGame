import pygame, sys, time, random, copy, os

# ===========================================================================================
# KONFIGURASI APLIKASI
# ===========================================================================================
# Pengaturan dasar untuk tampilan dan performa game
CELL = 60                    # Ukuran setiap sel dalam pixel (60x60)
GRID_SIZE = CELL * 9         # Total ukuran grid 9x9 (540x540 pixel)
SIDEBAR_WIDTH = 280          # Lebar panel kontrol di samping
WINDOW_W = GRID_SIZE + SIDEBAR_WIDTH + 60  # Total lebar window (880px)
WINDOW_H = GRID_SIZE + 100   # Total tinggi window (640px)
FPS = 60                     # Frame per second untuk smooth animation
ANIM_DELAY = 0.015           # Delay 15ms antar step saat visualisasi solving

# ===========================================================================================
# PALET WARNA - DESAIN MINIMAL & MODERN
# ===========================================================================================
# Warna background dan grid
BG_COLOR = (250, 251, 252)      # Background utama (abu-abu sangat terang)
GRID_COLOR = (220, 225, 232)    # Garis grid tipis
GRID_BOLD = (130, 145, 165)     # Garis grid tebal (setiap 3 baris/kolom untuk subgrid)

# Warna sel berdasarkan state
CELL_BG = (255, 255, 255)       # Background sel kosong (putih bersih)
CELL_PREFILLED = (242, 246, 252)  # Sel prefilled/clue (biru muda)
CELL_SELECTED = (254, 249, 241)   # Sel yang sedang dipilih user (kuning muda)
CELL_HOVER = (248, 250, 252)      # Sel saat mouse hover (abu sangat terang)
CELL_WRONG = (254, 240, 240)      # Sel dengan jawaban salah (merah muda)
CELL_CORRECT = (240, 253, 244)    # Sel dengan jawaban benar (hijau muda)

# Warna teks
TEXT_PRIMARY = (30, 41, 59)       # Teks utama/angka user (hitam kebiruan)
TEXT_SECONDARY = (100, 116, 139)  # Teks sekunder/label (abu-abu)
TEXT_PREFILLED = (71, 85, 105)    # Teks angka prefilled (abu gelap)

# Warna aksen untuk tombol dan highlight
ACCENT_BLUE = (99, 102, 241)      # Biru - tombol medium & info
ACCENT_GREEN = (34, 197, 94)      # Hijau - tombol easy & sukses
ACCENT_RED = (239, 68, 68)        # Merah - tombol hard & error
ACCENT_PURPLE = (168, 85, 247)    # Ungu - drop zone & step counter

# ===========================================================================================
# FUNGSI UTILITAS FILE I/O
# ===========================================================================================

def read_sudoku_file(path):
    """
    Membaca file sudoku dari path yang diberikan.
    
    Format file yang diharapkan:
    - 9 baris
    - Setiap baris berisi 9 angka dipisah spasi
    - Angka 0 merepresentasikan sel kosong
    
    Args:
        path (str): Path ke file sudoku
    
    Returns:
        list: Grid 2D (9x9) berisi puzzle sudoku
    
    Raises:
        ValueError: Jika format file tidak valid (bukan 9x9)
    
    Contoh file:
        5 3 0 0 7 0 0 0 0
        6 0 0 1 9 5 0 0 0
        ... (7 baris lagi)
    """
    grid = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()  # Hapus whitespace di awal/akhir
            if not line: continue  # Skip baris kosong
            # Split by space dan convert setiap elemen ke integer
            row = [int(x) for x in line.split()]
            grid.append(row)
    
    # Validasi ukuran grid harus 9x9
    if len(grid) != 9 or any(len(r) != 9 for r in grid):
        raise ValueError("File must contain 9x9 grid")
    return grid

def validate_sudoku_file(path):
    """
    Validasi file sudoku sebelum dimuat ke dalam game.
    Mengecek format, ukuran, dan nilai angka.
    
    Args:
        path (str): Path ke file yang akan divalidasi
    
    Returns:
        tuple: (bool, result)
            - Jika valid: (True, grid)
            - Jika tidak valid: (False, error_message)
    
    Validasi yang dilakukan:
    1. File bisa dibuka dan dibaca
    2. Setiap baris punya 9 kolom
    3. Semua nilai adalah angka 0-9
    4. Total 9 baris
    """
    try:
        grid = []
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    row = [int(x) for x in line.split()]
                    
                    # Cek jumlah kolom per baris
                    if len(row) != 9:
                        return False, "Each row must have 9 columns"
                    
                    # Cek range angka (0-9 saja yang valid)
                    if any(x < 0 or x > 9 for x in row):
                        return False, "Numbers must be 0-9"
                    
                    grid.append(row)
                except ValueError:
                    # Terjadi jika ada karakter non-numerik
                    return False, "File contains non-numeric characters"
        
        # Cek jumlah baris total
        if len(grid) != 9:
            return False, f"File must have 9 rows (found {len(grid)})"
        
        return True, grid
    except Exception as e:
        # Catch error lain (file not found, permission denied, dll)
        return False, str(e)

def write_grid_file(grid, path):
    """
    Menyimpan grid sudoku ke file dengan format yang sama.
    
    Args:
        grid (list): Grid 2D (9x9) berisi sudoku
        path (str): Path file tujuan untuk menyimpan
    
    Format output:
    - Setiap baris dipisah newline
    - Angka dalam satu baris dipisah spasi
    """
    with open(path, "w") as f:
        for r in grid:
            # Join setiap angka dengan spasi, tambah newline di akhir
            f.write(" ".join(str(x) for x in r) + "\n")

# ===========================================================================================
# LOGIKA SUDOKU - VALIDASI & SOLVING
# ===========================================================================================

def valid(grid, r, c, val):
    """
    Cek apakah nilai 'val' valid untuk diletakkan di posisi (r, c).
    
    Aturan Sudoku yang dicek:
    1. Tidak ada duplikat di baris yang sama
    2. Tidak ada duplikat di kolom yang sama
    3. Tidak ada duplikat di subgrid 3x3 yang sama
    
    Args:
        grid (list): Grid sudoku saat ini
        r (int): Index baris (0-8)
        c (int): Index kolom (0-8)
        val (int): Nilai yang akan dicek (1-9)
    
    Returns:
        bool: True jika valid (tidak melanggar aturan), False jika invalid
    """
    # Cek baris - pastikan val tidak sudah ada di baris r
    if val in grid[r]: 
        return False
    
    # Cek kolom - pastikan val tidak ada di kolom c
    for i in range(9):
        if grid[i][c] == val: 
            return False
    
    # Cek subgrid 3x3
    # Hitung posisi top-left dari subgrid tempat (r,c) berada
    # Contoh: jika r=5, c=7 maka sr=3, sc=6 (subgrid kanan-tengah)
    sr, sc = 3*(r//3), 3*(c//3)
    
    # Cek semua sel dalam subgrid 3x3
    for i in range(sr, sr+3):
        for j in range(sc, sc+3):
            if grid[i][j] == val: 
                return False
    
    # Semua pengecekan lolos, nilai valid
    return True

def find_empty(grid):
    """
    Mencari sel kosong pertama dalam grid (bernilai 0).
    Scanning dilakukan dari kiri ke kanan, atas ke bawah.
    
    Args:
        grid (list): Grid sudoku
    
    Returns:
        tuple or None: 
            - (row, col) jika ada sel kosong
            - None jika tidak ada (grid sudah penuh)
    """
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                return (i, j)
    return None

def domain(grid, r, c):
    """
    Menghitung domain (himpunan nilai yang mungkin) untuk sel (r, c).
    Digunakan untuk heuristik MRV (Minimum Remaining Values).
    
    Domain adalah nilai-nilai yang bisa diisi pada sel tanpa melanggar aturan.
    
    Args:
        grid (list): Grid sudoku saat ini
        r (int): Baris sel
        c (int): Kolom sel
    
    Returns:
        list: List nilai yang valid untuk sel tersebut
              Empty list jika sel sudah terisi atau tidak ada pilihan
    
    Cara kerja:
    1. Mulai dengan semua kemungkinan (1-9)
    2. Hapus nilai yang sudah ada di baris yang sama
    3. Hapus nilai yang sudah ada di kolom yang sama
    4. Hapus nilai yang sudah ada di subgrid 3x3 yang sama
    """
    if grid[r][c] != 0: 
        return []  # Sel sudah terisi, tidak perlu domain
    
    # Mulai dengan semua kemungkinan (1-9)
    s = set(range(1, 10))
    
    # Hapus nilai yang ada di baris yang sama
    s -= set(grid[r])
    
    # Hapus nilai yang ada di kolom yang sama
    s -= {grid[i][c] for i in range(9)}
    
    # Hapus nilai yang ada di subgrid 3x3 yang sama
    sr, sc = 3*(r//3), 3*(c//3)
    for i in range(sr, sr+3):
        for j in range(sc, sc+3):
            s.discard(grid[i][j])
    
    return list(s)

def count_solutions(grid, limit=2, timeout=1.0):
    """
    Menghitung jumlah solusi valid yang mungkin dari puzzle.
    Digunakan oleh generator untuk memastikan puzzle punya solusi unik.
    
    Args:
        grid (list): Grid sudoku yang akan dicek
        limit (int): Batas maksimal solusi yang dicari (default 2 cukup untuk cek uniqueness)
        timeout (float): Batas waktu pencarian dalam detik
    
    Returns:
        int: Jumlah solusi yang ditemukan (maksimal = limit)
    
    Catatan:
    - Puzzle valid harus punya tepat 1 solusi
    - Jika ditemukan 2 solusi, langsung stop (tidak unik)
    - Jika timeout, return jumlah solusi yang sudah ditemukan
    """
    g = copy.deepcopy(grid)  # Copy agar tidak mengubah grid asli
    cnt = 0
    start = time.perf_counter()
    
    def rec():
        """Fungsi rekursif untuk menghitung solusi"""
        nonlocal cnt
        
        # Stop jika timeout atau sudah menemukan cukup solusi
        if (time.perf_counter()-start) > timeout or cnt >= limit:
            return
        
        # Cari sel kosong
        e = find_empty(g)
        if not e:
            # Tidak ada sel kosong = ketemu satu solusi lengkap
            cnt += 1
            return
        
        r, c = e
        # Coba semua angka 1-9
        for v in range(1, 10):
            if valid(g, r, c, v):
                g[r][c] = v
                rec()  # Rekursif untuk cari solusi berikutnya
                g[r][c] = 0  # Backtrack untuk cari solusi alternatif
                if cnt >= limit: 
                    return  # Stop early jika sudah cukup
    
    rec()
    return cnt

# ===========================================================================================
# GENERATOR PUZZLE SUDOKU
# ===========================================================================================

def generate_full_grid():
    """
    Generate grid sudoku yang sudah terisi penuh dan valid (solved sudoku).
    Digunakan sebagai solusi, kemudian beberapa sel dihapus untuk membuat puzzle.
    
    Returns:
        list: Grid 9x9 yang valid dan terisi penuh
    
    Algoritma:
    1. Mulai dari grid kosong (semua 0)
    2. Untuk setiap posisi, coba angka random 1-9
    3. Jika valid (sesuai aturan sudoku), lanjut ke posisi berikutnya
    4. Jika tidak ada angka yang valid, backtrack ke posisi sebelumnya
    5. Ulangi sampai semua 81 sel terisi
    """
    grid = [[0]*9 for _ in range(9)]
    nums = list(range(1, 10))  # [1,2,3,4,5,6,7,8,9]
    
    def rec(pos=0):
        """
        Fungsi rekursif untuk generate grid.
        
        Args:
            pos (int): Posisi linear (0-80) dalam grid
                      pos 0 = (0,0), pos 8 = (0,8), pos 9 = (1,0), dst.
        """
        if pos == 81:  # 9x9 = 81 sel, berarti sudah selesai
            return True
        
        # Convert posisi linear ke koordinat (row, col)
        # divmod(pos, 9) = (pos // 9, pos % 9)
        r, c = divmod(pos, 9)
        
        if grid[r][c] != 0:  # Skip jika sel sudah terisi
            return rec(pos+1)
        
        random.shuffle(nums)  # Randomize urutan untuk variasi
        for v in nums:
            if valid(grid, r, c, v):
                grid[r][c] = v
                if rec(pos+1):  # Lanjut ke posisi berikutnya
                    return True
                grid[r][c] = 0  # Backtrack jika gagal
        
        return False  # Tidak ada solusi dari state ini
    
    rec()
    return grid

def generate_puzzle(difficulty="medium"):
    """
    Generate puzzle sudoku dengan tingkat kesulitan tertentu.
    
    Args:
        difficulty (str): "easy", "medium", atau "hard"
    
    Returns:
        tuple: (puzzle, solution)
            - puzzle: Grid dengan beberapa sel kosong (0)
            - solution: Grid lengkap (solved)
    
    Tingkat kesulitan berdasarkan jumlah sel yang dihapus:
    - Easy: 30-36 sel kosong (45-51 clue)
    - Medium: 40-48 sel kosong (33-41 clue)
    - Hard: 50-56 sel kosong (25-31 clue)
    
    Algoritma:
    1. Generate full grid (solved sudoku)
    2. Randomize urutan sel
    3. Coba hapus sel satu per satu
    4. Setiap kali hapus, cek apakah solusi masih unik
    5. Jika tidak unik, kembalikan sel tersebut
    6. Ulangi sampai mencapai target jumlah sel kosong
    """
    full = generate_full_grid()  # Generate solved grid sebagai solusi
    puzzle = copy.deepcopy(full)
    
    # Tentukan target jumlah sel yang dihapus berdasarkan difficulty
    if difficulty == "easy":
        remove_target = random.randint(30, 36)
    elif difficulty == "hard":
        remove_target = random.randint(50, 56)
    else:  # medium
        remove_target = random.randint(40, 48)
    
    # Randomize urutan sel untuk dihapus (agar distribusi acak)
    cells = [(r,c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    
    removed = 0
    attempts = 0
    
    # Coba hapus sel satu per satu
    for (r,c) in cells:
        # Stop jika sudah cukup atau terlalu banyak percobaan
        if removed >= remove_target or attempts > 300:
            break
        
        attempts += 1
        backup = puzzle[r][c]
        puzzle[r][c] = 0  # Hapus sel (set ke 0)
        
        # Cek apakah puzzle masih punya solusi unik
        solcount = count_solutions(puzzle, limit=2, timeout=0.5)
        
        if solcount != 1:
            # Solusi tidak unik atau tidak ada solusi, kembalikan sel
            puzzle[r][c] = backup
        else:
            # OK, solusi masih unik, bisa dihapus
            removed += 1
    
    return puzzle, full

# ===========================================================================================
# SETUP PYGAME
# ===========================================================================================
pygame.init()
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
pygame.display.set_caption("Sudoku")
clock = pygame.time.Clock()

# Font - Modern & Clean
FONT_TITLE = pygame.font.SysFont("Arial", 28, bold=True)   # Judul "SUDOKU"
FONT_CELL = pygame.font.SysFont("Arial", 32, bold=True)    # Angka dalam sel
FONT_BTN = pygame.font.SysFont("Arial", 15, bold=True)     # Teks tombol
FONT_SMALL = pygame.font.SysFont("Arial", 13)              # Label biasa
FONT_TINY = pygame.font.SysFont("Arial", 11)               # Instruksi kecil

# ===========================================================================================
# KOMPONEN UI - FUNGSI HELPER UNTUK DRAWING
# ===========================================================================================

def draw_text(text, x, y, font, color=TEXT_PRIMARY, center=False):
    """
    Render dan draw teks di layar.
    
    Args:
        text (str): String yang akan ditampilkan
        x, y (int): Posisi teks
        font (pygame.font.Font): Font yang digunakan
        color (tuple): Warna teks RGB
        center (bool): Jika True, (x,y) adalah center; jika False adalah topleft
    
    Returns:
        pygame.Rect: Rectangle dari teks (untuk collision detection)
    """
    surf = font.render(text, True, color)
    if center:
        rect = surf.get_rect(center=(x, y))
    else:
        rect = surf.get_rect(topleft=(x, y))
    screen.blit(surf, rect)
    return rect

def draw_rounded_rect(surface, color, rect, radius=8):
    """
    Draw rectangle dengan sudut rounded (melengkung).
    Membuat UI terlihat lebih modern dan friendly.
    
    Args:
        surface (pygame.Surface): Surface untuk drawing
        color (tuple): Warna rectangle RGB
        rect (tuple): (x, y, width, height)
        radius (int): Radius kelengkungan sudut dalam pixel
    """
    x, y, w, h = rect
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def draw_button(text, x, y, w, h, color, hover_color=None):
    """
    Draw tombol interaktif dengan efek hover dan shadow.
    
    Fitur:
    - Hover effect: warna berubah saat mouse di atas tombol
    - Shadow: bayangan di bawah tombol untuk kesan 3D
    - Rounded corners: sudut melengkung untuk estetika modern
    
    Args:
        text (str): Teks pada tombol
        x, y (int): Posisi topleft tombol
        w, h (int): Ukuran tombol (width, height)
        color (tuple): Warna default tombol
        hover_color (tuple, optional): Warna saat hover
    
    Returns:
        pygame.Rect: Rectangle tombol (untuk collision detection di event handler)
    """
    mouse_pos = pygame.mouse.get_pos()
    # Cek apakah mouse ada di atas tombol
    is_hover = x <= mouse_pos[0] <= x+w and y <= mouse_pos[1] <= y+h
    
    # Tentukan warna tombol
    btn_color = hover_color if (is_hover and hover_color) else color
    if is_hover and not hover_color:
        # Jika tidak ada hover_color, buat sedikit lebih terang
        btn_color = tuple(min(c + 15, 255) for c in color)
    
    # Draw shadow (offset 2px ke kanan bawah dengan opacity rendah)
    shadow = pygame.Rect(x+2, y+2, w, h)
    draw_rounded_rect(screen, (0,0,0,20), shadow, 8)
    
    # Draw tombol utama
    draw_rounded_rect(screen, btn_color, (x, y, w, h), 8)
    
    # Draw teks di tengah tombol (putih untuk kontras)
    text_x = x + w//2
    draw_text(text, text_x, y + h//2, FONT_BTN, (255,255,255), center=True)
    
    return pygame.Rect(x, y, w, h)

def format_time(seconds):
    """
    Format waktu dalam detik menjadi string MM:SS yang mudah dibaca.
    
    Args:
        seconds (float): Waktu dalam detik
    
    Returns:
        str: Format "MM:SS" (contoh: "05:34", "12:08")
    """
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"  # :02d = 2 digit dengan leading zero

# ===========================================================================================
# MAIN GAME CLASS - LOGIKA UTAMA APLIKASI
# ===========================================================================================

class SudokuGame:
    """
    Class utama untuk mengatur state dan logic game Sudoku.
    
    Responsibilities:
    - Manage puzzle state (puzzle, solution, user input)
    - Handle UI interaction (click, keyboard)
    - Visualize solving algorithms
    - File I/O (load, save)
    - Timer dan scoring
    
    Attributes:
        puzzle: Grid puzzle asli (9x9) dengan clue
        solution: Grid solusi yang benar
        user_grid: Grid yang sedang dikerjakan user
        prefilled: Set koordinat sel yang prefilled (tidak bisa diubah)
        selected: Koordinat sel yang sedang dipilih (row, col) atau None
        wrong_cells: Set koordinat sel dengan jawaban salah
        correct_cells: Set koordinat sel dengan jawaban benar
        start_time: Timestamp saat puzzle dimulai
        elapsed: Waktu yang sudah berlalu (saat pause atau selesai)
        timer_paused: Flag apakah timer sedang pause
        solved_time: Waktu saat puzzle berhasil diselesaikan
        visual_solving: Flag untuk mode visual solving
        step_count: Jumlah step saat visual solving
        message: Tuple (text, color) untuk notifikasi temporary
        difficulty: Tingkat kesulitan puzzle saat ini
        current_puzzle_name: Nama file puzzle yang sedang dimainkan
        current_solution_name: Nama file untuk menyimpan solusi
    """
    
    def __init__(self):
        """Inisialisasi game dengan default values"""
        # === GRID STATES ===
        self.puzzle = [[0]*9 for _ in range(9)]      # Puzzle asli dengan clue
        self.solution = [[0]*9 for _ in range(9)]    # Solusi yang benar
        self.user_grid = [[0]*9 for _ in range(9)]   # Input user
        self.prefilled = set()  # Set (row, col) yang prefilled/clue
        
        # === UI STATES ===
        self.selected = None    # Sel yang dipilih: (row, col) atau None
        self.hover = None       # Sel yang di-hover (tidak digunakan saat ini)
        self.wrong_cells = set()    # Sel dengan jawaban salah (highlight merah)
        self.correct_cells = set()  # Sel dengan jawaban benar (highlight hijau)
        
        # === TIMER ===
        self.start_time = time.time()  # Timestamp saat mulai
        self.elapsed = 0               # Waktu elapsed (untuk pause)
        self.timer_paused = False      # Flag pause
        self.pause_start = 0           # Timestamp saat mulai pause
        self.solved_time = None        # Waktu saat selesai (None jika belum)
        
        # === SOLVING STATE ===
        self.solving = False           # Flag sedang solving (deprecated)
        self.visual_solving = False    # Flag mode visual solving aktif
        self.step_count = 0            # Counter jumlah step/operasi
        self.current_step_info = ""    # Info step saat ini (untuk display)
        self.highlight_cell = None     # Sel yang di-highlight saat solving
        
        # === MESSAGE NOTIFICATION ===
        self.message = None            # (text, color) atau None
        self.message_time = 0          # Timestamp saat message muncul
        
        # === FILE MANAGEMENT ===
        self.difficulty = "file"                         # Difficulty saat ini
        self.drag_hover = False                          # Flag hover pada drop zone
        self.current_puzzle_name = "SudokuTest.txt"     # Nama file puzzle aktif
        self.current_solution_name = "SolusiSudoku.txt" # Nama file solusi
        self.generate_counter = 0      # Counter untuk auto-numbering generate
        self.drop_counter = 0          # Counter untuk auto-numbering drop
        
        # Load puzzle default saat startup
        self.load_default_file()
    
    def load_default_file(self):
        """
        Load file SudokuTest.txt saat aplikasi pertama kali dijalankan.
        Jika file tidak ada atau error, generate puzzle medium sebagai fallback.
        
        Flow:
        1. Cek apakah SudokuTest.txt ada
        2. Jika ada, baca dan load puzzle
        3. Solve puzzle untuk mendapatkan solusi
        4. Jika error atau file tidak ada, generate puzzle baru
        """
        if os.path.exists("SudokuTest.txt"):
            try:
                # Baca file
                self.puzzle = read_sudoku_file("SudokuTest.txt")
                self.user_grid = copy.deepcopy(self.puzzle)
                # Tandai sel yang prefilled (sudah ada angkanya)
                self.prefilled = {(r,c) for r in range(9) for c in range(9) 
                                  if self.puzzle[r][c] != 0}
                
                # Reset UI state
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
                
                # Solve untuk mendapatkan solusi (internal, tanpa visualisasi)
                self.solve_for_solution()
                self.show_message("Loaded SudokuTest.txt", ACCENT_GREEN)
            except:
                # Jika error (format salah, dll), generate puzzle baru
                self.new_puzzle("medium")
        else:
            # File tidak ada, generate puzzle baru
            self.new_puzzle("medium")
    
    def solve_for_solution(self):
        """
        Solve puzzle secara internal untuk mendapatkan solusi.
        Tidak menampilkan visualisasi, hanya untuk mendapatkan answer key.
        
        Menggunakan algoritma Backtracking + MRV untuk efisiensi.
        Result disimpan di self.solution.
        """
        g = copy.deepcopy(self.puzzle)
        
        def rec():
            """Fungsi rekursif untuk solving dengan MRV"""
            # Cari sel kosong
            e = find_empty(g)
            if not e: 
                return True  # Sudah selesai
            
            r, c = e
            # Dapatkan semua sel kosong
            empties = [(r2,c2) for r2 in range(9) for c2 in range(9) if g[r2][c2]==0]
            if not empties: 
                return True
            
            # MRV: Pilih sel dengan domain terkecil
            best = None
            best_dom = None
            for (r2,c2) in empties:
                dom = domain(g, r2, c2)
                if len(dom) == 0:
                    return False  # Dead-end
                if best is None or len(dom) < len(best_dom):
                    best = (r2, c2)
                    best_dom = dom
            
            r, c = best
            # Coba semua nilai dalam domain
            for v in best_dom:
                g[r][c] = v
                if rec(): 
                    return True
                g[r][c] = 0  # Backtrack
            
            return False
        
        # Jika berhasil solve, simpan ke solution
        if rec():
            self.solution = copy.deepcopy(g)
    
    def get_next_generate_number(self):
        """
        Mendapatkan nomor urut berikutnya untuk file generated puzzle.
        Auto-increment counter sampai menemukan nomor yang belum dipakai.
        
        Returns:
            int: Nomor urut berikutnya (contoh: 1, 2, 3, ...)
        
        Contoh output: SudokuTest_generate(1).txt, SudokuTest_generate(2).txt, dst.
        """
        self.generate_counter += 1
        # Loop sampai menemukan nomor yang belum dipakai
        while os.path.exists(f"SudokuTest_generate({self.generate_counter}).txt"):
            self.generate_counter += 1
        return self.generate_counter
    
    def get_next_drop_number(self):
        """
        Mendapatkan nomor urut berikutnya untuk file yang di-drop user.
        Auto-increment counter sampai menemukan nomor yang belum dipakai.
        
        Returns:
            int: Nomor urut berikutnya
        
        Contoh output: SudokuTest_drop(1).txt, SudokuTest_drop(2).txt, dst.
        """
        self.drop_counter += 1
        # Loop sampai menemukan nomor yang belum dipakai
        while os.path.exists(f"SudokuTest_drop({self.drop_counter}).txt"):
            self.drop_counter += 1
        return self.drop_counter
    
    def new_puzzle(self, difficulty):
        """
        Generate puzzle baru dengan tingkat kesulitan tertentu.
        Puzzle dan solusi disimpan otomatis ke file.
        
        Args:
            difficulty (str): "easy", "medium", atau "hard"
        
        Flow:
        1. Set difficulty
        2. Generate puzzle dan solusi
        3. Copy puzzle ke user_grid
        4. Tandai sel prefilled
        5. Reset semua state (timer, UI, dll)
        6. Generate nama file dengan auto-numbering
        7. Simpan puzzle ke file
        8. Show success message
        """
        self.difficulty = difficulty
        
        # Generate puzzle dan solusinya
        self.puzzle, self.solution = generate_puzzle(difficulty)
        self.user_grid = copy.deepcopy(self.puzzle)
        
        # Tandai sel yang prefilled (sudah ada angkanya)
        self.prefilled = {(r,c) for r in range(9) for c in range(9) 
                          if self.puzzle[r][c] != 0}
        
        # Reset UI state
        self.selected = None
        self.wrong_cells.clear()
        self.correct_cells.clear()
        self.start_time = time.time()
        self.elapsed = 0
        self.solving = False
        self.solved_time = None
        self.timer_paused = False
        
        # Generate nama file dengan auto-numbering
        num = self.get_next_generate_number()
        self.current_puzzle_name = f"SudokuTest_generate({num}).txt"
        self.current_solution_name = f"SolusiSudoku_generate({num}).txt"
        
        # Simpan puzzle ke file
        write_grid_file(self.puzzle, self.current_puzzle_name)
        
        # Show notification
        self.show_message(f"New {difficulty} puzzle!", ACCENT_GREEN)
    
    def load_from_file(self, filepath):
        """
        Load puzzle dari file yang di-drag-drop user.
        File divalidasi terlebih dahulu sebelum di-load.
        
        Args:
            filepath (str): Path ke file sudoku yang di-drop
        
        Returns:
            bool: True jika berhasil load, False jika gagal
        
        Flow:
        1. Validasi file (format, ukuran, nilai)
        2. Jika valid, load puzzle
        3. Solve puzzle untuk mendapatkan solusi
        4. Generate nama file baru dengan auto-numbering
        5. Simpan dengan nama baru
        6. Show success/error message
        """
        try:
            # Validasi file terlebih dahulu
            is_valid, result = validate_sudoku_file(filepath)
            
            if is_valid:
                # File valid, load puzzle
                self.puzzle = result
                self.user_grid = copy.deepcopy(self.puzzle)
                self.prefilled = {(r,c) for r in range(9) for c in range(9) 
                                  if self.puzzle[r][c] != 0}
                
                # Reset state
                self.selected = None
                self.wrong_cells.clear()
                self.correct_cells.clear()
                self.start_time = time.time()
                self.solving = False
                self.solved_time = None
                self.timer_paused = False
                self.difficulty = "file"
                
                # Generate nama file baru dengan auto-numbering
                num = self.get_next_drop_number()
                self.current_puzzle_name = f"SudokuTest_drop({num}).txt"
                self.current_solution_name = f"SolusiSudoku_drop({num}).txt"
                
                # Simpan puzzle dengan nama baru
                write_grid_file(self.puzzle, self.current_puzzle_name)
                
                # Solve untuk mendapatkan solusi
                self.solve_for_solution()
                
                # Show success message
                self.show_message(f"Loaded as drop({num})", ACCENT_GREEN)
                return True
            else:
                # File tidak valid, show error message
                self.show_message(f"Invalid file: {result}", ACCENT_RED)
                return False
                
        except Exception as e:
            # Catch error lain (file not found, permission, dll)
            self.show_message(f"Error: {str(e)}", ACCENT_RED)
            return False
    
    def show_message(self, text, color=ACCENT_BLUE):
        """
        Tampilkan notifikasi temporary di UI.
        Pesan akan otomatis hilang setelah 3 detik.
        
        Args:
            text (str): Teks pesan yang akan ditampilkan
            color (tuple): Warna teks RGB
        
        Digunakan untuk feedback seperti:
        - "New puzzle generated"
        - "3 mistakes found"
        - "Perfect! Solved in 05:34"
        - "Invalid file format"
        """
        self.message = (text, color)
        self.message_time = time.time()
    
    def check_answer(self):
        """
        Cek jawaban user dengan membandingkan dengan solusi.
        
        Proses:
        1. Clear highlight sebelumnya
        2. Loop semua sel yang diisi user (bukan prefilled)
        3. Bandingkan dengan solusi
        4. Tandai yang salah (merah) dan benar (hijau)
        5. Cek apakah puzzle sudah lengkap dan benar semua
        6. Show appropriate message
        7. Jika perfect, simpan solusi ke file
        
        Feedback:
        - "Perfect! Solved in MM:SS" - Semua benar dan lengkap
        - "X mistakes found" - Ada kesalahan
        - "Correct so far! Keep going" - Benar tapi belum lengkap
        """
        # Clear highlight sebelumnya
        self.wrong_cells.clear()
        self.correct_cells.clear()
        all_correct = True
        
        # Loop semua sel
        for r in range(9):
            for c in range(9):
                # Cek hanya sel yang diisi user (bukan prefilled)
                if self.user_grid[r][c] != 0 and (r,c) not in self.prefilled:
                    # Bandingkan dengan solusi
                    if self.user_grid[r][c] != self.solution[r][c]:
                        # Jawaban salah, tandai merah
                        self.wrong_cells.add((r,c))
                        all_correct = False
                    else:
                        # Jawaban benar, tandai hijau
                        self.correct_cells.add((r,c))
        
        # Cek apakah puzzle sudah lengkap terisi
        is_complete = all(self.user_grid[r][c] != 0 for r in range(9) for c in range(9))
        
        if all_correct and is_complete:
            # SUKSES! Puzzle solved perfectly
            self.elapsed = time.time() - self.start_time
            self.solved_time = self.elapsed
            
            # Simpan solusi ke file
            write_grid_file(self.user_grid, self.current_solution_name)
            
            # Show success message dengan waktu
            self.show_message(f"Perfect! Solved in {format_time(self.elapsed)}", ACCENT_GREEN)
            
        elif self.wrong_cells:
            # Ada kesalahan
            count = len(self.wrong_cells)
            self.show_message(f"{count} mistakes found", ACCENT_RED)
            
        else:
            # Benar tapi belum lengkap
            self.show_message("Correct so far! Keep going", ACCENT_BLUE)
    
    def solve_with_algo_visual(self, algo="mrv"):
        """
        Solve puzzle dengan algoritma tertentu DENGAN VISUALISASI step-by-step.
        User bisa melihat proses solving secara real-time.
        
        Args:
            algo (str): "backtracking" atau "mrv" (backtracking+MRV)
        
        Flow:
        1. Pause timer jika sedang berjalan
        2. Set flag visual_solving = True
        3. Reset counters dan highlights
        4. Copy puzzle ke grid temporary
        5. Start performance counter
        6. Run algoritma yang dipilih (dengan visualisasi)
        7. Hitung elapsed time
        8. Jika berhasil, update user_grid dan simpan solusi
        9. Show hasil (steps, time)
        10. Reset visual mode
        
        Visualisasi features:
        - Highlight sel yang sedang dicoba (kuning terang)
        - Counter steps real-time
        - Info sel dan nilai yang dicoba
        - Animasi backtrack (hijau → merah → kosong)
        - Performance measurement (milliseconds)
        """
        # Pause timer saat auto-solve (agar tidak unfair)
        if not self.timer_paused and not self.solved_time:
            self.timer_paused = True
            self.pause_start = time.time()
            self.elapsed = self.pause_start - self.start_time
        
        # Set visual solving mode
        self.visual_solving = True
        self.step_count = 0
        self.wrong_cells.clear()
        self.correct_cells.clear()
        
        # Copy puzzle untuk di-solve (agar tidak mengubah original)
        grid = copy.deepcopy(self.puzzle)
        
        # Start performance counter (high precision)
        start_time = time.perf_counter()
        
        # Pilih dan run algoritma
        if algo == "backtracking":
            success = self.solve_backtracking_visual(grid)
            algo_name = "Backtracking"
        else:  # mrv
            success = self.solve_backtracking_mrv_visual(grid)
            algo_name = "MRV"
        
        # Hitung elapsed time dalam milliseconds
        elapsed = (time.perf_counter() - start_time) * 1000.0
        
        if success:
            # Berhasil solve
            self.user_grid = copy.deepcopy(grid)
            write_grid_file(grid, self.current_solution_name)
            self.solved_time = self.elapsed
            
            # Show hasil dengan statistik lengkap
            self.show_message(
                f"Solved with {algo_name} | {self.step_count} steps | {elapsed:.1f}ms", 
                ACCENT_GREEN
            )
        else:
            # Gagal solve (seharusnya tidak terjadi untuk puzzle valid)
            self.show_message("Failed to solve", ACCENT_RED)
        
        # Reset visual mode
        self.visual_solving = False
        self.current_step_info = ""
        self.highlight_cell = None
    
    def solve_backtracking_visual(self, grid):
        """
        Algoritma Backtracking standar DENGAN VISUALISASI.
        Setiap langkah ditampilkan di layar dengan delay kecil.
        
        Args:
            grid (list): Grid yang akan di-solve (modified in-place)
        
        Returns:
            bool: True jika berhasil solve, False jika tidak ada solusi
        
        Algoritma:
        1. Cari sel kosong pertama (dari kiri ke kanan, atas ke bawah)
        2. Jika tidak ada, berarti sudah selesai (return True)
        3. Coba angka 1-9 pada sel tersebut
        4. Jika valid, visualisasikan dan rekursif ke sel berikutnya
        5. Jika rekursif berhasil, return True
        6. Jika gagal, BACKTRACK: reset sel ke 0, visualisasikan, coba angka lain
        7. Jika semua angka gagal, return False
        
        Visualisasi:
        - Sel yang dicoba: highlight kuning terang
        - Step counter increment
        - Info: "Try: row X, col Y = value"
        - Delay ANIM_DELAY agar terlihat
        - Backtrack: highlight merah sesaat
        """
        # Cari sel kosong pertama
        empty = find_empty(grid)
        if not empty:
            return True  # Tidak ada sel kosong = selesai
        
        r, c = empty
        
        # Coba angka 1-9
        for val in range(1, 10):
            if valid(grid, r, c, val):
                # Angka valid, isi sel
                self.step_count += 1
                grid[r][c] = val
                
                # === VISUALISASI: MENCOBA NILAI ===
                self.highlight_cell = (r, c)
                self.current_step_info = f"Try: row {r+1}, col {c+1} = {val}"
                self.correct_cells.add((r, c))
                
                # Render ke layar
                self.draw()
                pygame.display.flip()
                time.sleep(ANIM_DELAY)  # Delay agar terlihat
                
                # Handle event quit (agar bisa close window saat solving)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                
                # Rekursif ke sel berikutnya
                if self.solve_backtracking_visual(grid):
                    return True  # Berhasil!
                
                # === BACKTRACK - Nilai ini tidak berhasil ===
                self.step_count += 1
                grid[r][c] = 0  # Reset sel
                
                # === VISUALISASI: BACKTRACK ===
                self.current_step_info = f"Backtrack: row {r+1}, col {c+1}"
                self.correct_cells.discard((r, c))
                self.wrong_cells.add((r, c))  # Highlight merah
                
                # Render backtrack
                self.draw()
                pygame.display.flip()
                time.sleep(ANIM_DELAY)
                
                # Clear highlight merah
                self.wrong_cells.discard((r, c))
        
        return False  # Semua angka gagal, tidak ada solusi dari state ini
    
    def solve_backtracking_mrv_visual(self, grid):
        """
        Algoritma Backtracking + MRV DENGAN VISUALISASI.
        Lebih efisien karena memilih sel dengan domain terkecil terlebih dahulu.
        
        Args:
            grid (list): Grid yang akan di-solve (modified in-place)
        
        Returns:
            bool: True jika berhasil solve
        
        MRV (Minimum Remaining Values) Heuristic:
        - Pilih sel dengan jumlah pilihan nilai paling sedikit
        - Fail-First Principle: Deteksi dead-end lebih cepat
        - Pruning efektif: Mengurangi ruang pencarian
        
        Algoritma:
        1. Dapatkan semua sel kosong
        2. Jika tidak ada, return True (selesai)
        3. Untuk setiap sel kosong, hitung domain (nilai yang mungkin)
        4. Pilih sel dengan domain terkecil (MRV)
        5. Jika domain kosong (0 pilihan), langsung return False (dead-end)
        6. Coba semua nilai dalam domain
        7. Visualisasikan dan rekursif
        8. Backtrack jika gagal
        
        Visualisasi:
        - Info tambahan: domain sel yang dipilih
        - Contoh: "MRV: row 3, col 5 = 7 (options: 3, 7, 9)"
        - Counter steps
        - Highlight dan animasi sama dengan backtracking standar
        """
        # Cari semua sel kosong
        empties = [(r,c) for r in range(9) for c in range(9) if grid[r][c]==0]
        if not empties:
            return True  # Tidak ada sel kosong = selesai
        
        # === MRV: PILIH SEL DENGAN DOMAIN MINIMUM ===
        best = None
        best_dom = None
        
        for (r,c) in empties:
            dom = domain(grid, r, c)  # Hitung domain
            
            if len(dom) == 0:
                # Dead-end detected! Domain kosong = tidak ada pilihan
                return False
            
            if best is None or len(dom) < len(best_dom):
                # Update best jika domain lebih kecil
                best = (r,c)
                best_dom = dom
        
        r, c = best
        dom_str = ", ".join(map(str, best_dom))  # Format domain untuk display
        
        # Coba semua nilai dalam domain
        for val in best_dom:
            self.step_count += 1
            grid[r][c] = val
            
            # === VISUALISASI: MENCOBA NILAI (MRV) ===
            self.highlight_cell = (r, c)
            # Info lebih lengkap: tampilkan domain
            self.current_step_info = f"MRV: row {r+1}, col {c+1} = {val} (options: {dom_str})"
            self.correct_cells.add((r, c))
            
            # Render
            self.draw()
            pygame.display.flip()
            time.sleep(ANIM_DELAY)
            
            # Handle quit event
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            # Rekursif
            if self.solve_backtracking_mrv_visual(grid):
                return True  # Berhasil!
            
            # === BACKTRACK ===
            self.step_count += 1
            grid[r][c] = 0
            
            # === VISUALISASI: BACKTRACK ===
            self.current_step_info = f"Backtrack: row {r+1}, col {c+1}"
            self.correct_cells.discard((r, c))
            self.wrong_cells.add((r, c))
            
            # Render
            self.draw()
            pygame.display.flip()
            time.sleep(ANIM_DELAY)
            
            # Clear highlight
            self.wrong_cells.discard((r, c))
        
        return False  # Semua nilai dalam domain gagal
    
    def clear_inputs(self):
        """
        Hapus semua input user (kembalikan ke puzzle awal).
        Sel prefilled tidak dihapus (tetap ada).
        
        Digunakan untuk:
        - Reset puzzle jika user ingin mulai dari awal
        - Clear setelah check answer menunjukkan banyak kesalahan
        
        Flow:
        1. Loop semua sel
        2. Jika bukan prefilled, set ke 0
        3. Clear semua highlight
        4. Show confirmation message
        """
        for r in range(9):
            for c in range(9):
                if (r,c) not in self.prefilled:
                    self.user_grid[r][c] = 0
        
        # Clear highlight
        self.wrong_cells.clear()
        self.correct_cells.clear()
        
        self.show_message("Cleared all inputs", ACCENT_BLUE)
    
    def draw_grid(self):
        """
        Render grid sudoku 9x9 ke layar dengan semua visual effects.
        
        Returns:
            tuple: (board_x, board_y, GRID_SIZE, GRID_SIZE) - koordinat dan ukuran grid
        
        Fitur:
        - Hover effect: sel berubah warna saat mouse di atasnya
        - Color coding berdasarkan state sel:
          * Putih: Kosong
          * Abu muda: Prefilled
          * Kuning: Selected
          * Merah muda: Wrong answer
          * Hijau muda: Correct answer
          * Kuning terang: Highlight saat solving
        - Bold lines setiap 3 baris/kolom untuk subgrid 3x3
        - Angka dengan warna berbeda (abu untuk prefilled, hitam untuk user input)
        """
        board_x = 30  # Posisi X grid (padding dari kiri)
        board_y = 50  # Posisi Y grid (padding dari atas)
        
        # Get posisi mouse untuk hover effect
        mx, my = pygame.mouse.get_pos()
        
        # === DRAW SETIAP SEL (9x9 = 81 sel) ===
        for r in range(9):
            for c in range(9):
                # Hitung posisi sel di layar
                x = board_x + c * CELL
                y = board_y + r * CELL
                rect = pygame.Rect(x, y, CELL, CELL)
                
                # === TENTUKAN WARNA SEL BERDASARKAN STATE ===
                cell_color = CELL_BG  # Default: putih
                
                # Priority order (dari highest ke lowest):
                if self.highlight_cell == (r,c) and self.visual_solving:
                    # Highest priority: Highlight saat solving
                    cell_color = (255, 255, 200)  # Kuning terang
                elif self.selected == (r,c):
                    # Sel yang dipilih user
                    cell_color = CELL_SELECTED
                elif rect.collidepoint(mx, my) and (r,c) not in self.prefilled:
                    # Mouse hover (hanya untuk sel yang bisa diedit)
                    cell_color = CELL_HOVER
                elif (r,c) in self.prefilled:
                    # Sel prefilled (tidak bisa diubah)
                    cell_color = CELL_PREFILLED
                elif (r,c) in self.wrong_cells:
                    # Sel dengan jawaban salah
                    cell_color = CELL_WRONG
                elif (r,c) in self.correct_cells:
                    # Sel dengan jawaban benar
                    cell_color = CELL_CORRECT
                
                # Draw background sel
                pygame.draw.rect(screen, cell_color, rect)
                
                # === DRAW ANGKA DI DALAM SEL ===
                val = self.user_grid[r][c]
                if val != 0:  # Hanya draw jika sel tidak kosong
                    # Warna angka: abu untuk prefilled, hitam untuk user input
                    color = TEXT_PREFILLED if (r,c) in self.prefilled else TEXT_PRIMARY
                    
                    # Highlight angka yang sedang dicoba saat solving (biru)
                    if self.highlight_cell == (r,c) and self.visual_solving:
                        color = ACCENT_BLUE
                    
                    # Draw angka di center sel
                    draw_text(str(val), x + CELL//2, y + CELL//2, FONT_CELL, color, center=True)
        
        # === DRAW GARIS GRID ===
        for i in range(10):  # 0-9 = 10 garis (horizontal dan vertikal)
            # Garis tebal setiap 3 baris/kolom (untuk subgrid 3x3)
            lw = 3 if i % 3 == 0 else 1  # Line width
            color = GRID_BOLD if i % 3 == 0 else GRID_COLOR
            
            # Garis horizontal
            pygame.draw.line(screen, color, 
                           (board_x, board_y + i*CELL), 
                           (board_x + GRID_SIZE, board_y + i*CELL), lw)
            
            # Garis vertikal
            pygame.draw.line(screen, color, 
                           (board_x + i*CELL, board_y), 
                           (board_x + i*CELL, board_y + GRID_SIZE), lw)
        
        return (board_x, board_y, GRID_SIZE, GRID_SIZE)
    
    def draw_sidebar(self):
        """
        Render panel kontrol di sebelah kanan grid.
        
        Returns:
            dict: Dictionary berisi semua button rect untuk collision detection
        
        Panel berisi (dari atas ke bawah):
        1. Judul "SUDOKU"
        2. Timer (MM:SS) dengan label PAUSED jika pause
        3. Step counter (saat visual solving)
        4. Info step saat ini (saat visual solving)
        5. Tombol New Puzzle (Easy/Medium/Hard) dengan highlight difficulty aktif
        6. Tombol Check dan Clear
        7. Drop zone untuk drag & drop file (border dashed ungu)
        8. Tombol Auto Solve (Backtracking dan MRV)
        9. Tombol Quit Game
        10. Area notifikasi pesan (3 detik)
        """
        sidebar_x = GRID_SIZE + 60  # Posisi X sidebar
        y = 50  # Posisi Y mulai (sama dengan grid)
        
        # === 1. JUDUL ===
        draw_text("SUDOKU", sidebar_x, y, FONT_TITLE, TEXT_PRIMARY)
        y += 45
        
        # === 2. TIMER ===
        # Hitung current time berdasarkan state
        if not self.solved_time:
            # Game masih berlangsung
            if self.timer_paused:
                current_time = self.elapsed  # Gunakan elapsed saat pause
            else:
                current_time = time.time() - self.start_time  # Real-time
        else:
            # Game sudah selesai, tampilkan waktu final
            current_time = self.solved_time
        
        timer_text = format_time(current_time)
        # Warna timer: abu jika pause, biru jika aktif
        timer_color = TEXT_SECONDARY if self.timer_paused else ACCENT_BLUE
        draw_text(timer_text, sidebar_x, y, FONT_TITLE, timer_color)
        
        # Label "PAUSED" jika timer pause
        if self.timer_paused:
            draw_text("PAUSED", sidebar_x + 140, y + 8, FONT_TINY, ACCENT_RED)
        y += 50
        
        # === 3 & 4. STEP COUNTER & INFO (saat visual solving) ===
        if self.visual_solving:
            # Step counter dengan warna ungu
            draw_text(f"Steps: {self.step_count}", sidebar_x, y, FONT_SMALL, ACCENT_PURPLE)
            y += 25
            
            # Info step saat ini
            if self.current_step_info:
                info = self.current_step_info
                # Wrap text panjang ke 2 baris (max 30 karakter per baris)
                if len(info) > 30:
                    words = info.split()
                    line1 = " ".join(words[:4])  # 4 kata pertama
                    line2 = " ".join(words[4:])  # Sisanya
                    draw_text(line1, sidebar_x, y, FONT_TINY, TEXT_SECONDARY)
                    y += 15
                    draw_text(line2, sidebar_x, y, FONT_TINY, TEXT_SECONDARY)
                else:
                    draw_text(info, sidebar_x, y, FONT_TINY, TEXT_SECONDARY)
            y += 30
        
        # === 5. TOMBOL NEW PUZZLE ===
        draw_text("New Puzzle", sidebar_x, y, FONT_SMALL, TEXT_SECONDARY)
        y += 25
        
        btn_w = 80
        btn_h = 32
        
        # Highlight tombol sesuai difficulty saat ini
        easy_color = ACCENT_GREEN if self.difficulty == "easy" else GRID_COLOR
        med_color = ACCENT_BLUE if self.difficulty == "medium" else GRID_COLOR
        hard_color = ACCENT_RED if self.difficulty == "hard" else GRID_COLOR
        
        # Draw 3 tombol difficulty side by side
        easy_btn = draw_button("Easy", sidebar_x, y, btn_w, btn_h, easy_color)
        med_btn = draw_button("Med", sidebar_x + 90, y, btn_w, btn_h, med_color)
        hard_btn = draw_button("Hard", sidebar_x + 180, y, btn_w, btn_h, hard_color)
        y += 50
        
        # === 6. TOMBOL CHECK & CLEAR ===
        check_btn = draw_button("Check", sidebar_x, y, 125, 40, ACCENT_GREEN)
        clear_btn = draw_button("Clear", sidebar_x + 135, y, 125, 40, ACCENT_RED)
        y += 55
        
        # === 7. DROP ZONE (Drag & Drop File) ===
        drop_zone = pygame.Rect(sidebar_x, y, 260, 60)
        # Warna lebih terang saat hover
        drop_color = ACCENT_PURPLE if not self.drag_hover else tuple(min(c + 30, 255) for c in ACCENT_PURPLE)
        
        # Background putih
        pygame.draw.rect(screen, (255, 255, 255), drop_zone, border_radius=10)
        
        # === DRAW BORDER GARIS PUTUS-PUTUS (DASHED) ===
        dash_length = 10
        gap_length = 5
        border_color = drop_color
        
        # Top border (horizontal, putus-putus)
        x_pos = drop_zone.left
        while x_pos < drop_zone.right:
            end_x = min(x_pos + dash_length, drop_zone.right)
            pygame.draw.line(screen, border_color, (x_pos, drop_zone.top), (end_x, drop_zone.top), 3)
            x_pos += dash_length + gap_length
        
        # Bottom border
        x_pos = drop_zone.left
        while x_pos < drop_zone.right:
            end_x = min(x_pos + dash_length, drop_zone.right)
            pygame.draw.line(screen, border_color, (x_pos, drop_zone.bottom), (end_x, drop_zone.bottom), 3)
            x_pos += dash_length + gap_length
        
        # Left border (vertical, putus-putus)
        y_pos = drop_zone.top
        while y_pos < drop_zone.bottom:
            end_y = min(y_pos + dash_length, drop_zone.bottom)
            pygame.draw.line(screen, border_color, (drop_zone.left, y_pos), (drop_zone.left, end_y), 3)
            y_pos += dash_length + gap_length
        
        # Right border
        y_pos = drop_zone.top
        while y_pos < drop_zone.bottom:
            end_y = min(y_pos + dash_length, drop_zone.bottom)
            pygame.draw.line(screen, border_color, (drop_zone.right, y_pos), (drop_zone.right, end_y), 3)
            y_pos += dash_length + gap_length
        
        # Teks instruksi di tengah drop zone
        draw_text("Drop .txt file here", drop_zone.centerx, drop_zone.centery, 
                 FONT_SMALL, TEXT_SECONDARY, center=True)
        
        y += 75
        
        # === 8. TOMBOL AUTO SOLVE ===
        draw_text("Auto Solve ", sidebar_x, y, FONT_SMALL, TEXT_SECONDARY)
        y += 25
        solve_bt = draw_button("Backtrack", sidebar_x, y, 125, 40, ACCENT_BLUE)
        solve_mrv = draw_button("Backtrack+MRV", sidebar_x + 135, y, 125, 40, ACCENT_BLUE)
        y += 55
        
        # === 9. TOMBOL QUIT ===
        quit_btn = draw_button("Quit Game", sidebar_x, y, 260, 40, ACCENT_RED)
        y += 55
        
        # === 10. AREA NOTIFIKASI PESAN ===
        # Pesan tampil selama 3 detik setelah muncul
        if self.message and (time.time() - self.message_time) < 3.0:
            text, color = self.message
            # Wrap text panjang ke 2 baris
            if len(text) > 30:
                words = text.split()
                mid = len(words) // 2
                line1 = " ".join(words[:mid])
                line2 = " ".join(words[mid:])
                draw_text(line1, sidebar_x, y, FONT_TINY, color)
                draw_text(line2, sidebar_x, y + 15, FONT_TINY, color)
            else:
                draw_text(text, sidebar_x, y, FONT_SMALL, color)
        
        # Return semua button rect untuk collision detection di event handler
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
        """
        Render semua elemen UI ke layar.
        Dipanggil setiap frame dalam game loop.
        
        Returns:
            tuple: (board_rect, buttons) untuk event handling
        
        Flow:
        1. Clear screen dengan background color
        2. Draw grid sudoku (9x9 dengan angka dan highlight)
        3. Draw sidebar (tombol, timer, message)
        4. Draw instruksi di bagian bawah
        """
        screen.fill(BG_COLOR)  # Clear screen
        board_rect = self.draw_grid()  # Draw grid sudoku
        buttons = self.draw_sidebar()  # Draw panel kontrol
        
        # Instruksi di bagian bawah layar
        draw_text("Drag & drop .txt file to purple zone | Click cell & type 1-9 | Arrow keys to move", 
                 WINDOW_W//2, WINDOW_H - 20, FONT_TINY, TEXT_SECONDARY, center=True)
        
        return board_rect, buttons
    
    def handle_click(self, pos, board_rect, buttons):
        """
        Handle event mouse click.
        
        Args:
            pos (tuple): (x, y) posisi mouse click
            board_rect (tuple): (x, y, w, h) area grid untuk collision detection
            buttons (dict): Dictionary button rect untuk collision detection
        
        Kemungkinan aksi:
        - Klik pada grid: pilih sel untuk diisi (kecuali prefilled)
        - Klik tombol Easy/Med/Hard: generate puzzle baru
        - Klik Check: cek jawaban
        - Klik Clear: hapus semua input
        - Klik Backtrack/MRV: auto solve dengan visualisasi
        - Klik Quit: keluar dari aplikasi
        
        Note: Click diblokir saat sedang visual solving
        """
        # Blokir click saat sedang visual solving (agar tidak interfere)
        if self.visual_solving:
            return
        
        bx, by, bw, bh = board_rect
        mx, my = pos
        
        # === CEK CLICK PADA GRID ===
        if bx <= mx <= bx+bw and by <= my <= by+bh:
            # Click ada di dalam grid area
            # Hitung sel mana yang diklik (convert pixel ke grid coordinate)
            col = (mx - bx) // CELL
            row = (my - by) // CELL
            
            # Hanya bisa select sel yang bukan prefilled
            if (row, col) not in self.prefilled:
                self.selected = (row, col)
            else:
                self.selected = None  # Deselect jika klik prefilled
            return
        
        # === CEK CLICK PADA TOMBOL ===
        # Gunakan collidepoint untuk cek apakah pos ada di dalam button rect
        
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
            self.solve_with_algo_visual("backtracking")
        elif buttons["solve_mrv"].collidepoint(pos):
            self.solve_with_algo_visual("backtracking+mrv")
        elif buttons["quit"].collidepoint(pos):
            pygame.quit()
            sys.exit()
    
    def handle_key(self, key):
        """
        Handle event keyboard input.
        
        Args:
            key (int): Pygame key constant (pygame.K_1, pygame.K_UP, dll)
        
        Input yang didukung:
        - Angka 1-9: isi sel yang dipilih dengan angka
        - Backspace/Delete/0: hapus isi sel (set ke 0)
        - Arrow keys (↑↓←→): navigasi antar sel, skip sel prefilled
        
        Note: Hanya berfungsi jika ada sel yang dipilih (self.selected != None)
        """
        if not self.selected:
            return  # Tidak ada sel yang dipilih, ignore
        
        r, c = self.selected
        
        # === INPUT ANGKA 1-9 ===
        if pygame.K_1 <= key <= pygame.K_9:
            val = key - pygame.K_0  # Convert key code ke angka (K_1=49, K_2=50, ...)
            self.user_grid[r][c] = val
            # Clear highlight dari check (merah/hijau)
            self.wrong_cells.discard((r,c))
            self.correct_cells.discard((r,c))
        
        # === HAPUS ISI SEL (SET KE 0) ===
        elif key in [pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_0]:
            self.user_grid[r][c] = 0
            self.wrong_cells.discard((r,c))
            self.correct_cells.discard((r,c))
        
        # === ARROW KEYS - PINDAH SEL ===
        # Navigasi dengan skip sel prefilled (agar langsung ke sel yang bisa diisi)
        
        elif key == pygame.K_UP and r > 0:
            # Pindah ke atas
            nr = r - 1
            # Skip sel prefilled
            while nr >= 0 and (nr,c) in self.prefilled:
                nr -= 1
            if nr >= 0:  # Masih dalam bounds
                self.selected = (nr, c)
        
        elif key == pygame.K_DOWN and r < 8:
            # Pindah ke bawah
            nr = r + 1
            while nr < 9 and (nr,c) in self.prefilled:
                nr += 1
            if nr < 9:
                self.selected = (nr, c)
        
        elif key == pygame.K_LEFT and c > 0:
            # Pindah ke kiri
            nc = c - 1
            while nc >= 0 and (r,nc) in self.prefilled:
                nc -= 1
            if nc >= 0:
                self.selected = (r, nc)
        
        elif key == pygame.K_RIGHT and c < 8:
            # Pindah ke kanan
            nc = c + 1
            while nc < 9 and (r,nc) in self.prefilled:
                nc += 1
            if nc < 9:
                self.selected = (r, nc)
    
    def handle_file_drop(self, filepath):
        """
        Handle event file di-drop ke window (pygame.DROPFILE).
        File akan divalidasi dan dimuat sebagai puzzle baru.
        
        Args:
            filepath (str): Path ke file yang di-drop oleh user
        
        Note: Validasi dilakukan di load_from_file()
        """
        self.load_from_file(filepath)

# ===========================================================================================
# MAIN GAME LOOP
# ===========================================================================================

def main():
    """
    Fungsi utama - entry point aplikasi.
    Menjalankan game loop pygame dengan event handling.
    
    Game loop:
    1. Handle events (mouse, keyboard, file drop, quit)
    2. Update game state (implicit dalam event handlers)
    3. Render frame (draw semua UI)
    4. Maintain FPS (60 FPS untuk smooth animation)
    5. Repeat forever sampai user quit
    
    Event yang di-handle:
    - QUIT: Close window (X button)
    - DROPFILE: Drag & drop file
    - MOUSEBUTTONDOWN: Click mouse (button 1 = left click)
    - KEYDOWN: Keyboard input
    """
    # Inisialisasi game
    game = SudokuGame()
    
    # Enable hanya event yang dibutuhkan (optimasi performa)
    pygame.event.set_allowed([
        pygame.QUIT,            # Tombol close window
        pygame.MOUSEBUTTONDOWN, # Click mouse
        pygame.KEYDOWN,         # Keyboard input
        pygame.DROPFILE         # Drag & drop file
    ])
    
    # === MAIN GAME LOOP (Infinite Loop) ===
    while True:
        # === 1. EVENT HANDLING ===
        for event in pygame.event.get():
            
            # Event: User close window (klik X)
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Event: File di-drop ke window
            elif event.type == pygame.DROPFILE:
                filepath = event.file  # Path file yang di-drop
                game.handle_file_drop(filepath)
            
            # Event: Mouse click
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click only
                # Get board rect dan buttons untuk collision detection
                board_rect, buttons = game.draw()
                game.handle_click(event.pos, board_rect, buttons)
            
            # Event: Keyboard input
            elif event.type == pygame.KEYDOWN:
                game.handle_key(event.key)
        
        # === 2. RENDER FRAME ===
        game.draw()              # Draw semua UI ke screen surface
        pygame.display.flip()    # Update display (swap buffer)
        
        # === 3. MAINTAIN FPS ===
        clock.tick(FPS)  # Limit ke 60 FPS (tunggu jika terlalu cepat)

# ===========================================================================================
# ENTRY POINT
# ===========================================================================================

if __name__ == "__main__":
    """
    Entry point aplikasi.
    Menjalankan main() dengan exception handling untuk cleanup yang proper.
    
    Jika terjadi error:
    1. Quit pygame untuk cleanup resources
    2. Print error message
    3. Print full traceback untuk debugging
    """
    try:
        main()
    except Exception as e:
        # Cleanup pygame jika terjadi error
        pygame.quit()
        print("Error:", e)
        import traceback
        traceback.print_exc()  # Print full error trace untuk debugging
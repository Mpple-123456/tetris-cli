import curses
import random
import time

# 定义7种经典方块（相对坐标）
SHAPES = {
    'I': [(0,0), (1,0), (2,0), (3,0)],
    'O': [(0,0), (1,0), (0,1), (1,1)],
    'T': [(0,0), (1,0), (2,0), (1,1)],
    'S': [(1,0), (2,0), (0,1), (1,1)],
    'Z': [(0,0), (1,0), (1,1), (2,1)],
    'J': [(0,0), (0,1), (1,1), (2,1)],
    'L': [(0,0), (1,0), (2,0), (2,1)],
}

def rotate(shape):
    """顺时针旋转（核心数学，看不懂就硬记）"""
    # 先找中心偏移，再旋转坐标 (x,y) -> (y, -x)
    return [(y, -x) for x, y in shape]

def check_collision(board, shape, offset_x, offset_y):
    """检测 shape 在 (offset_x, offset_y) 位置是否与 board 或边界碰撞"""
    for dx, dy in shape:
        nx, ny = offset_x + dx, offset_y + dy
        # 超出左右下边界 或 与已固定方块重叠
        if nx < 0 or nx >= 10 or ny >= 20 or (ny >= 0 and board[ny][nx]):
            return True
    return False

def lock_shape(board, shape, offset_x, offset_y):
    """将当前方块写入 board"""
    for dx, dy in shape:
        nx, ny = offset_x + dx, offset_y + dy
        if 0 <= ny < 20 and 0 <= nx < 10:
            board[ny][nx] = 1  # 1 表示已固定

def clear_lines(board):
    """消除所有满行，返回消除的行数，并更新board"""
    lines_cleared = 0
    y = 19  # 从底部开始检查
    while y >= 0:
        # 检查第 y 行是否全部为 1
        if all(board[y]):  # 如果该行所有格子都是1
            # 删除该行，在顶部插入一个空行
            del board[y]
            board.insert(0, [0] * 10)
            lines_cleared += 1
            # 注意：删除后，原来的上一行变成了当前位置，所以y不需要变
            # 但我们要继续检查同一位置（现在已经是上一行）
        else:
            y -= 1
    return lines_cleared

def get_ghost_y(board, shape, offset_x, offset_y):
    """计算当前方块从 (offset_x, offset_y) 开始下落，最终停在哪个 y 坐标"""
    y = offset_y
    while not check_collision(board, shape, offset_x, y + 1):
        y += 1
    return y

def main(stdscr):
    # ----- 1. 初始化颜色（新增）-----
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)   # 定义颜色对1为红字黑底
    curses.curs_set(0)          # 隐藏光标
    stdscr.nodelay(1)           # 非阻塞输入
    stdscr.timeout(100)         # 刷新率100ms
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)   # 颜色对2：白色（可用于辅助线）

    # 游戏状态
    board = [[0] * 10 for _ in range(20)]
    current_shape = random.choice(list(SHAPES.values()))
    pos_x, pos_y = 4, 0
    fall_time = time.time()
    
    while True:
        # 处理键盘输入...
        key = stdscr.getch()
        if key == ord('q'): break

        if key == curses.KEY_LEFT:
            if not check_collision(board, current_shape, pos_x - 1, pos_y):
                pos_x -= 1
        elif key == curses.KEY_RIGHT:
            if not check_collision(board, current_shape, pos_x + 1, pos_y):
                pos_x += 1
        elif key == curses.KEY_DOWN:
            # 如果你将来要加“加速下落”，也可以这里加碰撞
            if not check_collision(board, current_shape, pos_x, pos_y + 1):
                pos_y += 1
        elif key == curses.KEY_UP:
            new_shape = rotate(current_shape)
            if not check_collision(board, new_shape, pos_x, pos_y):
                current_shape = new_shape
        
        # 自动下落...
        if time.time() - fall_time > 1.0:
            if not check_collision(board, current_shape, pos_x, pos_y + 1):
                pos_y += 1
            else:
                lock_shape(board, current_shape, pos_x, pos_y)
                
                # ------- 新增消行 -------
                cleared = clear_lines(board)
                if cleared > 0:
                    # 计分规则：1行100分，2行300分，3行500分，4行800分
                    score_map = {1: 100, 2: 300, 3: 500, 4: 800}
                    score += score_map.get(cleared, 0)
                # ------------------------
                
                # 生成新方块
                current_shape = random.choice(list(SHAPES.values()))
                pos_x, pos_y = 4, 0
                if check_collision(board, current_shape, pos_x, pos_y):
                    break
                fall_time = time.time()
        
        # 渲染
        stdscr.clear()
        # 画网格（现有的）
        for y in range(20):
            for x in range(10):
                if board[y][x]:
                    stdscr.addstr(y, x*2, "[]")
                    # 画辅助线（ghost）
                    ghost_y = get_ghost_y(board, current_shape, pos_x, pos_y)
                    for dx, dy in current_shape:
                        nx, ny = pos_x + dx, ghost_y + dy
                        if 0 <= ny < 20 and 0 <= nx < 10:
                            try:
                                # 用不同的样式，比如 dim 或者颜色对2
                                stdscr.addstr(ny, nx*2, "[]", curses.A_DIM)  # 或者使用颜色对2：curses.color_pair(2)
                            except curses.error:
                                pass
        
        # 画当前方块（加边界保护）
        for dx, dy in current_shape:
            nx, ny = pos_x + dx, pos_y + dy
            # ---- 新增边界检查，防止画出屏幕 ----
            if 0 <= ny < 20 and 0 <= nx < 10:
                try:
                    stdscr.addstr(ny, nx*2, "[]", curses.color_pair(1))
                except curses.error:
                    pass   # 如果还是画不出去，就忽略（通常不会）
        
        stdscr.refresh()

# 启动curses应用（必须这样包一层）
if __name__ == "__main__":
    curses.wrapper(main)
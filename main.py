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
    """顺时针旋转"""
    return [(y, -x) for x, y in shape]

def check_collision(board, shape, offset_x, offset_y):
    """碰撞检测"""
    for dx, dy in shape:
        nx, ny = offset_x + dx, offset_y + dy
        if nx < 0 or nx >= 10 or ny >= 20 or (ny >= 0 and board[ny][nx]):
            return True
    return False

def lock_shape(board, shape, offset_x, offset_y):
    """固定方块到面板"""
    for dx, dy in shape:
        nx, ny = offset_x + dx, offset_y + dy
        if 0 <= ny < 20 and 0 <= nx < 10:
            board[ny][nx] = 1

def clear_lines(board):
    """消行并返回消除行数"""
    lines_cleared = 0
    y = 19
    while y >= 0:
        if all(board[y]):
            del board[y]
            board.insert(0, [0] * 10)
            lines_cleared += 1
        else:
            y -= 1
    return lines_cleared

def get_ghost_y(board, shape, offset_x, offset_y):
    """计算辅助线（落点）的 y 坐标"""
    y = offset_y
    while not check_collision(board, shape, offset_x, y + 1):
        y += 1
    return y

def main(stdscr):
    # 初始化颜色
    curses.start_color()
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)   # 当前方块
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK) # 辅助线（白色）
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)

    # 游戏状态
    board = [[0] * 10 for _ in range(20)]
    current_shape = random.choice(list(SHAPES.values()))
    pos_x, pos_y = 4, 0
    fall_time = time.time()
    score = 0                     # ✅ 新增：初始化分数
    game_over = False             # ✅ 新增：游戏结束标志

    while not game_over:
        key = stdscr.getch()
        if key == ord('q'):
            break

        # 按键处理（左右移动、旋转、软降）
        if key == curses.KEY_LEFT:
            if not check_collision(board, current_shape, pos_x - 1, pos_y):
                pos_x -= 1
        elif key == curses.KEY_RIGHT:
            if not check_collision(board, current_shape, pos_x + 1, pos_y):
                pos_x += 1
        elif key == curses.KEY_DOWN:
            if not check_collision(board, current_shape, pos_x, pos_y + 1):
                pos_y += 1
        elif key == curses.KEY_UP:
            new_shape = rotate(current_shape)
            if not check_collision(board, new_shape, pos_x, pos_y):
                current_shape = new_shape

        # 自动下落
        if time.time() - fall_time > 1.0:
            if not check_collision(board, current_shape, pos_x, pos_y + 1):
                pos_y += 1
            else:
                lock_shape(board, current_shape, pos_x, pos_y)
                cleared = clear_lines(board)
                if cleared > 0:
                    score_map = {1: 100, 2: 300, 3: 500, 4: 800}
                    score += score_map.get(cleared, 0)
                # 生成新方块
                current_shape = random.choice(list(SHAPES.values()))
                pos_x, pos_y = 4, 0
                if check_collision(board, current_shape, pos_x, pos_y):
                    game_over = True   # ✅ 设置结束标志，而不是直接 break
                fall_time = time.time()

        # ----- 渲染部分 -----
        stdscr.clear()

        # 1. 绘制已固定的方块
        for y in range(20):
            for x in range(10):
                if board[y][x]:
                    stdscr.addstr(y, x*2, "[]")

        # 2. 绘制辅助线（ghost）  ✅ 移到了独立位置，不再嵌套
        ghost_y = get_ghost_y(board, current_shape, pos_x, pos_y)
        for dx, dy in current_shape:
            nx, ny = pos_x + dx, ghost_y + dy
            if 0 <= ny < 20 and 0 <= nx < 10:
                try:
                    stdscr.addstr(ny, nx*2, "[]", curses.A_DIM)  # 可用颜色对2
                except curses.error:
                    pass

        # 3. 绘制当前方块（红色）
        for dx, dy in current_shape:
            nx, ny = pos_x + dx, pos_y + dy
            if 0 <= ny < 20 and 0 <= nx < 10:
                try:
                    stdscr.addstr(ny, nx*2, "[]", curses.color_pair(1))
                except curses.error:
                    pass

        # 4. 显示分数（右上角） ✅ 新增
        score_text = f"Score: {score}"
        try:
            stdscr.addstr(0, 22, score_text)
        except curses.error:
            pass

        # 5. 如果游戏结束，显示提示
        if game_over:
            try:
                stdscr.addstr(10, 5, "GAME OVER! Press Q to exit.", curses.A_BOLD)
            except curses.error:
                pass

        stdscr.refresh()

    # 游戏循环结束后，等待用户按 q 退出（如果 game_over 触发，可以再等按键）
    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break

if __name__ == "__main__":
    curses.wrapper(main)
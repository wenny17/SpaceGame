import asyncio
import curses
import time
import random
import os

import physics
from curses_tools import draw_frame, get_frame_size, read_controls
from obstacles import Obstacle, show_obstacles
from explosion import explode
from untitledgame_scenario import get_garbage_delay_tics, gameover_frame, PHRASES


class GameStatus:

    year = 1957
    coroutines = []
    obstacles = []
    obstacles_in_last_collisions = []
    spaceship_frame = ""




async def show_gameover(canvas, status):
    for coro in status.coroutines:
        if coro.__name__ == fill_orbit_with_garbage.__name__:
            status.coroutines.remove(coro)
            break
    max_row, max_column = canvas.getmaxyx()
    heigh, width = get_frame_size(gameover_frame)
    while True:
        draw_frame(canvas, (max_row-heigh)//2, (max_column-width)//2, gameover_frame)
        await sleep()



async def animate_spaceship(canvas,frame_1,frame_2, status):
    while True:
        status.spaceship_frame = frame_1
        await sleep(1)
        status.spaceship_frame = frame_2
        await sleep(1)


async def run_spaceship(canvas,frame_1,frame_2, status):
    max_row, max_column = canvas.getmaxyx()
    ship_height, ship_width = get_frame_size(frame_1)
    ship_coordinate_y = max_row - ship_height - 3
    ship_coordinate_x = (max_column-ship_width) // 2
    row_speed = 0
    column_speed = 0
    change_frame = animate_spaceship(canvas,frame_1,frame_2, status)
    while True:
        change_frame.send(None)
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        row_speed, column_speed = physics.update_speed(row_speed, column_speed, rows_direction, columns_direction)
        ship_coordinate_y = max(min(ship_coordinate_y + row_speed, max_row - ship_height - 1), 1)
        ship_coordinate_x = max(min(ship_coordinate_x + column_speed, max_column - ship_width - 1), 1)
        if space_pressed and status.year >= 2020:
            status.coroutines.append(fire(canvas, ship_coordinate_y-1, ship_coordinate_x+2, status))
        draw_frame(canvas, ship_coordinate_y, ship_coordinate_x, status.spaceship_frame)
        await sleep(1)

        draw_frame(canvas, ship_coordinate_y, ship_coordinate_x, status.spaceship_frame, negative=True)
        for obs in status.obstacles:
            if obs.has_collision(ship_coordinate_y, ship_coordinate_x, ship_height, ship_width):
                await explode(canvas, ship_coordinate_y+ship_height//2, ship_coordinate_x+ship_width//2)
                await show_gameover(canvas, status)


async def blink(canvas, row, column, symbol='*', time_before_shine=0):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)
        
        await sleep(time_before_shine)
        time_before_shine = 0
        

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)





async def fly_garbage(canvas, column, garbage_frame, status, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0
    rows_size, columns_size = get_frame_size(garbage_frame)
    obstacle_object = Obstacle(row, column, rows_size, columns_size)
    status.obstacles.append(obstacle_object)
    while row < rows_number:
        if obstacle_object in status.obstacles_in_last_collisions:
            status.obstacles_in_last_collisions.remove(obstacle_object)
            await explode(canvas, row+rows_size//2, column+columns_size//2)
            return
        draw_frame(canvas, row, column, garbage_frame)
        await sleep()
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obstacle_object.row = row
    status.obstacles.remove(obstacle_object)


async def fill_orbit_with_garbage(canvas, garbage, status):
    #status.coroutines.append(show_obstacles(canvas, status.obstacles))
    
    _, max_column = canvas.getmaxyx()
    while True:
        delay = get_garbage_delay_tics(status.year)
        if delay != None:
            status.coroutines.append(fly_garbage(canvas, random.randint(1,max_column-2), random.choice(garbage), status))
            await sleep(delay)
        else:
            await sleep()


async def sleep(ticks=1):
    for _ in range(ticks):
        await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, status, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        for obs in status.obstacles[:]:
            if obs.has_collision(round(row), round(column)):
                status.obstacles_in_last_collisions.append(obs)
                status.obstacles.remove(obs)
                return
        row += rows_speed
        column += columns_speed



async def  change_year(canvas, status):
    while True:
        await sleep(15)
        status.year += 1


def update_infoplate(canvas, status):
    max_row, max_column = canvas.getmaxyx()
    plate = canvas.derwin(3, 0, max_row-3, 0)
    phrase = PHRASES.get(status.year) or ""
    plate.clear()
    draw_frame(plate, 1, (max_column-len(phrase))//2, phrase)   
    draw_frame(plate, 1, max_column-15, "Year: %d" % status.year)
    plate.box()

def main(canvas):
    status = GameStatus()
    curses.curs_set(False)
    canvas.nodelay(True)
    max_row, max_column = canvas.getmaxyx()
    garbage = []

    with open("rocket_frame_1.txt") as f:
        rocket_frame_1 = f.read()

    with open("rocket_frame_2.txt") as f:
        rocket_frame_2 = f.read()

    for garbage_file_name in os.listdir(os.getcwd()+"/trash"):
        with open(f"trash/{garbage_file_name}") as f:
            garbage_frame = f.read()
            garbage.append(garbage_frame)

    status.coroutines.append(run_spaceship(canvas,rocket_frame_1,rocket_frame_2, status))
    status.coroutines.append(fill_orbit_with_garbage(canvas, garbage, status))
    status.coroutines.append(change_year(canvas, status))

    for _ in range(100):
        coordinate_y = random.randint(1, max_row-2)
        coordinate_x = random.randint(1, max_column-2)
        star = random.choice("+*.:")
        status.coroutines.append(blink(canvas, coordinate_y, coordinate_x, star, random.randint(0,31)))
    
    while True:
        for coroutine in status.coroutines[:]:
            try:
                coroutine.send(None)
            except StopIteration:
                status.coroutines.remove(coroutine)
        
        update_infoplate(canvas, status)
        canvas.border()
        canvas.refresh()
        time.sleep(0.1)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(main)

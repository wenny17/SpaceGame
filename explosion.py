import asyncio
import curses
from curses_tools import draw_frame, get_frame_size

EXPLOSION_FRAMES = [
    """\
           (_) 
       (  (   (  (
      () (  (  )
        ( )  ()
    """,
    """\
           (_) 
       (  (   (   
         (  (  )
          )  (
    """,
    """\
            (  
          (   (   
         (     (
          )  (
    """,
    """\
            ( 
              (
            (  
    """,
]

async def explode(canvas, center_row, center_column):
    rows, columns = get_frame_size(EXPLOSION_FRAMES[0])
    corner_row = center_row - rows / 2
    corner_column = center_column - columns / 2
    
    curses.beep()
    for frame in EXPLOSION_FRAMES:
        
        draw_frame(canvas, corner_row, corner_column, frame)
        
        await asyncio.sleep(0)
        draw_frame(canvas, corner_row, corner_column, frame, negative=True)
        await asyncio.sleep(0)
import os, tty, sys, re, signal, select
from contextlib import contextmanager

CSI = '\033' # Control Sequence Introducer
ESC, CtrlC, CtrlQ = b'\x1b', b'\x03', b'\x11'
UP, DOWN, RIGHT, LEFT = b'[A', b'[B', b'[C', b'[D'
# https://github.com/junegunn/fzf/blob/master/src/tui/tui.go
ThickLeft = '▌'

def write(content:str|None=None, go_nextline=False, flush=False):
  if go_nextline: content = content + '\r\n' if content else '\r\n'
  if content: sys.stdout.write(content)
  if flush: sys.stdout.flush()

def terminal_size_handler():
  return # update per specific display

def get_cursor_position():
  write(CSI+'[6n', flush=True)
  seq = ''.join(iter(lambda: sys.stdin.read(1), 'R')) # \x1b[y;xR
  coordinates = re.split(r'\[|;', seq)
  y,x = int(coordinates[1]), int(coordinates[2])
  return x,y

@contextmanager
def screen(fd):
  # Switch to non-canonical (raw) terminal mode
  tty.setraw(fd)
  # Switch to alternate screen buffer, move cursor to home (top-left)
  write(CSI+'[?1049h'+CSI+'[H', flush=True)

  try: yield
  finally:
    # Escape alternate screen buffer
    write(CSI+'[?1049l', flush=True)
    
@contextmanager
def backdrop(color):
  write(CSI+'['+str(color)+'m')
  try: yield
  finally: write(CSI+'[0m', flush=True)

def SearchDisplay(height:int):
  sample_list = iter(range(1,100))
  for line in range(height):
    write(content=ThickLeft+" "+str(next(sample_list)), go_nextline=line!=height, flush=True)
  write(content="  "+"11/12", go_nextline=True, flush=True)
  write(content="> ", flush=True)

def renderer():
  fd = sys.stdin.fileno()
  columns, lines = os.get_terminal_size()
  signal.signal(signal.SIGWINCH, terminal_size_handler)

  with screen(fd):
    SearchDisplay(lines // 5 * 2)

    x,y = get_cursor_position()

    while True:
      char = os.read(fd, 1)
      if char == ESC:
        more, _, _ = select.select([fd], [], [], 0) # checks if more bytes in buffer
        if more:
          seq = os.read(fd, 2)
          if seq == UP: y = max(1, y-1)
          elif seq == DOWN: y = min(lines, y+1)
          elif seq == RIGHT: x = min(columns, x+1)
          elif seq == LEFT: x = max(1, x-1)
          write(CSI+f"[{y};{x}H", flush=True)
          continue
        else: break # ESC

      if char == CtrlC or char == CtrlQ: # Ctrl+C, Ctrl+Q
        break
      
      # else:
      #   write(char, flush=True)
      

if __name__ == "__main__":
  renderer()
  
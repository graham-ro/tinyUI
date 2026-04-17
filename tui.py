import os, sys, time, re
from contextlib import contextmanager

CSI = '\033' # Control Sequence Introducer
ESS = '\x1b' # Escape Sequence Start
# https://github.com/junegunn/fzf/blob/master/src/tui/tui.go
UP, DOWN, RIGHT, LEFT = '[A', '[B', '[C', '[D'
ThickLeft = '▌'

def write(content:str|None=None, go_next=False, flush=False):
  if go_next: content = content + '\r\n' if content else '\r\n'
  if content: sys.stdout.write(content)
  if flush: sys.stdout.flush()

def get_cursor_position():
  write(CSI+'[6n', flush=True)
  seq = ''.join(iter(lambda: sys.stdin.read(1), 'R')) + 'R'
  coordinates = re.search(rf'{ESS}\[(.*?)R', seq)
  y,x = coordinates.group(1).split(';')
  return x,y

@contextmanager
def screen():
  # Switch to non-canonical terminal mode
  os.system("stty raw -echo")
  # Switch to alternate screen buffer, move cursor to home (top-left)
  write(CSI+'[?1049h'+CSI+'[H', flush=True)

  try: yield
  finally:
    # Escape alternate screen buffer
    write(CSI+'[?1049l', flush=True)
    # Return to canonical terminal mode
    os.system("stty cooked echo")

@contextmanager
def backdrop(color):
  write(CSI+'['+str(color)+'m')
  try: yield
  finally: write(CSI+'[0m', flush=True)

def renderer():
  columns, lines = os.get_terminal_size()
  with screen():
    for i in range(lines//2): 
      with backdrop(100):
        write(ThickLeft, go_next=(i != range(lines//2)), flush=(i != range(lines//2)))

    x,y = get_cursor_position()

    while True:
      char = sys.stdin.read(1)

      if char == ESS:
        seq = sys.stdin.read(2)
        if seq == UP: y = max(1, y-1)
        elif seq == DOWN: y = min(lines, y+1)
        elif seq == RIGHT: x = min(columns, x+1)
        elif seq == LEFT: x = max(1, x-1)
        write(CSI+f"[{y};{x}H", flush=True)

      if char == '\x03' or char == '\x11': # Ctrl+C, Ctrl+Q
        break

if __name__ == "__main__":
  renderer()
  
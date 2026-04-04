"""
Demo functions for ScrollingRegion and TextBufferViewer.
Separated to keep testdoor.py cleaner.
"""

import time
from notorious_doorkit import (
    clear_screen, writeln, write, goto_xy,
    CYAN, YELLOW, GREEN, WHITE, RED, RESET, BOLD,
    BG_BLACK, BG_BLUE,
    RawInput, ScrollingRegion, TextBufferViewer, ansi_box
)
from notorious_doorkit.lnwp_door import LnwpDoor


def scrolling_region_demo(door: LnwpDoor):
    """Demonstrate ScrollingRegion as a chat/log viewport."""
    door.set_activity("Scrolling Region Demo")
    clear_screen()
    
    # Create a boxed area for the scrolling region
    box_x, box_y = 4, 3
    box_w, box_h = 72, 18
    
    ansi_box(
        x=box_x, y=box_y, width=box_w, height=box_h,
        style="double",
        border_color=f"{WHITE}{BG_BLUE}{BOLD}",
        fill_color=f"{WHITE}{BG_BLACK}",
        fill_char=" ",
    )
    
    title = "Scrolling Region Demo - Chat/Log Viewport"
    inner_w = box_w - 2
    title_start = max(0, (inner_w - len(title)) // 2)
    title_line = (" " * title_start) + title
    title_line = title_line + (" " * max(0, inner_w - len(title_line)))
    goto_xy(box_x + 1, box_y + 1)
    write(f"{WHITE}{BG_BLUE}{BOLD}{title_line}{RESET}")
    
    # Instructions
    help_text = "Arrows Scroll  PgUp/PgDn Page  Home/End  Space Add  Esc Exit"
    pad_left = max(0, (inner_w - len(help_text)) // 2)
    pad_right = max(0, inner_w - len(help_text) - pad_left)
    goto_xy(box_x + 1, box_y + box_h - 2)
    write(f"{WHITE}{BG_BLUE}{' ' * pad_left}{help_text}{' ' * pad_right}{RESET}")
    
    # Create scrolling region inside the box
    # Note: scrollbar draws at x+width (outside text area).
    # We deliberately size it so the scrollbar lands on (and overwrites) the right border.
    region = ScrollingRegion(
        x=box_x + 2,
        y=box_y + 3,
        width=box_w - 3,
        height=box_h - 6,
        max_lines=100,
        show_scrollbar=True,
    )
    
    # Add some initial messages with ANSI colors
    region.append(f"{CYAN}[System]{RESET} Welcome to the chat!")
    region.append(f"{GREEN}[Alice]{RESET} Hey everyone!")
    region.append(f"{YELLOW}[Bob]{RESET} Hi Alice!")
    region.append(f"{CYAN}[System]{RESET} 3 users online")
    region.append(f"{GREEN}[Alice]{RESET} How's everyone doing?")
    region.append(f"{YELLOW}[Bob]{RESET} Pretty good! Just testing this scrolling region.")
    region.append(f"{RED}[Charlie]{RESET} This is cool! ANSI colors work!")
    region.append(f"{CYAN}[System]{RESET} Press SPACE to add more messages, or scroll with arrows")
    
    region.render()
    
    message_count = 8
    
    from notorious_doorkit.ansi import hide_cursor, show_cursor
    from notorious_doorkit.input import KEY_UP, KEY_DOWN, KEY_PAGEUP, KEY_PAGEDOWN
    from notorious_doorkit.input import KEY_HOME, KEY_END, KEY_ESC

    hide_cursor()
    try:
        with RawInput(extended_keys=True) as inp:
            while True:
                key = inp.get_key()
                
                if key == KEY_ESC or key == 'q':
                    break
                
                elif key == KEY_UP:
                    region.scroll_up()
                    region.render()
                
                elif key == KEY_DOWN:
                    region.scroll_down()
                    region.render()
                
                elif key == KEY_PAGEUP or key == '\x15':  # Ctrl+U
                    region.page_up()
                    region.render()
                
                elif key == KEY_PAGEDOWN or key == '\x04':  # Ctrl+D
                    region.page_down()
                    region.render()
                
                elif key == KEY_HOME or key == '\x08':  # Ctrl+H
                    region.scroll_to_top()
                    region.render()
                
                elif key == KEY_END or key == '\x05':  # Ctrl+E
                    region.scroll_to_bottom()
                    region.render()
                
                elif key == ' ':
                    # Add a new message
                    message_count += 1
                    colors = [GREEN, YELLOW, RED, CYAN]
                    names = ["Alice", "Bob", "Charlie", "System"]
                    messages = [
                        "This is a test message!",
                        "Auto-scroll should work when at bottom",
                        "But not when you've scrolled up to read history",
                        "Pretty neat, right?",
                        f"Message #{message_count}",
                        "The scrollbar updates automatically",
                        "Try scrolling up and then pressing SPACE",
                    ]
                    
                    import random
                    color = random.choice(colors)
                    name = random.choice(names)
                    msg = random.choice(messages)
                    
                    region.append(f"{color}[{name}]{RESET} {msg}")
                    region.render()
    finally:
        show_cursor()
    
    clear_screen()
    writeln(f"{GREEN}Scrolling Region Demo Complete!{RESET}")
    writeln()
    writeln("Press any key to continue...")
    with RawInput() as inp:
        inp.get_key()


def text_buffer_viewer_demo(door: LnwpDoor):
    """Demonstrate TextBufferViewer for viewing large text files."""
    door.set_activity("Text Buffer Viewer Demo")
    clear_screen()
    
    # Generate a large text buffer with ANSI colors
    lines = []
    lines.append(f"{CYAN}{BOLD}═══ Text Buffer Viewer Demo ═══{RESET}")
    lines.append("")
    lines.append("This is a demonstration of the TextBufferViewer component.")
    lines.append("It works like 'less' - you can navigate through large text buffers.")
    lines.append("")
    lines.append(f"{YELLOW}Controls:{RESET}")
    lines.append("  - Arrow keys: scroll line by line or char by char")
    lines.append("  - PgUp/PgDn or Ctrl+U/Ctrl+D: page up/down")
    lines.append("  - Home/End or Ctrl+H/Ctrl+E: jump to top/bottom")
    lines.append("  - ESC or 'q': exit viewer")
    lines.append("")
    lines.append(f"{GREEN}Features:{RESET}")
    lines.append("  - ANSI color support (as you can see!)")
    lines.append("  - Scrollbar showing position")
    lines.append("  - Status line showing line number and percentage")
    lines.append("  - Horizontal scrolling for wide content")
    lines.append("")
    
    # Add some sample content with colors
    for i in range(1, 51):
        if i % 10 == 0:
            lines.append(f"{CYAN}{BOLD}─── Section {i // 10} ───{RESET}")
        elif i % 5 == 0:
            lines.append(f"{YELLOW}Line {i}: This is a highlighted line with important info{RESET}")
        elif i % 3 == 0:
            lines.append(f"{GREEN}Line {i}: Success message or positive content{RESET}")
        else:
            lines.append(f"Line {i}: Regular text content here. The quick brown fox jumps over the lazy dog.")
    
    lines.append("")
    lines.append(f"{RED}{BOLD}═══ End of Document ═══{RESET}")
    
    text = '\n'.join(lines)
    
    # Create viewer
    viewer = TextBufferViewer(
        x=1, y=1,
        width=79, height=24,
        show_status=True,
        show_scrollbar=True,
    )
    
    viewer.set_text(text)
    viewer.view()  # Blocks until user presses ESC
    
    clear_screen()
    writeln(f"{GREEN}Text Buffer Viewer Demo Complete!{RESET}")
    writeln()
    writeln("Press any key to continue...")
    with RawInput() as inp:
        inp.get_key()

"""
Multi-window demo for OpenDoors-compatible shadow screen buffer.

Demonstrates:
- Shadow buffer manipulation (ShadowScreen)
- Multiple overlapping windows with different border styles
- Incremental dirty-region painting (no flicker)
- Window Z-order management (bring to front)
- Per-window text buffers with typing support
- Save-under restoration
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from notorious_doorkit import (
    clear_screen,
    ShadowScreen,
    get_screen,
    set_screen,
    save_screen,
    restore_screen,
    set_attrib,
    RawInput,
    KEY_ESC,
    KEY_UP,
    KEY_DOWN,
    KEY_LEFT,
    KEY_RIGHT,
    KEY_BACKSPACE,
    KEY_ENTER,
)
from notorious_doorkit.lnwp_door import LnwpDoor


def opendoors_screen_demo(door: LnwpDoor) -> None:
    """
    Interactive multi-window demo showcasing shadow buffer and incremental painting.
    
    Controls:
    - 1/2/3: Open/activate windows
    - TAB: Cycle through windows (brings to front)
    - Arrow keys: Move active window
    - Typing: Type into active window
    - Backspace/Enter: Edit text in active window
    - C: Close active window
    - ESC: Exit demo
    """
    door.set_activity("OpenDoors Screen Demo")
    clear_screen()
    
    # Draw header using the shared draw_header helper from testdoor
    from testdoor import draw_header
    draw_header("OpenDoors Compatibility ─ Multi-Window Demo")

    # Initialize shadow buffer (80x25 default)
    screen = ShadowScreen(width=80, height=25)
    set_screen(screen)

    # Draw patterned background into shadow buffer
    for r in range(1, 26):
        for c in range(1, 81):
            ch = "." if ((r + c) % 2 == 0) else " "
            attr = 0x1E if (r % 2 == 0) else 0x1F
            screen.set_cell(r, c, ch, attr)

    # Write instructions
    screen.goto(2, 2)
    screen.write_text("Shadow buffer active (80x25). Multiple overlapping windows!", attr=0x1F)
    screen.goto(3, 2)
    screen.write_text("1-3: Open | TAB: Cycle | Arrows: Move | C: Close | ESC: Exit", attr=0x1F)
    screen.paint_all()

    # Save base snapshot for restore operations
    base_snap = save_screen()
    
    # Window state
    windows = []  # List of open windows (Z-order: first=bottom, last=top)
    active_idx = -1  # Index of active window in windows list
    toast_until = 0.0  # Timestamp when toast message expires

    # Window templates (id, position, title, style, colors)
    window_configs = [
        {"id": 1, "left": 10, "top": 5, "right": 50, "bottom": 12, "title": "Window 1 - Blue", "style": "single", "border_attr": 0x1F, "fill_attr": 0x1E},
        {"id": 2, "left": 25, "top": 8, "right": 65, "bottom": 16, "title": "Window 2 - Red", "style": "double", "border_attr": 0x4F, "fill_attr": 0x4E},
        {"id": 3, "left": 15, "top": 11, "right": 55, "bottom": 20, "title": "Window 3 - Green", "style": "ascii", "border_attr": 0x2F, "fill_attr": 0x2A},
    ]

    def _box_style(style: str) -> tuple[str, str, str, str, str, str]:
        """Return box drawing characters for the given style (tl, tr, bl, br, h, v)."""
        s = (style or "").lower()
        if s == "double":
            return ("╔", "╗", "╚", "╝", "═", "║")
        if s == "single":
            return ("┌", "┐", "└", "┘", "─", "│")
        return ("+", "+", "+", "+", "-", "|")

    def draw_window_to_shadow(cfg: dict, *, active: bool) -> None:
        """
        Draw a window into the shadow buffer (cells only, no terminal I/O).
        
        This updates the shadow buffer cells with the window's border, fill, title,
        and text content. It does NOT paint to the terminal - that's done separately
        by _repaint_dirty_region to minimize flicker.
        """
        screen = get_screen()
        l = int(cfg["left"])
        t = int(cfg["top"])
        r = int(cfg["right"])
        b = int(cfg["bottom"])
        fa = int(cfg["fill_attr"]) & 0xFF
        ba = int(cfg["border_attr"]) & 0xFF
        
        # Active window gets bright white border
        if active:
            ba = 0x0F

        tl, tr, bl, br, h, v = _box_style(str(cfg.get("style", "")))

        # Fill interior with fill_attr
        for rr in range(t, b + 1):
            for cc in range(l, r + 1):
                screen.set_cell(rr, cc, " ", fa)

        # Draw border if window is large enough
        if r - l >= 1 and b - t >= 1:
            screen.set_cell(t, l, tl, ba)
            screen.set_cell(t, r, tr, ba)
            screen.set_cell(b, l, bl, ba)
            screen.set_cell(b, r, br, ba)
            for cc in range(l + 1, r):
                screen.set_cell(t, cc, h, ba)
                screen.set_cell(b, cc, h, ba)
            for rr in range(t + 1, b):
                screen.set_cell(rr, l, v, ba)
                screen.set_cell(rr, r, v, ba)

            # Draw title in top border
            title = str(cfg.get("title") or "")
            if title:
                max_len = max(0, (r - l + 1) - 4)
                title = title[:max_len]
                start = l + 2
                for i, ch in enumerate(title):
                    screen.set_cell(t, start + i, ch, ba)

        # Render per-window text buffer into the interior
        text = cfg.get("text")
        if isinstance(text, list) and (r - l) >= 2 and (b - t) >= 2:
            inner_w = max(0, (r - l + 1) - 2)
            inner_h = max(0, (b - t + 1) - 2)
            for rr in range(inner_h):
                row_cells = "" if rr >= len(text) else str(text[rr] or "")
                row_cells = row_cells[:inner_w].ljust(inner_w, " ")
                for cc in range(inner_w):
                    screen.set_cell(t + 1 + rr, l + 1 + cc, row_cells[cc], fa)

    def _rect_overlaps(r1: tuple[int, int, int, int], r2: tuple[int, int, int, int]) -> bool:
        """Check if two rectangles (left, top, right, bottom) overlap."""
        l1, t1, r1_right, b1 = r1
        l2, t2, r2_right, b2 = r2
        return not (r1_right < l2 or r2_right < l1 or b1 < t2 or b2 < t1)

    def _restore_region_from_base(left: int, top: int, right: int, bottom: int) -> None:
        """Restore a rectangular region from the base snapshot into the shadow buffer."""
        screen = get_screen()
        for rr in range(int(top), int(bottom) + 1):
            for cc in range(int(left), int(right) + 1):
                if 1 <= rr <= 25 and 1 <= cc <= 80:
                    idx = (rr - 1) * 80 + (cc - 1)
                    if 0 <= idx < len(base_snap.cells):
                        cell = base_snap.cells[idx]
                        screen.set_cell(rr, cc, cell.ch, cell.attr)

    def _repaint_dirty_region(left: int, top: int, right: int, bottom: int) -> None:
        """
        Incremental dirty-region repaint to eliminate flicker.
        
        Steps:
        1. Restore the dirty region from base snapshot (shadow buffer cells)
        2. Redraw only windows that overlap the dirty region (shadow buffer cells)
        3. Paint only the dirty region to the terminal (single I/O operation)
        
        This minimizes terminal output and prevents full-screen repaints.
        """
        _restore_region_from_base(left, top, right, bottom)
        dirty_rect = (int(left), int(top), int(right), int(bottom))
        
        # Redraw overlapping windows into shadow buffer
        for idx, win_cfg in enumerate(windows):
            win_rect = (int(win_cfg["left"]), int(win_cfg["top"]), int(win_cfg["right"]), int(win_cfg["bottom"]))
            if _rect_overlaps(dirty_rect, win_rect):
                draw_window_to_shadow(win_cfg, active=(idx == active_idx))
        
        # Single paint of dirty region to terminal
        screen = get_screen()
        screen.paint_region(left, top, right, bottom)

    def repaint_all_windows() -> None:
        """Full screen repaint (used for initial draw and toast clear)."""
        restore_screen(base_snap)
        for idx, win_cfg in enumerate(windows):
            draw_window_to_shadow(win_cfg, active=(idx == active_idx))

    def _toast(msg: str, *, seconds: float = 1.0) -> None:
        """Show a brief message in the bottom-right corner."""
        nonlocal toast_until
        toast_until = time.time() + float(seconds)
        screen = get_screen()
        text = (str(msg) if msg is not None else "").strip()
        if not text:
            return
        row = 25
        col = max(1, 80 - len(text) + 1)
        for i, ch in enumerate(text[:80]):
            screen.set_cell(row, col + i, ch, 0x0E)
        screen.paint_region(col, row, 80, row)

    def _clear_toast_if_needed() -> None:
        """Clear toast message when it expires."""
        nonlocal toast_until
        if toast_until and time.time() >= toast_until:
            toast_until = 0.0
            repaint_all_windows()

    def _find_window_index_by_id(win_id: int) -> int:
        """Find window index by its ID, or -1 if not found."""
        for i, w in enumerate(windows):
            try:
                if int(w.get("id", -1)) == int(win_id):
                    return i
            except Exception:
                continue
        return -1

    def _bring_to_front(idx: int) -> None:
        """
        Bring a window to the front (top of Z-order).
        
        Moves the window to the end of the windows list and repaints
        the affected region (bounding box of all windows that changed Z-order).
        """
        nonlocal active_idx
        if idx < 0 or idx >= len(windows):
            return
        
        # Move window to end of list (top of Z-order)
        w = windows.pop(idx)
        windows.append(w)
        old_active = active_idx
        active_idx = len(windows) - 1
        _clamp_cursor(w)
        
        # Compute bounding box of affected windows and repaint
        affected_windows = set()
        for i in range(min(idx, old_active), len(windows)):
            if i < len(windows):
                affected_windows.add(i)
        
        if affected_windows:
            min_l = min(int(windows[i]["left"]) for i in affected_windows if i < len(windows))
            min_t = min(int(windows[i]["top"]) for i in affected_windows if i < len(windows))
            max_r = max(int(windows[i]["right"]) for i in affected_windows if i < len(windows))
            max_b = max(int(windows[i]["bottom"]) for i in affected_windows if i < len(windows))
            _repaint_dirty_region(min_l, min_t, max_r, max_b)
        else:
            _repaint_dirty_region(int(w["left"]), int(w["top"]), int(w["right"]), int(w["bottom"]))

    def _ensure_window_text(cfg: dict) -> None:
        """Initialize per-window text buffer and cursor if not present."""
        if "text" not in cfg or not isinstance(cfg.get("text"), list):
            cfg["text"] = [""]
        if "cursor" not in cfg or not isinstance(cfg.get("cursor"), tuple):
            cfg["cursor"] = (0, 0)

    def _inner_dims(cfg: dict) -> tuple[int, int]:
        """Calculate window interior dimensions (excluding border)."""
        l = int(cfg["left"])
        t = int(cfg["top"])
        r = int(cfg["right"])
        b = int(cfg["bottom"])
        inner_w = max(0, (r - l + 1) - 2)
        inner_h = max(0, (b - t + 1) - 2)
        return inner_w, inner_h

    def _clamp_cursor(cfg: dict) -> None:
        """Clamp window cursor to valid interior bounds."""
        _ensure_window_text(cfg)
        inner_w, inner_h = _inner_dims(cfg)
        row, col = cfg["cursor"]
        row = max(0, min(int(row), max(0, inner_h - 1)))
        col = max(0, min(int(col), max(0, inner_w - 1)))
        cfg["cursor"] = (row, col)
        while len(cfg["text"]) <= row:
            cfg["text"].append("")

    def _type_char(cfg: dict, ch: str) -> None:
        """Type a character into the active window at cursor position."""
        _ensure_window_text(cfg)
        inner_w, inner_h = _inner_dims(cfg)
        if inner_w <= 0 or inner_h <= 0:
            return

        row, col = cfg["cursor"]
        row = int(row)
        col = int(col)
        while len(cfg["text"]) <= row:
            cfg["text"].append("")

        line = str(cfg["text"][row] or "")
        if col >= inner_w:
            col = inner_w - 1
        if len(line) < col:
            line = line.ljust(col, " ")
        if col == len(line):
            line = line + ch
        else:
            line = line[:col] + ch + line[col + 1 :]
        cfg["text"][row] = line[:inner_w]

        # Advance cursor (wrap to next line if needed)
        col += 1
        if col >= inner_w:
            col = 0
            row = min(inner_h - 1, row + 1)
        cfg["cursor"] = (row, col)

    def _type_backspace(cfg: dict) -> None:
        """Handle backspace in the active window."""
        _ensure_window_text(cfg)
        inner_w, inner_h = _inner_dims(cfg)
        if inner_w <= 0 or inner_h <= 0:
            return

        row, col = cfg["cursor"]
        row = int(row)
        col = int(col)
        if row == 0 and col == 0:
            return
        if col == 0:
            row = max(0, row - 1)
            col = inner_w - 1
        else:
            col -= 1

        while len(cfg["text"]) <= row:
            cfg["text"].append("")
        line = str(cfg["text"][row] or "")
        if len(line) < col + 1:
            line = line.ljust(col + 1, " ")
        line = line[:col] + " " + line[col + 1 :]
        cfg["text"][row] = line[:inner_w]
        cfg["cursor"] = (row, col)

    def _type_newline(cfg: dict) -> None:
        """Handle enter/newline in the active window."""
        _ensure_window_text(cfg)
        inner_w, inner_h = _inner_dims(cfg)
        if inner_w <= 0 or inner_h <= 0:
            return
        row, _col = cfg["cursor"]
        row = min(inner_h - 1, int(row) + 1)
        cfg["cursor"] = (row, 0)
        while len(cfg["text"]) <= row:
            cfg["text"].append("")

    # Main input loop
    with RawInput(extended_keys=True) as inp:
        while True:
            _clear_toast_if_needed()
            k = inp.get_key(timeout=0.25)
            if k is None:
                continue
            if k == KEY_ESC:
                break

            # Arrow keys: move active window
            if k in (KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT):
                if windows and active_idx >= 0:
                    cfg = windows[active_idx]
                    old_l = int(cfg["left"])
                    old_t = int(cfg["top"])
                    old_r = int(cfg["right"])
                    old_b = int(cfg["bottom"])
                    
                    dy = -1 if k == KEY_UP else 1 if k == KEY_DOWN else 0
                    dx = -1 if k == KEY_LEFT else 1 if k == KEY_RIGHT else 0

                    l = old_l + dx
                    r = old_r + dx
                    t = old_t + dy
                    b = old_b + dy

                    # Clamp to screen bounds
                    if l < 1:
                        r += (1 - l)
                        l = 1
                    if t < 1:
                        b += (1 - t)
                        t = 1
                    if r > 80:
                        l -= (r - 80)
                        r = 80
                    if b > 25:
                        t -= (b - 25)
                        b = 25

                    cfg["left"], cfg["right"], cfg["top"], cfg["bottom"] = l, r, t, b
                    
                    # Repaint union of old and new positions (minimal dirty region)
                    dirty_l = min(old_l, l)
                    dirty_t = min(old_t, t)
                    dirty_r = max(old_r, r)
                    dirty_b = max(old_b, b)
                    _repaint_dirty_region(dirty_l, dirty_t, dirty_r, dirty_b)
                continue

            # Backspace: delete character
            if k == KEY_BACKSPACE or k == "\x7f":
                if windows and active_idx >= 0:
                    cfg = windows[active_idx]
                    _type_backspace(cfg)
                    _repaint_dirty_region(int(cfg["left"]), int(cfg["top"]), int(cfg["right"]), int(cfg["bottom"]))
                continue

            # Enter: newline
            if k == KEY_ENTER:
                if windows and active_idx >= 0:
                    cfg = windows[active_idx]
                    _type_newline(cfg)
                    _repaint_dirty_region(int(cfg["left"]), int(cfg["top"]), int(cfg["right"]), int(cfg["bottom"]))
                continue

            # Single character keys
            if isinstance(k, str) and len(k) == 1:
                ch = k.lower()
                
                # 1/2/3: Open or activate window
                if ch in ("1", "2", "3"):
                    win_id = int(ch)
                    existing_idx = _find_window_index_by_id(win_id)
                    if existing_idx >= 0:
                        _toast("Already open!")
                        _bring_to_front(existing_idx)
                    else:
                        template = next((w for w in window_configs if int(w.get("id", -1)) == win_id), None)
                        if template is not None:
                            cfg = dict(template)
                            _ensure_window_text(cfg)
                            windows.append(cfg)
                            active_idx = len(windows) - 1
                            _clamp_cursor(cfg)
                            _repaint_dirty_region(int(cfg["left"]), int(cfg["top"]), int(cfg["right"]), int(cfg["bottom"]))
                
                # C: Close active window
                elif ch == "c":
                    if windows:
                        idx = active_idx if active_idx >= 0 else (len(windows) - 1)
                        closed_win = windows[idx]
                        closed_l = int(closed_win["left"])
                        closed_t = int(closed_win["top"])
                        closed_r = int(closed_win["right"])
                        closed_b = int(closed_win["bottom"])
                        windows.pop(idx)
                        if not windows:
                            active_idx = -1
                        else:
                            active_idx = min(idx, len(windows) - 1)
                        _repaint_dirty_region(closed_l, closed_t, closed_r, closed_b)
                
                # TAB: Cycle windows (brings to front)
                elif ch == "\t" or k == "\t":
                    if windows:
                        next_idx = (active_idx + 1) % len(windows)
                        _bring_to_front(next_idx)

                # Printable characters: type into active window
                else:
                    if windows and active_idx >= 0 and len(ch) == 1:
                        if ord(ch) >= 32:
                            cfg = windows[active_idx]
                            _type_char(cfg, ch)
                            _repaint_dirty_region(int(cfg["left"]), int(cfg["top"]), int(cfg["right"]), int(cfg["bottom"]))

    # Cleanup
    set_attrib(0x07)
    clear_screen()

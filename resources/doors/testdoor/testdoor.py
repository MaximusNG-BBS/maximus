#!/usr/bin/env python3
"""
Example door demonstrating NotoriousPTY Door Kit features.

This door shows:
- ANSI file display
- Lightbar menus (basic and advanced)
- Input forms
- Activity management
- Raw input handling
"""

import sys
import os
import time
from typing import Optional

# Add notorious_doorkit to path — use the copy bundled with the smuggler door
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'smuggler'))

from notorious_doorkit import (
    Door,
    clear_screen, writeln, write, goto_xy,
    BLACK, CYAN, YELLOW, GREEN, WHITE, RED, RESET,
    BRIGHT_BLACK, BRIGHT_CYAN, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_WHITE, BRIGHT_RED,
    BG_BLACK, BG_RED, BG_YELLOW, BG_BLUE, BG_CYAN, BG_GREEN, BG_WHITE,
    BG_BRIGHT_YELLOW,
    BOLD, BLINK,
    LightbarMenu, AdvancedLightbarMenu, LightbarItem,
    RawInput, RegionEditor,
    KEY_ENTER, KEY_ESC, KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_BACKSPACE,
    ScrollingRegion, TextBufferViewer,
    get_runtime_config,
    printf,
    sprintf,
    disp_str,
    putch,
    repeat,
    disp,
    disp_emu,
    get_answer,
    play_ansi_music,
    hotkey_menu,
    key_pending,
    clear_keybuffer,
    input_str,
    ShadowScreen,
    get_screen,
    set_screen,
    gettext,
    puttext,
    save_screen,
    restore_screen,
    window_create,
    window_remove,
    set_attrib,
    display_file_paged,
)
from notorious_doorkit import AdvancedForm, FormField
from notorious_doorkit import ansi_box
from notorious_doorkit.forms import InputField
from notorious_doorkit.display import display_file
from notorious_doorkit.lnwp import RawLnwpEvent, MessageEvent, NodeInfoEvent, NodesInfoEvent
from scrolling_demo_funcs import scrolling_region_demo, text_buffer_viewer_demo
from screen_demo import opendoors_screen_demo


def draw_header(title: str, width: int = 78):
    """Draw a consistent header box with title."""
    ansi_box(
        x=1,
        y=1,
        width=width,
        height=3,
        style="double",
        border_color=f"{BRIGHT_CYAN}",
        fill_color="",
        fill_char=" ",
    )
    goto_xy(3, 2)
    write(f"{BRIGHT_WHITE}{title}{RESET}")


def main():
    has_dropfile_args = len(sys.argv) >= 3

    door = Door()
    if not has_dropfile_args:
        door.start_local(username="Local", node=1)
    else:
        door.start()

    door.set_activity("In Example Door")

    # Welcome screen
    clear_screen()
    draw_header("NotoriousPTY Door Kit Example Door")
    goto_xy(1, 5)
    writeln(f"{YELLOW}This door demonstrates the features of the")
    writeln(f"NotoriousPTY Door Kit library.{RESET}")
    writeln()
    writeln(f"{GREEN}Press any key to continue...{RESET}")
    
    with RawInput() as inp:
        inp.get_key()

    while True:
        clear_screen()
        door.set_activity("Main Menu")

        draw_header("TESTDOOR ─ Category Menu")
        goto_xy(1, 5)

        menu = LightbarMenu(
            items=[
                "Native / Doorkit Tests",
                "OpenDoors Compat Tests",
                "Example Doors",
                "Exit to BBS",
            ],
            x=5,
            y=6,
            width="auto",
            justify="left",
            selected_color=f"{WHITE}{BG_BLUE}{BOLD}",
            normal_color=f"{CYAN}",
            hotkeys=True,
            hotkey_format="[X]",
            hotkey_color=f"{YELLOW}{BOLD}",
            margin_inner=1,
            wrap=True,
        )

        choice = menu.run()
        if choice is None or choice == 3:
            break
        if choice == 0:
            native_tests_menu(door)
        elif choice == 1:
            opendoors_compat_menu(door)
        elif choice == 2:
            example_doors_menu(door)

    door.set_activity("")
    clear_screen()
    writeln(f"{GREEN}Thanks for trying the Door Kit!{RESET}")
    writeln()


def opendoors_hotkey_menu_demo(door: Door):
    door.set_activity("OpenDoors Hotkey Menu Demo")
    clear_screen()

    ansi_path = os.path.join(os.path.dirname(__file__), "..", "chatdoor", "pychat_logo.ans")

    def go_text() -> Optional[str]:
        opendoors_text_demo(door)
        return None

    def go_input() -> Optional[str]:
        opendoors_input_demo(door)
        return None

    def quit_menu() -> Optional[str]:
        return "quit"

    hotkey_menu(
        ansi_path,
        {
            "T": go_text,
            "I": go_input,
            "Q": quit_menu,
        },
        clear=True,
        redraw=True,
        overlay_mode=2,
        overlay_pos=(20, 3),
        overlay_items=[
            ("T", "Text demo"),
            ("I", "Input demo"),
            ("Q", "Quit"),
            ("ESC", "Back"),
        ],
        overlay_hotkey_format="[X]",
        overlay_hotkey_color=f"{YELLOW}{BOLD}",
        overlay_text_color=f"{CYAN}",
    )
    return


def native_tests_menu(door: Door) -> None:
    while True:
        clear_screen()
        door.set_activity("Native Tests")

        draw_header("Native / Doorkit Tests")
        goto_xy(1, 5)

        menu = LightbarMenu(
            items=[
                "Lightbar Menu (Basic)",
                "Lightbar Menu (Advanced)",
                "Forms (Basic)",
                "Forms (Advanced)",
                "New User Questionnaire",
                "Region Editor",
                "Scrolling Region",
                "Text Buffer Viewer",
                "Paged ANSI File Viewer",
                "ANSI Color Demo",
                "Terminal Autodetect (Caps + Size)",
                "Door32 / LNWP Probe",
                "Back",
            ],
            x=5,
            y=5,
            width="auto",
            justify="left",
            selected_color=f"{WHITE}{BG_BLUE}{BOLD}",
            normal_color=f"{CYAN}",
            hotkeys=True,
            hotkey_format="[X]",
            hotkey_color=f"{YELLOW}{BOLD}",
            margin_inner=1,
            wrap=True,
        )

        choice = menu.run()
        if choice is None or choice == 12:
            break
        elif choice == 0:
            basic_lightbar_demo(door)
        elif choice == 1:
            advanced_lightbar_demo(door)
        elif choice == 2:
            input_form_demo(door)
        elif choice == 3:
            advanced_form_demo(door)
        elif choice == 4:
            questionnaire_demo(door)
        elif choice == 5:
            region_editor_demo(door)
        elif choice == 6:
            scrolling_region_demo(door)
        elif choice == 7:
            text_buffer_viewer_demo(door)
        elif choice == 8:
            paged_file_viewer_demo(door)
        elif choice == 9:
            color_demo(door)
        elif choice == 10:
            terminal_autodetect_demo(door)
        elif choice == 11:
            door32_probe_demo(door)


def example_doors_menu(door: Door) -> None:
    while True:
        clear_screen()
        door.set_activity("Example Doors")

        draw_header("Example Doors")
        goto_xy(1, 5)

        menu = LightbarMenu(
            items=[
                "Hello World (Minimal Door)",
                "ANSI Music (Happy Birthday)",
                "Vote (Survey/Polling Door)",
                "Back",
            ],
            x=5,
            y=6,
            width="auto",
            justify="left",
            selected_color=f"{WHITE}{BG_BLUE}{BOLD}",
            normal_color=f"{CYAN}",
            hotkeys=True,
            hotkey_format="[X]",
            hotkey_color=f"{YELLOW}{BOLD}",
            margin_inner=1,
            wrap=True,
        )

        choice = menu.run()
        if choice is None or choice == 3:
            break
        if choice == 0:
            import ex_hello
            ex_hello.main()
        elif choice == 1:
            import ex_music
            ex_music.main()
        elif choice == 2:
            import ex_vote
            ex_vote.main()


def opendoors_compat_menu(door: Door) -> None:
    while True:
        clear_screen()
        door.set_activity("OpenDoors Compat")

        draw_header("OpenDoors Compatibility Tests")
        goto_xy(1, 5)

        menu = LightbarMenu(
            items=[
                "Output/Text Smoke Test (printf + shims)",
                "Input Smoke Test (get_answer + shims)",
                "Hotkey Menu Demo (ANSI file + key map)",
                "Screen/Windows Demo (shadow buffer)",
                "Back",
            ],
            x=5,
            y=6,
            width="auto",
            justify="left",
            selected_color=f"{WHITE}{BG_BLUE}{BOLD}",
            normal_color=f"{CYAN}",
            hotkeys=True,
            hotkey_format="[X]",
            hotkey_color=f"{YELLOW}{BOLD}",
            margin_inner=1,
            wrap=True,
        )

        choice = menu.run()
        if choice is None or choice == 4:
            break
        elif choice == 0:
            opendoors_text_demo(door)
        elif choice == 1:
            opendoors_input_demo(door)
        elif choice == 2:
            opendoors_hotkey_menu_demo(door)
        elif choice == 3:
            opendoors_screen_demo(door)


def _fmt_bool01(s: str) -> str:
    return "yes" if (s or "").strip() == "1" else "no"


def _print_node_info_fields(fields: dict) -> None:
    node_id = fields.get("NODE_ID", "")
    username = fields.get("USERNAME", "")
    activity = fields.get("ACTIVITY", "")
    door_mode = _fmt_bool01(fields.get("DOOR_MODE", "0"))
    door_id = fields.get("DOOR_ID", "")
    writeln(f"[NODE_INFO] node={node_id} user='{username}' activity='{activity}' door_mode={door_mode} door_id='{door_id}'")


def _print_nodes_info(nodes_info: dict) -> None:
    writeln(f"[NODES_INFO] {len(nodes_info)} nodes")
    for nid in sorted(nodes_info.keys()):
        info = nodes_info.get(nid, {}) or {}
        username = info.get("USERNAME", "")
        activity = info.get("ACTIVITY", "")
        door_mode = _fmt_bool01(info.get("DOOR_MODE", "0"))
        door_id = info.get("DOOR_ID", "")
        writeln(f"  node {nid:>2}: user='{username}' activity='{activity}' door_mode={door_mode} door_id='{door_id}'")


def _probe_print_menu(push_on: bool) -> None:
    writeln(f"{YELLOW}Commands:{RESET}")
    writeln("  A - ARM_LNWP")
    writeln("  D - DISARM_LNWP")
    writeln("  R - RAW_MODE ON")
    writeln("  C - RAW_MODE OFF")
    writeln(f"  P - PUSH_MSG toggle (currently: {'ON' if push_on else 'OFF'})")
    writeln("  N - REQ_INFO NODES_INFO")
    writeln("  I - REQ_INFO NODE_INFO")
    writeln("  T - Update activity (cycles)")
    writeln("  ? - Show this menu")
    writeln("  ESC - Exit")
    writeln()


def _probe_drain_lnwp_events(door: Door, max_iters: int = 25) -> int:
    total = 0
    for _ in range(max_iters):
        events, _passthrough = door.poll_events(timeout=0.0)
        if not events:
            break
        for ev in events:
            total += 1
            if isinstance(ev, NodesInfoEvent):
                _print_nodes_info(ev.nodes_info)
                continue
            if isinstance(ev, NodeInfoEvent):
                _print_node_info_fields(ev.fields)
                continue
            if isinstance(ev, MessageEvent):
                prm = ev.fields.get("PRM", "")
                box = ev.fields.get("BOX", "")
                tag = ev.fields.get("TAG", "")
                frm = ev.fields.get("FROM_NODE", ev.fields.get("FROM", ""))
                writeln(f"[LNWP] MSG prm={prm} box={box} tag={tag} from={frm}")
                continue
            if isinstance(ev, RawLnwpEvent):
                prm = ev.fields.get("PRM", "")
                val = ev.fields.get("VAL", "")
                writeln(f"[LNWP] kind={ev.kind} prm={prm} val={val}")
                continue
            writeln(f"[LNWP] {type(ev).__name__}: {ev}")
    return total


def door32_probe_demo(door: Door) -> None:
    door.set_activity("Door32 Probe")
    clear_screen()
    draw_header("Door32 / LNWP Protocol Probe")
    goto_xy(1, 5)

    writeln(f"{CYAN}═══ DOOR32 PROBE ═══{RESET}")
    writeln()
    writeln(f"door32_mode={door.door32_mode} terminal_fd={door.terminal_fd} control_fd={door.control_fd}")
    writeln()
    writeln(f"{GREEN}FD3 is terminal bytes. FD4 is LNWP control frames. This probe exercises both.{RESET}")
    writeln()

    push_on = False
    activity_n = 0

    door.arm()
    door.set_activity("Doorkit Door32 Probe")

    _probe_print_menu(push_on)

    with RawInput(extended_keys=True) as inp:
        while True:
            _probe_drain_lnwp_events(door)

            k = inp.get_key(timeout=0.25)
            if k is None:
                continue
            if k == KEY_ESC:
                break

            if isinstance(k, str) and len(k) == 1:
                ch = k.lower()
                if ch == "a":
                    door.arm()
                    writeln("[CMD] ARM_LNWP")
                elif ch == "d":
                    door.disarm()
                    writeln("[CMD] DISARM_LNWP")
                elif ch == "r":
                    door.set_input_mode("raw")
                    writeln("[CMD] RAW_MODE ON")
                elif ch == "c":
                    door.set_input_mode("cooked")
                    writeln("[CMD] RAW_MODE OFF")
                elif ch == "p":
                    push_on = not push_on
                    door.set_push_messages(push_on)
                    writeln(f"[CMD] PUSH_MSG {'ON' if push_on else 'OFF'}")
                elif ch == "n":
                    door.request_nodes_info(keys=["*"])
                    writeln("[CMD] REQ_INFO NODES_INFO")
                elif ch == "i":
                    door.request_node_info(keys=["*"])
                    writeln("[CMD] REQ_INFO NODE_INFO")
                elif ch == "t":
                    activity_n += 1
                    door.set_activity(f"Doorkit Probe #{activity_n}")
                    writeln(f"[CMD] ACTIVITY Doorkit Probe #{activity_n}")
                elif ch == "?":
                    _probe_print_menu(push_on)
                else:
                    writeln(f"KEY={repr(k)}")
            else:
                writeln(f"KEY={repr(k)}")

    door.set_input_mode("cooked")
    door.set_activity("Main Menu")
    return


def opendoors_input_demo(door: Door):
    """Demonstrate OpenDoors 2/12 input compatibility APIs."""
    door.set_activity("OpenDoors Input Demo")
    clear_screen()
    
    draw_header("OpenDoors Compatibility ─ Input Smoke Test")
    
    goto_xy(1, 4)
    writeln(f"{CYAN}Testing OpenDoors 2/12 input compatibility functions{RESET}")
    writeln()
    
    # Test 1: get_answer
    goto_xy(1, 7)
    writeln(f"{BRIGHT_CYAN}[1] get_answer(){RESET}")
    writeln(f"  {CYAN}Press Y or N:{RESET}")
    write(f"  {BRIGHT_YELLOW}Your choice:{RESET} ")
    answer = get_answer("YN")
    writeln(f"{GREEN}{answer}{RESET}")
    writeln()
    
    # Test 2: key_pending and clear_keybuffer
    goto_xy(1, 12)
    writeln(f"{BRIGHT_CYAN}[2] key_pending() + clear_keybuffer(){RESET}")
    writeln(f"  {CYAN}Type some keys quickly, then wait...{RESET}")
    import time
    time.sleep(2)
    if key_pending():
        writeln(f"  {BRIGHT_GREEN}Keys detected in buffer!{RESET}")
        clear_keybuffer()
        writeln(f"  {BRIGHT_YELLOW}Buffer cleared.{RESET}")
    else:
        writeln(f"  {BRIGHT_YELLOW}No keys waiting.{RESET}")
    writeln()
    
    # Test 3: input_str
    goto_xy(1, 17)
    writeln(f"{BRIGHT_CYAN}[3] input_str(){RESET}")
    writeln(f"  {CYAN}Enter a 2-digit number (0-9 only):{RESET}")
    write(f"  {BRIGHT_YELLOW}Number:{RESET} ")
    num = input_str(2, ord('0'), ord('9'))
    if num:
        writeln(f"  {BRIGHT_GREEN}You entered:{RESET} {num}")
    
    goto_xy(1, 22)
    writeln(f"{CYAN}Press any key to continue...{RESET}")
    with RawInput() as inp:
        inp.get_key()


def opendoors_text_demo(door: Door):
    door.set_activity("OpenDoors Text Demo")
    clear_screen()

    # Draw header box
    draw_header("OpenDoors Compatibility ─ Output/Text Smoke Test")
    
    # Draw AVATAR demo box in upper right below header
    box_x = 69
    box_y = 5
    box_w = 11
    box_h = 3
    ansi_box(
        x=box_x,
        y=box_y,
        width=box_w,
        height=box_h,
        style="single",
        border_color=f"{CYAN}{BG_BLACK}",
        fill_color=f"{BG_BLUE}",
        fill_char=" ",
    )
    goto_xy(box_x + 1, box_y + 1)
    write(f"{BOLD}{YELLOW}{BG_BLUE} AVATAR! {RESET}")
    
    # Position cursor below header box for config line
    goto_xy(1, 4)
    cfg = get_runtime_config()
    writeln(f"{CYAN}Config:{RESET} expand_ra_qbbs={WHITE}{cfg.text.expand_ra_qbbs}{RESET} delimiter={WHITE}{cfg.text.color_delimiter!r}{RESET}")
    writeln()

    # LEFT COLUMN - Tests 1-3
    goto_xy(1, 7)
    writeln(f"{BRIGHT_CYAN}[1] printf(){RESET}")
    writeln(f"  {CYAN}Backtick colors:{RESET}")
    printf("  `GREEN`GRN`WHITE` `RED`RED`WHITE` `BRIGHT YELLOW BLUE`YEL/BLU`WHITE`\r\n")
    writeln()
    
    goto_xy(1, 11)
    writeln(f"{BRIGHT_CYAN}[2] sprintf(){RESET}")
    writeln(f"  {BRIGHT_GREEN}Exp:{RESET} Hello world 123 %")
    writeln(f"  {BRIGHT_YELLOW}Act:{RESET} {sprintf('Hello %s %d %%', 'world', 123)}")
    writeln()
    
    goto_xy(1, 15)
    writeln(f"{BRIGHT_CYAN}[3] RA/QBBS{RESET}")
    writeln(f"  {BRIGHT_GREEN}Exp (ON):{RESET}  User: Kevin")
    printf(f"  {BRIGHT_YELLOW}Act (ON):{RESET}  User: \x06A\r\n", expand_ra_qbbs=True, ra_qbbs_f_map={"A": "Kevin"})
    writeln(f"  {BRIGHT_GREEN}Exp (OFF):{RESET} User: [ctrl]")
    printf(f"  {BRIGHT_YELLOW}Act (OFF):{RESET} User: \x06A\r\n", expand_ra_qbbs=False, ra_qbbs_f_map={"A": "Kevin"})

    # RIGHT COLUMN - Tests 4-5
    goto_xy(40, 7)
    writeln(f"{BRIGHT_CYAN}[4] Thin Shims{RESET}")
    goto_xy(40, 8)
    writeln(f"  {BRIGHT_GREEN}Exp:{RESET} X ----------")
    goto_xy(40, 9)
    disp_str(f"  {BRIGHT_YELLOW}Act:{RESET} ")
    putch("X")
    disp_str(" ")
    repeat("-", 10)
    goto_xy(40, 10)
    writeln(f"  {BRIGHT_GREEN}Exp:{RESET} RAWBYTES")
    goto_xy(40, 11)
    disp_str(f"  {BRIGHT_YELLOW}Act:{RESET} ")
    disp(b"RAWBYTES")
    
    goto_xy(40, 13)
    writeln(f"{BRIGHT_CYAN}[5] disp_emu(){RESET}")
    goto_xy(40, 14)
    writeln(f"  {CYAN}See box above →{RESET}")
    goto_xy(40, 15)
    writeln(f"  {BRIGHT_GREEN}AVATAR positioning{RESET}")

    goto_xy(1, 22)
    writeln(f"{CYAN}Press any key to continue...{RESET}")
    with RawInput() as inp:
        inp.get_key()


def region_editor_demo(door: Door):
    """Demonstrate RegionEditor constrained to a boxed area."""
    door.set_activity("Region Editor Demo")
    clear_screen()
    draw_header("Region Editor Demo")
    goto_xy(1, 5)

    door.set_input_mode("editor")

    box_x, box_y = 4, 3
    box_w, box_h = 72, 20
    ansi_box(
        x=box_x,
        y=box_y,
        width=box_w,
        height=box_h,
        style="double",
        border_color=f"{WHITE}{BG_BLUE}{BOLD}",
        fill_color=f"{WHITE}{BG_BLACK}",
        fill_char=" ",
    )

    title = "Region Editor Demo"
    goto_xy(box_x + (box_w - len(title)) // 2, box_y + 1)
    write(f"{WHITE}{BG_BLUE}{BOLD}{title}{RESET}")

    goto_xy(box_x + 2, box_y + box_h - 2)
    write(f"{WHITE}{BG_BLUE}CTRL+S=Save  ESC=Cancel  PgUp/PgDn/^U/^D=Page  Ins=Toggle  Del=FwdDel{RESET}")

    editor = RegionEditor(
        x1=box_x + 2,
        y1=box_y + 3,
        x2=box_x + box_w - 3,
        y2=box_y + box_h - 4,
        show_scrollbar=True,
    )

    initial = "This is a boxed RegionEditor.\n\nTry editing, then press Ctrl+S to save.\nOr press ESC to cancel." \
        "\n\n(Mode alias used: door.set_input_mode(\"editor\"))"

    result = editor.edit(initial=initial)

    door.set_input_mode("menu")

    clear_screen()
    writeln(f"{CYAN}═══ REGION EDITOR RESULT ═══{RESET}")
    writeln()
    if result is None:
        writeln(f"{YELLOW}Canceled (ESC).{RESET}")
    else:
        writeln(f"{GREEN}Saved text:{RESET}")
        writeln()
        for line in result.split("\n"):
            writeln(line)
    writeln()
    writeln("Press any key to continue...")
    with RawInput() as inp:
        inp.get_key()


def questionnaire_demo(door: Door):
    """Demonstrate a masked, required-field questionnaire form."""
    door.set_activity("New User Questionnaire")
    clear_screen()
    draw_header("New User Questionnaire")
    goto_xy(1, 5)

    box_x, box_y = 4, 2
    box_w, box_h = 72, 22
    ansi_box(
        x=box_x,
        y=box_y,
        width=box_w,
        height=box_h,
        style="double",
        border_color=f"{WHITE}{BG_BLUE}{BOLD}",
        fill_color=f"{WHITE}{BG_BLUE}",
        fill_char=" ",
    )

    title = "New User Questionaire"
    goto_xy(box_x + (box_w - len(title)) // 2, box_y + 1)
    write(f"{WHITE}{BG_BLUE}{BOLD}{title}{RESET}")

    label_color = f"{WHITE}{BG_BLUE}"
    input_color = f"{WHITE}{BG_BLACK}"
    focus_color = f"{WHITE}{BG_RED}{BOLD}"

    ox = box_x + 2
    oy = box_y + 2

    def rq(label: str, required: bool) -> str:
        return f"{label}*" if required else label

    def field_x(label_x: int, label: str) -> int:
        return label_x + len(label) + 2

    ap = 9

    fields = [
        FormField(name="real_name", x=field_x(ox + 0, rq("Enter your REAL NAME", True)), y=oy + 0, width=34, label=rq("Enter your REAL NAME", True), required=True, max_length=34),

        FormField(name="home_phone", x=field_x(ox + 0, rq("Enter your HOME phone number", True)), y=oy + 2, width=14, label=rq("Enter your HOME phone number", True), required=True, format_mask="(000) 000-0000", max_length=10),
        FormField(name="data_phone", x=field_x(ox + 0, "Enter your DATA phone number"), y=oy + 3, width=14, label="Enter your DATA phone number", format_mask="(000) 000-0000", max_length=10),

        FormField(
            name="sex",
            x=field_x(ox + 0, rq("Enter your sex (Male, Female or Nondisclosed)", True)),
            y=oy + 5,
            width=14,
            label=rq("Enter your sex (Male, Female or Nondisclosed)", True),
            required=True,
            value="N",
            options=[("M", "Male"), ("F", "Female"), ("N", "Nondisclosed")],
        ),
        FormField(name="dob", x=field_x(ox + 0, rq("Enter your date of birth", True)), y=oy + 6, width=8, label=rq("Enter your date of birth", True), required=True, format_mask="00/00/00", max_length=6),

        FormField(name="company", x=field_x(ox + 0, "Your Company Name"), y=oy + (ap - 1), width=30, label="Your Company Name", max_length=30),

        FormField(name="addr1", x=field_x(ox + 1, rq("Address line 1", True)), y=oy + (ap + 2), width=30, label=rq("Address line 1", True), required=True, max_length=30),
        FormField(name="addr2", x=field_x(ox + 1, "Address line 2"), y=oy + (ap + 3), width=30, label="Address line 2", max_length=30),
        FormField(name="city", x=field_x(ox + 1, rq("City", True)), y=oy + (ap + 4), width=30, label=rq("City", True), required=True, max_length=30),
        FormField(name="state", x=field_x(ox + 39, rq("State", True)), y=oy + (ap + 4), width=2, label=rq("State", True), required=True, format_mask="AA", max_length=2, normalize=lambda s: (s or "").strip().upper()),
        FormField(name="zip", x=field_x(ox + 59, rq("ZIP", True)), y=oy + (ap + 4), width=5, label=rq("ZIP", True), required=True, format_mask="00000", max_length=5),
        FormField(name="country", x=field_x(ox + 1, rq("Country", True)), y=oy + (ap + 5), width=30, label=rq("Country", True), required=True, max_length=30),

        FormField(
            name="use_hotkeys",
            x=field_x(ox + 1, rq("Use hot keys in menus?", True)),
            y=oy + (ap + 8),
            width=3,
            label=rq("Use hot keys in menus?", True),
            required=True,
            value="No",
            options=[("No", "No"), ("Yes", "Yes")],
        ),
    ]

    form = AdvancedForm(
        fields,
        wrap=True,
        save_mode="esc_prompt",
        label_color=label_color,
        input_color=input_color,
        focus_color=focus_color,
        required_splash_text="You must fill out required fields",
        required_splash_x=box_x + 2,
        required_splash_y=box_y + box_h - 3,
        required_splash_color=f"{YELLOW}{BG_BLUE}{BOLD}",
    )

    goto_xy(box_x + 2, box_y + box_h - 2)
    write(f"{WHITE}{BG_BLUE}CTRL+S=Save  ESC=Menu  Arrows=Move  Enter=Edit{RESET}")

    result = form.run()
    if result is None:
        return

    clear_screen()
    writeln(f"{GREEN}Questionnaire submitted!{RESET}")
    writeln()
    for k, v in result.items():
        writeln(f"{k}: {v}")
    writeln()
    writeln("Press any key to continue...")
    with RawInput() as inp:
        inp.get_key()


def basic_lightbar_demo(door: Door):
    """Demonstrate basic lightbar menu."""
    door.set_activity("Basic Lightbar Demo")
    clear_screen()
    
    draw_header("Basic Lightbar Demo")
    goto_xy(1, 5)
    writeln("This menu uses uniform positioning and width.")
    writeln("Use arrow keys to navigate, Enter to select, ESC to go back.")
    writeln()
    
    menu = LightbarMenu(
        items=[
            "Option One",
            "Option Two",
            "Option Three",
            "A Very Long Option Name Here",
            "Short",
            "Back"
        ],
        x=10, y=10,
        width="auto",  # Width of longest item
        justify="center",
        selected_color=f"{WHITE}{BG_BLUE}{BOLD}",
        normal_color=f"{CYAN}",
        hotkeys=True,
        hotkey_format="underline",
        hotkey_color=f"{RED}{BOLD}",
        margin_inner=1,
        wrap=True
    )
    
    choice = menu.run()
    
    if choice is not None and choice < 5:
        clear_screen()
        writeln(f"{GREEN}You selected: {menu.items[choice]}{RESET}")
        writeln()
        writeln("Press any key to continue...")
        with RawInput() as inp:
            inp.get_key()


def advanced_form_demo(door: Door):
    """Demonstrate positioned, multi-field form with arrow navigation."""
    door.set_activity("Advanced Form Demo")
    clear_screen()

    draw_header("Advanced Form Demo")
    goto_xy(1, 5)
    writeln("Arrow keys or hotkeys (N/A/H/P) move between fields.")
    writeln("Enter edits the focused field.")
    writeln("ESC shows save prompt. Ctrl+S saves directly.")
    writeln()

    label_color = f"{YELLOW}{BOLD}"
    input_color = f"{WHITE}{BG_BLUE}"
    focus_color = f"{BLACK}{BG_BRIGHT_YELLOW}{BOLD}"

    fields = [
        FormField(name="name", x=25, y=8, width=22, label="Name", max_length=22, hotkey="n"),
        FormField(name="age", x=25, y=10, width=3, label="Age", max_length=3, hotkey="a"),
        FormField(name="handle", x=25, y=12, width=22, label="Handle", max_length=22, hotkey="h"),
        FormField(name="password", x=25, y=14, width=22, label="Password", max_length=22, mask=True, hotkey="p"),
    ]

    form = AdvancedForm(
        fields,
        wrap=True,
        save_mode="esc_prompt",
        label_color=label_color,
        input_color=input_color,
        focus_color=focus_color,
    )

    result = form.run()
    if result is None:
        return

    clear_screen()
    writeln(f"{GREEN}Form submitted!{RESET}")
    writeln()
    writeln(f"Name: {result.get('name', '')}")
    writeln(f"Age: {result.get('age', '')}")
    writeln(f"Handle: {result.get('handle', '')}")
    pw = result.get('password', '')
    writeln(f"Password: {'*' * len(pw)}")
    writeln()
    writeln("Press any key to continue...")
    with RawInput() as inp:
        inp.get_key()


def advanced_lightbar_demo(door: Door):
    """Demonstrate advanced lightbar menu with custom positioning."""
    door.set_activity("Advanced Lightbar Demo")
    clear_screen()
    
    draw_header("Advanced Lightbar Demo")
    goto_xy(1, 5)
    writeln("This menu has individually positioned items.")
    writeln()
    
    # Create a two-column menu
    items = [
        LightbarItem("New Game", x=10, y=8, width=20, justify="center", hotkey="n"),
        LightbarItem("Load Game", x=10, y=10, width=20, justify="center", hotkey="l"),
        LightbarItem("Save Game", x=10, y=12, width=20, justify="center", hotkey="s"),
        LightbarItem("Options", x=40, y=8, width=15, justify="left", hotkey="o"),
        LightbarItem("Help", x=40, y=10, width=15, justify="left", hotkey="h"),
        LightbarItem("Quit", x=40, y=12, width=15, justify="left", hotkey="q"),
    ]
    
    menu = AdvancedLightbarMenu(
        items,
        selected_color=f"{WHITE}{BG_BLUE}{BOLD}",
        normal_color=f"{CYAN}",
        hotkeys=True,
        margin_inner=1,
        wrap=True
    )
    
    choice = menu.run()
    
    if choice is not None:
        clear_screen()
        writeln(f"{GREEN}You selected: {items[choice].text}{RESET}")
        writeln()
        writeln("Press any key to continue...")
        with RawInput() as inp:
            inp.get_key()


def input_form_demo(door: Door):
    """Demonstrate input forms."""
    door.set_activity("Input Form Demo")
    clear_screen()
    
    draw_header("Input Form Demo")
    goto_xy(1, 5)
    writeln("Fill out the form below:")
    writeln()
    
    # Name field
    name_field = InputField(
        prompt=f"{YELLOW}Name: {WHITE}",
        max_length=30,
        default=""
    )
    name = name_field.get_input()
    
    if name is None:
        return
    
    # Age field
    age_field = InputField(
        prompt=f"{YELLOW}Age: {WHITE}",
        max_length=3,
        default=""
    )
    age = age_field.get_input()
    
    if age is None:
        return
    
    # Password field
    password_field = InputField(
        prompt=f"{YELLOW}Password: {WHITE}",
        max_length=20,
        default="",
        mask=True
    )
    password = password_field.get_input()
    
    if password is None:
        return
    
    # Show results
    writeln()
    writeln(f"{GREEN}Form submitted!{RESET}")
    writeln()
    writeln(f"Name: {name}")
    writeln(f"Age: {age}")
    writeln(f"Password: {'*' * len(password)}")
    writeln()
    writeln("Press any key to continue...")
    with RawInput() as inp:
        inp.get_key()


def terminal_autodetect_demo(door: Door):
    """Manually run terminal capability and window size detection."""
    from notorious_doorkit.input import detect_capabilities_probe, detect_window_size_probe, clear_keybuffer
    
    door.set_activity("Terminal Autodetect")
    clear_screen()
    
    draw_header("Terminal Autodetect Demo")
    goto_xy(1, 5)
    
    writeln(f"{YELLOW}This will probe your terminal for capabilities and window size.{RESET}")
    writeln(f"{CYAN}(BBS/dropfile info is preserved; probes only fill missing fields){RESET}")
    writeln()
    writeln(f"{CYAN}Current terminal info:{RESET}")
    writeln(f"  Capabilities: {door.session.terminal.capabilities}")
    writeln(f"  Rows: {door.session.terminal.rows}")
    writeln(f"  Cols: {door.session.terminal.cols}")
    writeln()
    writeln(f"{GREEN}Press any key to run detection...{RESET}")
    
    with RawInput() as inp:
        inp.get_key()
    
    # Save original values from dropfile/BBS
    orig_caps = door.session.terminal.capabilities
    orig_rows = door.session.terminal.rows
    orig_cols = door.session.terminal.cols
    
    writeln()
    writeln(f"{BRIGHT_CYAN}Detecting capabilities...{RESET}")
    term = detect_capabilities_probe(timeout_ms=500)
    # Only update if we had no capabilities before
    if not orig_caps or orig_caps == ["ascii"]:
        door.session.terminal.capabilities = term.capabilities
        writeln(f"  Result: {term.capabilities}")
    else:
        writeln(f"  Skipped (using dropfile/BBS: {orig_caps})")
    
    writeln()
    writeln(f"{BRIGHT_CYAN}Detecting window size...{RESET}")
    sz = detect_window_size_probe(timeout_ms=500)
    if sz is not None:
        probed_rows = int(sz[0])
        probed_cols = int(sz[1])
        if orig_rows != probed_rows:
            door.session.terminal.rows = probed_rows
        if orig_cols != probed_cols:
            door.session.terminal.cols = probed_cols
        writeln(f"  Result: {probed_rows} rows x {probed_cols} cols")
    else:
        writeln(f"  {RED}No response (timeout){RESET}")
    
    writeln()
    writeln(f"{GREEN}Final terminal info:{RESET}")
    writeln(f"  Capabilities: {door.session.terminal.capabilities}")
    writeln(f"  Rows: {door.session.terminal.rows}")
    writeln(f"  Cols: {door.session.terminal.cols}")
    writeln()
    writeln(f"{YELLOW}Press any key to return to menu...{RESET}")
    with RawInput() as inp:
        inp.get_key()
    
    # Clear any stray probe responses before returning to menu
    clear_keybuffer()


def paged_file_viewer_demo(door: Door):
    """Demonstrate paged ANSI file viewing."""
    door.set_activity("Paged ANSI Viewer")
    clear_screen()
    
    draw_header("Paged ANSI File Viewer Demo")
    goto_xy(1, 5)
    
    writeln(f"{YELLOW}This demo shows display_file_paged() with a long ANSI file.{RESET}")
    writeln(f"{CYAN}The file will page at (rows-1) lines with a pause prompt.{RESET}")
    writeln()
    writeln(f"{GREEN}Press any key to start...{RESET}")

    with RawInput() as inp:
        inp.get_key()
    
    clear_screen()
    
    # Display the id22-intro.ans file with paging
    ansi_path = "id22-intro.ans"
    
    if os.path.exists(ansi_path):
        display_file_paged(
            ansi_path,
            pause_prompt=f"{BRIGHT_YELLOW}-- Press any key to continue --{RESET}",
            clear=False,
        )
    else:
        writeln(f"{RED}Error: id22-intro.ans not found!{RESET}")
        writeln()
        writeln(f"{YELLOW}Press any key to continue...{RESET}")
        with RawInput() as inp:
            inp.get_key()
        return
    
    writeln()
    writeln(f"{GREEN}End of file. Press any key to return to menu...{RESET}")
    with RawInput() as inp:
        inp.get_key()


def color_demo(door: Door):
    """Demonstrate ANSI colors."""
    door.set_activity("Color Demo")
    clear_screen()
    
    from notorious_doorkit.ansi import (
        BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE,
        BRIGHT_RED, BRIGHT_GREEN, BRIGHT_YELLOW, BRIGHT_BLUE,
        BRIGHT_MAGENTA, BRIGHT_CYAN, BRIGHT_WHITE
    )
    
    writeln(f"{CYAN}═══ COLOR DEMO ═══{RESET}")
    writeln()
    
    colors = [
        ("Black", BLACK),
        ("Red", RED),
        ("Green", GREEN),
        ("Yellow", YELLOW),
        ("Blue", BLUE),
        ("Magenta", MAGENTA),
        ("Cyan", CYAN),
        ("White", WHITE),
    ]
    
    bright_colors = [
        ("Bright Red", BRIGHT_RED),
        ("Bright Green", BRIGHT_GREEN),
        ("Bright Yellow", BRIGHT_YELLOW),
        ("Bright Blue", BRIGHT_BLUE),
        ("Bright Magenta", BRIGHT_MAGENTA),
        ("Bright Cyan", BRIGHT_CYAN),
        ("Bright White", BRIGHT_WHITE),
    ]
    
    writeln("Standard Colors:")
    for name, color in colors:
        writeln(f"  {color}{name:15}{RESET} The quick brown fox jumps over the lazy dog")
    
    writeln()
    writeln("Bright Colors:")
    for name, color in bright_colors:
        writeln(f"  {color}{name:15}{RESET} The quick brown fox jumps over the lazy dog")
    
    writeln()
    writeln("Press any key to continue...")
    with RawInput() as inp:
        inp.get_key()


if __name__ == "__main__":
    main()

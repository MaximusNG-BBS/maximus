#!/usr/bin/env python3
"""
TestDoor for NotoriousPTY

Simple interactive ANSI door to validate STDIO connectivity.

Usage:
    python testdoor.py <node_number> <path_to_DOOR.SYS>

Example:
    python testdoor.py 1 C:\\BBS\\NODE1\\DOOR.SYS
"""

import argparse
import os
import random
import sys
from typing import List, Tuple, Optional


# --- ANSI helpers ------------------------------------------------------------

class ANSI:
    RESET = "\x1b[0m"
    BOLD = "\x1b[1m"

    FG_BLACK = "\x1b[30m"
    FG_RED = "\x1b[31m"
    FG_GREEN = "\x1b[32m"
    FG_YELLOW = "\x1b[33m"
    FG_BLUE = "\x1b[34m"
    FG_MAGENTA = "\x1b[35m"
    FG_CYAN = "\x1b[36m"
    FG_WHITE = "\x1b[37m"

    BG_BLACK = "\x1b[40m"
    BG_RED = "\x1b[41m"
    BG_GREEN = "\x1b[42m"
    BG_YELLOW = "\x1b[43m"
    BG_BLUE = "\x1b[44m"
    BG_MAGENTA = "\x1b[45m"
    BG_CYAN = "\x1b[46m"
    BG_WHITE = "\x1b[47m"

    CLEAR = "\x1b[2J"
    HOME = "\x1b[H"


def println(text: str = "") -> None:
    """BBS-friendly line output using CRLF."""
    sys.stdout.write(text + "\r\n")
    sys.stdout.flush()


def send_lnwp_notify(payload: str) -> None:
    b = payload.encode("ascii", errors="strict")
    sys.stdout.buffer.write(bytes([0x10, 0x02, ord('N')]))
    sys.stdout.buffer.write(b)
    sys.stdout.buffer.write(bytes([0x10, 0x03]))
    sys.stdout.buffer.write(b"\r\n")
    sys.stdout.flush()


def send_lnwp_triple_sequence() -> None:
    send_lnwp_notify('LNWP V1 PRM=USERNAME VAL="LIMPINGNINJA"')
    send_lnwp_notify('LNWP V1 PRM=ACTIVITY VAL="LOGIN"')
    send_lnwp_notify('LNWP V1 PRM=USER_STAT KEY="FROM" VAL="VANCOUVER"')


def safe_input(prompt: str = "") -> str:
    """Input wrapper around sys.stdin.readline()."""
    if prompt:
        sys.stdout.write(prompt)
        sys.stdout.flush()
    try:
        if os.environ.get("TESTDOOR_DEBUG_STDIN"):
            raw = sys.stdin.buffer.readline()
            sys.stdout.write("\r\n[DEBUG] stdin bytes: " + repr(raw) + "\r\n")
            sys.stdout.flush()
            value = raw.decode("utf-8", errors="replace")
        else:
            value = sys.stdin.readline()
    except UnicodeDecodeError as e:
        return ""
    return value


def ansi_wrap(text: str, *codes: str, enabled: bool = True) -> str:
    if not enabled or not codes:
        return text
    return "".join(codes) + text + ANSI.RESET


# --- DOOR.SYS handling -------------------------------------------------------

def load_door_sys(path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Very light DOOR.SYS reader.

    We care about:
      - User full name  (line 10, index 9)
      - Graphics mode   (line 21, index 20) (GR / NG / 7E)

    Returns: (username, graphics_mode)
    """
    try:
        with open(path, "r", encoding="cp437", errors="replace") as f:
            lines = [line.rstrip("\r\n") for line in f]
    except FileNotFoundError:
        return None, None
    except OSError:
        return None, None

    username = lines[9].strip() if len(lines) >= 10 else None
    graphics_mode = lines[20].strip().upper() if len(lines) >= 21 else None
    return username or None, graphics_mode or None


# --- Word puzzle game --------------------------------------------------------

WORD_LIST = [
    "ANSI", "NODES", "MODEM", "ELITE", "DOORS", "SYSEX", "BYTES", "LOGIN",
    "CODES", "SYSOP", "LINES", "BOARD", "RINGS", "CARRIER", "TERMS"
]

# Filter down to 5-letter words only, uppercase
VALID_WORDS = sorted({w.upper() for w in WORD_LIST if len(w) == 5})


def choose_secret_word() -> str:
    return random.choice(VALID_WORDS)


def score_guess(secret: str, guess: str) -> List[str]:
    """
    Compare guess to secret (both 5-char strings).
    Returns a list of states per position: "correct", "present", "absent".
    """
    secret = secret.upper()
    guess = guess.upper()

    result = ["absent"] * 5
    remaining = list(secret)

    # First pass: correct positions
    for i in range(5):
        if guess[i] == secret[i]:
            result[i] = "correct"
            remaining[i] = None  # consume

    # Second pass: present but misplaced
    for i in range(5):
        if result[i] == "absent" and guess[i] in remaining:
            result[i] = "present"
            remaining[remaining.index(guess[i])] = None

    return result


def render_guess_line(
    guess: str, states: List[str], color_on: bool
) -> str:
    """Render a coloured guess line like Wordle."""
    blocks = []
    for ch, st in zip(guess, states):
        if st == "correct":
            block = ansi_wrap(f" {ch} ", ANSI.BG_GREEN, ANSI.FG_BLACK, ANSI.BOLD, enabled=color_on)
        elif st == "present":
            block = ansi_wrap(f" {ch} ", ANSI.BG_YELLOW, ANSI.FG_BLACK, ANSI.BOLD, enabled=color_on)
        else:
            block = ansi_wrap(f" {ch} ", ANSI.BG_BLACK, ANSI.FG_WHITE, enabled=color_on)
        blocks.append(block)
    return " ".join(blocks)


def play_word_puzzle(color_on: bool) -> None:
    secret = choose_secret_word()
    attempts = 6
    used_words: List[str] = []

    println()
    println(ansi_wrap(" BBS WORD PUZZLE ", ANSI.BG_BLUE, ANSI.FG_WHITE, ANSI.BOLD, enabled=color_on))
    println()
    println("Guess the 5-letter BBS/tech-themed word.")
    println("You have 6 tries. Letters:")
    println("  " + ansi_wrap("GREEN", ANSI.FG_GREEN, enabled=color_on) +
            " = right letter, right spot.")
    println("  " + ansi_wrap("YELLOW", ANSI.FG_YELLOW, enabled=color_on) +
            " = right letter, wrong spot.")
    println("  Normal = not in the word.")
    println()

    for attempt in range(1, attempts + 1):
        while True:
            println()
            guess = safe_input(f"[Attempt {attempt}/{attempts}] Enter a 5-letter word: ").strip().upper()
            if len(guess) != 5:
                println(f"\r\nYour guess '{guess}' is not 5 letters long.")
                continue
            if not guess.isalpha():
                println("Letters only, please.")
                continue
            break

        used_words.append(guess)
        states = score_guess(secret, guess)
        println(render_guess_line(guess, states, color_on))

        if guess == secret:
            println()
            println(ansi_wrap("You got it! Nicely done, caller.", ANSI.FG_GREEN, ANSI.BOLD, enabled=color_on))
            break
    else:
        # Ran out of attempts
        println()
        println(
            ansi_wrap("Out of attempts! The word was: ",
                      ANSI.FG_RED, ANSI.BOLD, enabled=color_on) +
            ansi_wrap(secret, ANSI.FG_YELLOW, ANSI.BOLD, enabled=color_on)
        )

    println()
    println("Thanks for playing the test door.")
    println("Press ENTER to return to the main menu.")
    safe_input("")


# --- UI ----------------------------------------------------------------------

def draw_banner(bbs_name: str, username: str, node: int, color_on: bool) -> None:
    println(ANSI.CLEAR + ANSI.HOME)
    title = f":: {bbs_name} TestDoor ::"
    border = "=" * len(title)
    println(ansi_wrap(border, ANSI.FG_CYAN, ANSI.BOLD, enabled=color_on))
    println(ansi_wrap(title, ANSI.FG_MAGENTA, ANSI.BOLD, enabled=color_on))
    println(ansi_wrap(border, ANSI.FG_CYAN, ANSI.BOLD, enabled=color_on))
    println()
    println(f"Caller : {ansi_wrap(username, ANSI.FG_YELLOW, enabled=color_on)}")
    println(f"Node   : {ansi_wrap(str(node), ANSI.FG_YELLOW, enabled=color_on)}")
    println()


def main_menu(
    bbs_name: str,
    username: str,
    node: int,
    color_on: bool,
    has_dropfile: bool,
    dropfile_path: str
) -> None:
    while True:
        draw_banner(bbs_name, username, node, color_on)

        if not has_dropfile:
            println(
                ansi_wrap(
                    "WARNING: DOOR.SYS not found. Running in local/test mode.",
                    ANSI.FG_RED, ANSI.BOLD, enabled=color_on,
                )
            )
            println()

        println("1) Play the BBS Word Puzzle")
        println("2) Toggle ANSI colours (currently: " +
                ("ON" if color_on else "OFF") + ")")
        println("3) Show DOOR.SYS info")
        println("4) Send LNWP triple (USERNAME/ACTIVITY/USER_STAT)")
        println("5) Quit to BBS")
        println()

        choice = safe_input("Select an option (1-5): ").strip()

        if choice == "1":
            play_word_puzzle(color_on)
        elif choice == "2":
            color_on = not color_on
        elif choice == "3":
            draw_banner(bbs_name, username, node, color_on)
            println("DOOR.SYS path       : " + (dropfile_path or "<none>"))
            println("DOOR.SYS detected   : " + (has_dropfile and "YES" or "NO"))
            println("ANSI/Graphics mode  : " +
                    ("RESPECT DOOR.SYS (GR/7E) or manual toggle."))  # simple note
            println()
            println("Press ENTER to return to the menu.")
            safe_input("")
        elif choice == "4":
            println()
            println("Sending LNWP triple...")
            send_lnwp_triple_sequence()
            println("Sent. Press ENTER to return to the menu.")
            safe_input("")
        elif choice == "5":
            println()
            println(ansi_wrap("Goodbye! Returning you to the BBS...", ANSI.FG_CYAN, enabled=color_on))
            println()
            break
            println("Invalid choice. Press ENTER to try again.")
            safe_input("")


# --- Entry point -------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TestDoor for NotoriousPTY - simple ANSI test door"
    )
    parser.add_argument(
        "node",
        type=int,
        help="Node number (from BBS)"
    )
    parser.add_argument(
        "dropfile",
        help="Path to DOOR.SYS drop file"
    )
    parser.add_argument(
        "--lnwp-triple",
        action="store_true",
        help="Send three LNWP frames (USERNAME/ACTIVITY/USER_STAT) then exit"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    node = args.node
    dropfile_path = args.dropfile

    if args.lnwp_triple or os.environ.get("LNWP_TRIPLE"):
        send_lnwp_triple_sequence()
        return

    username, graphics_mode = load_door_sys(dropfile_path)
    has_dropfile = username is not None or graphics_mode is not None

    if not has_dropfile and not os.path.exists(dropfile_path):
        # Explicit warning; we still run anyway.
        # We'll also show another warning inside the main menu.
        println()
        println(f"DOOR.SYS not found at: {dropfile_path}")
        println("Continuing anyway in local/test mode...")
        println()

    # Default display options
    if username is None:
        username = "Mystery Caller"

    # GR = graphics, NG = non-graphics
    color_on = True
    if graphics_mode is not None:
        gm = graphics_mode.upper()
        if gm.startswith("NG"):
            color_on = False

    bbs_name = "NotoriousPTY"

    try:
        main_menu(
            bbs_name=bbs_name,
            username=username,
            node=node,
            color_on=color_on,
            has_dropfile=has_dropfile,
            dropfile_path=dropfile_path,
        )
    except KeyboardInterrupt:
        # Graceful exit back to BBS
        println()
        println("Interrupted. Returning you to the BBS...")
        println()


if __name__ == "__main__":
    main()

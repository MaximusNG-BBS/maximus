#!/usr/bin/env python3
"""
EX_HELLO.PY - Trivial example door program.

This program demonstrates just how simple a fully functional door program can be.
Shows all the basic elements required by any program using Notorious DoorKit.

This program shows how to do the following:
- Import the DoorKit library
- Display text on multiple lines
- Wait for a single key to be pressed
- Properly exit a door program

Converted from OpenDoors ex_hello.c to Notorious DoorKit.
"""

import sys

from notorious_doorkit import (
    Door,
    RawInput,
    printf,
)


def main() -> None:
    """Main entry point for the door program."""
    
    # Initialize door session
    door = Door()
    
    # For local testing, use start_local(); for BBS use, use start()
    try:
        door.start()
    except RuntimeError:
        door.start_local(username="User", node=1)
    
    # Display a message
    printf("Hello world! This is a very simple DoorKit program.\n\r")
    printf("Press any key to return to the BBS!\n\r")
    
    # Wait for user to press a key
    with RawInput() as inp:
        inp.get_key()


if __name__ == "__main__":
    main()

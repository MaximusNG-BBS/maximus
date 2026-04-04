#!/usr/bin/env python3
"""
EX_MUSIC.PY - Example program plays "Happy Birthday" to the remote user.

This program demonstrates:
- How to play sound effects or music on a remote terminal that supports ANSI music
- Basic door session initialization and I/O patterns

Converted from OpenDoors ex_music.c to Notorious DoorKit.
"""

import sys

from notorious_doorkit import (
    Door,
    RawInput,
    clear_screen,
    printf,
    get_answer,
    play_ansi_music,
)


# Global flag to track whether sound is enabled
sound_enabled = True


def test_sound() -> bool:
    """Test whether the user's terminal program supports ANSI music.
    
    You can either do this every time the user runs your program, or only the
    first time they use the program, saving the result in a data file.
    
    Returns:
        True if user confirmed they heard sound, False otherwise
    """
    global sound_enabled
    clear_screen()
    
    # Display description of test to user
    printf("We need to know whether or not your terminal program supports ANSI music.\n\r")
    printf("In order to test this, we will send a short ANSI music sequence. We will then\n\r")
    printf("ask whether or not you heard any sound.\n\r")
    printf("Press any key to begin this test... ")
    
    # Wait for user to press a key to begin
    with RawInput() as inp:
        inp.get_key()
    printf("\n\r\n\r")
    
    # Temporarily enable sound
    sound_enabled = True
    
    # Send sound test sequence
    play_ansi_music("MBT120L4MFMNO4C8C8DC", reset=True)
    
    # Clear screen and ask whether user heard the sound
    clear_screen()
    printf("Did you just hear sound from your speaker? (Y/n)")
    response = get_answer("YN")
    
    # Set ANSI music on/off according to user's response
    sound_enabled = (response == 'Y')
    
    return sound_enabled


def play_sound(sequence: str) -> None:
    """Play an ANSI music sequence if sound is enabled.
    
    Args:
        sequence: The ANSI music sequence to play
    """
    if not sound_enabled:
        return
    
    play_ansi_music(sequence)


def main() -> None:
    """Main entry point for the door program."""
    
    # Initialize door session
    door = Door()
    
    # For local testing, use start_local(); for BBS use, use start()
    try:
        door.start()
    except RuntimeError:
        door.start_local(username="User", node=1)
    
    # Display introductory message
    printf("This is a simple door program that will play the song Happy Birthday\n\r")
    printf("tune on the remote system, if the user's terminal program supports ANSI\n\r")
    printf("music. Music is not played on the local speaker, as BBS system operators\n\r")
    printf("do not wish to have the BBS computer making sounds at any time of the day\n\r")
    printf("or night. However, the program can easily be modified to also echo sound to\n\r")
    printf("the local speaker.\n\r\n\r")
    
    # Test whether user's terminal supports ANSI music
    test_sound()
    
    # Send birthday greetings to the remote user
    clear_screen()
    
    # Display a message
    printf("\n\rHappy Birthday!\n\r")
    
    # If ANSI music is available, play "Happy Birthday"
    play_sound("MBT120L4MFMNO4C8C8DCFE2C8C8DCGF2C8C8O5CO4AFED2T90B-8B-8AFGF2")
    
    # Reset sound after finished playing
    play_sound("00m")
    
    # Wait for user to press a key before returning to BBS
    printf("\n\rPress any key to return to BBS...\n\r")
    with RawInput() as inp:
        inp.get_key()


if __name__ == "__main__":
    main()

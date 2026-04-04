#!/usr/bin/env python3
"""
EX_VOTE.PY - Online voting/survey door program.

This program demonstrates a voting system where users can:
- Vote on questions/surveys
- View results of voting
- Add new questions

This is a simplified version of the OpenDoors ex_vote.c example, demonstrating:
- Menu display and navigation
- User input handling
- Basic file I/O for persistence
- Color-coded output

Converted from OpenDoors ex_vote.c to Notorious DoorKit.
"""

import sys
import os
import json
from pathlib import Path
from typing import Optional

from notorious_doorkit import (
    Door,
    RawInput,
    clear_screen,
    printf,
    get_answer,
    hotkey_menu,
    input_str,
    get_username,
    BRIGHT_RED,
    BRIGHT_GREEN,
    RED,
    GREEN,
    BRIGHT_WHITE,
    RESET,
)


# Constants
MAX_QUESTIONS = 200
MAX_ANSWERS = 15
QUESTION_FILE = "vote_questions.json"
USER_FILE = "vote_users.json"


class VoteData:
    """Manages vote data persistence."""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.questions_file = self.data_dir / QUESTION_FILE
        self.users_file = self.data_dir / USER_FILE
        self.questions = []
        self.users = {}
        self.load_data()
    
    def load_data(self):
        """Load questions and user data from disk."""
        if self.questions_file.exists():
            try:
                with open(self.questions_file, 'r') as f:
                    self.questions = json.load(f)
            except:
                self.questions = []
        
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
    
    def save_data(self):
        """Save questions and user data to disk."""
        try:
            with open(self.questions_file, 'w') as f:
                json.dump(self.questions, f, indent=2)
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            printf(f"Error saving data: {e}\n\r")
    
    def get_user_votes(self, username: str) -> list:
        """Get list of question indices user has voted on."""
        return self.users.get(username, [])
    
    def mark_voted(self, username: str, question_idx: int):
        """Mark that user has voted on a question."""
        if username not in self.users:
            self.users[username] = []
        if question_idx not in self.users[username]:
            self.users[username].append(question_idx)
    
    def add_question(self, question: str, answers: list, creator: str):
        """Add a new question."""
        if len(self.questions) >= MAX_QUESTIONS:
            return False
        
        self.questions.append({
            "question": question,
            "answers": [{"text": ans, "votes": 0} for ans in answers],
            "total_votes": 0,
            "creator": creator,
            "can_add_answers": True
        })
        return True
    
    def vote(self, question_idx: int, answer_idx: int):
        """Record a vote."""
        if 0 <= question_idx < len(self.questions):
            q = self.questions[question_idx]
            if 0 <= answer_idx < len(q["answers"]):
                q["answers"][answer_idx]["votes"] += 1
                q["total_votes"] += 1
    
    def add_answer(self, question_idx: int, answer_text: str) -> int:
        """Add a new answer to a question. Returns answer index or -1."""
        if 0 <= question_idx < len(self.questions):
            q = self.questions[question_idx]
            if len(q["answers"]) < MAX_ANSWERS and q.get("can_add_answers", True):
                q["answers"].append({"text": answer_text, "votes": 0})
                return len(q["answers"]) - 1
        return -1


def wait_for_enter():
    """Wait for user to press Enter."""
    printf("\n\rPress Enter to continue...")
    with RawInput() as inp:
        while True:
            key = inp.get_key()
            if key == '\r' or key == '\n':
                break


def display_question_list(data: VoteData, username: str, voted_only: bool = False) -> Optional[int]:
    """Display list of questions and let user choose one. Returns question index or None."""
    user_votes = data.get_user_votes(username)
    
    while True:
        clear_screen()
        printf(f"{BRIGHT_RED}                              Question List\n\r")
        printf(f"{RED}{'=' * 79}\n\r\n\r")
        
        available = []
        for idx, q in enumerate(data.questions):
            has_voted = idx in user_votes
            if voted_only and not has_voted:
                continue
            if not voted_only and has_voted:
                continue
            available.append(idx)
        
        if not available:
            printf(f"{BRIGHT_WHITE}No questions available.\n\r")
            wait_for_enter()
            return None
        
        for i, idx in enumerate(available[:20]):
            q = data.questions[idx]
            printf(f"{BRIGHT_GREEN}{i+1:2d}. {GREEN}{q['question'][:60]}\n\r")
        
        printf(f"\n\r{BRIGHT_WHITE}Enter question number, or [Q] to quit: {GREEN}")
        choice = input_str(max_length=3)
        
        if choice.upper() == 'Q':
            return None
        
        try:
            num = int(choice) - 1
            if 0 <= num < len(available):
                return available[num]
        except:
            pass
        
        printf(f"{BRIGHT_WHITE}Invalid choice.\n\r")
        wait_for_enter()


def display_results(question: dict):
    """Display voting results for a question."""
    clear_screen()
    printf(f"{BRIGHT_RED}{question['question']}\n\r\n\r")
    
    total = question['total_votes']
    if total == 0:
        printf(f"{BRIGHT_WHITE}No votes yet.\n\r")
    else:
        for ans in question['answers']:
            votes = ans['votes']
            pct = (votes * 100.0 / total) if total > 0 else 0
            printf(f"{BRIGHT_GREEN}{ans['text']:30s} {GREEN}{votes:4d} votes ({pct:5.1f}%)\n\r")
        printf(f"\n\r{BRIGHT_WHITE}Total votes: {total}\n\r")
    
    wait_for_enter()


def vote_on_question(data: VoteData, username: str):
    """Let user vote on a question."""
    while True:
        question_idx = display_question_list(data, username, voted_only=False)
        if question_idx is None:
            return
        
        question = data.questions[question_idx]
        
        while True:
            clear_screen()
            printf(f"{BRIGHT_RED}{question['question']}\n\r\n\r")
            
            for i, ans in enumerate(question['answers']):
                printf(f"{BRIGHT_GREEN}{i+1}. {GREEN}{ans['text']}\n\r")
            
            printf(f"\n\r{BRIGHT_WHITE}Enter answer number")
            if question.get('can_add_answers') and len(question['answers']) < MAX_ANSWERS:
                printf(", [A] to add your own")
            printf(f", [Q] to quit: {GREEN}")
            
            choice = input_str(max_length=3)
            
            if choice.upper() == 'Q':
                return
            
            if choice.upper() == 'A' and question.get('can_add_answers'):
                printf(f"\n\r{BRIGHT_GREEN}Enter your answer (max 30 chars):\n\r{GREEN}")
                new_answer = input_str(max_length=30)
                if new_answer.strip():
                    answer_idx = data.add_answer(question_idx, new_answer.strip())
                    if answer_idx >= 0:
                        data.vote(question_idx, answer_idx)
                        data.mark_voted(username, question_idx)
                        data.save_data()
                        display_results(question)
                        return
                continue
            
            try:
                answer_idx = int(choice) - 1
                if 0 <= answer_idx < len(question['answers']):
                    data.vote(question_idx, answer_idx)
                    data.mark_voted(username, question_idx)
                    data.save_data()
                    display_results(question)
                    return
            except:
                pass
            
            printf(f"{BRIGHT_WHITE}Invalid choice.\n\r")
            wait_for_enter()


def view_results(data: VoteData, username: str):
    """View results of questions user has voted on."""
    while True:
        question_idx = display_question_list(data, username, voted_only=True)
        if question_idx is None:
            return
        
        display_results(data.questions[question_idx])


def add_question(data: VoteData, username: str):
    """Add a new question."""
    clear_screen()
    printf(f"{BRIGHT_RED}                                Add A Question\n\r")
    printf(f"{RED}{'=' * 79}\n\r\n\r")
    
    printf(f"{BRIGHT_GREEN}Enter your question (max 70 chars):\n\r{GREEN}")
    question_text = input_str(max_length=70)
    
    if not question_text.strip():
        return
    
    answers = []
    printf(f"\n\r{BRIGHT_GREEN}Enter answers (2-{MAX_ANSWERS}). Press Enter on blank line when done.\n\r")
    
    for i in range(MAX_ANSWERS):
        printf(f"{BRIGHT_GREEN}Answer {i+1}: {GREEN}")
        answer = input_str(max_length=30)
        if not answer.strip():
            break
        answers.append(answer.strip())
        if len(answers) >= 2:
            printf(f"{GREEN}(Press Enter on blank line if done)\n\r")
    
    if len(answers) < 2:
        printf(f"{BRIGHT_WHITE}Need at least 2 answers.\n\r")
        wait_for_enter()
        return
    
    if data.add_question(question_text.strip(), answers, username):
        data.save_data()
        printf(f"\n\r{BRIGHT_WHITE}Question added successfully!\n\r")
    else:
        printf(f"\n\r{BRIGHT_WHITE}Unable to add question (maximum reached).\n\r")
    
    wait_for_enter()


def main() -> None:
    """Main entry point for the door program."""
    
    # Initialize door session
    door = Door()
    
    # For local testing, use start_local(); for BBS use, use start()
    try:
        door.start()
    except RuntimeError:
        door.start_local(username="User", node=1)

    username = get_username()
    
    # Initialize vote data
    data = VoteData()
    
    # Main menu loop
    while True:

        def menu_file_exists(base: str) -> bool:
            if os.path.exists(base):
                return True
            for ext in (".rip", ".avt", ".ans", ".asc", ".txt"):
                if os.path.exists(base + ext) or os.path.exists(base + ext.upper()):
                    return True
            return False

        choice: Optional[str]
        if menu_file_exists("VOTE"):
            choice = hotkey_menu(
                "VOTE",
                {
                    "V": lambda: "V",
                    "R": lambda: "R",
                    "A": lambda: "A",
                    "E": lambda: "E",
                    "H": lambda: "H",
                },
                overlay_mode=1,
                overlay_prompt="Select [V]ote [R]esults [A]dd [E]xit [H]angup (ESC=back): ",
            )
            if choice is None:
                continue
        else:
            clear_screen()

            printf(f"{BRIGHT_RED}                     Vote - DoorKit Example Program\n\r")
            printf(f"{RED}{'=' * 79}\n\r\n\r\n\r")
            printf(f"{GREEN}                        [{BRIGHT_GREEN}V{GREEN}] Vote on a question\n\r\n\r")
            printf(f"                        [{BRIGHT_GREEN}R{GREEN}] View the results of question\n\r\n\r")
            printf(f"                        [{BRIGHT_GREEN}A{GREEN}] Add a new question\n\r\n\r")
            printf(f"                        [{BRIGHT_GREEN}E{GREEN}] Exit door and return to the BBS\n\r\n\r")
            printf(f"                        [{BRIGHT_GREEN}H{GREEN}] End call (hangup)\n\r\n\r\n\r")
            printf(f"{BRIGHT_WHITE}Press the key corresponding to your choice: {GREEN}")

            choice = get_answer("VRAEH")
        
        if choice == 'V':
            vote_on_question(data, username)
        elif choice == 'R':
            view_results(data, username)
        elif choice == 'A':
            add_question(data, username)
        elif choice == 'H':
            printf(f"\n\r{BRIGHT_WHITE}Are you sure you wish to hangup? (Y/N) ")
            if get_answer("YN") == 'N':
                continue
            break
        elif choice == 'E':
            break
    
    printf(f"{BRIGHT_WHITE}Returning to BBS, please wait...\n\r")


if __name__ == "__main__":
    main()

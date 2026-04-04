#!/usr/bin/env python3
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from notorious_doorkit import clear_screen, writeln, RESET, CYAN, YELLOW, GREEN
from notorious_doorkit import Door
from notorious_doorkit.input import RawInput, KEY_ESC
from notorious_doorkit.lnwp import RawLnwpEvent, MessageEvent, NodeInfoEvent, NodesInfoEvent


def _fmt_bool01(s: str) -> str:
    return "yes" if (s or "").strip() == "1" else "no"


def _print_node_info_fields(fields: dict) -> None:
    # fields includes PRM=INFO VAL=NODE_INFO plus key/value pairs
    node_id = fields.get("NODE_ID", "")
    username = fields.get("USERNAME", "")
    activity = fields.get("ACTIVITY", "")
    door_mode = _fmt_bool01(fields.get("DOOR_MODE", "0"))
    door_id = fields.get("DOOR_ID", "")

    writeln(f"[NODE_INFO] node={node_id} user='{username}' activity='{activity}' door_mode={door_mode} door_id='{door_id}'")


def _print_nodes_info(nodes_info: dict) -> None:
    # nodes_info is Dict[int, Dict[str, str]] with keys like USERNAME/ACTIVITY/DOOR_MODE/DOOR_ID
    writeln(f"[NODES_INFO] {len(nodes_info)} nodes")
    for nid in sorted(nodes_info.keys()):
        info = nodes_info.get(nid, {}) or {}
        username = info.get("USERNAME", "")
        activity = info.get("ACTIVITY", "")
        door_mode = _fmt_bool01(info.get("DOOR_MODE", "0"))
        door_id = info.get("DOOR_ID", "")
        writeln(f"  node {nid:>2}: user='{username}' activity='{activity}' door_mode={door_mode} door_id='{door_id}'")


def print_menu(push_on: bool) -> None:
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


def drain_lnwp_events(door: Door, max_iters: int = 25) -> int:
    """Drain and print LNWP events that arrived on the control channel.

    In door32 mode, LNWP should be FD4 only, so passthrough bytes should be empty.
    """
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


def main() -> None:
    door = Door()

    clear_screen()
    writeln(f"{CYAN}Doorkit Door32 Probe{RESET}")
    writeln()
    writeln(f"door32_mode={door.door32_mode} terminal_fd={door.terminal_fd} control_fd={door.control_fd}")
    writeln()

    writeln(f"{GREEN}FD3 is terminal bytes. FD4 is LNWP control frames. This probe exercises both.{RESET}")
    writeln()

    push_on = False
    activity_n = 0

    door.arm()
    door.set_activity("Doorkit Door32 Probe")

    print_menu(push_on)

    with RawInput(extended_keys=True) as inp:
        while True:
            # Drain LNWP events frequently so responses show up quickly.
            drain_lnwp_events(door)

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
                    print_menu(push_on)
                else:
                    writeln(f"KEY={repr(k)}")
            else:
                writeln(f"KEY={repr(k)}")

    door.set_input_mode("cooked")
    door.set_activity("")
    writeln("\r\nExiting.")
    time.sleep(0.25)


if __name__ == "__main__":
    main()

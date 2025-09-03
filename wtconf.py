#!/usr/bin/env python3

import yaml
import subprocess
import sys
import os
import argparse
from pathlib import Path
import shutil

from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text



# === Globals ===

parser = argparse.ArgumentParser(description="wtconf is a tiny config file launcher")
parser.add_argument("--add", help="Add new config")  # e.g. wtconf --add /etc/foo.conf
args = parser.parse_args()

TABLE_WIDTH = 64



# === Load configs and init ===

def load_configs():
    global loaded, editor, SETTINGS_FILE, CONFIGLIST_FILE

    # load configlist.yaml
    with open(CONFIGLIST_FILE) as f:
        loaded = yaml.safe_load(f) or {}

    # Load settings.yaml
    with open(SETTINGS_FILE) as f:
        config = yaml.safe_load(f) or {}

    editor = config.get("editor") or os.environ.get("EDITOR") or "nano"


def init():
    global SETTINGS_FILE, CONFIGLIST_FILE

    CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / ""
    SETTINGS_FILE = CONFIG_DIR/"wtconf" / "settings.yaml"
    CONFIGLIST_FILE = CONFIG_DIR/"wtconf" /"configlist.yaml"

    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not CONFIGLIST_FILE.exists():
        CONFIGLIST_FILE.touch()
    if not SETTINGS_FILE.exists():
        SETTINGS_FILE.write_text("editor: nano")

    load_configs()

    if args.add is None: # Default behavior: if no --add argument is passed, show the menu
        console = Console()
        menu_loop()



# === Draw the menu ===

def menu_loop(): # draw the menu
    
    console = Console()
    status = None
    try: #for KeyboardInterrupt exception
        while True:
            console.clear()

            # Banner
            console.print("\n[bold black on blue]wtconf[/bold black on blue] a tiny config launcher", 
            justify="center")

            # Table
            table = Table(show_lines=False, box=box.SIMPLE, width=TABLE_WIDTH, collapse_padding=True, show_header=True, border_style="dim")
            table.add_column("#", justify="center", header_style="bold blue" ,style="blue")
            table.add_column("Config", justify="left")
            table.add_column("Path", justify="left", style="dim", header_style="dim")

            items = list(loaded.items()) if loaded else []

            for i, (label, path) in enumerate(items, start=1): # Populate table
                table.add_row(str(i), str(label), str(path))

            if not items:
                table.add_row("-", "[dim]<empty>[/dim]", "[dim]wtconf --add /path/to/file.conf[/dim]")

            console.print(table, justify="center")

            #console.print("[dim]─[/dim]" * 62, justify="center")

            if status:
                console.print(pad_for_table(status) + status)
                status = None

            console.print(
                "[bold blue]ID[/bold blue] = open | "
                "[green]s[/green] = settings | "
                "[cyan]c[/cyan] = configlist | "
                "[yellow]r[/yellow] = reload | "
                "[red]q[/red] = quit",
                justify="center"
            )

            prompt = "> "
            pad = pad_for_table(prompt)
            sel = console.input("\n" + pad + prompt).strip()

            if sel.lower() == "q":
                console.print("\n")
                sys.exit(0)

            if sel.lower() == "s":
                run_editor_and_reload(SETTINGS_FILE)
                continue

            if sel.lower() == "c":
                run_editor_and_reload(CONFIGLIST_FILE)
                continue

            if sel.lower() == "r":
                load_configs()
                status = "[green]Config files reloaded[/green]\n"
                continue

            if not sel.isdigit():
                info("ID must be a number. Press Enter...")
                continue

            idx = int(sel) - 1
            if not (0 <= idx < len(items)):
                info("ID out of range. Press Enter...")
                continue

            label, path = items[idx]
            run_editor_and_reload(path)

    except KeyboardInterrupt:
        console.print("\n\n")
        sys.exit(0)



# === Menu helpers ===

def pad_for_table(text, table_width=TABLE_WIDTH):
    cols = shutil.get_terminal_size().columns
    block_pad = max(0, (cols - table_width) // 2)               # left offset of the centered block
    display_width = Text.from_markup(text).cell_len             # visible width (ignores markup)
    inner_pad = max(0, (table_width - display_width) // 2)      # center inside the block
    return " " * (block_pad + inner_pad)

def run_editor_and_reload(path):
    try:
        rc = subprocess.run([editor, str(path)]).returncode
        if rc == 0:
            load_configs()
        else:
            info(f"[red]{editor} exited with code {rc}[/red]")
    except FileNotFoundError:
        # show error line, then centered Y/N prompt
        info(f"[red]{editor} not found[/red]", pause=False)
        if ask_yes_no(f"Open [bold]{SETTINGS_FILE.name}[/bold] in [bold]nano[/bold] to fix it now?", default=True):
            try:
                subprocess.run(["nano", str(SETTINGS_FILE)], check=False)
                load_configs()
                if ask_yes_no("Retry the previous action with the updated editor?", default=True):
                    try:
                        rc = subprocess.run([editor, str(path)]).returncode
                        if rc == 0:
                            load_configs()
                        else:
                            info(f"[red]{editor} exited with code {rc}[/red]")
                    except FileNotFoundError:
                        info(f"[red]{editor} still not found[/red]. Please verify your settings.")
            except FileNotFoundError:
                info("[red]nano not found[/red]. Please edit settings.yaml manually.")
        else:
            info("Set a valid editor in settings.yaml and try again.")



def ask_yes_no(prompt, default=False):
    console = Console()
    suffix = " [Y/n]: " if default else " [y/N]: "
    text = prompt + suffix
    pad = pad_for_table(text)
    while True:
        ans = console.input("\n" + pad + text).strip().lower()
        if not ans:
            return default
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False


def info(msg, pause=True):
    console = Console()
    console.print()  # blank line
    console.print(pad_for_table(msg) + msg)
    if pause:
        input()



# === Handle arguments ===

def handle_args():
    if args.add:
        path = Path(args.add).expanduser().resolve()
        label = os.path.splitext(os.path.basename(args.add))[0]

        # add to dict
        loaded[label] = str(path)

        # write to yaml
        with open(CONFIGLIST_FILE, "w") as f:
            yaml.safe_dump(loaded, f, sort_keys=False)

            print(f"Added {label}: {path}")



# === Main execution ===

def main():
    init()
    handle_args()

if __name__ == "__main__":
    main()
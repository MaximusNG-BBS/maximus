---
layout: default
section: "configuration"
title: "Configuration"
description: "TOML-based system configuration for Maximus BBS"
---

Maximus NG uses plain-text TOML files for everything that used to live
in compiled PRM/CTL binaries. You can edit them with any text editor,
diff them in Git, and deploy them without a recompile step. MaxCFG
gives you a full TUI if you'd rather point-and-click.

Here's what lives in this section:

- **[MaxCFG]({% link maxcfg.md %})** — The configuration editor. A
  curses-based TUI for managing menus, areas, users, display files,
  and system settings. Includes a
  [CLI reference]({% link maxcfg-cli.md %}) for batch operations.

- **[Core Settings]({% link config-core-settings.md %})** — The
  fundamentals: BBS name, sysop identity, paths, session behavior,
  [login flow]({% link config-session-login.md %}), and
  [equipment & comm]({% link config-equipment-comm.md %}) settings.

- **[Menu System]({% link config-menu-system.md %})** — How callers
  navigate your board. Menu
  [definitions]({% link config-menu-definitions.md %}) and
  [options]({% link config-menu-options.md %}),
  [lightbar menus]({% link config-lightbar-menus.md %}), and
  [canned & bounded layouts]({% link config-canned-bounded-menus.md %}).

- **[Security & Access]({% link config-security-access.md %})** —
  Privilege levels, access flags, and the ACS (Access Control String)
  system that gates every area, menu option, and command.

- **[Door Games]({% link config-door-games.md %})** — Running
  external programs, dropfile formats, and Door32 support.

- **[Legacy Migration]({% link legacy-migration.md %})** — Moving
  from the old CTL/PRM/MAD pipeline to TOML. Conversion tools, delta
  overlays, and language file migration.

/*
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 * listpicker.c - Scrollable list picker dialog for maxcfg
 *
 * Copyright (C) 2025 Kevin Morgan (Limping Ninja) - https://github.com/LimpingNinja
 */

#include <ncurses.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include "maxcfg.h"
#include "ui.h"

/* List picker state */
typedef struct {
    const char *title;
    ListItem *items;
    int item_count;
    int selected;
    int scroll_offset;
    int visible_rows;
    bool space_is_filter;
} ListPickerState;

/* Forward declarations */
static void draw_list_picker(ListPickerState *state, int y, int x, int height, int width);
ListPickResult listpicker_show_ex(const char *title, ListItem *items, int item_count, int *selected, bool space_is_filter);

/*
 * listpicker_show - Display a list picker dialog
 *
 * Parameters:
 *   title - Dialog title
 *   items - Array of list items
 *   item_count - Number of items
 *   selected - Pointer to selected index (updated on return)
 *
 * Returns:
 *   ListPickResult indicating what action was taken
 */
ListPickResult listpicker_show(const char *title, ListItem *items, int item_count, int *selected)
{
    return listpicker_show_ex(title, items, item_count, selected, false);
}

ListPickResult listpicker_show_ex(const char *title, ListItem *items, int item_count, int *selected, bool space_is_filter)
{
    int max_rows, max_cols;
    getmaxyx(stdscr, max_rows, max_cols);
    
    /* Calculate dialog dimensions */
    int width = max_cols - 8;
    if (width > 76) width = 76;
    if (width < 50) width = 50;
    
    int height = max_rows - 6;
    if (height > 20) height = 20;
    if (height < 10) height = 10;
    
    int x = (max_cols - width) / 2;
    int y = (max_rows - height) / 2;
    
    /* Initialize state */
    ListPickerState state = {
        .title = title,
        .items = items,
        .item_count = item_count,
        .selected = *selected,
        .scroll_offset = 0,
        .visible_rows = height - 2,  /* Minus top and bottom borders */
        .space_is_filter = space_is_filter
    };
    
    /* Adjust scroll if needed */
    if (state.selected >= state.visible_rows) {
        state.scroll_offset = state.selected - state.visible_rows + 1;
    }
    
    ListPickResult result = LISTPICK_NONE;
    bool done = false;
    
    /* Enable keypad for special keys */
    keypad(stdscr, TRUE);
    curs_set(0);
    
    while (!done) {
        draw_list_picker(&state, y, x, height, width);
        doupdate();
        
        int ch = getch();
        
        switch (ch) {
            case KEY_UP:
            case 'k':
                if (state.selected > 0) {
                    state.selected--;
                    if (state.selected < state.scroll_offset) {
                        state.scroll_offset = state.selected;
                    }
                }
                break;
                
            case KEY_DOWN:
            case 'j':
                if (state.selected < state.item_count - 1) {
                    state.selected++;
                    if (state.selected >= state.scroll_offset + state.visible_rows) {
                        state.scroll_offset = state.selected - state.visible_rows + 1;
                    }
                }
                break;
                
            case KEY_PPAGE:
                state.selected -= state.visible_rows;
                if (state.selected < 0) state.selected = 0;
                state.scroll_offset = state.selected;
                break;
                
            case KEY_NPAGE:
                state.selected += state.visible_rows;
                if (state.selected >= state.item_count) {
                    state.selected = state.item_count - 1;
                }
                if (state.selected >= state.scroll_offset + state.visible_rows) {
                    state.scroll_offset = state.selected - state.visible_rows + 1;
                }
                break;
                
            case KEY_HOME:
                state.selected = 0;
                state.scroll_offset = 0;
                break;
                
            case KEY_END:
                state.selected = state.item_count - 1;
                if (state.selected >= state.visible_rows) {
                    state.scroll_offset = state.selected - state.visible_rows + 1;
                }
                break;
                
            case '\n':
            case '\r':
            case KEY_ENTER:
                result = LISTPICK_EDIT;
                done = true;
                break;
                
            case KEY_IC:  /* Insert key */
            case 'i':
            case 'I':
                result = LISTPICK_INSERT;
                done = true;
                break;

            case 'a':
            case 'A':
                result = LISTPICK_ADD;
                done = true;
                break;
                
            case KEY_DC:  /* Delete key */
                if (state.item_count > 0) {
                    result = LISTPICK_DELETE;
                    done = true;
                }
                break;

            case 'd':
            case 'D':
                if (state.item_count > 0) {
                    result = LISTPICK_DELETE;
                    done = true;
                }
                break;
                
            case 27:  /* ESC */
                result = LISTPICK_EXIT;
                done = true;
                break;

            case KEY_F(10):
                result = LISTPICK_EXIT;
                done = true;
                break;
                
            case ' ':
                if (space_is_filter) {
                    result = LISTPICK_FILTER;
                    done = true;
                } else {
                    /* Space bar - jump to last item */
                    state.selected = state.item_count - 1;
                    if (state.selected >= state.visible_rows) {
                        state.scroll_offset = state.selected - state.visible_rows + 1;
                    }
                }
                break;

            case 'c':
            case 'C':
                if (space_is_filter) {
                    result = LISTPICK_CLEAR;
                    done = true;
                }
                break;
                
            default:
                /* Number keys for quick jump */
                if (ch >= '0' && ch <= '9') {
                    int target = ch - '0';
                    if (target < state.item_count) {
                        state.selected = target;
                        if (state.selected < state.scroll_offset) {
                            state.scroll_offset = state.selected;
                        } else if (state.selected >= state.scroll_offset + state.visible_rows) {
                            state.scroll_offset = state.selected - state.visible_rows + 1;
                        }
                    }
                }
                break;
        }
    }
    
    *selected = state.selected;
    curs_set(1);
    
    return result;
}

static void draw_list_picker(ListPickerState *state, int y, int x, int height, int width)
{
    /* Draw border */
    attron(COLOR_PAIR(CP_DIALOG_BORDER));
    
    /* Top border with title */
    mvaddch(y, x, ACS_ULCORNER);
    for (int i = 1; i < width - 1; i++) {
        mvaddch(y, x + i, ACS_HLINE);
    }
    mvaddch(y, x + width - 1, ACS_URCORNER);
    
    /* Title centered */
    if (state->title) {
        int title_len = strlen(state->title);
        int title_x = x + (width - title_len - 2) / 2;
        mvaddch(y, title_x - 1, ' ');
        attron(COLOR_PAIR(CP_DIALOG_TITLE) | A_BOLD);
        mvprintw(y, title_x, "%s", state->title);
        attroff(COLOR_PAIR(CP_DIALOG_TITLE) | A_BOLD);
        attron(COLOR_PAIR(CP_DIALOG_BORDER));
        mvaddch(y, title_x + title_len, ' ');
    }
    
    /* Side borders and content area */
    for (int i = 1; i < height - 1; i++) {
        mvaddch(y + i, x, ACS_VLINE);
        
        /* Clear content area */
        attron(COLOR_PAIR(CP_DIALOG_TEXT));
        for (int j = 1; j < width - 1; j++) {
            mvaddch(y + i, x + j, ' ');
        }
        attron(COLOR_PAIR(CP_DIALOG_BORDER));
        
        mvaddch(y + i, x + width - 1, ACS_VLINE);
    }
    
    /* Bottom border with embedded status line */
    int bottom_y = y + height - 1;
    mvaddch(bottom_y, x, ACS_LLCORNER);
    addch(ACS_HLINE);
    addch(' ');
    attroff(COLOR_PAIR(CP_DIALOG_BORDER));
    
    /* Status items embedded in border - INS=(I)nsert */
    attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    printw("INS");
    attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    attron(COLOR_PAIR(CP_MENU_BAR));
    printw("=(");
    attroff(COLOR_PAIR(CP_MENU_BAR));
    attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    printw("I");
    attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    attron(COLOR_PAIR(CP_MENU_BAR));
    printw(")nsert");
    attroff(COLOR_PAIR(CP_MENU_BAR));
    
    attron(COLOR_PAIR(CP_DIALOG_BORDER));
    addch(ACS_HLINE);
    attroff(COLOR_PAIR(CP_DIALOG_BORDER));

    /* A=Add */
    attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    printw("A");
    attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    attron(COLOR_PAIR(CP_MENU_BAR));
    printw("=Add");
    attroff(COLOR_PAIR(CP_MENU_BAR));
    
    attron(COLOR_PAIR(CP_DIALOG_BORDER));
    addch(ACS_HLINE);
    attroff(COLOR_PAIR(CP_DIALOG_BORDER));
    
    /* DEL=(D)isable */
    attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    printw("DEL");
    attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    attron(COLOR_PAIR(CP_MENU_BAR));
    printw("=(");
    attroff(COLOR_PAIR(CP_MENU_BAR));
    attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    printw("D");
    attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    attron(COLOR_PAIR(CP_MENU_BAR));
    printw(")isable");
    attroff(COLOR_PAIR(CP_MENU_BAR));

    if (state->space_is_filter) {
        attron(COLOR_PAIR(CP_DIALOG_BORDER));
        addch(ACS_HLINE);
        attroff(COLOR_PAIR(CP_DIALOG_BORDER));

        /* SPACE=Search */
        attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        printw("SPACE");
        attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        attron(COLOR_PAIR(CP_MENU_BAR));
        printw("=Search");
        attroff(COLOR_PAIR(CP_MENU_BAR));

        attron(COLOR_PAIR(CP_DIALOG_BORDER));
        addch(ACS_HLINE);
        attroff(COLOR_PAIR(CP_DIALOG_BORDER));

        /* C=Clear */
        attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        printw("C");
        attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        attron(COLOR_PAIR(CP_MENU_BAR));
        printw("=Clear");
        attroff(COLOR_PAIR(CP_MENU_BAR));
    }
    
    attron(COLOR_PAIR(CP_DIALOG_BORDER));
    addch(ACS_HLINE);
    attroff(COLOR_PAIR(CP_DIALOG_BORDER));
    
    /* ESC=Exit */
    attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    printw("ESC");
    attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
    attron(COLOR_PAIR(CP_MENU_BAR));
    printw("=Exit");
    attroff(COLOR_PAIR(CP_MENU_BAR));
    
    /* Fill rest of bottom border */
    attron(COLOR_PAIR(CP_DIALOG_BORDER));
    int cur_x = getcurx(stdscr);
    addch(' ');
    for (int i = cur_x + 1; i < x + width - 1; i++) {
        addch(ACS_HLINE);
    }
    mvaddch(bottom_y, x + width - 1, ACS_LRCORNER);
    attroff(COLOR_PAIR(CP_DIALOG_BORDER));
    
    /* Draw list items */
    for (int i = 0; i < state->visible_rows && (i + state->scroll_offset) < state->item_count; i++) {
        int item_idx = i + state->scroll_offset;
        ListItem *item = &state->items[item_idx];
        int row = y + 1 + i;
        
        /* Build display string */
        char display[256];
        if (item->extra && item->extra[0]) {
            snprintf(display, sizeof(display), "%d: %s (%s)", item_idx, item->name, item->extra);
        } else {
            snprintf(display, sizeof(display), "%d: %s", item_idx, item->name);
        }
        
        /* Truncate if too long */
        int max_len = width - 4;
        if ((int)strlen(display) > max_len) {
            display[max_len] = '\0';
        }
        
        if (item_idx == state->selected) {
            /* Selected item - blue background */
            attron(COLOR_PAIR(CP_MENU_HIGHLIGHT) | A_BOLD);
            mvprintw(row, x + 2, "%-*s", width - 4, display);
            attroff(COLOR_PAIR(CP_MENU_HIGHLIGHT) | A_BOLD);
        } else {
            /* Normal item */
            if (!item->enabled) {
                /* Disabled - dim */
                attron(COLOR_PAIR(CP_DIALOG_TEXT) | A_DIM);
            } else {
                attron(COLOR_PAIR(CP_DIALOG_TEXT));
            }
            mvprintw(row, x + 2, "%s", display);
            if (!item->enabled) {
                attroff(COLOR_PAIR(CP_DIALOG_TEXT) | A_DIM);
            } else {
                attroff(COLOR_PAIR(CP_DIALOG_TEXT));
            }
        }
    }
    
    /* Scroll indicator if needed */
    if (state->item_count > state->visible_rows) {
        if (state->scroll_offset > 0) {
            attron(COLOR_PAIR(CP_DIALOG_BORDER));
            mvaddch(y + 1, x + width - 2, ACS_UARROW);
            attroff(COLOR_PAIR(CP_DIALOG_BORDER));
        }
        if (state->scroll_offset + state->visible_rows < state->item_count) {
            attron(COLOR_PAIR(CP_DIALOG_BORDER));
            mvaddch(y + height - 2, x + width - 2, ACS_DARROW);
            attroff(COLOR_PAIR(CP_DIALOG_BORDER));
        }
    }
    
    wnoutrefresh(stdscr);
}

/*
 * Helper functions for managing list items
 */

/* ============================================================================
 * Tabbed list picker — listpicker_show_tabbed()
 * ============================================================================ */

typedef struct {
    const char *title;
    ListItem *items;
    int item_count;
    int selected;
    int scroll_offset;
    int visible_rows;
    const char **tabs;
    int tab_count;
    int active_tab;
} TabbedListState;

static int tabbed_list_total_width(const TabbedListState *state)
{
    int total = 0;

    if (state == NULL || state->tabs == NULL || state->tab_count <= 0) {
        return 0;
    }

    for (int i = 0; i < state->tab_count; i++) {
        int len = (int)strlen(state->tabs[i] ? state->tabs[i] : "");
        total += len + 4; /* "[name] " */
    }

    if (total > 0) {
        total -= 1; /* trim trailing inter-tab space */
    }

    return total;
}

static void draw_tabbed_list_picker(TabbedListState *state, int y, int x, int height, int width)
{
    /* Draw border */
    attron(COLOR_PAIR(CP_DIALOG_BORDER));

    /* Top border with title */
    mvaddch(y, x, ACS_ULCORNER);
    for (int i = 1; i < width - 1; i++) {
        mvaddch(y, x + i, ACS_HLINE);
    }
    mvaddch(y, x + width - 1, ACS_URCORNER);

    /* Title centered */
    if (state->title) {
        int title_len = strlen(state->title);
        int title_x = x + (width - title_len - 2) / 2;
        mvaddch(y, title_x - 1, ' ');
        attron(COLOR_PAIR(CP_DIALOG_TITLE) | A_BOLD);
        mvprintw(y, title_x, "%s", state->title);
        attroff(COLOR_PAIR(CP_DIALOG_TITLE) | A_BOLD);
        attron(COLOR_PAIR(CP_DIALOG_BORDER));
        mvaddch(y, title_x + title_len, ' ');
    }

    /* Tab bar row (y+1) */
    int tab_y = y + 1;
    mvaddch(tab_y, x, ACS_VLINE);
    mvaddch(tab_y, x + width - 1, ACS_VLINE);

    attron(COLOR_PAIR(CP_DIALOG_TEXT));
    for (int i = 1; i < width - 1; i++) {
        mvaddch(tab_y, x + i, ' ');
    }
    attroff(COLOR_PAIR(CP_DIALOG_TEXT));

    if (state->tab_count > 1) {
        /* Find the active tab's position for centering */
        int total_tab_width = tabbed_list_total_width(state);

        int tab_start_x = x + (width - total_tab_width) / 2;
        if (tab_start_x < x + 4) tab_start_x = x + 4;

        int cur_x = tab_start_x;
        for (int i = 0; i < state->tab_count; i++) {
            int tab_len = (int)strlen(state->tabs[i]);
            if (cur_x + tab_len + 1 > x + width - 4) break;

            if (i == state->active_tab) {
                attron(COLOR_PAIR(CP_MENU_HIGHLIGHT) | A_BOLD);
                mvprintw(tab_y, cur_x, "[%s]", state->tabs[i]);
                attroff(COLOR_PAIR(CP_MENU_HIGHLIGHT) | A_BOLD);
            } else {
                attron(COLOR_PAIR(CP_MENU_BAR));
                mvprintw(tab_y, cur_x, "[%s]", state->tabs[i]);
                attroff(COLOR_PAIR(CP_MENU_BAR));
            }
            cur_x += tab_len + 4;
        }

        /* Navigation arrows — isolated single-character controls */
        if (state->active_tab > 0) {
            attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
            mvaddch(tab_y, x + 2, ACS_LARROW);
            attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        }
        if (state->active_tab < state->tab_count - 1) {
            attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
            mvaddch(tab_y, x + width - 3, ACS_RARROW);
            attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        }
    }

    /* Separator between tab bar and content */
    int sep_y = tab_y + 1;
    attron(COLOR_PAIR(CP_DIALOG_BORDER));
    mvaddch(sep_y, x, ACS_LTEE);
    for (int i = 1; i < width - 1; i++) {
        mvaddch(sep_y, x + i, ACS_HLINE);
    }
    mvaddch(sep_y, x + width - 1, ACS_RTEE);
    attroff(COLOR_PAIR(CP_DIALOG_BORDER));

    /* Side borders and content area */
    int content_start = sep_y + 1;
    for (int i = 0; i < state->visible_rows; i++) {
        int row = content_start + i;
        if (row >= y + height - 1) break;
        mvaddch(row, x, ACS_VLINE);

        /* Clear content area */
        attron(COLOR_PAIR(CP_DIALOG_TEXT));
        for (int j = 1; j < width - 1; j++) {
            mvaddch(row, x + j, ' ');
        }
        attroff(COLOR_PAIR(CP_DIALOG_BORDER));

        mvaddch(row, x + width - 1, ACS_VLINE);
    }

    /* Bottom border */
    int bottom_y = y + height - 1;
    attron(COLOR_PAIR(CP_DIALOG_BORDER));
    mvaddch(bottom_y, x, ACS_LLCORNER);
    for (int i = 1; i < width - 1; i++) {
        mvaddch(bottom_y, x + i, ACS_HLINE);
    }
    mvaddch(bottom_y, x + width - 1, ACS_LRCORNER);
    attroff(COLOR_PAIR(CP_DIALOG_BORDER));

    /* Draw list items */
    for (int i = 0; i < state->visible_rows && (i + state->scroll_offset) < state->item_count; i++) {
        int item_idx = i + state->scroll_offset;
        ListItem *item = &state->items[item_idx];
        int row = content_start + i;
        if (row >= y + height - 1) break;

        /* Build display string */
        char display[256];
        if (item->extra && item->extra[0]) {
            snprintf(display, sizeof(display), "%d: %s (%s)", item_idx, item->name, item->extra);
        } else {
            snprintf(display, sizeof(display), "%d: %s", item_idx, item->name);
        }

        /* Truncate if too long */
        int max_len = width - 4;
        if ((int)strlen(display) > max_len) {
            display[max_len] = '\0';
        }

        if (item_idx == state->selected) {
            attron(COLOR_PAIR(CP_MENU_HIGHLIGHT) | A_BOLD);
            mvprintw(row, x + 2, "%-*s", width - 4, display);
            attroff(COLOR_PAIR(CP_MENU_HIGHLIGHT) | A_BOLD);
        } else {
            if (!item->enabled) {
                attron(COLOR_PAIR(CP_DIALOG_TEXT) | A_DIM);
            } else {
                attron(COLOR_PAIR(CP_DIALOG_TEXT));
            }
            mvprintw(row, x + 2, "%s", display);
            if (!item->enabled) {
                attroff(COLOR_PAIR(CP_DIALOG_TEXT) | A_DIM);
            } else {
                attroff(COLOR_PAIR(CP_DIALOG_TEXT));
            }
        }
    }

    /* Scroll indicator if needed */
    if (state->item_count > state->visible_rows) {
        if (state->scroll_offset > 0) {
            attron(COLOR_PAIR(CP_DIALOG_BORDER));
            mvaddch(content_start, x + width - 2, ACS_UARROW);
            attroff(COLOR_PAIR(CP_DIALOG_BORDER));
        }
        if (state->scroll_offset + state->visible_rows < state->item_count) {
            attron(COLOR_PAIR(CP_DIALOG_BORDER));
            mvaddch(content_start + state->visible_rows - 1, x + width - 2, ACS_DARROW);
            attroff(COLOR_PAIR(CP_DIALOG_BORDER));
        }
    }

    /* Help separator and expanded multi-line help text (inside dialog, above bottom border) */
    int help_sep_y = content_start + state->visible_rows;
    int help_lines = 5;
    if (help_sep_y + help_lines < bottom_y) {
        static const char *help_text[] = {
            "This list shows all of the menus that resolve for the currently selected",
            "theme. Bright items have a theme-specific variant, dim items are",
            "inherited from the base classic theme until you create one.",
            "Pressing Enter on a dim item will ask you to create a theme-specific",
            "copy. Use LEFT and RIGHT arrows to change themes."
        };

        mvaddch(help_sep_y, x, ACS_LTEE);
        addch(ACS_HLINE);
        addch(' ');

        attron(COLOR_PAIR(CP_MENU_BAR));
        printw("Help");
        attroff(COLOR_PAIR(CP_MENU_BAR));

        attron(COLOR_PAIR(CP_DIALOG_BORDER));
        printw(" - ");
        attroff(COLOR_PAIR(CP_DIALOG_BORDER));

        attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        printw("INS");
        attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        attron(COLOR_PAIR(CP_MENU_BAR));
        printw("=(");
        attroff(COLOR_PAIR(CP_MENU_BAR));
        attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        printw("I");
        attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        attron(COLOR_PAIR(CP_MENU_BAR));
        printw(")nsert  ");
        attroff(COLOR_PAIR(CP_MENU_BAR));

        attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        printw("A");
        attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        attron(COLOR_PAIR(CP_MENU_BAR));
        printw("=Add  ");
        attroff(COLOR_PAIR(CP_MENU_BAR));

        attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        printw("DEL");
        attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        attron(COLOR_PAIR(CP_MENU_BAR));
        printw("=(");
        attroff(COLOR_PAIR(CP_MENU_BAR));
        attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        printw("D");
        attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        attron(COLOR_PAIR(CP_MENU_BAR));
        printw(")isable  ");
        attroff(COLOR_PAIR(CP_MENU_BAR));

        attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        printw("←→");
        attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        attron(COLOR_PAIR(CP_MENU_BAR));
        printw("=Tabs  ");
        attroff(COLOR_PAIR(CP_MENU_BAR));

        attron(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        printw("ESC");
        attroff(COLOR_PAIR(CP_MENU_HOTKEY) | A_BOLD);
        attron(COLOR_PAIR(CP_MENU_BAR));
        printw("=Exit");
        attroff(COLOR_PAIR(CP_MENU_BAR));

        attron(COLOR_PAIR(CP_DIALOG_BORDER));
        for (int c = getcurx(stdscr); c < x + width - 1; c++) addch(ACS_HLINE);
        mvaddch(help_sep_y, x + width - 1, ACS_RTEE);
        attroff(COLOR_PAIR(CP_DIALOG_BORDER));

        for (int i = 0; i < help_lines; i++) {
            int help_y = help_sep_y + 1 + i;
            mvaddch(help_y, x, ACS_VLINE);

            attron(COLOR_PAIR(CP_DIALOG_TEXT));
            for (int j = 1; j < width - 1; j++) {
                mvaddch(help_y, x + j, ' ');
            }
            attroff(COLOR_PAIR(CP_DIALOG_TEXT));

            attron(COLOR_PAIR(CP_MENU_BAR));
            mvprintw(help_y, x + 2, "%s", help_text[i]);
            attroff(COLOR_PAIR(CP_MENU_BAR));

            if (i == 4) {
                int left_x = x + 2 + (int)strlen("copy. Use ");
                int right_x = x + 2 + (int)strlen("copy. Use LEFT and ");
                attron(COLOR_PAIR(CP_DIALOG_TITLE) | A_BOLD);
                mvprintw(help_y, left_x, "LEFT");
                mvprintw(help_y, right_x, "RIGHT");
                attroff(COLOR_PAIR(CP_DIALOG_TITLE) | A_BOLD);
            }

            attron(COLOR_PAIR(CP_DIALOG_BORDER));
            mvaddch(help_y, x + width - 1, ACS_VLINE);
            attroff(COLOR_PAIR(CP_DIALOG_BORDER));
        }
    }

    wnoutrefresh(stdscr);
}

ListPickResult listpicker_show_tabbed(const char *title, ListItem *items, int item_count, int *selected,
                                       const char **tabs, int tab_count, int *active_tab)
{
    int max_rows, max_cols;
    getmaxyx(stdscr, max_rows, max_cols);

    /* Calculate dialog dimensions — one extra row for tab bar */
    int width = max_cols - 8;
    if (width > 76) width = 76;
    if (width < 50) width = 50;

    int height = max_rows - 6;
    if (height > 22) height = 22;
    if (height < 14) height = 14;

    int x = (max_cols - width) / 2;
    int y = (max_rows - height) / 2;

    /* top border, tab row, separator, help separator, five help lines, bottom border */
    int visible_rows = height - 10;
    if (visible_rows < 1) visible_rows = 1;

    /* Initialize state */
    TabbedListState state = {
        .title = title,
        .items = items,
        .item_count = item_count,
        .selected = *selected,
        .scroll_offset = 0,
        .visible_rows = visible_rows,
        .tabs = tabs,
        .tab_count = tab_count,
        .active_tab = *active_tab
    };

    /* Adjust scroll if needed */
    if (state.selected >= state.visible_rows) {
        state.scroll_offset = state.selected - state.visible_rows + 1;
    }

    ListPickResult result = LISTPICK_NONE;
    bool done = false;

    keypad(stdscr, TRUE);
    curs_set(0);

    while (!done) {
        draw_tabbed_list_picker(&state, y, x, height, width);
        doupdate();

        int ch = getch();

        switch (ch) {
            case KEY_UP:
            case 'k':
                if (state.selected > 0) {
                    state.selected--;
                    if (state.selected < state.scroll_offset) {
                        state.scroll_offset = state.selected;
                    }
                }
                break;

            case KEY_DOWN:
            case 'j':
                if (state.selected < state.item_count - 1) {
                    state.selected++;
                    if (state.selected >= state.scroll_offset + state.visible_rows) {
                        state.scroll_offset = state.selected - state.visible_rows + 1;
                    }
                }
                break;

            case KEY_PPAGE:
                state.selected -= state.visible_rows;
                if (state.selected < 0) state.selected = 0;
                state.scroll_offset = state.selected;
                break;

            case KEY_NPAGE:
                state.selected += state.visible_rows;
                if (state.selected >= state.item_count) {
                    state.selected = state.item_count - 1;
                }
                if (state.selected >= state.scroll_offset + state.visible_rows) {
                    state.scroll_offset = state.selected - state.visible_rows + 1;
                }
                break;

            case KEY_HOME:
                state.selected = 0;
                state.scroll_offset = 0;
                break;

            case KEY_END:
                state.selected = state.item_count - 1;
                if (state.selected >= state.visible_rows) {
                    state.scroll_offset = state.selected - state.visible_rows + 1;
                }
                break;

            case '\n':
            case '\r':
            case KEY_ENTER:
                result = LISTPICK_EDIT;
                done = true;
                break;

            case KEY_IC:
            case 'i':
            case 'I':
                result = LISTPICK_INSERT;
                done = true;
                break;

            case 'a':
            case 'A':
                result = LISTPICK_ADD;
                done = true;
                break;

            case KEY_DC:
                if (state.item_count > 0) {
                    result = LISTPICK_DELETE;
                    done = true;
                }
                break;

            case 'd':
            case 'D':
                if (state.item_count > 0) {
                    result = LISTPICK_DELETE;
                    done = true;
                }
                break;

            case KEY_LEFT:
                if (state.tab_count > 1 && state.active_tab > 0) {
                    state.active_tab--;
                    result = LISTPICK_TAB_LEFT;
                    done = true;
                }
                break;

            case KEY_RIGHT:
                if (state.tab_count > 1 && state.active_tab < state.tab_count - 1) {
                    state.active_tab++;
                    result = LISTPICK_TAB_RIGHT;
                    done = true;
                }
                break;

            case 27:
                result = LISTPICK_EXIT;
                done = true;
                break;

            case KEY_F(10):
                result = LISTPICK_EXIT;
                done = true;
                break;

            case ' ':
                state.selected = state.item_count - 1;
                if (state.selected >= state.visible_rows) {
                    state.scroll_offset = state.selected - state.visible_rows + 1;
                }
                break;

            default:
                if (ch >= '0' && ch <= '9') {
                    int target = ch - '0';
                    if (target < state.item_count) {
                        state.selected = target;
                        if (state.selected < state.scroll_offset) {
                            state.scroll_offset = state.selected;
                        } else if (state.selected >= state.scroll_offset + state.visible_rows) {
                            state.scroll_offset = state.selected - state.visible_rows + 1;
                        }
                    }
                }
                break;
        }
    }

    *selected = state.selected;
    *active_tab = state.active_tab;
    curs_set(1);

    return result;
}

/*
 * Helper functions for managing list items
 */

ListItem *listitem_create(const char *name, const char *extra, void *data)
{
    ListItem *item = malloc(sizeof(ListItem));
    if (!item) return NULL;
    
    item->name = name ? strdup(name) : strdup("");
    item->extra = extra ? strdup(extra) : NULL;
    item->enabled = true;
    item->data = data;
    
    return item;
}

void listitem_free(ListItem *item)
{
    if (item) {
        free(item->name);
        free(item->extra);
        free(item);
    }
}

void listitem_array_free(ListItem *items, int count)
{
    if (items) {
        for (int i = 0; i < count; i++) {
            free(items[i].name);
            free(items[i].extra);
        }
        free(items);
    }
}

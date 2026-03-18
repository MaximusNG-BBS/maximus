/*
 * theme.h — Theme registry API declarations
 *
 * Copyright (C) 2025-2026 Kevin Morgan (Limping Ninja)
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 */

#ifndef THEME_H_DEFINED
#define THEME_H_DEFINED

/**
 * @file theme.h
 * @brief Theme registry API.
 *
 * The theme registry holds up to THEME_SLOT_MAX-1 themes loaded from
 * config/general/theme.toml.  Registry slots are 1-based, matching the
 * `index` field in the TOML file.  Slot 0 is reserved.
 *
 * `usr.theme` stores a 1-based slot index, or 0 to mean "BBS default
 * theme" (no explicit user selection).
 *
 * The public accessor functions take a 0-based *iteration index* — the
 * dense ordinal position among loaded themes — so callers can loop
 * 0..theme_get_count()-1 without knowing the sparse TOML indices.
 *
 * Use theme_get_slot() to convert an iteration index to the TOML slot
 * suitable for storing in usr.theme.
 */

/**
 * @brief Maximum registry capacity.
 *
 * Slots 1 through THEME_SLOT_MAX-1 (i.e. 1..15) are usable.
 * Slot 0 is reserved: usr.theme == 0 means "BBS default".
 */
#define THEME_SLOT_MAX 16

cpp_begin()

/* ------------------------------------------------------------------ */
/*  Lifecycle                                                          */
/* ------------------------------------------------------------------ */

/**
 * @brief Populate the theme registry from general.theme.* in ng_cfg.
 *
 * Must be called after theme.toml is loaded by Read_Cfg().
 *
 * @return Number of themes loaded (>= 0), or -1 on hard failure (NULL ng_cfg).
 */
int theme_registry_init(void);


/* ------------------------------------------------------------------ */
/*  Iteration accessors  (0-based iteration index)                    */
/* ------------------------------------------------------------------ */

/**
 * @brief Return the number of registered themes.
 *
 * Used as the loop bound for theme_get_name/shortname/lang.
 */
int theme_get_count(void);

/**
 * @brief Map a 0-based iteration index to the TOML slot index.
 *
 * Useful when building Chg_Theme() UI: the user selects from a list
 * numbered 0..count-1, and this converts the selection to the value
 * that should be stored in usr.theme.
 *
 * @param iter  0-based iteration index
 * @return TOML slot index (1..THEME_SLOT_MAX-1), or 0 if out of range
 */
int theme_get_slot(int iter);

/**
 * @brief Get the display name of the theme at iteration index.
 *
 * @param index  0-based iteration index
 * @return Display name string, or NULL if out of range
 */
const char *theme_get_name(int index);

/**
 * @brief Get the short_name of the theme at iteration index.
 *
 * short_name is filesystem-safe and used as a path component when
 * probing themed display files (e.g. "screens/main.maxng.bbs").
 *
 * @param index  0-based iteration index
 * @return Short name string, or NULL if out of range
 */
const char *theme_get_shortname(int index);

/**
 * @brief Get the language binding of the theme at iteration index.
 *
 * Returns the raw lang field.  An empty string means the theme inherits
 * the system default language; the caller decides how to resolve it.
 *
 * @param index  0-based iteration index
 * @return Language basename (possibly ""), or NULL if out of range
 */
const char *theme_get_lang(int index);


/* ------------------------------------------------------------------ */
/*  Reverse-lookup accessor                                           */
/* ------------------------------------------------------------------ */

/**
 * @brief Find the iteration index of a theme by short_name.
 *
 * @param short_name  Theme short name to search for (case-insensitive)
 * @return 0-based iteration index, or -1 if not found
 */
int theme_get_index(const char *short_name);


/* ------------------------------------------------------------------ */
/*  Current-user and default accessors                                */
/* ------------------------------------------------------------------ */

/**
 * @brief Get the short_name of the currently active theme.
 *
 * Reads usr.theme:
 *   - 0 → "BBS default" → returns the configured default_theme shortname
 *   - 1..THEME_SLOT_MAX-1 → direct slot lookup; falls back to default on miss
 *
 * Used by DisplayOpenFile(), mci.c |TN, and ngcfg_make_themed_key().
 *
 * @return Theme short_name (never NULL; falls back to compiled-in "maxng")
 */
const char *theme_get_current_shortname(void);

/**
 * @brief Get the configured default theme short_name.
 *
 * This is the value of general.theme.general.default_theme from theme.toml.
 * Defaults to "maxng" if the key is absent.
 *
 * @return Default theme short_name
 */
const char *theme_get_default_shortname(void);

cpp_end()

#endif /* THEME_H_DEFINED */

/*
 * theme.c — Theme registry: loads theme definitions from TOML config
 *           and provides accessors used by the rest of Maximus.
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

#include <string.h>
#include "libmaxcfg.h"
#include "prog.h"
#include "mm.h"
#include "theme.h"

/* ------------------------------------------------------------------ */
/*  Private types                                                      */
/* ------------------------------------------------------------------ */

/** @brief Per-theme record, keyed by TOML slot index (1-based). */
typedef struct
{
  byte used;                /**< 1 if this slot holds a loaded theme       */
  byte slot;                /**< TOML index (1-based); mirrors array pos   */
  char short_name[32];      /**< Filesystem-safe identifier (e.g. "maxng") */
  char name[64];            /**< Human-readable display name               */
  char lang[32];            /**< Language basename, or "" to inherit       */
} theme_entry_t;


/* ------------------------------------------------------------------ */
/*  Module state (file-scope only)                                     */
/* ------------------------------------------------------------------ */

/** Registry array.  Slot 0 stays zeroed (sentinel: usr.theme == 0). */
static theme_entry_t g_theme_registry[THEME_SLOT_MAX];

/** Count of occupied slots (loaded themes). */
static int g_theme_count;

/** Default theme shortname from general.theme.general.default_theme. */
static char g_default_shortname[32];

/** Default lang basename from general.theme.general.default_lang. */
static char g_default_lang[32];


/* ------------------------------------------------------------------ */
/*  Private helpers                                                    */
/* ------------------------------------------------------------------ */

/**
 * @brief Reset all registry state to clean defaults.
 *
 * Called at the start of theme_registry_init() to guarantee a known
 * baseline even if init is called more than once.
 */
static void near theme_registry_reset(void)
{
  memset(g_theme_registry, 0, sizeof(g_theme_registry));
  g_theme_count = 0;
  strcpy(g_default_shortname, "maxng");
  strcpy(g_default_lang, "english");
}

/**
 * @brief Return 1 if @p slot is a usable registry slot (1–THEME_SLOT_MAX-1).
 *
 * Slot 0 is the sentinel for "no explicit theme set" and is never valid
 * for a populated entry.
 *
 * @param slot  Slot index to test
 * @return Non-zero if valid
 */
static int near theme_slot_valid(int slot)
{
  return slot > 0 && slot < THEME_SLOT_MAX;
}

/**
 * @brief Look up the slot index for a given short_name.
 *
 * @param short_name  Short name to search for (case-insensitive)
 * @return Slot index (1–THEME_SLOT_MAX-1) if found, 0 otherwise
 */
static int near theme_slot_from_shortname(const char *short_name)
{
  int i;

  if (!short_name || !*short_name)
    return 0;

  for (i = 1; i < THEME_SLOT_MAX; i++)
  {
    if (g_theme_registry[i].used &&
        stricmp(g_theme_registry[i].short_name, short_name) == 0)
      return i;
  }

  return 0;
}

/**
 * @brief Map a 0-based iteration index to the underlying slot index.
 *
 * Walks occupied slots in ascending order and returns the slot of the
 * Nth occupied entry.
 *
 * @param iter  0-based iteration index
 * @return Slot index, or 0 if iter is out of range
 */
static int near theme_iter_to_slot(int iter)
{
  int i;
  int seen = 0;

  if (iter < 0 || iter >= g_theme_count)
    return 0;

  for (i = 1; i < THEME_SLOT_MAX; i++)
  {
    if (!g_theme_registry[i].used)
      continue;

    if (seen == iter)
      return i;

    seen++;
  }

  return 0;
}

/**
 * @brief Return a pointer to the registry entry for iteration index @p iter.
 *
 * @param iter  0-based iteration index
 * @return Pointer to entry, or NULL if out of range
 */
static const theme_entry_t * near theme_by_iter(int iter)
{
  int slot = theme_iter_to_slot(iter);
  return slot ? &g_theme_registry[slot] : NULL;
}


/* ------------------------------------------------------------------ */
/*  Lifecycle                                                          */
/* ------------------------------------------------------------------ */

/**
 * @brief Populate the theme registry from general.theme.* in ng_cfg.
 *
 * Expected TOML structure (loaded with prefix "general.theme"):
 * @code
 *   [general]
 *   default_theme = "maxng"    # shortname of the BBS default theme
 *   default_lang  = "english"  # system default language basename
 *
 *   [[theme]]
 *   index      = 1             # 1-based slot; must be unique, 1–15
 *   short_name = "maxng"       # filesystem-safe identifier; must be unique
 *   name       = "MaxNG Skin"  # display name (falls back to short_name)
 *   lang       = ""            # language basename, or "" to inherit
 * @endcode
 *
 * Must be called after theme.toml is loaded by Read_Cfg().
 *
 * @return Number of themes loaded (>= 0), or -1 on hard failure (NULL ng_cfg).
 */
int theme_registry_init(void)
{
  MaxCfgToml *toml;   /* cast of ng_cfg — MaxCfg * and MaxCfgToml * are the same handle */
  MaxCfgVar arr;
  MaxCfgVar item;
  MaxCfgVar v;
  size_t cnt = 0;
  size_t i;

  theme_registry_reset();

  if (!ng_cfg)
  {
    logit("!theme_registry_init: ng_cfg is NULL");
    return -1;
  }

  /* ng_cfg is MaxCfg * but the toml API takes MaxCfgToml *; same handle. */
  toml = (MaxCfgToml *)ng_cfg;

  /* Read [general] defaults */
  if (maxcfg_toml_get(toml, "general.theme.general.default_theme", &v) == MAXCFG_OK &&
      v.type == MAXCFG_VAR_STRING && v.v.s && *v.v.s)
  {
    strnncpy(g_default_shortname, (char *)v.v.s, sizeof(g_default_shortname) - 1);
  }

  if (maxcfg_toml_get(toml, "general.theme.general.default_lang", &v) == MAXCFG_OK &&
      v.type == MAXCFG_VAR_STRING && v.v.s && *v.v.s)
  {
    strnncpy(g_default_lang, (char *)v.v.s, sizeof(g_default_lang) - 1);
  }

  /* Read [[theme]] table array */
  if (maxcfg_toml_get(toml, "general.theme.theme", &arr) != MAXCFG_OK ||
      arr.type != MAXCFG_VAR_TABLE_ARRAY)
  {
    logit("!theme_registry_init: missing general.theme.theme");
    return 0;
  }

  if (maxcfg_var_count(&arr, &cnt) != MAXCFG_OK || cnt == 0)
    return 0;

  for (i = 0; i < cnt; i++)
  {
    int slot = 0;
    const char *short_name = "";
    const char *name = "";
    const char *lang = "";

    if (maxcfg_toml_array_get(&arr, i, &item) != MAXCFG_OK ||
        item.type != MAXCFG_VAR_TABLE)
      continue;

    /* index — required, 1..THEME_SLOT_MAX-1 */
    if (maxcfg_toml_table_get(&item, "index", &v) == MAXCFG_OK &&
        v.type == MAXCFG_VAR_INT)
      slot = v.v.i;

    if (!theme_slot_valid(slot))
    {
      logit("!theme_registry_init: skipping entry %d (index %d out of range)",
            (int)i, slot);
      continue;
    }

    if (g_theme_registry[slot].used)
    {
      logit("!theme_registry_init: duplicate index %d", slot);
      continue;
    }

    /* short_name — required */
    if (maxcfg_toml_table_get(&item, "short_name", &v) == MAXCFG_OK &&
        v.type == MAXCFG_VAR_STRING && v.v.s)
      short_name = v.v.s;

    if (!*short_name)
    {
      logit("!theme_registry_init: skipping entry %d (empty short_name)", (int)i);
      continue;
    }

    if (theme_slot_from_shortname(short_name) != 0)
    {
      logit("!theme_registry_init: duplicate short_name '%s'", short_name);
      continue;
    }

    /* name — optional; falls back to short_name */
    if (maxcfg_toml_table_get(&item, "name", &v) == MAXCFG_OK &&
        v.type == MAXCFG_VAR_STRING && v.v.s)
      name = v.v.s;

    if (!*name)
      name = short_name;

    /* lang — optional; empty string means "inherit default" */
    if (maxcfg_toml_table_get(&item, "lang", &v) == MAXCFG_OK &&
        v.type == MAXCFG_VAR_STRING && v.v.s)
      lang = v.v.s;

    /* Commit to registry */
    g_theme_registry[slot].used = 1;
    g_theme_registry[slot].slot = (byte)slot;
    strnncpy(g_theme_registry[slot].short_name, (char *)short_name,
             sizeof(g_theme_registry[slot].short_name) - 1);
    strnncpy(g_theme_registry[slot].name, (char *)name,
             sizeof(g_theme_registry[slot].name) - 1);
    strnncpy(g_theme_registry[slot].lang, (char *)lang,
             sizeof(g_theme_registry[slot].lang) - 1);
    g_theme_count++;
  }

  /* Warn if the configured default theme isn't registered */
  if (*g_default_shortname && theme_slot_from_shortname(g_default_shortname) == 0)
    logit("!theme_registry_init: default theme '%s' not present in registry",
          g_default_shortname);

  logit(">Theme registry: %d theme(s), default='%s'",
        g_theme_count, g_default_shortname);
  return g_theme_count;
}


/* ------------------------------------------------------------------ */
/*  Iteration accessors                                                */
/* ------------------------------------------------------------------ */

/**
 * @brief Return the number of registered themes.
 *
 * Callers iterate 0..theme_get_count()-1 to enumerate themes.
 */
int theme_get_count(void)
{
  return g_theme_count;
}

/**
 * @brief Map a 0-based iteration index to the TOML slot index.
 *
 * This is the bridge between the dense 0-based iteration API and the
 * sparse 1-based slot storage.  Use it to convert a user's selection
 * (after adjusting the display by +1 for "BBS Default") into the value
 * to store in usr.theme.
 *
 * @param iter  0-based iteration index (0..theme_get_count()-1)
 * @return TOML slot index (1..THEME_SLOT_MAX-1), or 0 if out of range
 */
int theme_get_slot(int iter)
{
  return theme_iter_to_slot(iter);
}

/**
 * @brief Get the display name of the theme at iteration index.
 *
 * @param index  0-based iteration index
 * @return Display name string, or NULL if out of range
 */
const char *theme_get_name(int index)
{
  const theme_entry_t *e = theme_by_iter(index);
  return e ? e->name : NULL;
}

/**
 * @brief Get the short_name of the theme at iteration index.
 *
 * short_name is used as a filesystem path component when probing themed
 * display files (e.g. "screens/main.maxng.bbs").
 *
 * @param index  0-based iteration index
 * @return Short name string, or NULL if out of range
 */
const char *theme_get_shortname(int index)
{
  const theme_entry_t *e = theme_by_iter(index);
  return e ? e->short_name : NULL;
}

/**
 * @brief Get the language binding of the theme at iteration index.
 *
 * Returns the raw lang field.  An empty string means the theme
 * inherits the system default language; callers must guard accordingly.
 *
 * @param index  0-based iteration index
 * @return Language basename (possibly ""), or NULL if out of range
 */
const char *theme_get_lang(int index)
{
  const theme_entry_t *e = theme_by_iter(index);
  return e ? e->lang : NULL;
}


/* ------------------------------------------------------------------ */
/*  Reverse-lookup accessor                                           */
/* ------------------------------------------------------------------ */

/**
 * @brief Find the iteration index of a theme by short_name.
 *
 * @param short_name  Short name to search for (case-insensitive)
 * @return 0-based iteration index, or -1 if not found
 */
int theme_get_index(const char *short_name)
{
  int i;
  int seen = 0;

  if (!short_name || !*short_name)
    return -1;

  for (i = 1; i < THEME_SLOT_MAX; i++)
  {
    if (!g_theme_registry[i].used)
      continue;

    if (stricmp(g_theme_registry[i].short_name, short_name) == 0)
      return seen;

    seen++;
  }

  return -1;
}


/* ------------------------------------------------------------------ */
/*  Current-user and default accessors                                */
/* ------------------------------------------------------------------ */

/**
 * @brief Get the short_name of the currently active theme.
 *
 * Interprets usr.theme as follows:
 *   - 0: "BBS default" — no explicit user selection; resolves to
 *        the configured default_theme shortname
 *   - 1–THEME_SLOT_MAX-1: direct slot lookup; falls back to the
 *        configured default if the slot is unused or out of range
 *
 * Used by DisplayOpenFile(), mci.c |TN, and ngcfg_make_themed_key().
 *
 * @return Theme short_name (never NULL; falls back to compiled-in "maxng")
 */
const char *theme_get_current_shortname(void)
{
  byte slot = usr.theme;

  /* 0 = no explicit selection; use BBS default */
  if (slot == 0)
    return g_default_shortname;

  /* Direct slot lookup for explicit selections */
  if (theme_slot_valid(slot) && g_theme_registry[slot].used)
    return g_theme_registry[slot].short_name;

  /* Stored slot is out of range or empty — fall back to default */
  return g_default_shortname;
}

/**
 * @brief Get the configured default theme short_name.
 *
 * This is the value of general.theme.general.default_theme from
 * theme.toml.  Defaults to "maxng" if the key is absent.
 *
 * @return Default theme short_name
 */
const char *theme_get_default_shortname(void)
{
  return g_default_shortname;
}

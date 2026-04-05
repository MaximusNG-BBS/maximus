/**
 * @file theme_tabs.c
 * @brief Build and free theme tab arrays from the loaded theme registry.
 *
 * Reads general.theme.theme[%d].* entries from the global TOML config
 * and produces a ThemeTab array suitable for driving a tabbed UI.
 */

#include "maxcfg.h"
#include "theme_tabs.h"
#include <stdlib.h>
#include <string.h>

/**
 * Probe a single TOML path and return the string value, or "".
 *
 * Mirrors the static toml_get_string_or_empty() helper in menubar.c.
 */
static const char *theme_toml_str(const char *path)
{
    MaxCfgVar v;
    if (g_maxcfg_toml != NULL &&
        maxcfg_toml_get(g_maxcfg_toml, path, &v) == MAXCFG_OK &&
        v.type == MAXCFG_VAR_STRING &&
        v.v.s != NULL) {
        return v.v.s;
    }
    return "";
}

/**
 * Probe a single TOML path and return the int value, or the default.
 *
 * Mirrors the static toml_get_int_or_default() helper in menubar.c.
 */
static int theme_toml_int(const char *path, int def)
{
    MaxCfgVar v;
    if (g_maxcfg_toml != NULL &&
        maxcfg_toml_get(g_maxcfg_toml, path, &v) == MAXCFG_OK &&
        v.type == MAXCFG_VAR_INT) {
        return v.v.i;
    }
    return def;
}

/**
 * Check whether a theme entry at the given index appears to exist.
 *
 * Uses the same probe strategy as theme_entry_load() in menubar.c:
 * check short_name first, then fall back to index field.
 */
static bool theme_entry_exists(int idx)
{
    char path[256];

    snprintf(path, sizeof(path), "general.theme.theme[%d].short_name", idx);
    const char *sn = theme_toml_str(path);
    if (sn[0] != '\0') {
        return true;
    }

    /* Handle entries with empty short_name but a valid index */
    snprintf(path, sizeof(path), "general.theme.theme[%d].index", idx);
    MaxCfgVar v;
    if (maxcfg_toml_get(g_maxcfg_toml, path, &v) == MAXCFG_OK) {
        return true;
    }

    return false;
}

ThemeTab *theme_tabs_build(int *out_count)
{
    if (!out_count) return NULL;

    /*
     * Scan indices 0..15 looking for configured themes.
     * This matches the upper bound used elsewhere in the codebase.
     */
    int theme_count = 0;
    char short_names[16][256];
    char names[16][256];
    int  indices[16];

    for (int i = 0; i < 16; i++) {
        if (!theme_entry_exists(i)) {
            continue;
        }

        char path[256];

        snprintf(path, sizeof(path), "general.theme.theme[%d].index", i);
        indices[theme_count] = theme_toml_int(path, i);

        snprintf(path, sizeof(path), "general.theme.theme[%d].short_name", i);
        strncpy(short_names[theme_count], theme_toml_str(path), sizeof(short_names[theme_count]) - 1);
        short_names[theme_count][sizeof(short_names[theme_count]) - 1] = '\0';

        snprintf(path, sizeof(path), "general.theme.theme[%d].name", i);
        strncpy(names[theme_count], theme_toml_str(path), sizeof(names[theme_count]) - 1);
        names[theme_count][sizeof(names[theme_count]) - 1] = '\0';

        theme_count++;
    }

    if (theme_count == 0) {
        *out_count = 0;
        return NULL;
    }

    /* Return only configured themes — no synthetic All tab. */
    int total = theme_count;
    ThemeTab *tabs = calloc((size_t)total, sizeof(ThemeTab));
    if (!tabs) {
        *out_count = 0;
        return NULL;
    }

    /* Tabs 0..N-1: configured themes from the registry */
    for (int i = 0; i < theme_count; i++) {
        tabs[i].short_name = strdup(short_names[i]);
        tabs[i].name = strdup(names[i]);
        tabs[i].index = indices[i];
    }

    *out_count = total;
    return tabs;
}

int theme_tabs_default_index(const ThemeTab *tabs, int count)
{
    const char *wanted = theme_toml_str("general.theme.general.default_theme");

    if (!tabs || count <= 0) {
        return 0;
    }

    if (wanted && wanted[0] != '\0') {
        for (int i = 0; i < count; i++) {
            if (tabs[i].short_name && strcmp(tabs[i].short_name, wanted) == 0) {
                return i;
            }
        }
    }

    return 0;
}

void theme_tabs_free(ThemeTab *tabs, int count)
{
    if (!tabs || count <= 0) return;

    for (int i = 0; i < count; i++) {
        free(tabs[i].short_name);
        free(tabs[i].name);
    }
    free(tabs);
}

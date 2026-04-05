#ifndef THEME_TABS_H
#define THEME_TABS_H

typedef struct {
    char *short_name;
    char *name;
    int   index;
} ThemeTab;

/**
 * Build an allocated tab array from the loaded theme registry.
 *
 * @param out_count  Receives the number of tabs in the returned array.
 * @return           Dynamically allocated ThemeTab array, or NULL on failure.
 *                   Caller must free with theme_tabs_free().
 */
ThemeTab *theme_tabs_build(int *out_count);

/**
 * Return the preferred default tab index based on general.theme.general.default_theme.
 * Falls back to 0 if the configured theme is missing or invalid.
 */
int theme_tabs_default_index(const ThemeTab *tabs, int count);

/**
 * Free a ThemeTab array and its contents.
 *
 * @param tabs   Pointer to the first element of the array (may be NULL).
 * @param count  Number of elements in the array.
 */
void theme_tabs_free(ThemeTab *tabs, int count);

#endif

/*
 * mexui.c — MEX UI intrinsics (popup overlays, lightbar, etc.)
 *
 * Copyright 2026 by Kevin Morgan.  All rights reserved.
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

#define MAX_LANG_m_area
#include "mexall.h"
#include "dv.h"
#include "mci.h"
#include "ui_field.h"
#include "ui_lightbar.h"
#include "ui_form.h"
#include "ui_scroll.h"

/**
 * @brief Duplicate a MEX VM string into a heap-allocated C string.
 *
 * @param pia  Pointer to the IADDR of the VM string.
 * @return Heap-allocated copy of the string, or NULL on failure.
 */
static char * near MexDupVMString(const IADDR *pia)
{
  char *vm_str;
  word wLen;
  char *rc;

  if (!pia)
    return NULL;

  vm_str = (char *)MexFetch(FormString, (IADDR *)pia);
  if (!vm_str)
    return NULL;

  wLen = *(word *)vm_str;
  vm_str += sizeof(word);

  rc = (char *)malloc((size_t)wLen + 1);
  if (!rc)
    return NULL;

  memcpy(rc, vm_str, wLen);
  rc[wLen] = 0;
  return rc;
}

/**
 * @brief Allocate a heap string containing just a NUL terminator.
 *
 * @return Heap-allocated empty string, or NULL on allocation failure.
 */
static char * near MexDupEmptyString(void)
{
  char *rc;

  rc = (char *)malloc(1);
  if (!rc)
    return NULL;

  rc[0] = 0;
  return rc;
}

#ifdef MEX

typedef struct mex_scroll_region_obj
{
  char *key;
  ui_scrolling_region_t r;
  struct mex_scroll_region_obj *next;
} mex_scroll_region_obj_t;

typedef struct mex_text_viewer_obj
{
  char *key;
  ui_text_viewer_t v;
  struct mex_text_viewer_obj *next;
} mex_text_viewer_obj_t;

typedef struct mex_overlay_obj
{
  char *key;
  int row;
  int col;
  int width;
  int height;
  word *cells;
  struct mex_overlay_obj *next;
} mex_overlay_obj_t;

typedef struct mex_region_obj
{
  char *key;
  int width;
  int height;
  word *cells;
  struct mex_region_obj *next;
} mex_region_obj_t;

typedef struct mex_screen_obj
{
  char *key;
  int width;
  int height;
  int cursor_row;
  int cursor_col;
  byte attr;
  word *cells;
  struct mex_screen_obj *next;
} mex_screen_obj_t;

static mex_scroll_region_obj_t *near g_scroll_regions = NULL;
static mex_text_viewer_obj_t *near g_text_viewers = NULL;
static mex_overlay_obj_t *near g_overlays = NULL;
static mex_region_obj_t *near g_regions = NULL;
static mex_screen_obj_t *near g_screens = NULL;

/**
 * @brief Determine whether a UI/output intrinsic should flush immediately.
 *
 * MEX scripts default to instant video, but batched UI updates temporarily
 * suppress per-call flushes so a composed region can appear in one pass.
 *
 * @return 1 if a flush should happen now, 0 otherwise.
 */
static int near mex_ui_should_flush(void)
{
  if (!pmisThis || !pmisThis->pmid)
    return 0;

  return (pmisThis->pmid->instant_video &&
          pmisThis->pmid->ui_update_depth == 0);
}

/**
 * @brief Look up a scrolling region object by key name.
 *
 * @param key  Unique key string identifying the region.
 * @return Pointer to the matching object, or NULL if not found.
 */
static mex_scroll_region_obj_t *near mex_find_scroll_region(const char *key)
{
  mex_scroll_region_obj_t *cur;

  if (!key || !*key)
    return NULL;

  for (cur = g_scroll_regions; cur; cur = cur->next)
    if (cur->key && strcmp(cur->key, key) == 0)
      return cur;

  return NULL;
}

/**
 * @brief Look up a text viewer object by key name.
 *
 * @param key  Unique key string identifying the viewer.
 * @return Pointer to the matching object, or NULL if not found.
 */
static mex_text_viewer_obj_t *near mex_find_text_viewer(const char *key)
{
  mex_text_viewer_obj_t *cur;

  if (!key || !*key)
    return NULL;

  for (cur = g_text_viewers; cur; cur = cur->next)
    if (cur->key && strcmp(cur->key, key) == 0)
      return cur;

  return NULL;
}

/**
 * @brief Look up a live-screen overlay snapshot by key name.
 *
 * @param key  Unique key string identifying the overlay.
 * @return Pointer to the matching object, or NULL if not found.
 */
static mex_overlay_obj_t *near mex_find_overlay(const char *key)
{
  mex_overlay_obj_t *cur;

  if (!key || !*key)
    return NULL;

  for (cur = g_overlays; cur; cur = cur->next)
    if (cur->key && strcmp(cur->key, key) == 0)
      return cur;

  return NULL;
}

/**
 * @brief Look up a region snapshot by key name.
 */
static mex_region_obj_t *near mex_find_region(const char *key)
{
  mex_region_obj_t *cur;

  if (!key || !*key)
    return NULL;

  for (cur = g_regions; cur; cur = cur->next)
    if (cur->key && strcmp(cur->key, key) == 0)
      return cur;

  return NULL;
}

/**
 * @brief Look up a full-screen snapshot by key name.
 */
static mex_screen_obj_t *near mex_find_screen(const char *key)
{
  mex_screen_obj_t *cur;

  if (!key || !*key)
    return NULL;

  for (cur = g_screens; cur; cur = cur->next)
    if (cur->key && strcmp(cur->key, key) == 0)
      return cur;

  return NULL;
}

/**
 * @brief Remove and free an overlay snapshot object.
 *
 * @param target  Overlay object to remove.
 * @return 0 on success, -1 if target not found.
 */
static int near mex_overlay_remove(mex_overlay_obj_t *target)
{
  mex_overlay_obj_t *cur;
  mex_overlay_obj_t *prev;

  if (!target)
    return -1;

  prev = NULL;
  for (cur = g_overlays; cur; prev = cur, cur = cur->next)
    if (cur == target)
      break;

  if (!cur)
    return -1;

  if (prev)
    prev->next = cur->next;
  else
    g_overlays = cur->next;

  if (cur->cells)
    free(cur->cells);
  if (cur->key)
    free(cur->key);
  free(cur);
  return 0;
}

/**
 * @brief Remove and free a region snapshot object.
 */
static int near mex_region_remove(mex_region_obj_t *target)
{
  mex_region_obj_t *cur;
  mex_region_obj_t *prev;

  if (!target)
    return -1;

  prev = NULL;
  for (cur = g_regions; cur; prev = cur, cur = cur->next)
    if (cur == target)
      break;

  if (!cur)
    return -1;

  if (prev)
    prev->next = cur->next;
  else
    g_regions = cur->next;

  if (cur->cells)
    free(cur->cells);
  if (cur->key)
    free(cur->key);
  free(cur);
  return 0;
}

/**
 * @brief Remove and free a full-screen snapshot object.
 */
static int near mex_screen_remove(mex_screen_obj_t *target)
{
  mex_screen_obj_t *cur;
  mex_screen_obj_t *prev;

  if (!target)
    return -1;

  prev = NULL;
  for (cur = g_screens; cur; prev = cur, cur = cur->next)
    if (cur == target)
      break;

  if (!cur)
    return -1;

  if (prev)
    prev->next = cur->next;
  else
    g_screens = cur->next;

  if (cur->cells)
    free(cur->cells);
  if (cur->key)
    free(cur->key);
  free(cur);
  return 0;
}

/**
 * @brief Capture a live-screen rectangle into a heap block.
 *
 * Coordinates are 1-based and inclusive. Output width/height reflect clipping.
 *
 * @return 0 on success, -1 on error.
 */
static int near mex_capture_live_rect(int left, int top, int right, int bottom,
                                      int *out_width, int *out_height, word **out_cells)
{
  int max_rows, max_cols;
  int width, height;
  int r, c;
  size_t count;
  word *cells;

  if (!out_width || !out_height || !out_cells)
    return -1;

  max_rows = VidNumRows();
  max_cols = VidNumCols();

  if (left < 1)
    left = 1;
  if (top < 1)
    top = 1;
  if (right > max_cols)
    right = max_cols;
  if (bottom > max_rows)
    bottom = max_rows;

  if (left > right || top > bottom)
    return -1;

  width = right - left + 1;
  height = bottom - top + 1;
  count = (size_t)width * (size_t)height;

  cells = (word *)malloc(count * sizeof(word));
  if (!cells)
    return -1;

  for (r = 0; r < height; r++)
    for (c = 0; c < width; c++)
      cells[(r * width) + c] = (word)VidGetch(left + c - 1, top + r - 1);

  *out_width = width;
  *out_height = height;
  *out_cells = cells;
  return 0;
}

/**
 * @brief Restore a heap block of live-screen cells at the given top-left.
 */
static void near mex_restore_live_rect(int left, int top, int width, int height, const word *cells)
{
  int max_rows, max_cols;
  int r, c;

  if (!cells || width < 1 || height < 1)
    return;

  max_rows = VidNumRows();
  max_cols = VidNumCols();

  for (r = 0; r < height; r++)
  {
    int dst_row = top + r;
    if (dst_row < 1 || dst_row > max_rows)
      continue;

    for (c = 0; c < width; c++)
    {
      int dst_col = left + c;
      word cell;

      if (dst_col < 1 || dst_col > max_cols)
        continue;

      cell = cells[(r * width) + c];
      VidPutch(dst_col - 1, dst_row - 1,
               (byte)(cell & 0x00ff),
               (byte)((cell >> 8) & 0x00ff));
    }
  }
}

/**
 * @brief Draw a boxed frame directly to the live screen.
 */
static void near mex_draw_box(int row, int col, int width, int height, byte attr, const char *title)
{
  int i;

  if (row < 1)
    row = 1;
  if (col < 1)
    col = 1;

  if (width < 2 || height < 2)
    return;

  ui_set_attr(attr);

  /* Top edge: corner + horizontal + corner */

  ui_goto(row, col);
  Putc('\xda');
  for (i = 1; i < width - 1; i++)
    Putc('\xc4');
  Putc('\xbf');

  /* Side edges */

  for (i = 1; i < height - 1; i++)
  {
    ui_goto(row + i, col);
    Putc('\xb3');
    ui_goto(row + i, col + width - 1);
    Putc('\xb3');
  }

  /* Bottom edge: corner + horizontal + corner */

  ui_goto(row + height - 1, col);
  Putc('\xc0');
  for (i = 1; i < width - 1; i++)
    Putc('\xc4');
  Putc('\xd9');

  /* Optional title on top edge */

  if (title && *title)
  {
    int title_len = (int)strlen(title);
    int max_title = width - 4;

    if (max_title > 0)
    {
      if (title_len > max_title)
        title_len = max_title;

      ui_goto(row, col + 1);
      for (i = 0; i < title_len; i++)
        Putc(title[i]);
    }
  }
}

/**
 * @brief MEX intrinsic: ui_goto(row, col) — Position cursor at row/col.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_goto(void)
{
  MA ma;
  int row, col;
  
  MexArgBegin(&ma);
  row = (int)MexArgGetWord(&ma);
  col = (int)MexArgGetWord(&ma);
  
  ui_goto(row, col);
  
  if (mex_ui_should_flush())
    vbuf_flush();
  
  return MexArgEnd(&ma);
}

/**
 * @brief ui_read_key() - Return a MaxUI decoded key code.
 */
word EXPENTRY intrin_ui_read_key(void)
{
  regs_2[0] = (word)ui_read_key();
  return 0;
}

/**
 * @brief ui_begin_update() - Suspend immediate per-call flushes for batched UI paint.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_begin_update(void)
{
  if (pmisThis && pmisThis->pmid && pmisThis->pmid->ui_update_depth < 0xffff)
    pmisThis->pmid->ui_update_depth++;

  return 0;
}

/**
 * @brief ui_end_update() - End a batched UI paint and flush once if needed.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_end_update(void)
{
  if (pmisThis && pmisThis->pmid && pmisThis->pmid->ui_update_depth > 0)
    pmisThis->pmid->ui_update_depth--;

  if (mex_ui_should_flush())
    vbuf_flush();

  return 0;
}

/**
 * @brief MEX intrinsic: ui_overlay_push(key, row, col, width, height) — Snapshot a live screen rectangle.
 *
 * Coordinates are 1-based. The captured area can later be restored exactly
 * with ui_overlay_pop(key) or discarded with ui_overlay_drop(key).
 *
 * @return MEX status; 0 on success, -1 on failure.
 */
word EXPENTRY intrin_ui_overlay_push(void)
{
  MA ma;
  char *key;
  int row, col, width, height;
  int max_rows, max_cols;
  mex_overlay_obj_t *obj;
  int clipped_w, clipped_h;
  word *cells = NULL;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  row = (int)MexArgGetWord(&ma);
  col = (int)MexArgGetWord(&ma);
  width = (int)MexArgGetWord(&ma);
  height = (int)MexArgGetWord(&ma);

  regs_2[0] = (word)-1;

  if (!key || !*key || width < 1 || height < 1)
  {
    if (key)
      free(key);
    return MexArgEnd(&ma);
  }

  if (mex_find_overlay(key))
  {
    free(key);
    return MexArgEnd(&ma);
  }

  max_rows = VidNumRows();
  max_cols = VidNumCols();

  if (row < 1)
    row = 1;
  if (col < 1)
    col = 1;
  if (row > max_rows || col > max_cols)
  {
    free(key);
    return MexArgEnd(&ma);
  }

  if ((row + height - 1) > max_rows)
    height = max_rows - row + 1;
  if ((col + width - 1) > max_cols)
    width = max_cols - col + 1;

  if (width < 1 || height < 1)
  {
    free(key);
    return MexArgEnd(&ma);
  }

  obj = (mex_overlay_obj_t *)calloc(1, sizeof(*obj));
  if (!obj)
  {
    free(key);
    return MexArgEnd(&ma);
  }

  if (mex_capture_live_rect(col, row, col + width - 1, row + height - 1,
                            &clipped_w, &clipped_h, &cells) != 0)
  {
    free(obj);
    free(key);
    return MexArgEnd(&ma);
  }

  obj->cells = cells;

  obj->key = key;
  obj->row = row;
  obj->col = col;
  obj->width = clipped_w;
  obj->height = clipped_h;

  obj->next = g_overlays;
  g_overlays = obj;

  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_overlay_pop(key) — Restore and free a live screen snapshot.
 *
 * @return MEX status; 0 on success, -1 if not found.
 */
word EXPENTRY intrin_ui_overlay_pop(void)
{
  MA ma;
  char *key;
  mex_overlay_obj_t *obj;
  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);

  regs_2[0] = (word)-1;

  obj = mex_find_overlay(key);
  if (key)
    free(key);

  if (!obj || !obj->cells)
    return MexArgEnd(&ma);

  mex_restore_live_rect(obj->col, obj->row, obj->width, obj->height, obj->cells);

  mex_overlay_remove(obj);
  if (mex_ui_should_flush())
    vbuf_flush();
  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_overlay_drop(key) — Free a live screen snapshot without restoring it.
 *
 * @return MEX status; 0 on success, -1 if not found.
 */
word EXPENTRY intrin_ui_overlay_drop(void)
{
  MA ma;
  char *key;
  mex_overlay_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);

  regs_2[0] = (word)-1;
  obj = mex_find_overlay(key);
  if (key)
    free(key);

  if (!obj)
    return MexArgEnd(&ma);

  mex_overlay_remove(obj);
  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief ui_region_get(key, left, top, right, bottom) - Capture a named live-screen block.
 *
 * Coordinates are 1-based and inclusive.
 *
 * @return MEX status; result in regs_2[0] (0 success, -1 error).
 */
word EXPENTRY intrin_ui_region_get(void)
{
  MA ma;
  char *key;
  int left, top, right, bottom;
  int width, height;
  word *cells = NULL;
  mex_region_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  left = (int)MexArgGetWord(&ma);
  top = (int)MexArgGetWord(&ma);
  right = (int)MexArgGetWord(&ma);
  bottom = (int)MexArgGetWord(&ma);

  regs_2[0] = (word)-1;

  if (!key || !*key)
  {
    if (key)
      free(key);
    return MexArgEnd(&ma);
  }

  if (mex_find_region(key))
  {
    free(key);
    return MexArgEnd(&ma);
  }

  if (mex_capture_live_rect(left, top, right, bottom, &width, &height, &cells) != 0)
  {
    free(key);
    return MexArgEnd(&ma);
  }

  obj = (mex_region_obj_t *)calloc(1, sizeof(*obj));
  if (!obj)
  {
    free(cells);
    free(key);
    return MexArgEnd(&ma);
  }

  obj->key = key;
  obj->width = width;
  obj->height = height;
  obj->cells = cells;
  obj->next = g_regions;
  g_regions = obj;

  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief ui_region_put(key, left, top) - Restore a named block at a destination.
 *
 * @return MEX status; result in regs_2[0] (0 success, -1 not found).
 */
word EXPENTRY intrin_ui_region_put(void)
{
  MA ma;
  char *key;
  int left, top;
  mex_region_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  left = (int)MexArgGetWord(&ma);
  top = (int)MexArgGetWord(&ma);

  regs_2[0] = (word)-1;

  obj = mex_find_region(key);
  if (key)
    free(key);

  if (!obj || !obj->cells)
    return MexArgEnd(&ma);

  mex_restore_live_rect(left, top, obj->width, obj->height, obj->cells);

  if (mex_ui_should_flush())
    vbuf_flush();

  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief ui_region_drop(key) - Free a named block without restoring it.
 *
 * @return MEX status; result in regs_2[0] (0 success, -1 not found).
 */
word EXPENTRY intrin_ui_region_drop(void)
{
  MA ma;
  char *key;
  mex_region_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);

  regs_2[0] = (word)-1;
  obj = mex_find_region(key);
  if (key)
    free(key);

  if (!obj)
    return MexArgEnd(&ma);

  mex_region_remove(obj);
  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief ui_region_width(key) - Return a named block's width.
 */
word EXPENTRY intrin_ui_region_width(void)
{
  MA ma;
  char *key;
  mex_region_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  regs_2[0] = 0;

  obj = mex_find_region(key);
  if (key)
    free(key);

  if (obj)
    regs_2[0] = (word)obj->width;

  return MexArgEnd(&ma);
}

/**
 * @brief ui_region_height(key) - Return a named block's height.
 */
word EXPENTRY intrin_ui_region_height(void)
{
  MA ma;
  char *key;
  mex_region_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  regs_2[0] = 0;

  obj = mex_find_region(key);
  if (key)
    free(key);

  if (obj)
    regs_2[0] = (word)obj->height;

  return MexArgEnd(&ma);
}

/**
 * @brief ui_paint_region(left, top, right, bottom) - Finalize a bounded paint update.
 *
 * Current backend paints directly to the live video buffer, so this helper is
 * primarily a semantic boundary and flush point.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_paint_region(void)
{
  MA ma;

  MexArgBegin(&ma);
  (void)MexArgGetWord(&ma);
  (void)MexArgGetWord(&ma);
  (void)MexArgGetWord(&ma);
  (void)MexArgGetWord(&ma);

  if (mex_ui_should_flush())
    vbuf_flush();

  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief ui_save_screen(key) - Save the full visible screen plus cursor/attr state.
 *
 * @return MEX status; result in regs_2[0] (0 success, -1 error).
 */
word EXPENTRY intrin_ui_save_screen(void)
{
  MA ma;
  char *key;
  mex_screen_obj_t *obj;
  int width, height;
  word *cells = NULL;
  int col, row;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  regs_2[0] = (word)-1;

  if (!key || !*key)
  {
    if (key)
      free(key);
    return MexArgEnd(&ma);
  }

  if (mex_find_screen(key))
  {
    free(key);
    return MexArgEnd(&ma);
  }

  if (mex_capture_live_rect(1, 1, VidNumCols(), VidNumRows(), &width, &height, &cells) != 0)
  {
    free(key);
    return MexArgEnd(&ma);
  }

  obj = (mex_screen_obj_t *)calloc(1, sizeof(*obj));
  if (!obj)
  {
    free(cells);
    free(key);
    return MexArgEnd(&ma);
  }

  VidGetXY(&col, &row);

  obj->key = key;
  obj->width = width;
  obj->height = height;
  obj->cursor_row = row;
  obj->cursor_col = col;
  obj->attr = (byte)VidGetAttr();
  obj->cells = cells;
  obj->next = g_screens;
  g_screens = obj;

  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief ui_restore_screen(key) - Restore a previously saved full screen.
 *
 * @return MEX status; result in regs_2[0] (0 success, -1 not found).
 */
word EXPENTRY intrin_ui_restore_screen(void)
{
  MA ma;
  char *key;
  mex_screen_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  regs_2[0] = (word)-1;

  obj = mex_find_screen(key);
  if (key)
    free(key);

  if (!obj || !obj->cells)
    return MexArgEnd(&ma);

  mex_restore_live_rect(1, 1, obj->width, obj->height, obj->cells);
  VidSetAttr((char)obj->attr);
  VidGotoXY(obj->cursor_col, obj->cursor_row, FALSE);

  if (mex_ui_should_flush())
    vbuf_flush();

  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief ui_drop_screen(key) - Free a full-screen snapshot without restoring it.
 *
 * @return MEX status; result in regs_2[0] (0 success, -1 not found).
 */
word EXPENTRY intrin_ui_drop_screen(void)
{
  MA ma;
  char *key;
  mex_screen_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);

  regs_2[0] = (word)-1;
  obj = mex_find_screen(key);
  if (key)
    free(key);

  if (!obj)
    return MexArgEnd(&ma);

  mex_screen_remove(obj);
  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief ui_window_push(...) - Save-under and draw a boxed window.
 *
 * @return MEX status; result in regs_2[0] (0 success, -1 error).
 */
word EXPENTRY intrin_ui_window_push(void)
{
  MA ma;
  char *key;
  int left, top, right, bottom;
  byte fill_attr, border_attr;
  char *title;
  mex_overlay_obj_t *obj;
  int width, height;
  word *cells = NULL;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  left = (int)MexArgGetWord(&ma);
  top = (int)MexArgGetWord(&ma);
  right = (int)MexArgGetWord(&ma);
  bottom = (int)MexArgGetWord(&ma);
  fill_attr = (byte)MexArgGetWord(&ma);
  border_attr = (byte)MexArgGetWord(&ma);
  title = MexArgGetString(&ma, FALSE);

  regs_2[0] = (word)-1;

  if (!key || !*key)
  {
    if (key)
      free(key);
    if (title)
      free(title);
    return MexArgEnd(&ma);
  }

  if (mex_find_overlay(key))
  {
    free(key);
    if (title)
      free(title);
    return MexArgEnd(&ma);
  }

  if (mex_capture_live_rect(left, top, right, bottom, &width, &height, &cells) != 0)
  {
    free(key);
    if (title)
      free(title);
    return MexArgEnd(&ma);
  }

  obj = (mex_overlay_obj_t *)calloc(1, sizeof(*obj));
  if (!obj)
  {
    free(cells);
    free(key);
    if (title)
      free(title);
    return MexArgEnd(&ma);
  }

  obj->key = key;
  obj->row = top;
  obj->col = left;
  obj->width = width;
  obj->height = height;
  obj->cells = cells;
  obj->next = g_overlays;
  g_overlays = obj;

  ui_fill_rect(top, left, width, height, ' ', fill_attr);
  mex_draw_box(top, left, width, height, border_attr, title);

  if (title)
    free(title);

  if (mex_ui_should_flush())
    vbuf_flush();

  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief ui_window_pop(key) - Restore and free a previously pushed window.
 *
 * @return MEX status; result in regs_2[0] (0 success, -1 not found).
 */
word EXPENTRY intrin_ui_window_pop(void)
{
  return intrin_ui_overlay_pop();
}

/**
 * @brief ui_window_drop(key) - Free a previously pushed window without restoring it.
 *
 * @return MEX status; result in regs_2[0] (0 success, -1 not found).
 */
word EXPENTRY intrin_ui_window_drop(void)
{
  return intrin_ui_overlay_drop();
}

/**
 * @brief MEX intrinsic: ui_lightbar_pos() — Run a positioned lightbar menu.
 *
 * Each item has independent x/y/width coordinates. Returns 1-based selection
 * index or -1 on cancel. The selected hotkey is stored in style->out_hotkey.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_lightbar_pos(void)
{
  MA ma;
  struct mex_ui_lightbar_item *items_ref;
  struct mex_ui_lightbar_style *style;
  int count;
  ui_lightbar_item_t *items = NULL;
  char **text_array = NULL;
  ui_lightbar_pos_menu_t menu;
  int i;
  int result;
  int out_key = 0;

  MexArgBegin(&ma);
  items_ref = (struct mex_ui_lightbar_item *)MexArgGetRef(&ma);
  count = (int)MexArgGetWord(&ma);
  style = (struct mex_ui_lightbar_style *)MexArgGetRef(&ma);

  if (!items_ref || count < 1 || !style)
  {
    regs_2[0] = (word)-1;
    return MexArgEnd(&ma);
  }

  items = (ui_lightbar_item_t *)calloc((size_t)count, sizeof(ui_lightbar_item_t));
  text_array = (char **)calloc((size_t)count, sizeof(char *));
  if (!items || !text_array)
  {
    free(items);
    free(text_array);
    regs_2[0] = (word)-1;
    return MexArgEnd(&ma);
  }

  for (i = 0; i < count; i++)
  {
    text_array[i] = MexDupVMString(&items_ref[i].text);
    if (!text_array[i])
      text_array[i] = MexDupEmptyString();

    items[i].text = text_array[i];
    items[i].x = (int)items_ref[i].x;
    items[i].y = (int)items_ref[i].y;
    items[i].width = (int)items_ref[i].width;
    items[i].justify = (int)items_ref[i].justify;
  }

  menu.items = (const ui_lightbar_item_t *)items;
  menu.count = count;
  menu.normal_attr = style->normal_attr;
  menu.selected_attr = style->selected_attr;
  menu.hotkey_attr = style->hotkey_attr;
  menu.hotkey_highlight_attr = style->hotkey_highlight_attr;
  menu.margin = (int)style->margin;
  menu.wrap = style->wrap;
  menu.enable_hotkeys = style->enable_hotkeys;
  menu.show_brackets = style->show_brackets;

  result = ui_lightbar_run_pos_hotkey(&menu, &out_key);

  for (i = 0; i < count; i++)
    if (text_array[i])
      free(text_array[i]);
  free(text_array);
  free(items);

  if (result >= 0)
  {
    style->out_hotkey = (word)out_key;
    regs_2[0] = (word)(result + 1);
  }
  else
  {
    style->out_hotkey = 0;
    regs_2[0] = (word)-1;
  }

  if (mex_ui_should_flush())
    vbuf_flush();

  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_select_prompt_hotkey() — Inline select prompt with hotkey output.
 *
 * Legacy wrapper that takes individual attribute parameters instead of a style
 * struct. Returns 1-based selection index or -1 on cancel.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_select_prompt_hotkey(void)
{
  MA ma;
  char *prompt;
  IADDR *options_ref;
  int count, flags;
  byte prompt_attr, normal_attr, selected_attr;
  word *hotkey_ref;
  char **options_array = NULL;
  int i;
  int result;
  int out_key = 0;

   MexArgBegin(&ma);
   prompt = MexArgGetString(&ma, FALSE);
   options_ref = (IADDR *)MexArgGetRef(&ma);
   count = (int)MexArgGetWord(&ma);
   prompt_attr = (byte)MexArgGetWord(&ma);
   normal_attr = (byte)MexArgGetWord(&ma);
   selected_attr = (byte)MexArgGetWord(&ma);
   flags = (int)MexArgGetWord(&ma);
   hotkey_ref = (word *)MexArgGetRef(&ma);

   if (hotkey_ref)
     *hotkey_ref = 0;

   if (!options_ref || count < 1)
   {
     if (prompt)
       free(prompt);
     regs_2[0] = (word)-1;
     return MexArgEnd(&ma);
   }

   options_array = (char **)malloc((size_t)count * sizeof(char *));
   if (!options_array)
   {
     if (prompt)
       free(prompt);
     regs_2[0] = (word)-1;
     return MexArgEnd(&ma);
   }

   for (i = 0; i < count; i++)
   {
     options_array[i] = MexDupVMString(&options_ref[i]);
     if (!options_array[i])
       options_array[i] = MexDupEmptyString();
   }

   result = ui_select_prompt(
     prompt ? prompt : "",
     (const char **)options_array,
     count,
     prompt_attr,
     normal_attr,
     selected_attr,
     flags,
     0,
     "",
     NULL, /* last_separator */
     &out_key
   );

   if (prompt)
     free(prompt);

   for (i = 0; i < count; i++)
     if (options_array[i])
       free(options_array[i]);
   free(options_array);

   if (result >= 0)
   {
     if (hotkey_ref)
       *hotkey_ref = (word)out_key;
     regs_2[0] = (word)(result + 1);
   }
   else
   {
     if (hotkey_ref)
       *hotkey_ref = 0;
     regs_2[0] = (word)-1;
   }

   if (mex_ui_should_flush())
     vbuf_flush();

   return MexArgEnd(&ma);
 }

/**
 * @brief MEX intrinsic: ui_lightbar_hotkey() — Vertical lightbar with hotkey output.
 *
 * Legacy wrapper using individual attribute parameters. Returns 1-based
 * selection index or -1 on cancel. The pressed hotkey is returned via ref.
 *
 * @return MEX status.
 */
 word EXPENTRY intrin_ui_lightbar_hotkey(void)
 {
   MA ma;
   IADDR *items_ref;
   word *hotkey_ref;
   int count, x, y, width, justify, wrap, enable_hotkeys;
   byte normal_attr, selected_attr;
   char **items_array = NULL;
   int i;
   int result;
   int out_key = 0;
   ui_lightbar_menu_t menu;

   MexArgBegin(&ma);
   items_ref = (IADDR *)MexArgGetRef(&ma);
   count = (int)MexArgGetWord(&ma);
   x = (int)MexArgGetWord(&ma);
   y = (int)MexArgGetWord(&ma);
   width = (int)MexArgGetWord(&ma);
   justify = (int)MexArgGetWord(&ma);
   normal_attr = (byte)MexArgGetWord(&ma);
   selected_attr = (byte)MexArgGetWord(&ma);
   wrap = (int)MexArgGetWord(&ma);
   enable_hotkeys = (int)MexArgGetWord(&ma);
   hotkey_ref = (word *)MexArgGetRef(&ma);

   if (hotkey_ref)
     *hotkey_ref = 0;

   if (!items_ref || count < 1)
   {
     regs_2[0] = (word)-1;
     return MexArgEnd(&ma);
   }

   items_array = (char **)malloc((size_t)count * sizeof(char *));
   if (!items_array)
   {
     regs_2[0] = (word)-1;
     return MexArgEnd(&ma);
   }

   for (i = 0; i < count; i++)
   {
     items_array[i] = MexDupVMString(&items_ref[i]);
     if (!items_array[i])
       items_array[i] = MexDupEmptyString();
   }

   menu.items = (const char **)items_array;
   menu.count = count;
   menu.x = x;
   menu.y = y;
   menu.width = width;
   menu.margin = 0;
   menu.justify = justify;
   menu.normal_attr = normal_attr;
   menu.selected_attr = selected_attr;
   menu.hotkey_attr = 0;
   menu.hotkey_highlight_attr = 0;
   menu.wrap = wrap;
   menu.enable_hotkeys = enable_hotkeys;
   menu.show_brackets = 1;

   result = ui_lightbar_run_hotkey(&menu, &out_key);

   for (i = 0; i < count; i++)
     if (items_array[i])
       free(items_array[i]);
   free(items_array);

   if (result >= 0)
   {
     if (hotkey_ref)
       *hotkey_ref = (word)out_key;
     regs_2[0] = (word)(result + 1);
   }
   else
   {
     if (hotkey_ref)
       *hotkey_ref = 0;
     regs_2[0] = (word)-1;
   }

   if (mex_ui_should_flush())
     vbuf_flush();

   return MexArgEnd(&ma);
 }

/**
 * @brief MEX intrinsic: ui_set_attr(attr) — Set the current display attribute byte.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_set_attr(void)
{
  MA ma;
  byte attr;
  
  MexArgBegin(&ma);
  attr = (byte)MexArgGetWord(&ma);
  
  ui_set_attr(attr);
  
  if (mex_ui_should_flush())
    vbuf_flush();
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_make_attr(fg, bg) — Compose a DOS attribute byte.
 *
 * Combines a 4-bit foreground and 4-bit background into a single attribute.
 *
 * @return MEX status; result in regs_2[0].
 */
word EXPENTRY intrin_ui_make_attr(void)
{
  MA ma;
  byte fg;
  byte bg;

  MexArgBegin(&ma);
  fg = (byte)MexArgGetWord(&ma);
  bg = (byte)MexArgGetWord(&ma);

  regs_2[0] = (word)((fg & 0x0f) | ((bg & 0x0f) << 4));
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_box(row, col, width, height, attr, title) — Draw a double-line border box.
 *
 * The interior is left untouched; callers can fill it separately if needed.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_box(void)
{
  MA ma;
  int row, col, width, height;
  byte attr;
  char *title;
  MexArgBegin(&ma);
  row = (int)MexArgGetWord(&ma);
  col = (int)MexArgGetWord(&ma);
  width = (int)MexArgGetWord(&ma);
  height = (int)MexArgGetWord(&ma);
  attr = (byte)MexArgGetWord(&ma);
  title = MexArgGetString(&ma, FALSE);

  mex_draw_box(row, col, width, height, attr, title);

  if (title)
    free(title);

  if (mex_ui_should_flush())
    vbuf_flush();

  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: mci2attr(string mci_str) -> int attr
 *
 * Converts an MCI pipe color string (e.g. "|15", "|15|17", "|pr") to a
 * single DOS attribute byte.  Starts from default attribute 0x07.
 */
word EXPENTRY intrin_mci2attr(void)
{
  MA ma;
  IADDR ia;
  word wLen;
  char *mci_str;

  MexArgBegin(&ma);
  mci_str = MexArgGetNonRefString(&ma, &ia, &wLen);

  regs_2[0] = (word)Mci2Attr(mci_str, 0x07);
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_fill_rect(row, col, width, height, ch, attr) — Fill a screen rectangle.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_fill_rect(void)
{
  MA ma;
  int row, col, width, height;
  char ch;
  byte attr;
  
  MexArgBegin(&ma);
  row = (int)MexArgGetWord(&ma);
  col = (int)MexArgGetWord(&ma);
  width = (int)MexArgGetWord(&ma);
  height = (int)MexArgGetWord(&ma);
  ch = (char)MexArgGetByte(&ma);
  attr = (byte)MexArgGetWord(&ma);
  
  ui_fill_rect(row, col, width, height, ch, attr);
  
  if (mex_ui_should_flush())
    vbuf_flush();
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_write_padded(row, col, width, s, attr) — Write a string padded to width.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_write_padded(void)
{
  MA ma;
  int row, col, width;
  byte attr;
  char *s;
  
  MexArgBegin(&ma);
  row = (int)MexArgGetWord(&ma);
  col = (int)MexArgGetWord(&ma);
  width = (int)MexArgGetWord(&ma);
  s = MexArgGetString(&ma, FALSE);
  attr = (byte)MexArgGetWord(&ma);
  
  if (s)
  {
    ui_write_padded(row, col, width, s, attr);
    free(s);
  }
  
  if (mex_ui_should_flush())
    vbuf_flush();
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_prompt_field() — Inline prompt followed by an editable field.
 *
 * Displays a prompt string then an editable input field. Returns the edited
 * string and a result code (UI_EDIT_OK, UI_EDIT_CANCEL, etc.) in regs_2[0].
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_prompt_field(void)
{
  MA ma;
  int width, max_len;
  char *prompt;
  char *buf;
  char *format_mask_str = NULL;
  char local_buf[PATHLEN];
  int result;
  struct mex_ui_prompt_field_style *mex_style;
  ui_prompt_field_style_t style;
  
  MexArgBegin(&ma);
  prompt = MexArgGetString(&ma, FALSE);
  width = (int)MexArgGetWord(&ma);
  max_len = (int)MexArgGetWord(&ma);
  
  /* Get initial buffer content */
  if ((buf = MexArgGetString(&ma, FALSE)) != NULL)
  {
    strncpy(local_buf, buf, PATHLEN - 1);
    local_buf[PATHLEN - 1] = '\0';
    free(buf);
  }
  else
  {
    local_buf[0] = '\0';
  }
  
  /* Get style struct reference */
  mex_style = (struct mex_ui_prompt_field_style *)MexArgGetRef(&ma);
  
  if (!mex_style)
  {
    if (prompt)
      free(prompt);
    regs_2[0] = (word)UI_EDIT_ERROR;
    return MexArgEnd(&ma);
  }
  
  /* Convert MEX style to C style */
  style.prompt_attr = (byte)mex_style->prompt_attr;
  style.field_attr = (byte)mex_style->field_attr;
  style.fill_ch = mex_style->fill_ch ? mex_style->fill_ch : ' ';
  style.flags = (int)mex_style->flags;
  style.start_mode = (int)mex_style->start_mode;
  
  /* Get format_mask string if present */
  format_mask_str = MexDupVMString(&mex_style->format_mask);
  style.format_mask = format_mask_str;
  
  /* Call the prompt field */
  if (prompt)
  {
    result = ui_prompt_field(prompt, width, max_len, local_buf, PATHLEN, &style);
    free(prompt);
  }
  else
  {
    result = UI_EDIT_ERROR;
  }
  
  if (format_mask_str)
    free(format_mask_str);
  
  /* Return the edited string */
  MexReturnString(local_buf);
  
  /* Return result code in regs_2[0] */
  regs_2[0] = (word)result;
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_edit_field() — In-place editable field at row/col.
 *
 * Renders an editable field at the given screen position. Returns the edited
 * string and a result code in regs_2[0].
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_edit_field(void)
{
  MA ma;
  int row, col, width, max_len;
  char *buf;
  char *format_mask_str = NULL;
  char local_buf[PATHLEN];
  int result;
  struct mex_ui_edit_field_style *mex_style;
  ui_edit_field_style_t style;
  
  MexArgBegin(&ma);
  row = (int)MexArgGetWord(&ma);
  col = (int)MexArgGetWord(&ma);
  width = (int)MexArgGetWord(&ma);
  max_len = (int)MexArgGetWord(&ma);
  
  /* Get initial buffer content */
  if ((buf = MexArgGetString(&ma, FALSE)) != NULL)
  {
    strncpy(local_buf, buf, PATHLEN - 1);
    local_buf[PATHLEN - 1] = '\0';
    free(buf);
  }
  else
  {
    local_buf[0] = '\0';
  }
  
  /* Get style struct reference */
  mex_style = (struct mex_ui_edit_field_style *)MexArgGetRef(&ma);
  
  if (!mex_style)
  {
    regs_2[0] = (word)UI_EDIT_ERROR;
    return MexArgEnd(&ma);
  }
  
  /* Convert MEX style to C style */
  style.normal_attr = (byte)mex_style->normal_attr;
  style.focus_attr = (byte)mex_style->focus_attr;
  style.fill_ch = mex_style->fill_ch ? mex_style->fill_ch : ' ';
  style.flags = (int)mex_style->flags;
  
  /* Get format_mask string if present */
  format_mask_str = MexDupVMString(&mex_style->format_mask);
  style.format_mask = format_mask_str;
  
  /* Call the editor */
  result = ui_edit_field(row, col, width, max_len, local_buf, PATHLEN, &style);
  
  if (format_mask_str)
    free(format_mask_str);
  
  /* Return the edited string */
  MexReturnString(local_buf);
  
  /* Return result code in regs_2[0] */
  regs_2[0] = (word)result;
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_edit_field_style_default(ref style) — Fill style with theme defaults.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_edit_field_style_default(void)
{
  MA ma;
  struct mex_ui_edit_field_style *style;
  
  MexArgBegin(&ma);
  style = (struct mex_ui_edit_field_style *)MexArgGetRef(&ma);
  
  if (style)
  {
    style->normal_attr = Mci2Attr("|tf|tb", 0x07);  /* theme textbox fg+bg */
    style->focus_attr = Mci2Attr("|tf|tb", 0x07);    /* theme textbox fg+bg (focused) */
    style->fill_ch = ' ';
    style->flags = 0;
    memset(&style->format_mask, 0, sizeof(style->format_mask));
  }
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_prompt_field_style_default(ref style) — Fill style with theme defaults.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_prompt_field_style_default(void)
{
  MA ma;
  struct mex_ui_prompt_field_style *style;
  
  MexArgBegin(&ma);
  style = (struct mex_ui_prompt_field_style *)MexArgGetRef(&ma);
  
  if (style)
  {
    style->prompt_attr = Mci2Attr("|pr", 0x07);    /* theme prompt */
    style->field_attr = Mci2Attr("|tf|tb", 0x07);   /* theme textbox fg+bg */
    style->fill_ch = ' ';
    style->flags = 0;
    style->start_mode = 0;      /* UI_PROMPT_START_HERE */
    memset(&style->format_mask, 0, sizeof(style->format_mask));
  }
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_lightbar() — Vertical lightbar menu with style struct.
 *
 * Presents a vertical list of items as a lightbar menu. Returns 1-based index
 * of the selected item or -1 on cancel. Hotkey stored in style->out_hotkey.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_lightbar(void)
{
  MA ma;
  IADDR *items_ref;
  struct mex_ui_lightbar_style *style;
  int count, x, y, width;
  char **items_array = NULL;
  int i;
  int result;
  int out_key = 0;
  ui_lightbar_menu_t menu;
  
  MexArgBegin(&ma);
  items_ref = (IADDR *)MexArgGetRef(&ma);
  count = (int)MexArgGetWord(&ma);
  x = (int)MexArgGetWord(&ma);
  y = (int)MexArgGetWord(&ma);
  width = (int)MexArgGetWord(&ma);
  style = (struct mex_ui_lightbar_style *)MexArgGetRef(&ma);
  
  if (!items_ref || count < 1 || !style)
  {
    regs_2[0] = (word)-1;
    return MexArgEnd(&ma);
  }
  
  items_array = (char **)malloc((size_t)count * sizeof(char *));
  if (!items_array)
  {
    regs_2[0] = (word)-1;
    return MexArgEnd(&ma);
  }
  
  for (i = 0; i < count; i++)
  {
    items_array[i] = MexDupVMString(&items_ref[i]);
    if (!items_array[i])
      items_array[i] = MexDupEmptyString();
  }
  
  menu.items = (const char **)items_array;
  menu.count = count;
  menu.x = x;
  menu.y = y;
  menu.width = width;
  menu.justify = style->justify;
  menu.normal_attr = style->normal_attr;
  menu.selected_attr = style->selected_attr;
  menu.hotkey_attr = style->hotkey_attr;
  menu.hotkey_highlight_attr = style->hotkey_highlight_attr;
  menu.margin = (int)style->margin;
  menu.wrap = style->wrap;
  menu.enable_hotkeys = style->enable_hotkeys;
  menu.show_brackets = style->show_brackets;
  
  result = ui_lightbar_run_hotkey(&menu, &out_key);

  for (i = 0; i < count; i++)
    if (items_array[i])
      free(items_array[i]);
  free(items_array);
  
  if (result >= 0)
  {
    style->out_hotkey = (word)out_key;
    regs_2[0] = (word)(result + 1);
  }
  else
  {
    style->out_hotkey = 0;
    regs_2[0] = (word)-1;
  }
  
  if (mex_ui_should_flush())
    vbuf_flush();
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_select_prompt() — Inline horizontal select prompt with style struct.
 *
 * Displays a prompt followed by bracketed options the user can arrow through.
 * Returns 1-based index of the selected option or -1 on cancel.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_select_prompt(void)
{
  MA ma;
  char *prompt;
  IADDR *options_ref;
  int count;
  struct mex_ui_select_prompt_style *style;
  char **options_array = NULL;
  char *separator_str = NULL;
  int i;
  int result;
  int out_key = 0;
  int flags = 0;
  
  MexArgBegin(&ma);
  prompt = MexArgGetString(&ma, FALSE);
  options_ref = (IADDR *)MexArgGetRef(&ma);
  count = (int)MexArgGetWord(&ma);
  style = (struct mex_ui_select_prompt_style *)MexArgGetRef(&ma);
  
  if (!options_ref || count < 1 || !style)
  {
    if (prompt)
      free(prompt);
    regs_2[0] = (word)-1;
    return MexArgEnd(&ma);
  }
  
  options_array = (char **)malloc((size_t)count * sizeof(char *));
  if (!options_array)
  {
    if (prompt)
      free(prompt);
    regs_2[0] = (word)-1;
    return MexArgEnd(&ma);
  }
  
  for (i = 0; i < count; i++)
  {
    options_array[i] = MexDupVMString(&options_ref[i]);
    if (!options_array[i])
      options_array[i] = MexDupEmptyString();
  }

  if (style->show_brackets == 0)
    flags |= UI_SP_FLAG_STRIP_BRACKETS;

  if (style->hotkey_attr)
    flags |= ((int)(style->hotkey_attr & 0xff) << UI_SP_HOTKEY_ATTR_SHIFT);

  if (style->default_index)
    flags |= ((int)(style->default_index & 0xff) << UI_SP_DEFAULT_SHIFT);

  separator_str = MexDupVMString(&style->separator);
  if (!separator_str)
    separator_str = MexDupEmptyString();
  
  result = ui_select_prompt(
    prompt ? prompt : "",
    (const char **)options_array,
    count,
    (byte)style->prompt_attr,
    (byte)style->normal_attr,
    (byte)style->selected_attr,
    flags,
    (int)style->margin,
    separator_str,
    NULL, /* last_separator */
    &out_key
  );
  
  if (prompt)
    free(prompt);

  for (i = 0; i < count; i++)
    if (options_array[i])
      free(options_array[i]);
  free(options_array);

  if (separator_str)
    free(separator_str);

  if (result >= 0)
  {
    style->out_hotkey = (word)out_key;
    regs_2[0] = (word)(result + 1);
  }
  else
  {
    style->out_hotkey = 0;
    regs_2[0] = (word)-1;
  }
  
  if (mex_ui_should_flush())
    vbuf_flush();
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_lightbar_style_default(ref style) — Fill lightbar style with theme defaults.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_lightbar_style_default(void)
{
  MA ma;
  struct mex_ui_lightbar_style *style;
  
  MexArgBegin(&ma);
  style = (struct mex_ui_lightbar_style *)MexArgGetRef(&ma);
  
  if (style)
  {
    style->justify = 0;           /* UI_JUSTIFY_LEFT */
    style->wrap = 1;
    style->enable_hotkeys = 1;
    style->show_brackets = 1;     /* UI_BRACKET_SQUARE */
    style->normal_attr = Mci2Attr("|tx", 0x07);    /* theme text */
    style->selected_attr = Mci2Attr("|lf|lb", 0x07); /* theme lightbar fg+bg */
    style->hotkey_attr = Mci2Attr("|hk", 0x07);      /* theme hotkey */
    style->hotkey_highlight_attr = 0;
    style->margin = 0;
    style->out_hotkey = 0;
  }
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_select_prompt_style_default(ref style) — Fill select prompt style with theme defaults.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_select_prompt_style_default(void)
{
  MA ma;
  struct mex_ui_select_prompt_style *style;
  
  MexArgBegin(&ma);
  style = (struct mex_ui_select_prompt_style *)MexArgGetRef(&ma);
  
  if (style)
  {
    style->prompt_attr = Mci2Attr("|pr", 0x07);    /* theme prompt */
    style->normal_attr = Mci2Attr("|tx", 0x07);     /* theme text */
    style->selected_attr = Mci2Attr("|lf|lb", 0x07); /* theme lightbar fg+bg */
    style->hotkey_attr = Mci2Attr("|hk", 0x07);      /* theme hotkey */
    style->show_brackets = 1;     /* UI_BRACKET_SQUARE */
    style->margin = 0;
    memset(&style->separator, 0, sizeof(style->separator));
    style->default_index = 0;     /* 0 = first option */
    style->out_hotkey = 0;
  }
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_form_style_default(ref style) — Fill form style with theme defaults.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_form_style_default(void)
{
  MA ma;
  struct mex_ui_form_style *style;
  
  MexArgBegin(&ma);
  
  style = (struct mex_ui_form_style *)MexArgGetRef(&ma);
  
  if (style)
  {
    style->label_attr = Mci2Attr("|pr", 0x07);     /* theme prompt for labels */
    style->normal_attr = Mci2Attr("|tf|tb", 0x07);  /* theme textbox fg+bg */
    style->focus_attr = Mci2Attr("|hi|tb", 0x07);   /* theme highlight fg + textbox bg */
    style->save_mode = 0;          /* UI_FORM_SAVE_CTRL_S */
    style->wrap = 1;
    style->edit_mode = 0;          /* UI_FORM_EDIT_ENTER */
    memset(&style->required_msg, 0, sizeof(style->required_msg));
    style->required_x = 1;
    style->required_y = 24;
    style->required_attr = Mci2Attr("|er", 0x07);  /* theme error */
  }
  
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_form_run() — Run a multi-field form editor.
 *
 * Accepts an array of form field descriptors and a style struct, runs the
 * interactive form, and copies edited values back to the MEX field structs
 * on save (rc == 1).
 *
 * @return MEX status; result code in regs_2[0] (1 = saved, -1 = cancel/error).
 */
word EXPENTRY intrin_ui_form_run(void)
{
  MA ma;
  struct mex_ui_form_field *fields_ref;
  word field_count;
  struct mex_ui_form_style *mex_style;
  ui_form_field_t *fields = NULL;
  ui_form_style_t style;
  int i;
  int rc = -1;
  
  MexArgBegin(&ma);
  
  fields_ref = (struct mex_ui_form_field *)MexArgGetRef(&ma);
  field_count = MexArgGetWord(&ma);
  mex_style = (struct mex_ui_form_style *)MexArgGetRef(&ma);
  
  if (!fields_ref || field_count < 1 || !mex_style)
  {
    regs_2[0] = (word)-1;
    return MexArgEnd(&ma);
  }
  
  /* Allocate C field array */
  fields = (ui_form_field_t *)calloc((size_t)field_count, sizeof(ui_form_field_t));
  if (!fields)
  {
    regs_2[0] = (word)-1;
    return MexArgEnd(&ma);
  }
  
  /* Convert MEX fields to C fields */
  for (i = 0; i < (int)field_count; i++)
  {
    int j;
    char *value_str;

    fields[i].name = MexDupVMString(&fields_ref[i].name);
    fields[i].label = MexDupVMString(&fields_ref[i].label);
    fields[i].x = (int)fields_ref[i].x;
    fields[i].y = (int)fields_ref[i].y;
    fields[i].width = (int)fields_ref[i].width;
    fields[i].max_len = (int)fields_ref[i].max_len;
    fields[i].field_type = (int)fields_ref[i].field_type;
    fields[i].hotkey = (char)fields_ref[i].hotkey;
    fields[i].required = (int)fields_ref[i].required;
    fields[i].label_attr = (byte)fields_ref[i].label_attr;
    fields[i].normal_attr = (byte)fields_ref[i].normal_attr;
    fields[i].focus_attr = (byte)fields_ref[i].focus_attr;
    fields[i].format_mask = MexDupVMString(&fields_ref[i].format_mask);
    fields[i].option_count = (int)fields_ref[i].option_count;
    if (fields[i].option_count < 0)
      fields[i].option_count = 0;
    if (fields[i].option_count > 8)
      fields[i].option_count = 8;
    if (fields[i].option_count > 0)
    {
      fields[i].options = (const char **)calloc((size_t)fields[i].option_count + 1, sizeof(char *));
      if (fields[i].options)
      {
        for (j = 0; j < fields[i].option_count; j++)
        {
          ((char **)fields[i].options)[j] = MexDupVMString(&fields_ref[i].options[j]);
          if (!((char **)fields[i].options)[j])
            ((char **)fields[i].options)[j] = MexDupEmptyString();
        }
      }
      else
      {
        fields[i].option_count = 0;
      }
    }
    
    /* Allocate value buffer and copy initial value */
    value_str = MexDupVMString(&fields_ref[i].value);
    fields[i].value_cap = fields[i].max_len + 1;
    if (fields[i].value_cap < 256)
      fields[i].value_cap = 256;
    fields[i].value = (char *)calloc((size_t)fields[i].value_cap, 1);
    if (fields[i].value && value_str)
    {
      strncpy(fields[i].value, value_str, (size_t)(fields[i].value_cap - 1));
      fields[i].value[fields[i].value_cap - 1] = 0;
    }
    if (value_str)
      free(value_str);
  }
  
  /* Convert MEX style to C style */
  style.label_attr = (byte)mex_style->label_attr;
  style.normal_attr = (byte)mex_style->normal_attr;
  style.focus_attr = (byte)mex_style->focus_attr;
  style.save_mode = (int)mex_style->save_mode;
  style.wrap = (int)mex_style->wrap;
  style.edit_mode = (int)mex_style->edit_mode;
  style.required_msg = MexDupVMString(&mex_style->required_msg);
  style.required_x = (int)mex_style->required_x;
  style.required_y = (int)mex_style->required_y;
  style.required_attr = (byte)mex_style->required_attr;
  
  /* Run form */
  rc = ui_form_run(fields, (int)field_count, &style);
  
  /* Copy values back to MEX fields */
  if (rc == 1)
  {
    for (i = 0; i < (int)field_count; i++)
    {
      if (!fields[i].value)
        continue;

      MexKillStructString(mex_ui_form_field, &fields_ref[i], value);
      StoreString(MexPtrToVM(&fields_ref[i]), struct mex_ui_form_field, value, fields[i].value);
    }
  }
  
  /* Cleanup */
  if (style.required_msg)
    free((void *)style.required_msg);
  
  for (i = 0; i < (int)field_count; i++)
  {
    int j;
    if (fields[i].name)
      free((void *)fields[i].name);
    if (fields[i].label)
      free((void *)fields[i].label);
    if (fields[i].format_mask)
      free((void *)fields[i].format_mask);
    if (fields[i].options)
    {
      for (j = 0; j < fields[i].option_count; j++)
        if (((char **)fields[i].options)[j])
          free(((char **)fields[i].options)[j]);
      free((void *)fields[i].options);
    }
    if (fields[i].value)
      free(fields[i].value);
  }
  free(fields);
  
  regs_2[0] = (word)rc;
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_scroll_region_style_default(ref style) — Fill scroll region style with defaults.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_scroll_region_style_default(void)
{
  MA ma;
  struct mex_ui_scroll_region_style *mex_style;
  ui_scrolling_region_style_t style;

  MexArgBegin(&ma);
  mex_style = (struct mex_ui_scroll_region_style *)MexArgGetRef(&ma);

  ui_scrolling_region_style_default(&style);

  if (mex_style)
  {
    mex_style->attr = (word)style.attr;
    mex_style->scrollbar_attr = (word)style.scrollbar_attr;
    mex_style->flags = (word)style.flags;
  }

  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_scroll_region_create() — Create a named scrolling region.
 *
 * Allocates and initializes a scrolling region identified by a unique key.
 * Returns 0 on success, -1 on error, -2 if key already exists, -3 on alloc failure.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_scroll_region_create(void)
{
  MA ma;
  char *key;
  int x;
  int y;
  int width;
  int height;
  int max_lines;
  struct mex_ui_scroll_region_style *mex_style;
  ui_scrolling_region_style_t style;
  mex_scroll_region_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  x = (int)MexArgGetWord(&ma);
  y = (int)MexArgGetWord(&ma);
  width = (int)MexArgGetWord(&ma);
  height = (int)MexArgGetWord(&ma);
  max_lines = (int)MexArgGetWord(&ma);
  mex_style = (struct mex_ui_scroll_region_style *)MexArgGetRef(&ma);

  regs_2[0] = (word)-1;

  if (!key || !*key || !mex_style)
  {
    if (key)
      free(key);
    return MexArgEnd(&ma);
  }

  if (mex_find_scroll_region(key))
  {
    free(key);
    regs_2[0] = (word)-2;
    return MexArgEnd(&ma);
  }

  ui_scrolling_region_style_default(&style);
  style.attr = (byte)mex_style->attr;
  style.scrollbar_attr = (byte)mex_style->scrollbar_attr;
  style.flags = (int)mex_style->flags;

  obj = (mex_scroll_region_obj_t *)calloc(1, sizeof(*obj));
  if (!obj)
  {
    free(key);
    regs_2[0] = (word)-3;
    return MexArgEnd(&ma);
  }

  obj->key = key;
  ui_scrolling_region_init(&obj->r, x, y, width, height, max_lines, &style);
  obj->next = g_scroll_regions;
  g_scroll_regions = obj;

  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_scroll_region_destroy(key) — Destroy a named scrolling region.
 *
 * @return MEX status; 0 on success, -1 if not found.
 */
word EXPENTRY intrin_ui_scroll_region_destroy(void)
{
  MA ma;
  char *key;
  mex_scroll_region_obj_t *cur;
  mex_scroll_region_obj_t *prev;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);

  regs_2[0] = (word)-1;

  if (!key)
    return MexArgEnd(&ma);

  prev = NULL;
  for (cur = g_scroll_regions; cur; prev = cur, cur = cur->next)
    if (cur->key && strcmp(cur->key, key) == 0)
      break;

  free(key);

  if (!cur)
    return MexArgEnd(&ma);

  if (prev)
    prev->next = cur->next;
  else
    g_scroll_regions = cur->next;

  ui_scrolling_region_free(&cur->r);
  if (cur->key)
    free(cur->key);
  free(cur);

  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_scroll_region_append(key, text, flags) — Append text to a scrolling region.
 *
 * @return MEX status; 0 on success, -1 if region not found.
 */
word EXPENTRY intrin_ui_scroll_region_append(void)
{
  MA ma;
  char *key;
  char *text;
  int flags;
  mex_scroll_region_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  text = MexArgGetString(&ma, FALSE);
  flags = (int)MexArgGetWord(&ma);

  regs_2[0] = (word)-1;

  obj = mex_find_scroll_region(key);
  if (obj)
  {
    ui_scrolling_region_append(&obj->r, text ? text : "", flags);
    regs_2[0] = 0;
  }

  if (key)
    free(key);
  if (text)
    free(text);

  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_scroll_region_render(key) — Redraw a scrolling region to screen.
 *
 * @return MEX status; 0 on success, -1 if region not found.
 */
word EXPENTRY intrin_ui_scroll_region_render(void)
{
  MA ma;
  char *key;
  mex_scroll_region_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);

  regs_2[0] = (word)-1;

  obj = mex_find_scroll_region(key);
  if (obj)
  {
    ui_scrolling_region_render(&obj->r);
    if (mex_ui_should_flush())
      vbuf_flush();
    regs_2[0] = 0;
  }

  if (key)
    free(key);

  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_scroll_region_handle_key(key, keycode) — Pass a keypress to a scrolling region.
 *
 * @return MEX status; result in regs_2[0] (1 if handled, 0 if not).
 */
word EXPENTRY intrin_ui_scroll_region_handle_key(void)
{
  MA ma;
  char *key;
  int keycode;
  mex_scroll_region_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  keycode = (int)MexArgGetWord(&ma);

  regs_2[0] = 0;

  obj = mex_find_scroll_region(key);
  if (obj)
    regs_2[0] = (word)ui_scrolling_region_handle_key(&obj->r, keycode);

  if (key)
    free(key);

  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_text_viewer_style_default(ref style) — Fill text viewer style with defaults.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_text_viewer_style_default(void)
{
  MA ma;
  struct mex_ui_text_viewer_style *mex_style;
  ui_text_viewer_style_t style;

  MexArgBegin(&ma);
  mex_style = (struct mex_ui_text_viewer_style *)MexArgGetRef(&ma);

  ui_text_viewer_style_default(&style);

  if (mex_style)
  {
    mex_style->attr = (word)style.attr;
    mex_style->status_attr = (word)style.status_attr;
    mex_style->scrollbar_attr = (word)style.scrollbar_attr;
    mex_style->flags = (word)style.flags;
  }

  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_text_viewer_create() — Create a named text viewer widget.
 *
 * Allocates and initializes a text viewer identified by a unique key.
 * Returns 0 on success, -1 on error, -2 if key exists, -3 on alloc failure.
 *
 * @return MEX status.
 */
word EXPENTRY intrin_ui_text_viewer_create(void)
{
  MA ma;
  char *key;
  int x;
  int y;
  int width;
  int height;
  struct mex_ui_text_viewer_style *mex_style;
  ui_text_viewer_style_t style;
  mex_text_viewer_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  x = (int)MexArgGetWord(&ma);
  y = (int)MexArgGetWord(&ma);
  width = (int)MexArgGetWord(&ma);
  height = (int)MexArgGetWord(&ma);
  mex_style = (struct mex_ui_text_viewer_style *)MexArgGetRef(&ma);

  regs_2[0] = (word)-1;

  if (!key || !*key || !mex_style)
  {
    if (key)
      free(key);
    return MexArgEnd(&ma);
  }

  if (mex_find_text_viewer(key))
  {
    free(key);
    regs_2[0] = (word)-2;
    return MexArgEnd(&ma);
  }

  ui_text_viewer_style_default(&style);
  style.attr = (byte)mex_style->attr;
  style.status_attr = (byte)mex_style->status_attr;
  style.scrollbar_attr = (byte)mex_style->scrollbar_attr;
  style.flags = (int)mex_style->flags;

  obj = (mex_text_viewer_obj_t *)calloc(1, sizeof(*obj));
  if (!obj)
  {
    free(key);
    regs_2[0] = (word)-3;
    return MexArgEnd(&ma);
  }

  obj->key = key;
  ui_text_viewer_init(&obj->v, x, y, width, height, &style);
  obj->next = g_text_viewers;
  g_text_viewers = obj;

  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_text_viewer_destroy(key) — Destroy a named text viewer.
 *
 * @return MEX status; 0 on success, -1 if not found.
 */
word EXPENTRY intrin_ui_text_viewer_destroy(void)
{
  MA ma;
  char *key;
  mex_text_viewer_obj_t *cur;
  mex_text_viewer_obj_t *prev;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);

  regs_2[0] = (word)-1;

  if (!key)
    return MexArgEnd(&ma);

  prev = NULL;
  for (cur = g_text_viewers; cur; prev = cur, cur = cur->next)
    if (cur->key && strcmp(cur->key, key) == 0)
      break;

  free(key);

  if (!cur)
    return MexArgEnd(&ma);

  if (prev)
    prev->next = cur->next;
  else
    g_text_viewers = cur->next;

  ui_text_viewer_free(&cur->v);
  if (cur->key)
    free(cur->key);
  free(cur);

  regs_2[0] = 0;
  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_text_viewer_set_text(key, text) — Load text content into a viewer.
 *
 * @return MEX status; 0 on success, -1 if viewer not found.
 */
word EXPENTRY intrin_ui_text_viewer_set_text(void)
{
  MA ma;
  char *key;
  char *text;
  mex_text_viewer_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  text = MexArgGetString(&ma, FALSE);

  regs_2[0] = (word)-1;

  obj = mex_find_text_viewer(key);
  if (obj)
  {
    ui_text_viewer_set_text(&obj->v, text ? text : "");
    regs_2[0] = 0;
  }

  if (key)
    free(key);
  if (text)
    free(text);

  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_text_viewer_render(key) — Redraw a text viewer to screen.
 *
 * @return MEX status; 0 on success, -1 if viewer not found.
 */
word EXPENTRY intrin_ui_text_viewer_render(void)
{
  MA ma;
  char *key;
  mex_text_viewer_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);

  regs_2[0] = (word)-1;

  obj = mex_find_text_viewer(key);
  if (obj)
  {
    ui_text_viewer_render(&obj->v);
    if (mex_ui_should_flush())
      vbuf_flush();
    regs_2[0] = 0;
  }

  if (key)
    free(key);

  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_text_viewer_handle_key(key, keycode) — Pass a keypress to a text viewer.
 *
 * @return MEX status; result in regs_2[0] (1 if handled, 0 if not).
 */
word EXPENTRY intrin_ui_text_viewer_handle_key(void)
{
  MA ma;
  char *key;
  int keycode;
  mex_text_viewer_obj_t *obj;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);
  keycode = (int)MexArgGetWord(&ma);

  regs_2[0] = 0;

  obj = mex_find_text_viewer(key);
  if (obj)
    regs_2[0] = (word)ui_text_viewer_handle_key(&obj->v, keycode);

  if (key)
    free(key);

  return MexArgEnd(&ma);
}

/**
 * @brief MEX intrinsic: ui_text_viewer_read_key(key) — Read and process a key within a text viewer.
 *
 * Blocks until a key is pressed, processes scroll/navigation internally,
 * and returns the key code for unhandled keys.
 *
 * @return MEX status; key code in regs_2[0].
 */
word EXPENTRY intrin_ui_text_viewer_read_key(void)
{
  MA ma;
  char *key;
  mex_text_viewer_obj_t *obj;
  int k;

  MexArgBegin(&ma);
  key = MexArgGetString(&ma, FALSE);

  regs_2[0] = 0;

  obj = mex_find_text_viewer(key);
  if (obj)
  {
    k = ui_text_viewer_read_key(&obj->v);
    regs_2[0] = (word)k;
  }

  if (key)
    free(key);

  return MexArgEnd(&ma);
}

#endif /* MEX */

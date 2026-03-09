/*
 * Maximus Version 3.02
 * Copyright 1989, 2002 by Lanius Corporation.  All rights reserved.
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

#ifndef __GNUC__
#pragma off(unreferenced)
static char rcs_id[]="$Id: med_quot.c,v 1.4 2004/01/28 06:38:10 paltas Exp $";
#pragma on(unreferenced)
#endif

/*# name=MaxEd editor: Routines for quoting and copying (legacy stubs)
 *
 *  The old split-screen quoting UI has been replaced by the Mystic-style
 *  popup quote window in med_qpop.c.  These functions are retained as
 *  stubs so that any remaining call sites compile without error.
*/

#define MAX_LANG_global
#define MAX_LANG_m_area
#define MAX_LANG_max_bor
#include "maxed.h"
#include "m_reply.h"
#include "mci.h"


/**
 * @brief Legacy quote toggle — now delegates to the popup window.
 *
 * Opens the popup quote window, then repaints the editor on return.
 */
void Quote_OnOff(struct _replyp *pr)
{
  Quote_Popup(pr);
  Fix_MagnEt();
}


/* ── legacy stubs (no longer used) ───────────────────────────────────── */

void Quote_Up(void)
{
  /* Stub — popup handles its own scrolling */
}

void Quote_Down(void)
{
  /* Stub — popup handles its own scrolling */
}

void Quote_Copy(void)
{
  /* Stub — popup handles line insertion directly */
}

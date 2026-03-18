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
static char rcs_id[]="$Id: max_chng.c,v 1.4 2004/01/28 06:38:10 paltas Exp $";
#pragma on(unreferenced)
#endif

/*# name=Change Setup menu options
*/

#define MAX_LANG_global
#define MAX_LANG_m_area
#define MAX_LANG_max_bor
#define MAX_LANG_max_chng
#define MAX_LANG_max_init
#define MAX_LANG_sysop
#include <stdio.h>
#include <ctype.h>
#include <string.h>
#include <stdlib.h>
#include "libmaxcfg.h"
#include "prog.h"
#include "mm.h"
#include "arc_def.h"
#include "md5.h"
#include "ui_field.h"
#include "theme.h"

static int near Invalid_City(char *usr_city);
static int near Invalid_Name(char *usr_name);
static int near Invalid_Phone(char *usr_phone);

static const ui_prompt_field_style_t newuser_prompt_style = {
  .prompt_attr = (byte)-1,
  .field_attr  = 0x1f,
  .fill_ch     = ' ',
  .flags       = 0,
  .start_mode  = UI_PROMPT_START_HERE
};

static void near Chg_RIP(void)
{
  usr.bits ^= BITS_RIP;

  if (usr.bits & BITS_RIP)
  {
    usr.bits  |= (BITS_HOTKEYS|BITS_FSR);

    usr.bits2 |= BITS2_CLS;

    if (!autodetect_rip())
      logit(log_rip_enabled_ndt);
  }
  else
  {
    RipReset();
    Puts("\r!|*");
  }

  Set_Lang_Alternate(hasRIP());
}

static void near Chg_Hotkeys(void)
{
  if (usr.bits & BITS_RIP)      /* Hitkeys must be left on in this case */
    usr.bits |= BITS_HOTKEYS;
  else
    usr.bits ^= BITS_HOTKEYS;
}

static void near Chg_FSR(void)
{
  usr.bits ^= BITS_FSR;

  if (usr.bits & BITS_RIP)      /* FSR must be left on in this case */
  {
    if ((usr.bits & BITS_FSR)==0)
    {
      usr.bits |= BITS_FSR;

      Puts(chg_need_fsr);
      Press_ENTER();
    }
  }

  if (usr.bits & BITS_FSR)
  {
    if (usr.video==GRAPH_TTY)   /* FSR requires graphics */
      usr.bits &= ~BITS_FSR;
    else
      usr.bits2 |= BITS2_MORE;  /* Also requires more prompting */
  }
}

static void near Chg_Userlist(void)
{
  usr.bits ^= BITS_NOULIST;
}

static void near Chg_Protocol(void)
{
  sword protocol;

  Puts(chose_default_proto);
  usr.def_proto = (byte)((File_Get_Protocol(&protocol, TRUE, FALSE)==-1)
                     ? PROTOCOL_NONE : protocol);
}

static void near Chg_Ibm(void)
{
  usr.bits2 ^= BITS2_IBMCHARS;
}

static void near Chg_Clear(void)
{
  if (usr.bits & BITS_RIP)
    usr.bits2 += BITS2_CLS;
  else
    usr.bits2 ^= BITS2_CLS;
}

static void near Chg_More(void)
{
  usr.bits2 ^= BITS2_MORE;
  
  /* User can't have both FSR and More on at the same time. */

  if ((usr.bits2 & BITS2_MORE)==0 && (usr.bits & BITS_FSR))
    usr.bits &= ~BITS_FSR;
}

static void near Chg_Tabs(void)
{
  usr.bits ^= BITS_TABS;
}


static void near Chg_Password(void)
{
  char string[BUFLEN];        /* string entered by the user */
#ifdef CANENCRYPT
  byte abMd5[MD5_SIZE];       /* MD5 of string entered by user */
#endif
  int fMatch;                 /* TRUE if correct pwd entered */
  int tries;                  /* Number of invalid passwords entered */

  tries=0;

  logit(log_ch_pwd);

  WhiteN();

  for (;;)
  {
    if (tries != 0)
    {
      Clear_KBuffer();
      logit(log_inv_pwd);
      { char _tb[16]; snprintf(_tb, sizeof(_tb), "%d", tries);
        LangPrintf(wrong_pwd, _tb); }
      Putc('\n');

      if (tries==3)
      {
        logit(l_invalid_pwd);
        Puts(invalid_pwd);
        ci_ejectuser();
        mdm_hangup();
      }
    }

    *string='\0';

    while (! *string)
    {
      InputGetsLLe(string,BUFLEN,'.',current_pwd);

      if (tries==0 && ! *string)                /* Abort if first attempt */
        return;
    }

#ifdef CANENCRYPT
    if (usr.bits & BITS_ENCRYPT)
    {
      string_to_MD5(strlwr(string), abMd5);

      fMatch = (memcmp(abMd5, usr.pwd, MD5_SIZE)==0);
    }
    else
#endif
      fMatch = (stricmp(cfancy_str(string), usr.pwd)==0);

    if (fMatch)
    {
      Get_Pwd();
      *string='\0';
      break;
    }

    tries++;
  }
}



static void near Chg_Help(void)
{
  char *hk=help_keys;
  int ch;

  ch='\x00';

  while (ch != hk[0] && ch != hk[1] && ch != hk[2])
  {
    if (! *linebuf)
      Puts(help_menu);

    ch=toupper(KeyGetRNP(help_prompt));

    if (ch==hk[0]) /* novice */
      usr.help=NOVICE;
    else if (ch==hk[1])  /* regular */
      usr.help=REGULAR;
    else if (ch==hk[2])  /* expert */
      usr.help=EXPERT;
    else Clear_KBuffer();
  }
}


static void near Chg_Nulls(void)
{
  char string[BUFLEN];

  WhiteN();

  InputGets(string, num_nulls);

  if ((usr.nulls=(byte)atoi(string)) > 200)
    usr.nulls=0;
}


static void near Chg_Width(void)
{
  char string[BUFLEN];
  extern int loc_cols;

  WhiteN();

  for (;;)
  {
    InputGets(string, mon_width);

    usr.width=(byte)atoi(string);

    if (usr.width < 20 || usr.width > 132)
    {
      usr.width=80;
      Puts(bad_width);
      Clear_KBuffer();
    }
    else
    {
      if (! *linebuf)
        { char _tb[16]; snprintf(_tb, sizeof(_tb), "%02d", usr.width);
          LangPrintf(draw_line, _tb); }

      if (GetYnAnswer(check_x, 0)==YES)
      {
        if (local)
          loc_cols = usr.width;

        return;
      }
      else
      {
        Puts(incorrect_width);
        Clear_KBuffer();
      }
    }
  }
}


static void near Chg_Length(void)
{
  char string[BUFLEN];
  extern int loc_rows;
  byte x;

  if (hasRIP())
    Puts("\r!|*|#|#|#\n");  /* Kludge, but required */

  WhiteN();

  if (! *linebuf)
    for (x=CHANGE_SCREENLEN;x >= 2;x--)
      Printf("%d\n", x);

  x=usr.help;       /* Temporarily change help level, so HFLASH doesn't */
  usr.help=NOVICE;  /* screw us up! */

  InputGets(string, top_num);

  usr.help=x;

  if ((usr.len=(byte)atoi(string)) < 8)
    usr.len=8;
  else if (usr.len > 200)
    usr.len=200;

  if (local)
    loc_rows = usr.len;
}



static void near Chg_Graphics(void)
{
  int ch;
  int min_graphics;

  ch=0;

  min_graphics = ngcfg_get_int("general.session.min_graphics_baud");

  if (local || baud >= (dword)min_graphics)
  {
    char *vk=video_keys;

    while (ch != vk[0] && ch != vk[1] && ch != vk[2])
    {
      if (! *linebuf)
        Puts(video_menu);

      ch=toupper(KeyGetRNP(select_p));

      if (ch==vk[0])
        usr.video=GRAPH_TTY;
      else if (ch==vk[1])
        usr.video=GRAPH_ANSI;
      else if (ch==vk[2])
        usr.video=GRAPH_AVATAR;
      else Clear_KBuffer();
    }
  }
  else if ((unsigned int)min_graphics==38400u)
  {
    Puts(no_colour);
    Press_ENTER();
  }
  else
  {
    { char _tb[16]; snprintf(_tb, sizeof(_tb), "%d", min_graphics);
      LangPrintf(col_too_slow, _tb); }
    Press_ENTER();
  }
}



static void near Chg_Edit(void)
{
  if (usr.video==GRAPH_TTY && (usr.bits2 & BITS2_BORED))
  {
    Puts(req_graph);
    Press_ENTER();
  }
  else if (ngcfg_get_bool("general.session.disable_magnet") && (usr.bits2 & BITS2_BORED))
  {
    Puts(unavailable);
    Press_ENTER();
  }
  else usr.bits2 ^= BITS2_BORED;
}



void Chg_City(void)
{
  char temp[PATHLEN];
  unsigned tries = 0; /* Counts invalid city entry attempts */

  do
  {
    if (!local && tries++ >= 3)
    {
      ci_ejectuser();
      logit("!Too many invalid city entries -- disconnecting");
      Puts(too_many_attempts);
      mdm_hangup();
    }

    *linebuf='\0';
    temp[0]='\0';
    WhiteN();

    PromptInput("general.display.general.bounded_input_newuser",
                enter_city, temp, 35, 35, &newuser_prompt_style);
  }
  while (Invalid_City(temp));

  strcpy(usr.city, fancier_str(temp));
}

void Chg_Alias(void)
{
  char temp[PATHLEN];
  unsigned tries = 0; /* Counts invalid alias entry attempts */

  do
  {
    int l;

    if (!local && tries++ >= 3)
    {
      ci_ejectuser();
      logit("!Too many invalid alias entries -- disconnecting");
      Puts(too_many_attempts);
      mdm_hangup();
    }

    *linebuf='\0';
    temp[0]='\0';
    WhiteN();

    PromptInput("general.display.general.bounded_input_newuser",
                enter_name, temp, sizeof(usr.alias)-1, sizeof(usr.alias)-1,
                &newuser_prompt_style);

    /* Strip trailing blanks from the alias entered by the user */

    l = strlen(temp);

    while (l && temp[l-1]==' ')
      temp[--l]=0;

    /* If nothing left, default to the user's name */

    if (! *temp)
      strnncpy(temp, usr.name, sizeof(usr.alias)-1);
  }
  while (Invalid_Name(temp));

  temp[sizeof(usr.alias)-1]='\0';

  cfancy_str(temp);

  strncpy(usr.alias, *temp ? temp : (char *)usr.name, sizeof(usr.alias)-1);
  usr.alias[sizeof(usr.alias)-1]='\0';

  SetUserName(&usr, usrname);
}

void Chg_Phone(void)
{
  char temp[PATHLEN];
  unsigned tries = 0; /* Counts invalid phone entry attempts */

  do
  {
    if (!local && tries++ >= 3)
    {
      ci_ejectuser();
      logit("!Too many invalid phone entries -- disconnecting");
      Puts(too_many_attempts);
      mdm_hangup();
    }

    *linebuf='\0';
    temp[0]='\0';
    WhiteN();

    PromptInput("general.display.general.bounded_input_newuser",
                enter_phone, temp, 14, 50, &newuser_prompt_style);
  }
  while (Invalid_Phone(temp));

  temp[14]='\0';
  strcpy(usr.phone, temp);
}




static int near Invalid_City(char *usr_city)
{
  char *p;

  for (p=usr_city;*p;p++)
    if (isalpha(*p))
      break;

  if (isblstr(usr_city) || *p=='\0')
  {
    Puts(cantskip);
    return TRUE;
  }

  return FALSE;
}


static int near Invalid_Name(char *usr_name)
{
  char *p;

  for (p=usr_name;*p;p++)
  {
    if (isalpha(*p) ||
        isdigit(*p) ||
        CharsetSwedish(usr_name, p) || 
        CharsetChinese(usr_name,p))
    {
      break;
    }
  }

  /* Names need at least one alnum */

  if (! *p)
    return TRUE;

  if (*p && !eqstri(usr_name, usr.name) && !eqstri(usr_name, usr.alias) &&
           (IsInUserList(usr_name, FALSE) || Bad_Word_Check(usr_name)))
  {
    Puts(already_used);
    return TRUE;
  }

  return FALSE;
}


static int near Invalid_Phone(char *usr_phone)
{
  char szNewPhone[PATHLEN];
  char *p, *s;

  /* Strip all spaces if the number is too long */

  if (strlen(usr_phone) <= 14)
    strcpy(szNewPhone, usr_phone);
  else
  {
    for (p=usr_phone, s=szNewPhone; *p; p++)
      if (! isspace(*p))
        *s++=*p;

    *s='\0';
  }

  /* If it's still too long, complain. */

  if (strlen(szNewPhone) > 14)
  {
    Puts(ph_too_long);
    return TRUE;
  }

  /* Now check to see if it contains any alpha chars... */

  for (p=szNewPhone; *p; p++)
    if (isalpha(*p))
      break;

  for (s=szNewPhone; *s; s++)
    if (isdigit(*s) && *s != '-')
      break;

  if (strlen(szNewPhone) < 4 || *p != '\0' || *s=='\0' ||
      strchr(szNewPhone, '>') || strchr(szNewPhone, '<'))
  {
    Puts(inv_phone);
    return TRUE;
  }

  /* Asshole detector */
  if (stristr(szNewPhone, "555-1212") || stristr(szNewPhone, "5551212"))
  {
    Puts(cantskip);
    return TRUE;
  }

  strcpy(usr_phone, szNewPhone);
  return FALSE;
}


/**
 * @brief Find language index by basename (e.g. "english").
 *
 * Iterates the lang_file array in language.toml and returns the
 * index that matches the given basename, or -1 if not found.
 *
 * @param basename  Language file basename to look up
 * @return Language index (0-based), or -1 if not found
 */
static int near find_lang_index(const char *basename)
{
  byte lng;

  if (!basename || !*basename)
    return -1;

  for (lng = 0; lng < MAX_LANG; lng++)
  {
    MaxCfgVar v, it;

    if (ng_cfg &&
        maxcfg_toml_get((MaxCfgToml *)ng_cfg, "general.language.lang_file", &v) == MAXCFG_OK &&
        v.type == MAXCFG_VAR_STRING_ARRAY)
    {
      size_t cnt = 0;
      if (maxcfg_var_count(&v, &cnt) == MAXCFG_OK && lng < cnt)
      {
        if (maxcfg_toml_array_get(&v, (size_t)lng, &it) == MAXCFG_OK &&
            it.type == MAXCFG_VAR_STRING && it.v.s && *it.v.s)
        {
          if (stricmp(it.v.s, basename) == 0)
            return (int)lng;
        }
      }
      else
        break; /* past end of array */
    }
    else
      break; /* no lang_file array */
  }

  return -1;
}


/**
 * @brief User-facing theme selection command.
 *
 * Displays the theme_sel screen, lists available themes for selection
 * (with option 1 always being "Set to BBS Default"), sets usr.theme
 * to the chosen slot index (0 = BBS default, slot = specific theme),
 * and optionally auto-binds language when the chosen theme specifies
 * a non-empty lang field.
 */
void Chg_Theme(void)
{
  char temp[PATHLEN];
  int count;
  int sel;
  int i;
  const char *dfpath;

  count = theme_get_count();
  if (count <= 0)
  {
    Puts(unavailable);
    Press_ENTER();
    return;
  }

  /* Display the theme selection screen if it exists */
  dfpath = ngcfg_get_path("general.display_files.theme_sel");
  if (dfpath && *dfpath)
    Display_File(0, NULL, dfpath);

  /* Show numbered list of themes.  Option 1 is always "BBS Default".
   * list_option format: "|pr  |!1|hi) |!2\n|cd"
   * The \n is inside the format, so we embed the [*] marker inside
   * the name parameter (|!2) to keep it on the same line.            */
  if (!*linebuf)
  {
    Puts(select_lang);  /* Re-use "Select:" prompt preamble */

    /* Option 1: "Default BBS Skin (Currently: <display name>)"
     * Embed [*] marker in label so it precedes the format's \n.      */
    {
      const char *def_sname = theme_get_default_shortname();
      int def_iter = theme_get_index(def_sname);
      const char *def_display = (def_iter >= 0) ? theme_get_name(def_iter) : def_sname;
      char def_label[160];

      if (usr.theme == 0)
        snprintf(def_label, sizeof(def_label),
                 "Default BBS Skin (Currently: %s) |ok[*]|hi",
                 def_display ? def_display : def_sname);
      else
        snprintf(def_label, sizeof(def_label),
                 "Default BBS Skin (Currently: %s)",
                 def_display ? def_display : def_sname);

      { char _tb[16];
        snprintf(_tb, sizeof(_tb), "1");
        LangPrintf(list_option, _tb, def_label); }
    }

    /* Options 2..N: the loaded themes */
    for (i = 0; i < count; i++)
    {
      const char *tname = theme_get_name(i);
      char tname_buf[160];
      char _tb[16];

      /* Embed [*] marker in name to keep it before the format's \n   */
      if (usr.theme != 0 && (int)usr.theme == theme_get_slot(i))
        snprintf(tname_buf, sizeof(tname_buf), "%s |ok[*]|hi",
                 tname ? tname : "");
      else
        snprintf(tname_buf, sizeof(tname_buf), "%s", tname ? tname : "");

      snprintf(_tb, sizeof(_tb), "%d", i + 2);
      LangPrintf(list_option, _tb, tname_buf);
    }

    /* Legend */
    WhiteN();
    Printf("|ok[*]|07 = Current Selected Theme\n");
  }

  WhiteN();

  InputGets(temp, select_p);

  sel = atoi(temp);

  if (!sel)
    return;  /* 0 or empty = abort */

  if (sel == 1)
  {
    /* User selected "BBS Default" */
    usr.theme = 0;
  }
  else
  {
    /* Convert 1-based display number (from option 2) to 0-based iter index */
    int iter = sel - 2;

    if (iter < 0 || iter >= count)
      return;  /* Out of range */

    usr.theme = (byte)theme_get_slot(iter);
  }

  logit("+Theme changed to slot %d ('%s')",
        (int)usr.theme,
        theme_get_current_shortname());

  /* Auto-bind language if the selected theme specifies one */
  if (usr.theme != 0)
  {
    int iter = sel - 2;
    const char *theme_lang = theme_get_lang(iter);

    if (theme_lang && *theme_lang)
    {
      int lang_idx = find_lang_index(theme_lang);

      if (lang_idx >= 0 && lang_idx != (int)usr.lang)
      {
        usr.lang = (byte)lang_idx;
        Switch_To_Language();
        logit("+Theme auto-bound language to %d (%s)", lang_idx, theme_lang);
      }
    }
  }

  /* Reload theme colors for the new theme */
  Reload_Theme_Colors();

  if (*language_change)
  {
    Puts(language_change);
    Press_ENTER();
  }
}


static void near Chg_Archiver(void)
{
  byte a=Get_Archiver();
  
  if (a)
    usr.compress=a;
}


/* Get the user to select an archiver */

byte Get_Archiver(void)
{
  char temp[PATHLEN];
  struct _arcinfo *ar;
  byte compressor, cn;
  
  Load_Archivers();

  if (!ari)
    return 0;

  do
  {
    if (*linebuf=='\0')
    {
      Puts(select_def_archiver);
    
      for (cn=1, ar=ari; ar; ar=ar->next, cn++)
        { char _tb[16]; snprintf(_tb, sizeof(_tb), "%d", cn);
          LangPrintf(list_option, _tb, ar->arcname); }

      WhiteN();
    }
    
    InputGets(temp,select_p);

    compressor=(byte)atoi(temp);
    
    if (!compressor)
      return usr.compress;
  }
  while (compressor==0 ||
         compressor > MAX_ARI || 
         UserAri(compressor)==NULL);

  return compressor;
}


int Exec_Change(int type, char **result)
{
  *result=NULL;

  switch (type)
  {
    case chg_city:      Chg_City();     break;
    case chg_password:  Chg_Password(); break;
    case chg_help:      Chg_Help();     break;
    case chg_nulls:     Chg_Nulls();    break;
    case chg_width:     Chg_Width();    break;
    case chg_length:    Chg_Length();   break;
    case chg_tabs:      Chg_Tabs();     break;
    case chg_more:      Chg_More();     break;
    case chg_video:     Chg_Graphics(); break;
    case chg_editor:    Chg_Edit();     break;
    case chg_clear:     Chg_Clear();    break;
    case chg_ibm:       Chg_Ibm();      break;
    case chg_phone:     Chg_Phone();    break;
    case chg_realname:  Chg_Alias();    break;
    case chg_hotkeys:   Chg_Hotkeys();  break;
    case chg_language:  Chg_Language(); break;
    case chg_userlist:  Chg_Userlist(); break;
    case chg_protocol:  Chg_Protocol(); break;
    case chg_fsr:       Chg_FSR();      break;
    case chg_archiver:  Chg_Archiver(); break;
    case chg_rip:       Chg_RIP();      break;
    case chg_theme:     Chg_Theme();    break;
    default:            { char _ib[8]; snprintf(_ib, sizeof(_ib), "%u", type);
                          logit(bad_menu_opt, _ib); }  return 0;
  }
  
  return 0;
}



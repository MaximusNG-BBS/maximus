/*
 * mexprm.c — MEX PRM_* compatibility resolver
 *
 * Maps legacy PRM_* numeric constants onto the NG TOML config layer
 * (ngcfg_get_*) so that prm_string() works for MEX scripts without
 * reviving the old .PRM binary blob.
 *
 * Copyright (C) 2025-2026 Kevin Morgan (Limping Ninja)
 * https://github.com/LimpingNinja
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

#define MAX_LANG_global
#include "libmaxcfg.h"
#include "mexall.h"

#ifdef MEX

/*
 * PRM_* numeric IDs — mirrored from resources/scripts/prm.mh.
 * We define them here as C constants so the switch is readable
 * without pulling in the MEX header preprocessor.
 */

/* Phase 1: high-value path/name constants */
#define PRM_SYSOP          0
#define PRM_SYSNAME        1
#define PRM_MDMBUSY        2
#define PRM_SYSPATH        3
#define PRM_MISCPATH       4   /* aka PRM_DISPLAYPATH */
#define PRM_NETPATH        5
#define PRM_TEMPPATH       6
#define PRM_IPCPATH        7   /* aka PRM_NODEPATH */
#define PRM_USERBBS        8
#define PRM_LOGNAME        9
#define PRM_CHATPROG      10
#define PRM_CHATBEGIN     11
#define PRM_CHATEND       12
#define PRM_LOCALEDITOR   13
#define PRM_NOTFOUND      14
/* 15 reserved */
#define PRM_LOGO          16
#define PRM_BADLOGON      17
#define PRM_WELCOME       18
#define PRM_QUOTE         19
#define PRM_NEWUSER1      20
#define PRM_NEWUSER2      21
#define PRM_ROOKIE        22
#define PRM_APPLIC        23
#define PRM_BYEBYE        24
#define PRM_OUTSIDE       25
#define PRM_RETURN        26
#define PRM_DAYLIMIT      27
#define PRM_NOTFIRST      28
#define PRM_TOOSLOW       29
#define PRM_BARRICADE     30
#define PRM_SHELLTOOS     31
#define PRM_BACKFROMOS    32
#define PRM_NOSUCHAREA    33
#define PRM_ACCESS        34
#define PRM_XFERBAUD      35
#define PRM_FILEAREAS     36
#define PRM_NOSPACE       37
#define PRM_NAMEFORMAT    38
#define PRM_UPLOADLOG     39
#define PRM_CALLERS      140

/* Phase 2: session/menu/display values */
#define PRM_TIMEFORMAT    90
#define PRM_DATEFORMAT    91
#define PRM_MAREADAT      92
#define PRM_FAREADAT      93
#define PRM_MENUPATH      94
#define PRM_FIRSTMENU     95
#define PRM_EDITMENU      96
#define PRM_ACHGKEYS      97
#define PRM_LANGPATH      99
#define PRM_NEWMSGAREA   113
#define PRM_NEWFILEAREA  115
#define PRM_CMMTAREA     117
#define PRM_TRKPRIVVIEW  124
#define PRM_TRKPRIVMOD   125
#define PRM_TRKEXCLUDE   127
#define PRM_STAGEPATH    128
#define PRM_ATTCHBASE    129
#define PRM_ATTCHPATH    130
#define PRM_INBOUND      132
#define PRM_RIPPATH      133
#define PRM_MCPPIPE      137
#define PRM_MAREANAME    138
#define PRM_FAREANAME    139
#define PRM_MEXDATAPATH  141

/**
 * @brief  Safe string return helper — returns "" for NULL pointers.
 */
static inline const char *safe(const char *s)
{
  return s ? s : "";
}

static const char *mex_data_path(void)
{
  static char buf[PATHLEN];
  const char *base = ngcfg_get_path("maximus.data_path");

  if (!base || !*base)
    return "";

  snprintf(buf, sizeof(buf), "%smex/", base);
  return buf;
}

/**
 * @brief  Resolve a legacy PRM_* constant to its NG TOML-backed value.
 *
 * Returns a pointer to a string owned by the ngcfg layer (or a static
 * literal).  The caller must copy the result before the next ngcfg call
 * if it needs to keep it.
 *
 * @param stringnum  The numeric PRM_* constant from prm.mh.
 * @return Resolved string, or "" for unsupported/unknown IDs.
 */
const char *mex_prm_resolve(int stringnum)
{
  switch (stringnum)
  {
    /* ------------------------------------------------------------------ */
    /* Phase 1: high-value path/name constants                            */
    /* ------------------------------------------------------------------ */

    /* Direct maximus.* lookups */
    case PRM_SYSOP:       return safe(ngcfg_get_string_raw("maximus.sysop"));
    case PRM_SYSNAME:     return safe(ngcfg_get_string_raw("maximus.system_name"));
    case PRM_SYSPATH:     return safe(ngcfg_get_path("maximus.sys_path"));
    case PRM_MISCPATH:    return safe(ngcfg_get_path("maximus.display_path"));
    case PRM_NETPATH:     return safe(ngcfg_get_path("maximus.net_info_path"));
    case PRM_TEMPPATH:    return safe(ngcfg_get_path("maximus.temp_path"));
    case PRM_IPCPATH:     return safe(ngcfg_get_path("maximus.node_path"));
    case PRM_USERBBS:     return safe(ngcfg_get_path("maximus.file_password"));
    case PRM_LOGNAME:     return safe(ngcfg_get_path("maximus.log_file"));
    case PRM_LANGPATH:    return safe(ngcfg_get_path("maximus.lang_path"));
    case PRM_STAGEPATH:   return safe(ngcfg_get_path("maximus.stage_path"));
    case PRM_INBOUND:     return safe(ngcfg_get_path("maximus.inbound_path"));
    case PRM_CALLERS:     return safe(ngcfg_get_path("maximus.file_callers"));
    case PRM_MEXDATAPATH: return mex_data_path();
    case PRM_ACCESS:      return safe(ngcfg_get_path("maximus.file_access"));
    case PRM_MAREANAME:   return safe(ngcfg_get_path("maximus.message_data"));
    case PRM_FAREANAME:   return safe(ngcfg_get_path("maximus.file_data"));
    case PRM_RIPPATH:     return safe(ngcfg_get_path("maximus.rip_path"));
    case PRM_MCPPIPE:     return safe(ngcfg_get_string_raw("maximus.mcp_pipe"));

    /* Session strings from general.session.* */
    case PRM_CHATPROG:    return safe(ngcfg_get_string_raw("general.session.chat_program"));
    case PRM_LOCALEDITOR: return safe(ngcfg_get_string_raw("general.session.local_editor"));
    case PRM_UPLOADLOG:   return safe(ngcfg_get_path("general.session.upload_log"));

    /* Display files from general.display_files.* */
    case PRM_CHATBEGIN:   return safe(ngcfg_get_path("general.display_files.chat_begin"));
    case PRM_CHATEND:     return safe(ngcfg_get_path("general.display_files.chat_end"));
    case PRM_NOTFOUND:    return safe(ngcfg_get_path("general.display_files.not_found"));
    case PRM_LOGO:        return safe(ngcfg_get_path("general.display_files.logo"));
    case PRM_BADLOGON:    return safe(ngcfg_get_path("general.display_files.bad_logon"));
    case PRM_WELCOME:     return safe(ngcfg_get_path("general.display_files.welcome"));
    case PRM_QUOTE:       return safe(ngcfg_get_path("general.display_files.quote"));
    case PRM_NEWUSER1:    return safe(ngcfg_get_path("general.display_files.new_user1"));
    case PRM_NEWUSER2:    return safe(ngcfg_get_path("general.display_files.new_user2"));
    case PRM_ROOKIE:      return safe(ngcfg_get_path("general.display_files.rookie"));
    case PRM_APPLIC:      return safe(ngcfg_get_path("general.display_files.application"));
    case PRM_BYEBYE:      return safe(ngcfg_get_path("general.display_files.bye_bye"));
    case PRM_OUTSIDE:     return safe(ngcfg_get_path("general.display_files.out_leaving"));
    case PRM_RETURN:      return safe(ngcfg_get_path("general.display_files.out_return"));
    case PRM_DAYLIMIT:    return safe(ngcfg_get_path("general.display_files.day_limit"));
    case PRM_NOTFIRST:    return safe(ngcfg_get_path("general.display_files.time_warn"));
    case PRM_TOOSLOW:     return safe(ngcfg_get_path("general.display_files.too_slow"));
    case PRM_BARRICADE:   return safe(ngcfg_get_path("general.display_files.barricade"));
    case PRM_SHELLTOOS:   return safe(ngcfg_get_path("general.display_files.shell_to_dos"));
    case PRM_BACKFROMOS:  return safe(ngcfg_get_path("general.display_files.back_from_dos"));
    case PRM_NOSUCHAREA:  return safe(ngcfg_get_path("general.display_files.area_not_exist"));
    case PRM_XFERBAUD:    return safe(ngcfg_get_path("general.display_files.xfer_baud"));
    case PRM_NOSPACE:     return safe(ngcfg_get_path("general.display_files.no_space"));
    case PRM_NAMEFORMAT:  return safe(ngcfg_get_path("general.display_files.fname_format"));

    /* PRM_FILEAREAS / PRM_MSGAREAS — these were display files for area lists;
     * in NG the area list display is format-string driven, not file-based.
     * Return "" as intentionally unsupported. */
    case PRM_FILEAREAS:   return "";
    /* PRM_MSGAREAS = 44 */

    /* ------------------------------------------------------------------ */
    /* Phase 2: session/menu/display values                               */
    /* ------------------------------------------------------------------ */

    case PRM_TIMEFORMAT:  return safe(ngcfg_get_string_raw("general.display.general.time_format"));
    case PRM_DATEFORMAT:  return safe(ngcfg_get_string_raw("general.display.general.date_format"));
    case PRM_FIRSTMENU:   return safe(ngcfg_get_string_raw("general.session.first_menu"));
    case PRM_EDITMENU:    return safe(ngcfg_get_string_raw("general.session.edit_menu"));
    case PRM_ACHGKEYS:    return safe(ngcfg_get_string_raw("general.session.area_change_keys"));
    case PRM_NEWMSGAREA:  return safe(ngcfg_get_string_raw("general.session.first_message_area"));
    case PRM_NEWFILEAREA: return safe(ngcfg_get_string_raw("general.session.first_file_area"));
    case PRM_CMMTAREA:    return safe(ngcfg_get_string_raw("general.session.comment_area"));
    case PRM_TRKPRIVVIEW: return safe(ngcfg_get_string_raw("general.session.track_privview"));
    case PRM_TRKPRIVMOD:  return safe(ngcfg_get_string_raw("general.session.track_privmod"));
    case PRM_TRKEXCLUDE:  return safe(ngcfg_get_path("general.session.track_exclude"));
    case PRM_ATTCHBASE:   return safe(ngcfg_get_path("general.session.attach_base"));
    case PRM_ATTCHPATH:   return safe(ngcfg_get_path("general.session.attach_path"));

    /* Intentionally unsupported in NG — legacy binary database concepts */
    case PRM_MAREADAT:    return "";
    case PRM_FAREADAT:    return "";
    case PRM_MENUPATH:    return "";

    /* Modem strings — not meaningful in NG but return "" safely */
    case PRM_MDMBUSY:     return "";

    default:
      logit("!MEX prm_string: unsupported PRM id %d", stringnum);
      return "";
  }
}

#endif /* MEX */

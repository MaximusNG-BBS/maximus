/*
 * Maximus Version 3.02
 * Copyright 1989, 2002 by Lanius Corporation.  All rights reserved.
 *
 * Modifications Copyright (C) 2025 Kevin Morgan (Limping Ninja)
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

/* vm_ifc.h
 *
 * Exported definitions for the VM module.  These funcions define the
 * interface for the MEXVM.DLL file.  None of the other functions can be
 * accessed externally.
 */

#ifndef VM_IFC_H_DEFINED__
#define VM_IFC_H_DEFINED__

#include <setjmp.h>

#ifndef MEX_H_DEFINED__
  #include "mex.h"
#endif

#ifndef vm_extern
  #define vm_extern extern
  #define VM_LEN(x)
#endif

vm_extern byte pascal regs_1[VM_LEN(MAX_REGS)]; /* Array of virtual regs (bytes) */
vm_extern word pascal regs_2[VM_LEN(MAX_REGS)]; /* Array of virtual regs (words) */
vm_extern dword pascal regs_4[VM_LEN(MAX_REGS)]; /* Array of virtual regs (dwords) */
vm_extern IADDR pascal regs_6[VM_LEN(MAX_REGS)]; /* Array of virtual regs (IADDR/strings) */


/*
 * struct _mex_vm_state
 *
 * Captures the entire VM interpreter state so that a parent MEX execution
 * can be suspended while a child MEX runs via MexExecute(), then restored
 * afterward.  Used by MexSaveVmState() / MexRestoreVmState().
 */

struct _mex_vm_state
{
  /* Code segment */
  INST *pinCs;
  VMADDR high_cs;

  /* Data segment (globals + stack + heap) */
  byte *pbDs;
  byte *pbSp;
  byte *pbBp;
  struct _dsheap *pdshDheap;

  /* Symbol table */
  struct _rtsym *rtsym;
  VMADDR n_rtsym;
  VMADDR n_entry;
  VMADDR vaLastAssigned;        /* from vm_symt.c static */

  /* VM header (sizes) */
  struct _vmh vmh;

  /* Instruction pointer */
  VMADDR vaIp;

  /* Function definitions */
  struct _funcdef *fdlist;
  struct _usrfunc *usrfn;

  /* Registers */
  byte  regs_1[MAX_REGS];
  word  regs_2[MAX_REGS];
  dword regs_4[MAX_REGS];
  IADDR regs_6[MAX_REGS];

  /* Debug flags */
  int deb;
  int debheap;

  /* Logger and hooks (static in vm_run.c) */
  void (_stdc *pfnLogger)(char *szStr, ...);
  void (EXPENTRY *pfnHookBefore)(void);
  void (EXPENTRY *pfnHookAfter)(void);

  /* Error recovery */
  jmp_buf jbError;
};


int    EXPENTRY MexExecute(char *pszFile, char *pszArgs, dword fFlag,
                           unsigned short uscIntrinsic, struct _usrfunc *puf,
                           int (EXPENTRY *pfnSetup)(void),
                           void (EXPENTRY *pfnTerm)(short *psRet),
                           void (_stdc *pfnLog)(char *szStr, ...),
                           void (EXPENTRY *pfnHookBefore)(void),
                           void (EXPENTRY *pfnHookAfter)(void));
void * EXPENTRY MexFetch(FORM form, IADDR *where);
void * EXPENTRY MexDSEG(VMADDR ofs);
VMADDR EXPENTRY MexEnterSymtab(char *name, word size);
VMADDR EXPENTRY MexStoreByte(char *name, byte b);
VMADDR EXPENTRY MexStoreWord(char *name, word w);
VMADDR EXPENTRY MexStoreDword(char *name, dword dw);
VMADDR EXPENTRY MexStoreString(char *name, char *str);
VMADDR EXPENTRY MexStoreStringAt(VMADDR vmaDesc, char *str);
void   EXPENTRY MexKillString(IADDR *pwhere);
VMADDR EXPENTRY MexPtrToVM(void *ptr);
VMADDR EXPENTRY MexStoreByteStringAt(VMADDR vmaDesc, char *str, int len);
VMADDR EXPENTRY MexIaddrToVM(IADDR *pia);
IADDR  EXPENTRY MexStoreHeapByteString(char *str, int len);
void   EXPENTRY MexRTError(char *szMsg);

/* VM state save/restore for nested MEX execution */
void   EXPENTRY MexSaveVmState(struct _mex_vm_state *pState);
void   EXPENTRY MexRestoreVmState(struct _mex_vm_state *pState);

#endif /* VM_IFC_H_DEFINED__ */


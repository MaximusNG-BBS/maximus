# Linux with GNU Make, GNU C
#
# Tested on: Ubuntu, Debian, Alpine
# Note: Requires ncurses-dev package
#
# $Id$

EXTRA_CPPFLAGS	+= -DLINUX
# Note: -lmsgapi repeated at end to resolve circular dependency with libmax
OS_LIBS		= -lpthread -lncurses -lmsgapi -lm

# Position-independent code for shared libraries
CFLAGS		+= -fPIC
CXXFLAGS	+= -fPIC

# Linux rpath for finding shared libraries relative to executable
LINUX_RPATH	= -Wl,-rpath,'$$ORIGIN/../lib'
# Allow undefined symbols in shared libraries (like macOS -undefined dynamic_lookup)
# This is needed because libmax.so has undefined references to symbols in executables (e.g., logit)
# Export dynamic symbols from executables so shared libraries can resolve them at runtime
LDFLAGS		+= $(LINUX_RPATH) -Wl,--allow-shlib-undefined -rdynamic

# Default prefix if not set
ifeq ($(PREFIX),)
PREFIX		= /var/max
endif

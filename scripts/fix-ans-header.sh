#!/usr/bin/env bash
# fix-ans-header.sh — Ensure ANS files start with ESC[2J ESC[H ESC[0m
#
# Strips any leading occurrences of these three sequences (in any order),
# then prepends the canonical header.  Binary-safe (preserves CP437).
#
# Usage: fix-ans-header.sh <file.ans> [file2.ans ...]

set -euo pipefail

for file in "$@"; do
  if [[ ! -f "$file" ]]; then
    echo "skip: $file (not found)" >&2
    continue
  fi

  perl -e '
    binmode STDIN;  binmode STDOUT;
    local $/;
    my $data = <STDIN>;

    # --- Strip SAUCE record (128 bytes at EOF starting with "SAUCE") ---
    my $stripped_sauce = 0;
    if (length($data) >= 128 && substr($data, -128, 5) eq "SAUCE") {
      $data = substr($data, 0, length($data) - 128);
      $stripped_sauce = 1;

      # Strip COMNT block if present (5-byte "COMNT" header + N * 64-byte lines)
      if (length($data) >= 69 && substr($data, -69) =~ /COMNT/) {
        my $pos = rindex($data, "COMNT");
        if ($pos >= 0) {
          my $tail = length($data) - $pos;
          # COMNT block = 5 + N*64; verify alignment
          if (($tail - 5) % 64 == 0) {
            $data = substr($data, 0, $pos);
          }
        }
      }

      # Strip trailing EOF marker (0x1A) if present
      $data =~ s/\x1A\z//;
    }

    # --- Strip any leading ESC[2J, ESC[H, ESC[0m in any order ---
    my $changed = 1;
    while ($changed) {
      $changed = 0;
      if ($data =~ s/\A\033\[2J//) { $changed = 1; }
      if ($data =~ s/\A\033\[H//)  { $changed = 1; }
      if ($data =~ s/\A\033\[0m//) { $changed = 1; }
    }

    # Prepend canonical header
    print "\033[2J\033[H\033[0m";
    print $data;
    print STDERR "SAUCE" if $stripped_sauce;
  ' < "$file" > "$file.tmp" 2>"$file.sauce"
  mv "$file.tmp" "$file"

  if [[ -s "$file.sauce" ]]; then
    echo "fixed: $file (SAUCE stripped)"
  else
    echo "fixed: $file"
  fi
  rm -f "$file.sauce"
done

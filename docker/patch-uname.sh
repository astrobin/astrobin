#!/bin/bash -ex

echo `uname -r`

# Debian glibc won't install on kernel revisions >=255, so add a wrapper script
# to clamp the revision number. Without also patching the uname syscalls,
# glibc's version math will overflow, resulting in an increased minor version
# number and possibly in glibc trying to use unavailable syscalls or features.
if [ ! -e /bin/uname.bin -a ! -e /usr/bin/uname.bin ]; then
    for uname in /bin/uname /usr/bin/uname; do
        # We don't use --rename since /bin may be a temp symlink to /usr/bin.
        # --no-rename doesn't exist on old dpkg, but --rename will become the
        # default in the future, so we have to try both with and without.
        dpkg-divert --divert "$uname.bin" --no-rename "$uname" 2>/dev/null \
            || dpkg-divert --divert "$uname.bin" "$uname"
        mv -f "$uname" "$uname.bin" 2>/dev/null || true
    done
    echo '#!/bin/sh -eu
uname.bin "$@" | sed '\''s/\.\(25[5-9]\|2[6-9][0-9]\|[3-9][0-9][0-9]\)-/.254-/g'\' > /bin/uname
    chmod +x /bin/uname
fi

echo `uname -r`

#!/bin/sh
set -eu

printf 'worker: %s\n' "$(cat input.txt)" >result.txt
exec tail -f /dev/null

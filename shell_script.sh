# Simple shell script which copies a file to an IP + specific directory over a network connection.
# Note: ssh should be enabled for the target machine.

rsync --progress -h filename user@address:/path/for/file

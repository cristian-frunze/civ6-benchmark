#!/usr/bin/env bash
# tunnel.sh [local port]: keep an SSH tunnel from this machine to the civ6-mcp HTTP server on the game PC
# (127.0.0.1:8771 there). Agents use http://127.0.0.1:<local port>/mcp. Reconnects if the link drops.
port=${1:-18771}
while true; do
  ssh -N -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=20 -o ServerAliveCountMax=3 \
    -L "127.0.0.1:${port}:127.0.0.1:8771" "${CIV_HOST:-zenbook}"
  echo "$(date -Is) tunnel dropped, reconnecting" >&2; sleep 3
done

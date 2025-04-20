#!/bin/bash

# Make binaries executable
chmod +x ipc_snippets/shared_mem_bin
chmod +x ipc_snippets/pipe_bin

# Run the appropriate binary based on the concept
case "$1" in
    "shared_memory")
        ./ipc_snippets/shared_mem_bin "$2" "$3"
        ;;
    "pipe")
        ./ipc_snippets/pipe_bin "$2" "$3"
        ;;
    *)
        echo "Invalid concept"
        exit 1
        ;;
esac

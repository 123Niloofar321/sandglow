#!/bin/bash
# Opens this Sandglow folder in Visual Studio Code.
cd "$(dirname "$0")"
open -a "Visual Studio Code" "$(pwd)"

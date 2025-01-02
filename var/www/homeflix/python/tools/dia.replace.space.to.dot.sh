#!/usr/bin/shell
for i in *; do mv "$i" $(echo "$i" | tr " " "."); done
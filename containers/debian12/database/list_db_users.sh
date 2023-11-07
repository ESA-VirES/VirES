#!/bin/bash
#
# Simple script listing PosgreSQL database users/roles

psql -tAc "SELECT rolname FROM pg_roles ;" | egrep -v '^(pg_|postgres$)'

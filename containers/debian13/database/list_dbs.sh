#!/bin/bash
#
# Simple script listing PosgreSQL databases

psql -tAc "SELECT datname FROM pg_database WHERE datistemplate IS FALSE ;" | grep -v postgres

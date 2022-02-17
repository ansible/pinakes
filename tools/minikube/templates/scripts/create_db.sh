#!/bin/bash
set -e
sql="CREATE DATABASE "$PINAKES_DATABASE_NAME";"
echo $sql > /tmp/my.sql

psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -f /tmp/my.sql

DBUSER= # set your actual local DB username
DBPASSWORD= # set your actual local DB password
DBHOST=127.0.0.1
DBPORT=5432
CONN=postgresql://$DBUSER:$DBPASSWORD@$DBHOST:$DBPORT
DBNAME=usaspending

DUMP_DIR=/Volumes/XYZ01 # set your actual source disk / path
DUMP=$DUMP_DIR/source

psql $CONN/postgres -c \
"DROP DATABASE IF EXISTS $DBNAME"
psql $CONN/postgres -c \
"CREATE DATABASE $DBNAME"

pg_restore --list $DUMP | sed '/MATERIALIZED VIEW DATA/d' > $DUMP_DIR/restore.list

pg_restore \
--jobs 16 \
--dbname $CONN/$DBNAME \
--verbose \
--exit-on-error \
--use-list $DUMP_DIR/restore.list \
$DUMP
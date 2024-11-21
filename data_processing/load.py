"""Creates markdown files for static site generation."""

import sqlite3

DISK_DIRECTORY = "/Volumes/CER01/"
DB_FILE_PATH = "usaspending.db"

conn = sqlite3.connect(DISK_DIRECTORY + DB_FILE_PATH)
cursor = conn.cursor()

# close the db connection
conn.close()

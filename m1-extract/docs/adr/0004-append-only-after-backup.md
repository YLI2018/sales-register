# 0004: Approved rows are appended after a backup

Date: 2026-11-05. Status: accepted.

Existing lines of the clean files are never rewritten. Before each addition both files are copied to clean/backup with the date and time; the new rows are appended in the files' own column order and new sales get the next free ids. Any addition can be undone by restoring the backup.

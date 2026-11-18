# 0003: Reports are identified by their fingerprint

Date: 2026-11-05. Status: accepted.

A report is new when the SHA-256 of its contents is not on extracted_reports.csv. Renaming a file does not cause a re-read; a corrected edition with the same name is read again. Reports already typed by hand during M1 are listed on the first run (by the file names in the data's source_file column) and not read.

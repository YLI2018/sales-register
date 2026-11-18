# 0005: Apple text recognition for the HSN screenshots

Date: 2026-11-05. Status: accepted.

The HSN valuation reports are saved as screenshots. Apple's Vision framework (built into macOS, used through pyobjc) reads them accurately and needs nothing else installed. Known slips (a comma read as a dot in DWT, 'WV' for 'VV') are handled in the sentence pattern; every row read from an image is flagged for checking.

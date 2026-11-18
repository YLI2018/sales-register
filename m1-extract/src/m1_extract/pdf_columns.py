"""Read a table from a PDF page by the position of its words.

Broker tables wrap: a yard can sit on two lines ("Hyundai Samho," / "Korea") and a name on two ("Saltwind" /
"Explorer"). Reading by table cells breaks such rows apart. Instead:

1. find the header line (the column titles) and take each title's left edge as the start of its column;
2. find the anchor of each table row: a word in the anchor column that looks like a value (for example a DWT);
3. give every other word below the header to the nearest anchor row (by vertical distance) and to the column whose
   band contains it;
4. join the words of each cell in reading order.

The result is one dictionary per row: {column title: text}, plus the page number and the row's position.
"""
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence


@dataclass
class Word:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float

    @property
    def mid_y(self) -> float:
        return (self.top + self.bottom) / 2


def page_words(page, x_tolerance: float = 1.5) -> List[Word]:
    """All words of a pdfplumber page as Word records."""
    return [Word(w["text"], w["x0"], w["x1"], w["top"], w["bottom"])
            for w in page.extract_words(x_tolerance=x_tolerance, y_tolerance=2, keep_blank_chars=False)]


def find_header(words: List[Word], titles: Sequence[str], after_y: float = -1) -> Optional[Dict[str, Word]]:
    """Find the first line (below after_y) holding all the given column titles; return {title: its Word}.
    A title may be several words ("Price ($ mills)" is matched on its first word)."""
    lines: Dict[int, List[Word]] = {}
    for w in words:
        if w.top > after_y:
            lines.setdefault(round(w.top / 3), []).append(w)
    for key in sorted(lines):
        line = lines.get(key, []) + lines.get(key + 1, [])
        found = {}
        for t in titles:
            first = t.split()[0].lower()
            match = [w for w in line if w.text.lower() == first]
            if match:
                found[t] = min(match, key=lambda w: w.x0)
        if len(found) == len(titles):
            return found
    return None


def read_table(words: List[Word], header: Dict[str, Word], anchor: str, is_anchor: Callable[[str], bool],
               stop_y: Optional[float] = None, max_gap: float = 14.0, left_margin: float = 6.0) -> List[Dict[str, str]]:
    """Rows of the table under `header`. `anchor` is the column whose values mark rows; `is_anchor` tests a word.
    Words further than max_gap points from any anchor are ignored (titles, footers)."""
    head_bottom = max(w.bottom for w in header.values())
    body = [w for w in words if w.top > head_bottom + 0.5 and (stop_y is None or w.top < stop_y)]
    # Rows first: anchor values sit under the anchor title (its centre lies within the anchor word's span, give or take).
    a_word = header[anchor]
    a_mid = (a_word.x0 + a_word.x1) / 2
    anchor_words = [w for w in body if is_anchor(w.text) and w.x0 - 25 <= a_mid <= w.x1 + 25]
    anchors = sorted({round(w.mid_y, 1) for w in anchor_words})
    if not anchors:
        return []
    body = [w for w in body if min(abs(w.mid_y - a) for a in anchors) <= max_gap]
    # Columns from the text itself: merge the horizontal spans of all body words; gaps between spans separate columns.
    spans = sorted([w.x0, w.x1] for w in body)
    clusters = []
    for x0, x1 in spans:
        if clusters and x0 <= clusters[-1][1] + 4.5:
            clusters[-1][1] = max(clusters[-1][1], x1)
        else:
            clusters.append([x0, x1])
    titles = sorted(header.items(), key=lambda kv: kv[1].x0)
    centres = [(t, (w.x0 + w.x1) / 2) for t, w in titles]
    # Two columns printed close together can merge into one span: split a span that holds two or more title centres
    # at the widest gap between its words that lies between those centres.
    split = []
    for x0, x1 in clusters:
        inside = [c for _, c in centres if x0 - 3 <= c <= x1 + 3]
        if len(inside) < 2:
            split.append([x0, x1])
            continue
        ws = sorted((w.x0, w.x1) for w in body if x0 - 0.1 <= w.x0 <= x1 + 0.1)
        cuts = []
        for left, right in zip(inside, inside[1:]):
            gaps = [(b0 - a1, a1, b0) for (_, a1), (b0, _) in zip(ws, ws[1:]) if left - 10 <= (a1 + b0) / 2 <= right + 10 and b0 > a1]
            if gaps:
                g = max(gaps)
                cuts.append((g[1] + g[2]) / 2)
        edges = [x0] + sorted(cuts) + [x1]
        split += [[a, b] for a, b in zip(edges, edges[1:])]
    clusters = split

    def title_for(x0: float, x1: float) -> str:
        inside = [t for t, c in centres if x0 - 3 <= c <= x1 + 3]
        if inside:
            return inside[0]
        mid = (x0 + x1) / 2
        return min(centres, key=lambda tc: abs(tc[1] - mid))[0]

    col_of_cluster = [title_for(x0, x1) for x0, x1 in clusters]

    def column_of(w: Word) -> Optional[str]:
        for (x0, x1), t in zip(clusters, col_of_cluster):
            if x0 - 0.1 <= w.x0 <= x1 + 0.1:
                return t
        return None

    if not anchors:
        return []
    cells: List[Dict[str, List[Word]]] = [dict() for _ in anchors]
    for w in body:
        col = column_of(w)
        if col is None:
            continue
        dist = [abs(w.mid_y - a) for a in anchors]
        i = dist.index(min(dist))
        if dist[i] > max_gap:
            continue
        cells[i].setdefault(col, []).append(w)
    rows = []
    for a, c in zip(anchors, cells):
        row = {t: " ".join(w.text for w in sorted(ws, key=lambda w: (round(w.top), w.x0))).strip()
               for t, ws in c.items()}
        row["_y"] = str(a)
        rows.append(row)
    return rows


NUM = re.compile(r"^\d{1,3}([.,]\d{3})+$|^\d{4,6}$")


def looks_like_size(text: str) -> bool:
    """A DWT or TEU figure such as 81.504, 158,517 or 2797."""
    return bool(NUM.match(text.strip()))

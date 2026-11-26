# The reviau Folder

*English · [Português (Brasil)](../pt-BR/reviau-folder.md)*

Everything that a review writes is kept in one folder, **`reviau/`**, inside the
segments folder:

```
segments/
├── PONTO_A/BOAALB/clip.wav       ← clips pending review
└── reviau/
    ├── correct/                  ← reviewed clips, by outcome
    ├── incorrect/
    ├── uncertain/
    ├── reviews.csv               ← the review log
    ├── labels.txt                ← the label list
    ├── settings.json             ← the reading settings
    └── annotations.csv           ← the annotation table, with --annotations
```

The collection under review is therefore never mixed with the results: the only
change made to it is that reviewed clips are moved out of it, and deleting
`reviau/` removes everything that reviau wrote. The `reviau/` folder is excluded
from the pending list, and every other folder of the collection is reviewed,
whatever it is called. `--output` places this folder elsewhere; see
[Writing to Another Location](#writing-to-another-location).

## The Label List

The label buttons are taken from a list stored in **`labels.txt`** in the
`reviau/` folder, one label per line. The first time a collection is opened, the
list is built from the labels the collection already uses, and it is written to
the file when the first segment is reviewed. From then on, the file is the list;
it can be edited in the interface or by hand (blank lines and lines beginning
with `#` are ignored).

The list is never extended automatically: a rescan that finds a new folder does
not add its name to the list. Removing labels from the list is also safe, since
the label a clip carries is always shown as a button whether or not it is on the
list, and a name typed into the field is both added to the list and selected for
the segment on screen.

`--labels-file` stores the list in another location. A relative path is resolved
inside the `reviau/` folder; an absolute path, such as `~/classes.txt`, gives
every folder opened the same list.

## Where a Reviewed Clip Is Filed

A reviewed clip is filed in the `reviau/` folder under its **outcome**, followed
by the path it had, including the folder of the **predicted** label. Each folder
therefore answers a single question: `incorrect/PONTO_A/BOAALB/` contains
exactly the clips that the model labelled BOAALB incorrectly, so the number of
files in each folder gives the precision for that class. The labels identified
during the review are appended to the file name, so the folder tree can be read
without consulting the log:

```
PONTO_A/BOAALB/clip.wav
   ├── ✔ Correct                  →  reviau/correct/PONTO_A/BOAALB/clip_BOAALB.wav
   ├── ✔ Correct, + PHYLUT        →  reviau/correct/PONTO_A/BOAALB/clip_BOAALB_PHYLUT.wav
   ├── ✘ Incorrect, TURDRU        →  reviau/incorrect/PONTO_A/BOAALB/clip_TURDRU.wav
   ├── ✘ Incorrect, TURDRU+PHYLUT →  reviau/incorrect/PONTO_A/BOAALB/clip_TURDRU_PHYLUT.wav
   ├── ✘ Incorrect, none          →  reviau/incorrect/PONTO_A/BOAALB/clip.wav
   └── ? Uncertain                →  reviau/uncertain/PONTO_A/BOAALB/clip.wav
```

- The file name **receives the labels that the clip was found to contain**. A
  correct clip receives the confirmed prediction, followed by any label added; an
  incorrect clip receives the labels that describe what it actually contains.
  Added labels follow the order in which they were selected, with spaces written
  as `_` (`chuva forte` becomes `_chuva_forte`), and the original name is kept in
  full before them. An Incorrect with no label from the list, and every segment
  marked Uncertain, keep their name unchanged.
- When the label is read from the file name, the prediction is already part of
  the name and is not appended a second time.
- With a label depth above 0, the folders *below* the label are **not** recreated:
  `BOAALB/PONTO_A/20240115/clip.wav` corrected to TURDRU becomes
  `incorrect/BOAALB/clip_TURDRU.wav`, with one folder per predicted label
  containing the clips directly.
- A clip that arrived **without a label** has no prediction to assess. It is
  filed under `labelled/`, keeping the folders it was in, and every label
  assigned to it is appended to its name.
- A name that already exists receives a `_2`, `_3`, … suffix; a reviewed file is
  never overwritten.
- The folder from which a clip was taken is **removed once its last clip has
  been filed**, together with any parent folder that becomes empty, so the tree
  of pending segments shrinks as the review progresses. A folder that still
  contains anything, whether a pending clip or another file, is preserved, and
  the segments folder itself is never removed.
- Clips already filed in `reviau/` are excluded from the pending list, so a
  review can be spread over several sessions.

The verdict folders are always named `correct/`, `incorrect/`, `uncertain/` and
`labelled/`, and the review log always records those outcome names, whatever the
interface language. The data written by a review therefore never depends on the
language in which it was carried out.

## Writing to Another Location

`--output` (or `-o`) replaces the `reviau/` folder with a folder of the
reviewer's choice, for example on another disk. The verdict folders, the review
log, the label list, the reading settings and the annotation table are all
written there:

```bash
reviau /data/segments --output /data/reviewed
```

A relative path is resolved against the segments folder (`-o reviewed` refers to
`/data/segments/reviewed/`), an absolute path is used as given, and over SSH the
path refers to the remote machine. To resume a review, the same `--output`
should be given again: that folder is where the counts of segments already
reviewed are taken, and clips already written there are never returned to the
pending list. Because the option applies to every folder opened during the
session, an absolute `--output` is intended for the review of a single
collection; folders opened with it share one results folder.

## The Review Log

Every review adds one row to **`reviews.csv`**, in the `reviau/` folder. The
log is always written and constitutes the record of the review:

| Column | Content |
| --- | --- |
| `reviewed_at` | Date and time of the review, with the time zone |
| `source`, `destination` | The original location of the clip, relative to the segments folder, and its new location, relative to the `reviau/` folder |
| `predicted`, `score` | The label the clip arrived with, and the score given in its name |
| `outcome` | `correct`, `incorrect`, `uncertain` or `labelled` |
| `labels` | The labels the reviewer identified in the clip, separated by `;`; empty when it contains no label from the list |
| `added` | The labels other than the prediction: the correction, or an additional species |
| `site`, `recording`, `start_time`, `end_time` | As in the annotation table described below |

The precision of each class is `correct / (correct + incorrect)`, grouped by
`predicted`; comparing `predicted` with `labels` in the incorrect rows gives the
confusion between classes. If the log cannot be written, the clip is moved back
to its original location and the review is rejected, so a clip is never filed
without a corresponding row.

## The Annotation Table

With `--annotations`, every label that a segment is **confirmed to contain** is
added to `annotations.csv`, in the `reviau/` folder, with the columns
`site, file, label, start_time, end_time`, one row per label, so a segment
containing two species produces two rows. A rejected prediction never appears
in the table, nor do segments marked uncertain or found to contain no label from
the list. The times give the position of the clip within the recording from
which it was cut; they are read from its name and extended to the actual
duration of the clip, so that any padding is included.

`file` names that source recording. Since the name of a clip rarely identifies
the recording from which it was cut, the recording is looked up in an optional
`segment_sources.csv` (`segment,recording`) in the segments folder. Without that
file the column is left empty, and the interface reports this below the buttons.

Rows are written as each segment is reviewed, and an existing table is extended,
so reviews spread over several sessions accumulate in the same table.
`--annotations-path` writes the table to another location.

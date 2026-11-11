# segment-reviewer

[Português (Brasil) →](README.pt-BR.md)

segment-reviewer is a command-line tool that serves a **browser interface for
reviewing a folder of audio segments**. Each clip is presented as a spectrogram,
together with the information its folder and file name provide. The reviewer
listens to the clip and records **what it contains**; whether the label it
arrived with is **correct** or **incorrect** is derived from that answer.
Reviewed clips are moved into `correct/`, `incorrect/` or `uncertain/`, every
review is recorded in `reviews.csv` (prediction, outcome and the labels actually
identified), and the confirmed labels may also be written to an annotation table.

The tool accepts any collection of clips, regardless of how it was produced: the
output of a detector, manually cut examples, or the predictions of a classifier
awaiting validation. The segments folder may be **local** or **remote over
SSH**, and the interface may be served to **another machine** on a local network
or a Tailscale network. The interface is available in **English** and
**Português (Brasil)**.

---

## How a segment is read

Information about a segment is taken from two independent sources, both of which
are configurable.

**The folder provides the label.** A collection under review is normally
organised with one folder per class, so the folder containing a clip is the label
it currently carries:

```
segments/
├── PONTO_A/BOAALB/PONTO_A_20240115_053000_12.0_17.0_det1.wav   → label BOAALB
├── PONTO_A/PHYLUT/PONTO_A_20240115_061500_3.5_8.5_det2.wav     → label PHYLUT
└── chuva/POCA_20240116_200000_5.0_10.0_det4.wav                → label chuva
```

Folders above the label are preserved: `2024/campo/PONTO_A/BOAALB/` labels the
clip `BOAALB` and retains the three folders above it. A clip placed directly in
the segments folder has no label.

**Collections with the class folder at the top.** Some collections are organised
the other way round, with the sites *inside* each class folder. In that case,
`--label-depth` specifies which level carries the label, counting down from the
segments folder. The folders below that level are read but not retained: they are
not offered as labels, and a reviewed clip is filed under its label alone, since
the site and the date are already present in the file name.

```
segments/                          # --label-depth 1
├── BOAALB/PONTO_A/20240115/clip.wav  → label BOAALB; the two folders below are not retained
├── BOAALB/POCA/clip.wav              → label BOAALB
└── PHYLUT/clip.wav                   → label PHYLUT (shallower than the depth, still labelled)
```

**The file name provides the remaining information.** By default it is read as

```
[site]_[YYYYMMDD]_[HHMMSS]_[start]_[end]_*
     PONTO_A_20240115_053000_12.0_17.0_det1.wav
```

- `site` may contain underscores; the match is anchored on the date and time.
- `start` and `end` give the position of the clip, in seconds, within the
  recording from which it was cut. Both forms are accepted: `12.0_17.0` and
  `12.0-17.0s`.
- `_*` covers any remaining text, which the interface displays as *Other*.
- Every part after the site is optional, and **a name that matches no part of
  the pattern can still be reviewed**; the interface simply displays less
  information about it.

Collections named according to another convention can be described with
`--filename-pattern`; see
[Reading other naming conventions](#reading-other-naming-conventions).

---

## Installation

### With [uv](https://docs.astral.sh/uv/) (recommended)

To run the tool without a permanent installation:

```bash
uvx --from git+https://github.com/biodiversica/segment-reviewer segment-reviewer /path/to/segments
```

To install it as a tool:

```bash
uv tool install git+https://github.com/biodiversica/segment-reviewer
segment-reviewer /path/to/segments
```

To work from a clone, for development:

```bash
git clone https://github.com/biodiversica/segment-reviewer
cd segment-reviewer
uv venv
uv pip install -e ".[dev]"
uv run segment-reviewer /path/to/segments
```

### With pip

```bash
python -m venv .venv && source .venv/bin/activate
pip install git+https://github.com/biodiversica/segment-reviewer
segment-reviewer /path/to/segments
```

Python 3.10 or later is required. The audio libraries (librosa and soundfile)
depend on `libsndfile`, which is included in the wheels for Linux, macOS and
Windows.

---

## Usage

```bash
# Start without a folder and open one from the browser
segment-reviewer

# Open a local folder at start-up, with the interface on this machine
segment-reviewer ~/segments

# Portuguese interface, a fixed set of label buttons and an annotation table
segment-reviewer ~/segments --lang pt-BR --labels "BOAALB, PHYLUT, chuva" --annotations

# Segments on a server, reviewed from another computer
segment-reviewer ssh://user@fieldserver/data/segments

# Serve the interface to the network (local network, Tailscale, …)
segment-reviewer /data/segments --host 0.0.0.0 --port 8765
```

The command prints a summary and the address to open. With `--host 0.0.0.0` it
also prints the address that other machines should use.

### Opening a folder

The **folder box** at the top of the page shows which segments folder is under
review. Typing another path and pressing <kbd>Enter</kbd>, or selecting a folder
with **Browse…**, opens that folder in place of the current one without
restarting the command. When the command is started without a `SEGMENTS`
folder, the page displays only the folder box.

- The folder box accepts the same paths as the command line: a local folder, a
  path beginning with `~/`, or `ssh://user@host/path` for a remote folder, which
  is reached with the SSH settings of the command line (`--ssh-key`,
  `~/.ssh/config`, the SSH agent, and so on).
- Every folder opened receives the options with which the command was started:
  the filename pattern, `--label-depth`, `--output`, `--labels` and
  `--annotations`.
- **Opening a folder does not write to it.** The verdict folders, the review log
  and the label list are created when the first segment is reviewed, so a folder
  opened by mistake, through a typing error or one level too high, is left
  unchanged.
- A folder that cannot be opened is rejected with an explanation, and the review
  in progress is not affected.
- **Browse…** lists the folders of the machine on which the reviewer runs, which
  is the machine that reads the clips; when the interface is served to another
  computer, this is not the computer running the browser. Folders that contain
  clips are marked with ♪. Remote `ssh://` folders cannot be browsed and must be
  typed.
- Recently opened folders are suggested while typing. This history is stored in
  the browser.
- When the filename pattern recognises only some of the names in the folder just
  opened, a notice below the folder box reports it, together with one name that
  was not recognised.

### In the browser

| Control | Function |
| --- | --- |
| **Label buttons** | Labels for anything *else* present in the clip, or for what the clip actually contains. Each segment starts with no label selected; clicking a label selects it, and clicking it again deselects it. The button of the predicted label is marked **◆ predicted** and cannot be selected: the prediction is assessed with Correct or Incorrect instead. <kbd>1</kbd>…<kbd>9</kbd> select the first nine labels. |
| **✔ Correct** | The prediction is correct. The segment is saved with the prediction and any selected label, for example a second species vocalising at the same time. The button shows what will be saved: *✔ Correct + PHYLUT*. |
| **✘ Incorrect** | The prediction is incorrect. The segment is saved with the selected labels, which describe what the clip actually contains, or, if none is selected, as containing no label from the list. The button shows which applies: *✘ Incorrect → TURDRU* or *✘ Incorrect · no label from the list*. |
| **? Uncertain** | The clip cannot be assessed. It is filed under `uncertain/` and excluded from the correct and incorrect counts and from the annotation table. |
| **← Previous / Next →** | Move between segments without recording a decision. |
| **Type / Minimum (Hz) / Maximum (Hz) / Floor (dB)** | Redraw the spectrogram immediately, on a mel, linear or logarithmic frequency axis. The audio player is not affected, so playback continues while the view changes. |
| **✎** | Edit the label list: each button displays a **×** that removes it, and the field below adds a new label. Changes are saved to the label list file (`labels.txt` in the segments folder by default). |
| **⟳** | Rescan the folder, for example after new segments have been added. |
| **Language** | Switch the interface between English and Português. |
| **◐ / ☀ / ☾** | Theme: system default, light or dark; each click selects the next. The selected theme is stored in the browser. The spectrogram keeps its colours in both themes. |

The prediction is the question, and Correct or Incorrect is the answer; the label
buttons only add what else is present. No label is ever selected in advance, so a
segment rejected without further selection is saved as containing no label from
the list, and never with a label carried over from the previous clip. When a
segment has no prediction to assess, a single **✔ Save** button files the
selected labels. The server derives the outcome from the labels it receives,
according to a single rule:

| Labels saved | Outcome |
| --- | --- |
| the prediction | correct |
| the prediction and other labels | correct (the other labels are recorded as *added*) |
| other labels only | incorrect; the clip contains those labels |
| none | incorrect; the clip contains no label from the list |
| any, with Uncertain | uncertain |

Several labels may be assigned to one segment, for example when two species
vocalise at the same time. This is the default behaviour; `--no-multi-label`
restricts each segment to a single label.

Keyboard shortcuts: <kbd>←</kbd> and <kbd>→</kbd> move between segments;
<kbd>T</kbd>, <kbd>F</kbd> and <kbd>U</kbd> record correct, incorrect and
uncertain; <kbd>1</kbd>…<kbd>9</kbd> select or deselect the first nine labels;
<kbd>Space</kbd> plays or pauses the audio.

### The label list

The label buttons are taken from a list stored in **`labels.txt`** in the
segments folder, one label per line. The first time a collection is opened, the
list is built from the labels the collection already uses, and it is written to
the file when the first segment is reviewed. From then on, the file is the list;
it can be edited in the interface or by hand (blank lines and lines beginning
with `#` are ignored).

When `--labels` is given, those labels are the only buttons offered for the
session. They replace the contents of the file and are written in its place.

The list is never extended automatically: a rescan that finds a new folder does
not add its name to the list. Removing labels from the list is also safe, since
the label a clip carries is always shown as a button whether or not it is on the
list, and a name typed into the field is both added to the list and selected for
the segment on screen.

`--labels-file` stores the list in another location, and `--no-labels-file`
keeps changes for the current session only.

### Where a reviewed clip is filed

A reviewed clip is filed under its **outcome**, followed by the path it had,
including the folder of the **predicted** label. Each folder therefore answers a
single question: `incorrect/PONTO_A/BOAALB/` contains exactly the clips that the
model labelled BOAALB incorrectly, so the number of files in each folder gives
the precision for that class. The labels added during the review are appended to
the file name, so the folder tree can be read without consulting the log:

```
PONTO_A/BOAALB/clip.wav
   ├── ✔ Correct                  →  correct/PONTO_A/BOAALB/clip.wav
   ├── ✔ Correct, + PHYLUT        →  correct/PONTO_A/BOAALB/clip_PHYLUT.wav
   ├── ✘ Incorrect, TURDRU        →  incorrect/PONTO_A/BOAALB/clip_TURDRU.wav
   ├── ✘ Incorrect, TURDRU+PHYLUT →  incorrect/PONTO_A/BOAALB/clip_TURDRU_PHYLUT.wav
   ├── ✘ Incorrect, none          →  incorrect/PONTO_A/BOAALB/clip.wav
   └── ? Uncertain                →  uncertain/PONTO_A/BOAALB/clip.wav
```

- The file name **receives every label added beyond the prediction**, in the
  order in which they were selected, with spaces written as `_` (`chuva forte`
  becomes `_chuva_forte`). The original name is kept in full before them. When no
  label is added (a plain Correct, or an Incorrect with no label from the list),
  and for every segment marked Uncertain, the name is left unchanged.
- With `--label-depth`, the folders *below* the label are **not** recreated:
  `BOAALB/PONTO_A/20240115/clip.wav` corrected to TURDRU becomes
  `incorrect/BOAALB/clip_TURDRU.wav`, with one folder per predicted label
  containing the clips directly.
- A clip that arrived **without a label** has no prediction to assess. It is
  filed under `labelled/`, keeping the folders it was in, and every label
  assigned to it is appended to its name.
- The folder names are the same in every interface language.
- A name that already exists receives a `_2`, `_3`, … suffix; a reviewed file is
  never overwritten.
- The folder from which a clip was taken is **removed once its last clip has
  been filed**, together with any parent folder that becomes empty, so the tree
  of pending segments shrinks as the review progresses. A folder that still
  contains anything, whether a pending clip or another file, is preserved, and
  the segments folder itself is never removed.
- Clips already in `correct/`, `incorrect/`, `uncertain/` or `labelled/` are
  excluded from the pending list, so a review can be spread over several
  sessions.

**Writing to another location.** `--output` (or `-o`) places the verdict folders
and the review log in a folder of the reviewer's choice instead of the segments
folder, leaving the collection under review unchanged:

```bash
segment-reviewer /data/segments --output /data/reviewed
```

A relative path is resolved against the segments folder (`-o reviewed` refers to
`/data/segments/reviewed/`), an absolute path is used as given, and over SSH the
path refers to the remote machine. The annotation table is written to the same
folder unless `--annotations-path` specifies otherwise. To resume a review, the
same `--output` should be given again: that folder is where the counts of
segments already reviewed are taken, and clips already written there are never
returned to the pending list.

### The review log

Every review adds one row to **`reviews.csv`**, next to the verdict folders. The
log is always written and constitutes the record of the review:

| Column | Content |
| --- | --- |
| `reviewed_at` | Date and time of the review, with the time zone |
| `source`, `destination` | The original location of the clip, relative to the segments folder, and its new location, relative to the output folder |
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

### The annotation table

With `--annotations`, every label that a segment is **confirmed to contain** is
added to a CSV file with the columns `site, file, label, start_time, end_time`,
one row per label, so a segment containing two species produces two rows. A
rejected prediction never appears in the table, nor do segments marked uncertain
or found to contain no label from the list. The times give the position of the
clip within the recording from which it was cut; they are read from its name and
extended to the actual duration of the clip, so that any padding is included.

`file` names that source recording. Since the name of a clip rarely identifies
the recording from which it was cut, the recording is looked up in an optional
`segment_sources.csv` (`segment,recording`) in the segments folder. Without that
file the column is left empty, and the interface reports this below the buttons.

Rows are written as each segment is reviewed, and an existing table is extended,
so reviews spread over several sessions accumulate in the same table.

---

## Reading other naming conventions

Names that do not match the pattern can still be reviewed; the interface
displays less information about them, and nothing that it cannot read reliably.
To display the site, the time, the window and the score, `--filename-pattern`
must describe how the names are built.

### Writing a template

The simpler form is to **write the name out, with its parts named in brackets**.
Everything outside the brackets is matched literally.

```bash
# PONTO_A_20240115T053000_REC_12.0_17.0_BOAALB_0.873.wav
segment-reviewer ~/segments \
    --filename-pattern '[site]_YYYYMMDDTHHMMSS_REC_[start_time]_[end_time]_[label]_[score]'
```

| In a template | Matches |
| --- | --- |
| `[site]`, `[label]` | free text, which may contain underscores |
| `YYYYMMDD`, `HHMMSS` | the date and the time, written as shown or as `[date]` and `[time]` |
| `[datetime]` | the date and time together, in any format, to be used with `--datetime-format` |
| `[start_time]`, `[end_time]` | the window of the clip within the recording, in seconds |
| `[score]` | a similarity or confidence value |
| `[extra]` | any remaining text, displayed in the interface as *Other* |
| `*` | any text, which is not captured |
| any other text | itself, literally |

Every placeholder is optional, but the template must match the **entire** name.
A partial match would fill the interface with information read from the wrong
parts of the name, so it is treated as no match. An unknown placeholder, such as
the misspelling `[speceis]`, is rejected at start-up rather than ignored.

### Writing a regular expression

For names that no template can describe, `--filename-pattern` also accepts **any
regular expression with named groups**: `site`, `date`, `time`, `datetime`,
`start`, `end`, `label`, `score` and `extra`. All of them are optional, and the
expression is matched against the name without its extension:

```bash
# label first, then site, then a 12-digit timestamp: BOAALB-siteA-202401150530.wav
segment-reviewer ~/segments \
    --filename-pattern '^(?P<label>[A-Z]+)-(?P<site>\w+)-(?P<datetime>\d{12})$' \
    --datetime-format '%Y%m%d%H%M'
```

### Source of the label

`--label-from` selects the source: `folder` (the default), `filename` (the
`label` group of the pattern) or `none`. A pattern that captures a `label` group
selects `filename` automatically unless `--label-from` states otherwise. In that
mode the clip is filed directly under its outcome and its predicted label, for
example `incorrect/BOAALB/clip_TURDRU.wav`.

To keep the folders instead, the folder source must be requested explicitly. For
segments organised as `[label]/[site]_YYYYMMDD/clip.wav`, the following command
reads the label from the top folder, keeps the site folder below it, and still
reads the site, times and score from the name:

```bash
segment-reviewer ~/segments \
    --filename-pattern '[site]_YYYYMMDDTHHMMSS_REC_[start_time]_[end_time]_[label]_[score]' \
    --label-from folder --label-depth 1
```

### The vector-search preset

`--filename-pattern vector-search` reads names of the form
`SITE_YYYYMMDD_HHMMSS_START-ENDs_SCORE_LABEL.wav`, as written by the bioacoustic
vector-search notebooks, with the **label and the similarity score in the
name**:

```bash
segment-reviewer ~/vector_search_segments --filename-pattern vector-search --annotations
```

Because the label is part of the name, clips are filed directly under their
outcome and predicted label (`correct/BOAALB/`, `incorrect/BOAALB/`), and the
labels added are appended to the name as in every other case: a segment named
`..._0.873_BOAALB.wav` and corrected to TURDRU becomes
`incorrect/BOAALB/..._0.873_BOAALB_TURDRU.wav`. The score is displayed next to
the label in the interface and is also recorded in the log.

---

## Reviewing segments over SSH

When a remote folder is given, every operation is carried out over SFTP: listing
the folder, reading clips, moving them into the verdict folders and writing the
log and the annotation table. Clips are cached locally as they are opened, so
returning to a previous clip does not require downloading it again.

```bash
segment-reviewer ssh://user@fieldserver:22/data/segments
segment-reviewer fieldserver:/data/segments          # scp-style address
segment-reviewer ssh://fieldserver/data/segments --ssh-key ~/.ssh/id_field
```

Host aliases, users, ports and identity files from `~/.ssh/config` are applied,
and an SSH agent is used when one is running. An unknown host key is rejected
unless `--accept-new-host-key` is given.

Nothing is written outside the segments folder and the output folder, and no
clip is ever deleted: files are only moved within those folders.

---

## Running on a server

The interface is an ordinary web page, so the tool can run on the machine that
holds the audio and be used from any other:

```bash
segment-reviewer /data/segments --host 0.0.0.0 --port 8765 --no-open
```

When a non-loopback address is bound, an **access token** is generated and
included in the printed address; once that address has been opened, the token is
stored in a cookie. `--token mysecret` sets the token explicitly, and `--no-auth`
serves the interface without one.

The token prevents casual access but does not provide encryption (TLS). Anyone
holding it can open and review (and therefore move clips in) any folder the
reviewer can read, and can list the folder names of that machine. The token
should therefore be treated as a password, and `--no-auth` should be avoided on
shared networks. On untrusted networks, Tailscale (binding to the Tailscale
address, or to `0.0.0.0` on a machine reachable only through the tailnet) or an
SSH tunnel is recommended:

```bash
# on the server
segment-reviewer /data/segments --port 8765 --no-open
# on the local computer
ssh -N -L 8765:127.0.0.1:8765 user@server   # then open http://127.0.0.1:8765
```

The tool supports one reviewer at a time. The pending list, the current position
and the open folder are held by the server, so two browsers connected to the same
instance control the same session; a folder opened in one is opened in both.

---

## Options

```
segment-reviewer [SEGMENTS] [OPTIONS]

  SEGMENTS                      Folder to open at start-up: a local path, or
                                ssh://[user@]host[:port]/path. Optional; a folder
                                can be opened, and changed, in the browser

  -l, --lang TEXT               Interface language at start-up: en, pt-BR  [default: en]
      --labels TEXT             The only labels offered, separated by commas.
                                Replaces a stored list
      --labels-file TEXT        Location of the label list, one label per line
                                [default: <SEGMENTS>/labels.txt]
      --no-labels-file          Do not read or write the list; changes last for the session
      --label-from TEXT         Source of the label: folder, filename or none
                                [default: folder]
      --label-depth INTEGER     Folder level that carries the label, counting down
                                from SEGMENTS: 1 for LABEL/SITE/clip.wav; 0 is the
                                folder containing the clip  [default: 0]
      --filename-pattern TEXT   'default', 'vector-search', a template such as
                                '[site]_YYYYMMDD_HHMMSS_[label]_[score]', or a regular
                                expression with the named groups site, date, time,
                                datetime, start, end, label, score, extra
                                [default: default]
      --datetime-format TEXT    strptime format of the captured date and time
                                [default: %Y%m%d%H%M%S]
      --no-multi-label          Restrict each segment to one label (several labels
                                per segment are allowed by default)
      --annotations             Also write the annotation table of confirmed labels
      --annotations-path TEXT   Location of the table  [default: <output>/annotations.csv]

      --spec-type [mel|fft|log] Initial frequency axis: mel scale, linear Hz or
                                logarithmic Hz  [default: mel]
      --fmin INTEGER            Initial minimum frequency, in Hz  [default: 0]
      --fmax INTEGER            Initial maximum frequency, in Hz; 0 = Nyquist  [default: 0]
      --db-floor INTEGER        Initial lower limit of the colour scale, in dB  [default: -80]

  -o, --output TEXT             Folder to which the reviewed segments and
                                reviews.csv are written  [default: the segments folder]

      --host TEXT               Address to bind  [default: 127.0.0.1]
  -p, --port INTEGER            Port  [default: 8765]
      --token TEXT              Access token for the interface
      --no-auth                 Serve the interface without an access token
      --open / --no-open        Open a browser at start-up  [default: open]

      --ssh-user / --ssh-port / --ssh-key / --ssh-password
      --known-hosts TEXT        Additional known_hosts file to trust
      --accept-new-host-key     Accept an unknown SSH host key
      --cache-dir TEXT          Location of the local cache of remote clips
                                [default: a temporary folder]

      --version                 Show the version and exit
```

### Verdict folders and language

The verdict folders are always named `correct/`, `incorrect/`, `uncertain/` and
`labelled/`, and the review log always records those outcome names, whatever the
interface language. The data written by a review therefore never depends on the
language in which it was carried out.

---

## Development

```bash
uv venv && uv pip install -e ".[dev]"
uv run pytest
```

The test suite covers the naming rules, the filing of reviewed clips, the HTTP
API, the interface texts in both languages and a complete review carried out over
an in-process SFTP server. The client's DOM-independent helpers are tested with
Node.js, and those tests are skipped when Node.js is not installed.

Before pushing, the suite should also be run as the continuous integration runs
it:

```bash
GITHUB_ACTIONS=true uv run pytest
```

Rich colours the Typer help output whenever it detects a terminal, which it
always does on GitHub Actions. This changes the rendered output enough to break a
test that passes locally.

## Licence

MIT; see [LICENSE](LICENSE).

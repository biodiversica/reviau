# Segment Reviewer

[Português (Brasil) →](README.pt-BR.md)

A command-line tool that serves a **browser GUI for reviewing a folder of audio
segments**. Each clip is shown as a spectrogram with whatever its folder and file
name say about it; you listen to it and say **what is in it**. Whether the label
it came with was **correct** or **wrong** follows from that answer. Reviewed
clips are moved into `correct/`, `wrong/` or `unsure/`, every review is logged to
`reviews.csv` — prediction, outcome and what was really heard — and the confirmed
labels can be written to an annotation table.

It works on any collection of clips, however they were produced — a detector's
output, hand-cut examples, a classifier's predictions to be validated. The
segments folder can be **local** or **remote over SSH**, and the GUI can be
served to **another machine** on your LAN or Tailscale network. The interface is
available in **English** and **Português (Brasil)**.

---

## How a segment is read

Two independent sources, both configurable:

**The folder gives the label.** A reviewed collection is normally organised one
folder per class, so the folder a clip sits in is the label it currently carries:

```
segments/
├── PONTO_A/BOAALB/PONTO_A_20240115_053000_12.0_17.0_det1.wav   → label BOAALB
├── PONTO_A/PHYLUT/PONTO_A_20240115_061500_3.5_8.5_det2.wav     → label PHYLUT
└── chuva/POCA_20240116_200000_5.0_10.0_det4.wav                → label chuva
```

Any folders above the label are kept as they are — `2024/campo/PONTO_A/BOAALB/`
labels the clip `BOAALB` and remembers the three folders above it. A clip sitting
directly in the segments folder simply has no label yet.

**Class folder on top?** Some collections are filed the other way round, with the
sites *inside* each class folder. Say which level carries the label with
`--label-depth`, counting down from the segments folder. The folders below it
are read through and then let go — they are not offered as labels, and a verdict
files the clip under the label alone, since the site and the day are in the file
name already:

```
segments/                          # --label-depth 1
├── BOAALB/PONTO_A/20240115/clip.wav  → label BOAALB, the two folders below it dropped
├── BOAALB/POCA/clip.wav              → label BOAALB
└── PHYLUT/clip.wav                   → label PHYLUT (shallower than the depth, still labelled)
```

**The file name gives the rest.** By default it is read as

```
[site]_[YYYYMMDD]_[HHMMSS]_[start]_[end]_*
     PONTO_A_20240115_053000_12.0_17.0_det1.wav
```

- `site` may contain underscores — the match is anchored on the date and time.
- `start`/`end` are the clip's position, in seconds, inside the recording it was
  cut from. Both separators work: `12.0_17.0` and `12.0-17.0s`.
- `_*` is anything else, shown in the GUI as *extra*.
- Every part after the site is optional, and **a name that matches nothing at all
  is still perfectly reviewable** — the GUI just shows less about it.

Named some other way? Write the shape out with `--filename-pattern` — see
[Reading other naming conventions](#reading-other-naming-conventions).

---

## Install

### With [uv](https://docs.astral.sh/uv/) (recommended)

Run it without installing anything permanently:

```bash
uvx --from git+https://github.com/biodiversica/segment-reviewer segment-reviewer /path/to/segments
```

Or install it as a tool:

```bash
uv tool install git+https://github.com/biodiversica/segment-reviewer
segment-reviewer /path/to/segments
```

From a clone, for development:

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

Python 3.10 or newer. The audio stack (librosa, soundfile) needs `libsndfile`,
which ships with the wheels on Linux, macOS and Windows.

---

## Use

```bash
# Start with no folder and open one from the browser
segment-reviewer

# Open a local folder straight away, GUI on this machine
segment-reviewer ~/segments

# Portuguese interface, a fixed set of drop-down labels, annotation table
segment-reviewer ~/segments --lang pt-BR --labels "BOAALB, PHYLUT, chuva" --annotations

# Segments on a server, reviewed from your laptop
segment-reviewer ssh://user@fieldserver/data/segments

# Serve the GUI to the network (LAN, Tailscale, …)
segment-reviewer /data/segments --host 0.0.0.0 --port 8765
```

The command prints a summary and the URL to open. With `--host 0.0.0.0` it also
prints the address other machines should use.

### Opening a folder

The **folder box** at the top of the page says which segments folder is under
review. Type another path and press <kbd>Enter</kbd> — or **Browse…** to click
through the folders — and that folder is opened in place of the current one,
without restarting the command. Started without a `SEGMENTS` folder, the page
opens on the folder box alone.

- It takes the same paths the command line does: a local folder, `~/…`, or
  `ssh://user@host/path` for a remote one, connected with the command line's SSH
  settings (`--ssh-key`, `~/.ssh/config`, the agent, …).
- Every folder opened gets the options the command was started with — the
  filename pattern, `--label-depth`, `--output`, `--labels`, `--annotations`.
- **Opening a folder writes nothing to it.** The verdict folders, the review log
  and the label list are created with the first segment reviewed, so a folder
  opened by mistake — a typo, a level too high — is left exactly as it was. Open
  the right one and carry on.
- A folder that cannot be opened is refused with the reason, and the review on
  screen carries on.
- **Browse…** lists the folders of the machine the reviewer runs on — the one
  that reads the clips, which is not the browser's when the GUI is served to
  another machine. Folders holding clips are marked ♪. Remote `ssh://` folders
  are typed, not browsed.
- The folders opened recently are offered as you type (kept in this browser).
- When a filename pattern reads few of the names in the folder just opened, a
  line under the folder box says so, with one name it missed.

### In the browser

| Control | What it does |
| --- | --- |
| **Label buttons** | Anything *else* in this clip — or what it really is. Every segment starts with none selected; click to pick a label, click again to drop it. The prediction's own button is marked **◆ predicted** and locked: it is answered by Correct or Wrong, not by clicking it. <kbd>1</kbd>…<kbd>9</kbd> hit the first nine. |
| **✔ Correct** | The prediction is right. Saved as the prediction plus any label selected — a second species singing too. The button says what it will save: *✔ Correct + PHYLUT*. |
| **✘ Wrong** | The prediction is wrong. Saved as the labels selected — what the clip really is — or, with none, as holding nothing on the list. The button says which: *✘ Wrong → TURDRU*, *✘ Wrong · nothing on the list*. |
| **? Unsure** | Cannot tell. Filed under `unsure/`, kept out of the correct/wrong tallies and out of the annotation table. |
| **← Prev / Next →** | Browse without making a decision. |
| **Type / Min Hz / Max Hz / dB floor** | Redraw the spectrogram instantly — mel, linear-Hz or log-Hz frequency axis. The audio player is not touched, so a clip keeps playing while you change the view. |
| **✎** | Edit the label list itself: each button grows a **×** to drop it, and the box below adds a new one. Changes are saved to `labels.txt` in the segments folder. |
| **⟳** | Re-read the folder, e.g. after more segments arrive. |
| **Language** | Switch the interface between English and Português. |
| **◐ / ☀ / ☾** | Theme: follow the system, light, or dark — click to cycle. A chosen theme is remembered in this browser. The spectrogram keeps its colours in both. |

The prediction is the question, and Correct or Wrong is the answer; the label
buttons only add what else is there. Nothing is ever pre-selected, so a segment
rejected without a second thought is saved as "nothing on the list" — never with
a label left over from the clip before. With no prediction to judge, a single
**✔ Save** button files the labels selected. The server works the outcome out
again from the labels it receives — one rule, in one place:

| Labels saved | Outcome |
| --- | --- |
| the prediction | correct |
| the prediction and others | correct (the others are logged as *added*) |
| other labels only | wrong, and the clip is really those |
| nothing | wrong, and the clip holds nothing on the list |
| anything, with Unsure | unsure |

Several labels can be given to one segment — two species singing at once — which
is the default; `--no-multi-label` restricts each segment to one.

Keyboard: <kbd>←</kbd> <kbd>→</kbd> to browse, <kbd>T</kbd> / <kbd>F</kbd> /
<kbd>U</kbd> for correct / wrong / unsure, <kbd>1</kbd>…<kbd>9</kbd> to toggle
the first nine labels, <kbd>Space</kbd> to play or pause.

### The label list

The buttons come from a list kept in **`labels.txt`** in the segments folder, one
label per line. The first time a collection is opened the list is seeded from the
labels the collection already uses, and written out with the first segment
reviewed; from then on that file *is*
the list, and you edit it from the GUI (or by hand — blank lines and `#` comments
are ignored).

Starting with `--labels` says what to offer instead: those are the only buttons
the session opens with, replacing whatever the file holds, and they are written
out in its place.

Nothing is ever added back behind your back: a rescan that finds a new folder
does not push its name onto the list. Trimming the list is safe, too — a clip's
own label always shows as a button whether or not it is on the list, and typing a
name into the box both adds it to the list and picks it for the segment on screen.

Use `--labels-file` to keep the list somewhere else, or `--no-labels-file` to make
edits last only for the session.

### Where a review puts a clip

A reviewed clip is filed under its **outcome**, then the path it had — the
**prediction's** folder included. Each folder answers one question:
`wrong/PONTO_A/BOAALB/` holds exactly the clips the model called BOAALB and got
wrong, so counting a folder is that class's precision. The labels you added go
on the end of the file name, so the tree reads without opening the log:

```
PONTO_A/BOAALB/clip.wav
   ├── ✔ Correct                 →  correct/PONTO_A/BOAALB/clip.wav
   ├── ✔ Correct, + PHYLUT       →  correct/PONTO_A/BOAALB/clip_PHYLUT.wav
   ├── ✘ Wrong, really TURDRU    →  wrong/PONTO_A/BOAALB/clip_TURDRU.wav
   ├── ✘ Wrong, TURDRU + PHYLUT  →  wrong/PONTO_A/BOAALB/clip_TURDRU_PHYLUT.wav
   ├── ✘ Wrong, nothing          →  wrong/PONTO_A/BOAALB/clip.wav
   └── ? Unsure                  →  unsure/PONTO_A/BOAALB/clip.wav
```

- A file name **gains every label added beyond the prediction**, in the order
  they were selected, with spaces written as `_` (`chuva forte` → `_chuva_forte`).
  The original name is kept whole in front of them. With nothing added — a plain
  Correct, or a Wrong holding nothing on the list — and for anything marked
  Unsure, the name is left exactly as it was found.
- Under `--label-depth`, the folders *below* the label are **not** rebuilt:
  `BOAALB/PONTO_A/20240115/clip.wav` corrected to TURDRU becomes
  `wrong/BOAALB/clip_TURDRU.wav` — one folder per predicted label, holding the
  clips themselves.
- A clip that came with **no label** has no prediction to be right or wrong
  about: it is filed under `labelled/`, keeping the folders it sat in, and every
  label given goes on its name.
- The folder names are the same in every interface language.
- A name collision gets a `_2`, `_3`, … suffix — a reviewed file is never
  overwritten.
- The folder a clip came from is **removed once its last clip leaves**, along
  with any parent it empties, so the pending tree shrinks as the review goes on.
  A folder still holding anything — a pending clip, a stray file — is left alone,
  and the segments folder itself is never removed.
- Clips already inside `correct/`, `wrong/`, `unsure/` or `labelled/` are
  excluded from the pending list, so a review can be spread over several sessions.

**Writing somewhere else.** `--output` (or `-o`) puts the verdict folders and the
review log in a folder of your choosing instead of the segments folder, leaving
the collection you are reviewing untouched:

```bash
segment-reviewer /data/segments --output /data/reviewed
```

A relative path is read against the segments folder (`-o reviewed` →
`/data/segments/reviewed/`), an absolute one is taken as given, and over SSH it
is a path on the remote machine. The annotation table follows it too, unless
`--annotations-path` says otherwise. Pass the same `--output` again to resume a
review: that is where the "already correct/wrong" tallies are counted, and clips
already written there are never handed back as pending.

### The review log

Every review appends one row to **`reviews.csv`**, beside the verdict folders.
It is always written, and it is the record of the review:

| Column | Holds |
| --- | --- |
| `reviewed_at` | When, with the time zone |
| `source`, `destination` | Where the clip was, relative to the segments folder, and where it went, relative to the output folder |
| `predicted`, `score` | The label the clip came with, and the score its name carried |
| `outcome` | `correct`, `wrong`, `unsure` or `labelled` |
| `labels` | What the reviewer says the clip holds, `;`-separated; empty for nothing on the list |
| `added` | Those labels other than the prediction: the correction, or a second species |
| `site`, `recording`, `start_time`, `end_time` | As in the annotation table below |

Per-class precision is `correct / (correct + wrong)` grouped by `predicted`, and
`predicted` against `labels` for the wrong rows is the confusion between classes.
If the log cannot be written, the clip is moved back and the review is refused —
a clip is never filed without its row.

### The annotation table

With `--annotations`, every label a segment is **confirmed to hold** is appended
to a CSV with columns `site, file, label, start_time, end_time` — one row per
label, so a segment with two species gives two rows. A rejected prediction never
appears in it, and neither do clips marked unsure or found to hold nothing on the
list. The times are the clip's position inside the recording it was cut from,
taken from its name and widened to the clip's real duration (so any padding is
included).

`file` names that source recording. A clip's own name rarely says which recording
it came from, so it is looked up in an optional `segment_sources.csv`
(`segment,recording`) beside the segments; without one the column is left empty
and the GUI says so under the buttons.

Rows are written as each segment is reviewed, and an existing table is appended to,
so reviews spread over several sessions add up.

---

## Reading other naming conventions

Names that do not match are still perfectly reviewable — the GUI just shows less
about them, and shows nothing it is unsure of. To get the site, the time, the
window and the score back, tell `--filename-pattern` how the name is built.

### Writing a template

The easy form: **write the name out, with its parts named in brackets.**
Everything outside the brackets is matched literally.

```bash
# PONTO_A_20240115T053000_REC_12.0_17.0_BOAALB_0.873.wav
segment-reviewer ~/segments \
    --filename-pattern '[site]_YYYYMMDDTHHMMSS_REC_[start_time]_[end_time]_[label]_[score]'
```

| In a template | Matches |
|---|---|
| `[site]`, `[label]` | free text — may contain underscores |
| `YYYYMMDD`, `HHMMSS` | the date and the time, written bare or as `[date]`/`[time]` |
| `[datetime]` | both at once, in whatever shape — pair it with `--datetime-format` |
| `[start_time]`, `[end_time]` | the clip's window in the recording, in seconds |
| `[score]` | a similarity or confidence number |
| `[extra]` | anything left, shown in the GUI as *extra* |
| `*` | anything, not captured |
| anything else | itself, literally |

Every placeholder is optional, but the template must match the **whole** name —
a half-match would fill the GUI with facts read off the wrong tokens, so it is
treated as no match at all. A typo like `[speceis]` is refused at startup rather
than silently ignored.

### Writing an expression

For shapes no template describes, `--filename-pattern` still takes **any regular
expression with named groups** — `site`, `date`, `time`, `datetime`, `start`,
`end`, `label`, `score`, `extra`, all optional, matched against the name without
its extension:

```bash
# label first, then site, then a 12-digit timestamp: BOAALB-siteA-202401150530.wav
segment-reviewer ~/segments \
    --filename-pattern '^(?P<label>[A-Z]+)-(?P<site>\w+)-(?P<datetime>\d{12})$' \
    --datetime-format '%Y%m%d%H%M'
```

### Where the label comes from

`--label-from` chooses: `folder` (the default), `filename` (the pattern's `label`
group), or `none`. A pattern that captures a `label` group switches to `filename`
on its own unless you say otherwise — and in that mode the clip is filed flat,
under its outcome and its predicted label: `wrong/BOAALB/clip_TURDRU.wav`.

To keep the folders instead, say so. With segments filed as
`[label]/[site]_YYYYMMDD/clip.wav`, this reads the label off the top folder,
keeps the site folder under it, and still takes the site, times and score from
the name:

```bash
segment-reviewer ~/segments \
    --filename-pattern '[site]_YYYYMMDDTHHMMSS_REC_[start_time]_[end_time]_[label]_[score]' \
    --label-from folder --label-depth 1
```

### The vector-search preset

`--filename-pattern vector-search` reads
`SITE_YYYYMMDD_HHMMSS_START-ENDs_SCORE_LABEL.wav`, the names the bioacoustic
vector-search notebooks write, with the **label and similarity score in the name**:

```bash
segment-reviewer ~/vector_search_segments --filename-pattern vector-search --annotations
```

Because the label lives in the name there, clips are filed flat under their
outcome and predicted label — `correct/BOAALB/`, `wrong/BOAALB/` — and the
labels added go on the end of the name as anywhere else: a segment called
`..._0.873_BOAALB.wav` and corrected to TURDRU becomes
`wrong/BOAALB/..._0.873_BOAALB_TURDRU.wav`. The score is shown next to the label
in the GUI, and logged too.

---

## Reviewing segments over SSH

Point the tool at a remote folder and it does everything over SFTP — listing,
reading clips, moving them into the verdict folders, writing the annotation
table. Clips are cached locally as they are opened, so scrolling back is instant.

```bash
segment-reviewer ssh://user@fieldserver:22/data/segments
segment-reviewer fieldserver:/data/segments          # scp-style
segment-reviewer ssh://fieldserver/data/segments --ssh-key ~/.ssh/id_field
```

Host aliases, users, ports and identity files from `~/.ssh/config` are honoured,
and an SSH agent is used when one is running. An unknown host key is refused
unless you pass `--accept-new-host-key`.

Nothing is written outside the segments folder, and no clip is deleted — files
are only moved between subfolders of the folder you named.

---

## Running on a server

The GUI is a normal web page, so the tool can run wherever the audio is and be
used from anywhere:

```bash
segment-reviewer /data/segments --host 0.0.0.0 --port 8765 --no-open
```

When you bind a non-loopback address, an **access token** is generated and
embedded in the printed URL; open that URL once and the token is stored in a
cookie. Pass `--token mysecret` to choose it, or `--no-auth` to serve without one.

The token keeps a casual passer-by out of your files; it is not TLS. Whoever
holds it can open — and review, which moves clips — any folder the reviewer can
read, and browse that machine's folder names, so treat it like a password and
think twice before `--no-auth` on a shared network. On an
untrusted network, prefer Tailscale (bind to the Tailscale address, or to
`0.0.0.0` with the machine only reachable over the tailnet) or an SSH tunnel:

```bash
# on the server
segment-reviewer /data/segments --port 8765 --no-open
# on your laptop
ssh -N -L 8765:127.0.0.1:8765 user@server   # then open http://127.0.0.1:8765
```

One reviewer at a time: the pending list, the current position and the folder
open live in the server, so two browsers pointed at the same instance drive the
same session — opening a folder in one opens it in both.

---

## Options

```
segment-reviewer [SEGMENTS] [OPTIONS]

  SEGMENTS                      Folder to open at start: a local path, or
                                ssh://[user@]host[:port]/path. Optional — a
                                folder can be opened, and changed, in the browser

  -l, --lang TEXT               Interface language at start: en, pt-BR  [default: en]
      --labels TEXT             The only labels offered, comma-separated. Replaces a
                                stored list
      --labels-file TEXT        Where the label list is kept, one per line
                                [default: <SEGMENTS>/labels.txt]
      --no-labels-file          Do not read or write it; edits last for this session
      --label-from TEXT         Where a segment's label is read from: folder, filename
                                or none  [default: folder]
      --label-depth INTEGER     Which folder carries the label, counting down from
                                SEGMENTS: 1 for LABEL/SITE/clip.wav. 0 is the folder
                                the clip sits in  [default: 0]
      --filename-pattern TEXT   'default', 'vector-search', a template such as
                                '[site]_YYYYMMDD_HHMMSS_[label]_[score]', or a regex
                                with the named groups site, date, time, datetime,
                                start, end, label, score, extra  [default: default]
      --datetime-format TEXT    strptime format for the captured date and time
                                [default: %Y%m%d%H%M%S]
      --no-multi-label          Restrict each segment to one label (several labels
                                per segment are allowed by default)
      --annotations             Also write the annotation table of confirmed labels
      --annotations-path TEXT   Where it lives  [default: <SEGMENTS>/annotations.csv]

      --spec-type [mel|fft|log] Initial frequency axis: mel scale, linear Hz, or
                                logarithmic Hz  [default: mel]
      --fmin INTEGER            Initial minimum frequency, Hz  [default: 0]
      --fmax INTEGER            Initial maximum frequency, Hz; 0 = Nyquist  [default: 0]
      --db-floor INTEGER        Initial dB floor  [default: -80]

  -o, --output TEXT             Folder the reviewed segments and reviews.csv are
                                written to  [default: the segments folder]

      --host TEXT               Address to bind  [default: 127.0.0.1]
  -p, --port INTEGER            Port  [default: 8765]
      --token TEXT              Access token for the GUI
      --no-auth                 Serve without an access token
      --open / --no-open        Open a browser on start  [default: open]

      --ssh-user / --ssh-port / --ssh-key / --ssh-password
      --known-hosts TEXT        Extra known_hosts file to trust
      --accept-new-host-key     Accept an unknown SSH host key
      --cache-dir TEXT          Where remote clips are cached  [default: a temp folder]

      --version                 Show the version and exit
```

### Verdict folders and language

The verdict folders are always `correct/`, `wrong/`, `unsure/` and `labelled/`,
and the review log always writes those outcome names, whichever language the
interface is in — the data a review writes never depends on who reviewed it.

---

## Development

```bash
uv venv && uv pip install -e ".[dev]"
uv run pytest
```

The suite covers the naming rules, the verdict layouts, the HTTP API and a full
review driven over an in-process SFTP server. The client's DOM-free helpers run
under node, and skip themselves when node is not installed.

Before pushing, it is worth one run as CI sees it:

```bash
GITHUB_ACTIONS=true uv run pytest
```

Rich colours Typer's help whenever it believes it is on a terminal, and it always
believes so on GitHub Actions — which changes the rendered output enough to break
a test that passes locally.

## License

MIT — see [LICENSE](LICENSE).

# Reading Settings

*English · [Português (Brasil)](../pt-BR/reading-settings.md)*

How the file names and folders of a collection are read
([How a Segment Is Read](segments.md)) is a property of the collection, so it is
set per folder, from the **⚙** button next to the folder box, rather than on the
command line. The settings are saved in **`settings.json`** in the
[`reviau/` folder](reviau-folder.md), so a folder reopens with its own settings
on any machine and in any browser. As with the label list, the file is written
only when settings are applied, never when a folder is merely opened.

| Setting | Function |
| --- | --- |
| **Filename pattern** | How file names are read: the *default* pattern, the *vector search* preset, or a custom template or regular expression, described below |
| **Date-time format** | The `strptime` format of the captured date and time (by default `%Y%m%d%H%M%S`) |
| **Label source** | *Automatic* (the file name when the pattern captures a label, otherwise the folder), *Folder*, *File name* or *None* |
| **Label depth** | The folder level that carries the label, counting down from the segments folder: 0 is the folder containing the clip, 1 the first folder below the segments folder |

While the settings are edited, a **preview** shows how many of the pending names
the pattern recognises and what it reads from the first few: label, site, date,
window and score. Settings that cannot be used, such as a template with an
unknown placeholder, are reported with the reason, and **Apply** remains
unavailable until they are corrected. Applying the settings saves them and
reopens the folder with them.

Names that do not match the pattern can still be reviewed; the interface
displays less information about them, and nothing that it cannot read reliably.
When a folder is opened, a notice below the folder box reports any names that
the pattern does not recognise.

## Writing a Template

The simpler form of custom pattern is to **write the name out, with its parts
named in brackets**. Everything outside the brackets is matched literally. For
names such as `PONTO_A_20240115T053000_REC_12.0_17.0_BOAALB_0.873.wav`:

```
[site]_YYYYMMDDTHHMMSS_REC_[start_time]_[end_time]_[label]_[score]
```

| In a template | Matches |
| --- | --- |
| `[site]`, `[label]` | free text, which may contain underscores |
| `YYYYMMDD`, `HHMMSS` | the date and the time, written as shown or as `[date]` and `[time]` |
| `[datetime]` | the date and time together, in any format, described by the date-time format |
| `[start_time]`, `[end_time]` | the window of the clip within the recording, in seconds |
| `[score]` | a similarity or confidence value |
| `[extra]` | any remaining text, displayed in the interface as *Other* |
| `*` | any text, which is not captured |
| any other text | itself, literally |

Every placeholder is optional, but the template must match the **entire** name.
A partial match would fill the interface with information read from the wrong
parts of the name, so it is treated as no match. An unknown placeholder, such as
the misspelling `[speceis]`, is rejected rather than ignored.

## Writing a Regular Expression

For names that no template can describe, the custom pattern also accepts **any
regular expression with named groups**: `site`, `date`, `time`, `datetime`,
`start`, `end`, `label`, `score` and `extra`. All of them are optional, and the
expression is matched against the name without its extension. For names such as
`BOAALB-siteA-202401150530.wav`, with the label first and a 12-digit timestamp:

```
^(?P<label>[A-Z]+)-(?P<site>\w+)-(?P<datetime>\d{12})$
```

with the date-time format `%Y%m%d%H%M`.

## Source of the Label

With the *Automatic* source, a pattern that captures a `label` group reads the
label from the file name, and any other pattern reads it from the folder. When
the label is read from the file name, the clip is filed directly under its
outcome and its predicted label, for example `incorrect/BOAALB/clip_TURDRU.wav`.

To keep the folders instead, the *Folder* source must be selected explicitly. For
segments organised as `[label]/[site]_YYYYMMDD/clip.wav`, the *Folder* source
with label depth 1 reads the label from the top folder and keeps the site folder
below it, while the site, times and score are still read from the name.

## The Vector-Search Preset

The *vector search* preset reads names of the form
`SITE_YYYYMMDD_HHMMSS_START-ENDs_SCORE_LABEL.wav`, as written by the bioacoustic
vector-search notebooks, with the **label and the similarity score in the
name**.

Because the label is part of the name, clips are filed directly under their
outcome and predicted label (`correct/BOAALB/`, `incorrect/BOAALB/`), and the
labels added are appended to the name as in every other case: a segment named
`..._0.873_BOAALB.wav` and corrected to TURDRU becomes
`incorrect/BOAALB/..._0.873_BOAALB_TURDRU.wav`. A segment confirmed as BOAALB
keeps its name, `correct/BOAALB/..._0.873_BOAALB.wav`, since the prediction is
already at its end. The score is displayed next to the label in the interface
and is also recorded in the log.

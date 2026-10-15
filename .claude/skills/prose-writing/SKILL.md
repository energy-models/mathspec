---
name: prose-writing
description: House rules for any prose written in this project, aiming at Simplified Technical English (ASD-STE100) — the reader, concrete sentences, and the words to use. Use when writing or editing a Markdown page, AGENTS.md, a PR title or body, an issue, a review comment, a commit message, or an exception, warning or log message in the code.
---

# Writing prose here

These rules apply to every Markdown page, to `AGENTS.md` and
[CONTRIBUTING.md](../../../CONTRIBUTING.md), to PR titles and bodies, issues,
comments and commit messages, and to every exception, warning, advice and log
message in `src/` and `tools/`. A documentation page also follows
[the docs-writing skill](../docs-writing/SKILL.md). The layout of a PR body, a
PR title and an issue is in `AGENTS.md`; this skill sets how their sentences
read.

Write the way the Python packages that NumFOCUS sponsors write their docs:
plain declarative sentences that answer a question. Aim for Simplified
Technical English (ASD-STE100) in the words: short common words, one meaning
per word, and the active voice. Do not follow it so strictly that the text
loses the words that join one idea to the next. A reader follows "because",
"so" and "which", and stalls on a list of bare claims. In conversation, keep
the same plainness, and put the emphasis on explaining technical subjects and mathematics so that the user
understands them.

## The reader

The reader of a page is a modeller who writes YAML, and who has read no other
page in this repository. They came to find out what the language accepts, and
what happens if they write X. A sentence that does not move that answer forward
is cut, however true it is.

The reader of a PR or an issue is a reviewer who has not seen the conversation.
The reader of a PR title is a changelog reader, who has no diff and none of our
vocabulary. The same rules hold for both.

**Read the text back as that reader before you call it done.** Every sentence
either tells them something they can act on, or goes. Text that only a
maintainer can follow has failed, whatever rule it obeys.

## The voice

Plain, direct, professional. Explain to a smart adult who does not work on
this project. They are not stupid, they are unfamiliar.

- **Short words.** "Use" not "utilise", "before" not "prior to", "so" not "in
  order that". A term the language owns, such as `piecewise`, a coordinate, a
  `where` or a macro, is never swapped for a plainer word. Everything around it
  is.
- **Confident and flat.** State the rule. Do not hedge with "generally",
  "typically" or "in most cases" unless the exception is real. Then name the
  exception instead.
- **Never grade the language.** "Says what it means", "reads naturally", "just
  works", "as you would expect", "powerful", "seamless", "elegant": the reader
  can neither check nor act on any of them. They argue for a decision the text
  has already made.
- **No filler that blames the reader.** "Simply", "just", "of course", "as you
  can see" and "note that" tell the reader their confusion is their fault, or
  say nothing.
- **Never say that something is subtle, important or the crux.** Say the thing.
  "That boundary behaviour is the whole subtlety of the operator" asks a
  question and leaves the reader holding it.
- **No jokes and no asides.** A reader who hits this text is stuck, and reads it
  in a hurry.
- **No apology and no warning voice.** For "unfortunately", "be careful" and
  "beware", say what happens and what to write instead.
- **One spelling convention per page.** The tree is mixed and this skill does
  not settle it. Match the page you are on.

## Concrete before abstract

A sentence can obey every rule below and still say nothing the reader can
picture. This one does:

> Where two different answers would mean the file says two different things, the
> question belongs to the language, and one answer is allowed.

Its subjects are "answers", "the question" and "one answer". Nobody in it does
anything. The reader has to supply the engine, the renderer, the file and the
disagreement themselves, and most will not. The same fact, written so that it
can be pictured:

> Suppose the engine sums `p` over `generator` and the renderer prints a sum
> over `snapshot`. The file now has two meanings, and that is a bug. The rule
> that stops it belongs to the language.

Four rules make the difference, and they come before every rule under
[Sentences](#sentences):

- **The subject of a sentence is a person, a tool or the file.** "You",
  "the engine", "the renderer", "the solver", "`to_spec`", "the file", "the
  table". Not "the question", "the rule", "the answer", "the construct", "the
  limit" or "the difference". Where an abstract noun is the subject, ask who is
  acting, and name them.
- **Every general statement is followed by its instance, or replaced by it.** A
  principle without an example is a sentence the reader has to trust. "Absence
  spreads through arithmetic" is followed by `x + y` losing its row at `old`.
  If no instance exists, the statement is cut.
- **Write the common word.** "Decided by", not "belongs to". "Tool", not
  "consumer", except where the term is being defined. "Is wrong", not "is a
  bug in the contract". "Reads", "prints", "builds", "refuses". A reader who
  knows YAML and a solver, and nothing about this project, has to follow every
  sentence without looking anything up.
- **Read each sentence back and ask: could the reader draw it?** A sentence
  about a file, a table, a row or a tool, doing one thing, can be drawn. A
  sentence about a rule owning a question cannot. Rewrite until it can.

A paragraph of short abstract sentences is not plain. It is the same
abstraction cut into pieces, and it is harder to read than one long concrete
sentence. A run of short sentences with no joining words is hard to read for
the same reason: the reader has to work out how each one follows from the
last.

## Sentences

- **Put the fact first**, with no build-up to it. A section that builds to its
  point makes the reader hold everything until the end.
- **One main thought per sentence.** The em dash that carries a turn, the
  appositive that carries a second thought and the tail that qualifies the
  claim each read as one sentence and parse as three, so split them. Two ideas
  that depend on each other stay in one sentence, joined by "because", "so",
  "which" or "when": "`to_spec` refuses the file, because it reads no data" is
  one sentence, not two. See also
  [Concrete before abstract](#concrete-before-abstract).
- **Every sentence has a subject and a finite verb.** A paragraph never opens
  on a title-like fragment. "Grammar first, which is usually free because
  `f(x, k=v)` already parses" is a caption. Write "Start with the grammar,
  which is usually free".
- **A colon or a dash does not excuse a missing verb.** "The probes: for each
  operator, the smallest spec that declares it, beside the equation it
  renders" is three noun phrases and no claim. Say who does what: "Each probe
  declares one operator in the smallest spec that can, and prints the equation
  beside it."
- **Active voice, with a real subject.** "The loader refuses it before any data
  is attached", not "the refusal comes before any data is attached".
- **Say what happens, not what kind of thing something is.** "A model is a
  declaration, so it prints the way a paper prints it" gives the reader nothing
  to do. "`to_latex` prints the spec as LaTeX equations, from the file alone"
  does. Cut any sentence that would stay true of another tool, another
  language, or nothing at all.
- **Do not describe the text.** "This page holds the argument in between", "Two
  things this page is not" and "The point of putting them together is" are all
  frames around a sentence. Write the sentence and delete the frame.
- **Bold marks what the reader must not miss.** That is a term where the text
  defines it, and a short phrase that changes what the sentence permits:
  **exactly one** of two keys, **at most once** per coordinate, the vacated
  edge is **absent**. It is never a whole sentence, and never a claim that reads
  better written out. In `AGENTS.md`, `CONTRIBUTING.md` and the skills it also
  names the rule that opens a list item or a paragraph.
- **A heading names the subject, or the question the section answers.** "How a
  new construct enters", not "Two tiers, and the limit". "Renaming and
  deleting", not "Breaking changes are free".
- **No metaphor the reader has to decode**: a tax, a seam, a fence, a front
  door, a tier. Name the thing. Where a metaphor is a defined term of this
  project with a page behind it, such as a **rung** of the examples ladder, keep
  it, define it at first use, and do not grow a new one beside it.
- **"When both of these are true", not "if and only if".**
- **No fronted participles** that suspend the subject: "Having no mask to
  narrow its frame, it is the one that…".
- **No elided possessives**: "The dimensions of a cased one cannot", not "A
  cased one's cannot".
- **A pronoun names its subject again** once a clause has intervened.
- **No double negatives, no stacked metaphors, and no relative clauses stacked
  without _that_.**
- **An example is the statement, so the paragraph ends on it.**
- **`So …`, `In other words …` and `That is to say …`** earn their place only
  where the second sentence adds the mechanism, the reason or the refusal.
- **Say it once.** The same claim in three paragraphs is load-bearing in none.
- **The test is subtraction.** Cover a clause and ask what the reader can no
  longer do. No answer means cut it, and the shorter paragraph ships.
- **A clause that points at a missing rule is replaced, not deleted.** It was
  standing where the rule belongs.

## Words

**A word the reader would have to look up is either replaced, or defined in the
sentence that first uses it.** Check it against the vocabulary that the
NumFOCUS packages already use. Gloss every acronym and domain term at first
use, in parentheses, in six words or fewer.

**One word, one meaning across the docs.** A word that already names an
operator cannot also name a concept: `ceiling` rounds up, so the limit of what
the language can express is **the limit**. _dims_, _dimensions_ and _axis_ are
three words, and a reader counts three ideas, so vary nothing for rhythm. A
word that stands in for three ordinary words is replaced by them: `sayable` is
_allowed_, or _written_, or _the language can express it_.

| Not this              | This                                                                  |
| --------------------- | --------------------------------------------------------------------- |
| idempotent            | calling it again returns the same object unchanged                    |
| the seam              | the boundary between a spec file and an engine, or name the functions |
| the export surface    | the public API                                                        |
| a verb                | a function, or a public function                                      |
| the ceiling           | the limit of what the language can express, then the limit            |
| sayable, unsayable    | allowed, written, or the language cannot express it                   |
| a restriction lifts   | a restriction no longer applies                                       |
| arity                 | the number of arguments                                               |
| memoised              | cached                                                                |
| the two-backend tax   | implemented twice, once for each backend                              |
| the closure           | the set of constructs the language admits                             |
| streamability         | what a build that streams its terms can carry                         |
| a lane                | a backend                                                             |
| affine COO rows       | rows of coefficients                                                  |
| a differential oracle | a second implementation whose answer the test compares against        |
| a surface             | the keys the language accepts, or name them                           |

Domain terms stay, because replacing one costs the reader more than it saves:
affine, degree, dimension, coordinate, broadcast, entry, invariant,
agnostic, and PyPSA's own names such as `p_nom`. A cardinality constraint keeps
its name and gains a clause that says it counts how many things are non-zero.

**A word this project owns is defined where the text first uses it.** Link to
the page that owns the term where one exists, and give the defining clause
anyway. Shorten a clause to fit the sentence, and never drop it:

| Project word  | Define it at first use as                                                                                                                        |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| a consumer    | a tool that reads a spec, such as an engine, a renderer or a checker                                                                             |
| a tool        | a piece of software that reads a spec: an engine, a renderer, a checker. Never "a program", because `Program` is the object `to_program` returns |
| a sink        | whatever a built model is handed to, which is a solver's API or a file format                                                                    |
| a backend     | one of the two implementations that build a model from the same syntax tree                                                                      |
| a primitive   | an operator built into the language, which no file can add to                                                                                    |
| a macro       | a template that takes arguments and is substituted into an expression before anything reads it                                                   |
| a formulation | an entry that expands into ordinary entries before the model is built                                                                            |
| a frame       | the dimensions an entry ranges over                                                                                                              |
| bounded-halo  | reads a fixed number of neighbouring positions, and no more                                                                                      |
| a rung        | one step of the PyPSA ladder, which is one `n.optimize()` keyword stated in full                                                                 |

**A file states a spec; a model is a spec with data.** Write "model" only for
what an engine builds and a solver takes, never for the file or the `Spec` in
hand ([glossary](../../../docs/reference/glossary.md)).

## Messages in the code

The reader of a message is the modeller whose file did not load, or the
person who ran a tool. They see the message in a terminal, with the file open
and no docs at hand. Every rule above applies, and these are added:

- **Say what is wrong, where, and what to write instead**, in that order.
  "`bounds.lower` is nan, which no value compares to. Write a number, or omit
  the bound." names the key, the fault and the rewrite. A message that only
  says what is wrong leaves the reader to guess the fix.
- **Name the thing as the file spells it.** Quote the key, the entry
  name and the value the reader wrote, so that they can search the file for
  it. Keep the quoting the module already uses.
- **No "invalid", "illegal", "failed" or "error" on their own.** Say which
  rule the file breaks. No exclamation marks, and no "you must".
- **A message after a context prefix**, such as `Named expression 'x': …`,
  starts in lower case and continues the sentence the prefix began.
- **Change a message together with what quotes it.** A test that matches the
  text and a page that quotes the message change in the same commit, because
  the docs quote error messages whole.

## Measure it

Aim for a median near 20 words per sentence, and few over 25, which is where
a newcomer re-reads. Run this on a page, or on a PR body
saved to a file, and put the numbers in the commit body or the PR's
`<details>`. The number is evidence, not a target or a limit. A list-shaped sentence may
be long and clear, and a run of short abstract sentences is not plain.

````bash
pixi run python - docs/reference/language/absence.md <<'PY'
import re, sys

SKIP = ('#', '$$', '|', '>', '    ')
GENERATED = re.compile(r'<!-- [\w:-]+:(?:begin|end) -->')
ABBREV = re.compile(r'(?:\b[A-Za-z]|\d|\be\.g|\bi\.e|\betc|\bcf|\bFig|\bvs)\.$')


def blocks(path: str) -> list[str]:
    """Prose blocks: one per paragraph and one per list item, code stripped.

    Inline code is stripped per line, so a code span reflowed across a line
    break cannot pair backticks across the whole page and eat the prose
    between them. Its stand-in is a word, not a letter, so a sentence that
    ends on code is not read as an initial. A generated block is skipped,
    because nobody writes its prose by hand.
    """
    out, buf, incode, incomment, ingen = [], [], False, False, False
    for line in open(path).read().split('\n'):
        if GENERATED.match(line):
            ingen = line.rstrip().endswith(':begin -->')
            continue
        if ingen:
            continue
        if incomment:
            incomment = '-->' not in line
            continue
        if line.startswith('<!--') and '-->' not in line:
            incomment = True
            continue
        if line.startswith('```'):
            incode = not incode
            continue
        line = re.sub(r'`[^`]*`', 'CODE', line)
        if incode or line.startswith(SKIP):
            continue
        item = re.match(r'\s*(?:[-*+]|\d+\.)\s+(.*)', line)
        if not line.strip() or item:
            if buf:
                out.append(' '.join(buf))
            buf = [item.group(1)] if item else []
            continue
        buf.append(line.strip())
    if buf:
        out.append(' '.join(buf))
    return [b for b in out if b.strip()]


def sentences(block: str) -> list[str]:
    """Split on terminal punctuation, rejoining across `1.5`, `e.g.` and initials."""
    parts, cur = [], ''
    for chunk in re.split(r'(?<=[.!?])\s+', block):
        cur = f'{cur} {chunk}'.strip()
        if not ABBREV.search(cur):
            parts.append(cur)
            cur = ''
    if cur:
        parts.append(cur)
    return [p for p in parts if p.strip()]


w = sorted(len(s.split()) for b in blocks(sys.argv[1]) for s in sentences(b))
print('n', len(w), 'avg', round(sum(w) / len(w), 1), 'median', w[len(w) // 2], 'over25', sum(x > 25 for x in w))
PY
````

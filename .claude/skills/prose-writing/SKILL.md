---
name: prose-writing
description: House rules for any prose written in this project — who reads it, which published style guides gate it, and the few words this project owns. Use when writing or editing a Markdown page, AGENTS.md, a PR title or body, an issue, a review comment, a commit message, or an exception, warning or log message in the code.
---

# Writing prose here

These rules apply to every Markdown page, to `AGENTS.md` and
[CONTRIBUTING.md](../../../CONTRIBUTING.md), to PR titles and bodies, issues,
comments and commit messages, and to every exception, warning, advice and log
message in `src/` and `tools/`. A documentation page also follows
[the docs-writing skill](../docs-writing/SKILL.md), which sets the shape of
each kind of page. The layout of a PR body, a PR title and an issue is in
`AGENTS.md`.

This skill does not define a style of its own. It names the published guides
that gate the prose, says which one wins where they differ, and adds the few
facts about this project that no guide can know.

## The reader

The reader of a page is a modeller who writes YAML and has read no other page
in this repository. They came to find out what the language accepts and what
happens if they write X. The reader of a PR or an issue is a reviewer who has
not seen the conversation. The reader of a PR title is a changelog reader
with no diff. The reader of a message in the code has the file open in a
terminal and no docs at hand.

Read the text back as that reader before you call it done. A sentence that
does not move their answer forward is cut, however true it is.

## The guides that gate the prose

Check a page against these, in this order. Where two differ, the earlier one
wins.

1. **Google developer documentation style guide**,
   <https://developers.google.com/style>. This is the primary guide for voice,
   tone, grammar and formatting. The parts that matter most here: write in
   the second person and the present tense; prefer the active voice but use
   the passive where the actor is unknown or does not matter; use sentence
   case for headings; do not attribute human qualities to software or to
   files, which is its rule against anthropomorphism; put conditions before
   instructions; keep sentences and paragraphs short; use its word list for
   contested words.
2. **GOV.UK content design guidance**,
   <https://www.gov.uk/guidance/content-design/writing-for-gov-uk>, and its
   [A to Z of style](https://www.gov.uk/guidance/style-guide/a-to-z-of-gov-uk-style),
   for plain English in British spelling: short common words, the fact
   first, no sentence that needs reading twice, and sentence length judged
   by the reader and not by a word count. Where the Google guide and GOV.UK
   differ on spelling or punctuation, GOV.UK wins, because the pages are
   British.
3. **Diátaxis**, <https://diataxis.fr>, for the language of each kind of
   page: imperatives in a how-to, results after every step in a tutorial,
   neutral description in reference, argument and comparison in explanation.
   The docs-writing skill holds the per-kind table.
4. **The pandas documentation**, <https://pandas.pydata.org/docs>, as the
   model of register for a Python library's docs: a concept in a sentence or
   two, then an example, then a sentence that reads the result. Its
   contributing guide,
   <https://pandas.pydata.org/docs/development/contributing_documentation.html>,
   and the numpydoc standard it follows set the shape of a docstring.
5. **The US federal plain language guidelines**,
   <https://www.plainlanguage.gov/guidelines>, where the Google guide is
   silent: organise for the reader, one idea per paragraph, say it once.

When unsure how to write a sentence, find the construct in the Google guide
and follow it. Do not invent a house rule in its place.

## What this project adds

A handful of facts the guides cannot know.

- **Describe things with flat verbs.** A file, key, entry, table, page or
  message does not say, read, hold, carry, own, name or stand. It is, has,
  contains, specifies, lists, sets, states, declares, defines, describes or
  requires. The acting verbs, such as reads, prints, builds, refuses and
  returns, belong to real actors: mathspec, a tool, a function, a solver, or
  the reader. A design decision is also mathspec's: "mathspec refuses
  arbitrary Python", never "this project refuses" or "the language refuses". The language, a grammar or a page may define, describe or list
  something, since that is what a text does. "Decides" belongs to mathspec
  and to a tool. The language defines; a file or an entry sets; and what the
  data settles "is known only when the data is attached".
  Data preparation is work, not an actor: "you compute it in data
  preparation", never "data preparation computes it". This is the Google guide's rule
  against anthropomorphism, and it is listed here because an earlier version
  of this skill caused the opposite habit.
- **Define by category first.** "A term is a named expression that adds to a
  sum another file declares." Then say what it does. A reference entry is a
  definition, then behaviour, then its keys.
- **Vary the joiner, and the length.** Two sentences that depend on each
  other may share a sentence through "because", "so", "which" or "when". A
  paragraph in which every sentence does so reads as one voice, and a
  paragraph of eight-word sentences reads as a list. Aim for a page average
  between 14 and 18 words, with some sentences under 10 and some near 25,
  and treat 25 as the point past which a sentence is read twice, so 25 is
  in and 26 is out. Link text counts as words. Judge the sentence by the
  reader first, as GOV.UK asks, and use the numbers as a check afterwards. Where one idea per
  sentence and the six-sentence paragraph pull against each other, keep the
  joined sentence.
- **One word, one meaning across the whole set of documents.** This is the
  one rule borrowed from ASD-STE100 Simplified Technical English. The word
  table below applies it to the words this project owns.
- **Spelling is British** on documentation pages, because the README is, and
  one spelling holds per page. Code, keys and quoted messages keep their own
  spelling. No semicolons: write two sentences, or a list.
- **A file states a spec, and a model is a spec with data.** Write "model" only
  for what an engine builds and a solver takes, never for the file or the
  `Spec` in hand ([glossary](../../../docs/reference/glossary.md)).
- **Gloss every acronym and domain term at first use** on a page. The
  explanation, in six words or fewer, runs in the sentence, and the term
  follows it in parentheses, as the Google guide spells out an acronym before
  it: "the specification of an optimisation model (a spec)", not "a spec (the
  specification of an optimisation model)". Link the term to the page that
  owns it where one exists. The
  eleven-rules table on the
  [language index](../../../docs/reference/language/index.md) lists which page
  owns which rule, so a term is defined once and linked elsewhere.
- **No history and no promises on a page.** "Previously", "renamed from" and
  "will support" belong in git, the changelog and the history page.
- **A number on a page is a measurement**, with the PR that measured it, as
  `AGENTS.md` asks for numbers in the tree.

### Words this project owns

A word that names an operator cannot also name a
concept, so `ceiling` rounds up and the limit of what the language can express
is _the limit_. _dims_ is a key; in prose the word is _dimensions_.

| Project word  | Define it at first use as                                                                                                                        |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| a tool        | a piece of software that reads a spec: an engine, a renderer, a checker. Never "a program", because `Program` is the object `to_program` returns |
| an engine     | a tool that attaches data to a spec, builds the model and hands it to a solver                                                                   |
| an operator   | a construct built into the language, which no file can add; never "primitive"                                                                    |
| a macro       | a template that takes arguments and is substituted into an expression before anything reads it                                                   |
| a formulation | an entry that expands into ordinary entries before the model is built                                                                            |
| to load       | to run `to_spec` on a file. "Refused at load" means `to_spec` raises before any data exists                                                      |
| to compile    | to turn a spec into its program, which `to_spec` does in the same call. Never "lower" in prose                                                   |
| a fragment    | one file of a spec that `merge` composes                                                                                                         |
| a patch       | a file that `override` lays over a base                                                                                                          |
| advice        | what `check` prints about a spec without refusing it                                                                                             |
| a rung        | one step of the PyPSA ladder, which is one `n.optimize()` keyword stated in full                                                                 |

Words to avoid, and what to write instead: consumer (a tool), bind data
(attach data), mask or predicate (a condition), reject or error out (refuse),
normal form (the canonical form), unbuilt or masked out (absent), summand
(a term of a sum), seam,
surface, lane, tax, closure, sayable (say the plain thing). The coupling
surface of a component library is a glossary term and is not this fault.

## Messages in the code

The reader of a message is the modeller whose file did not load, or the
person who ran a tool. They see the message in a terminal, with the file open
and no docs at hand. The Google guide's page on error messages applies, and
these are added:

- **Say what is wrong, where, and what to write instead**, in that order.
  "`bounds.lower` is nan, which no value compares to. Write a number, or omit
  the bound." has the key, the fault and the suggested rewrite, in that order.
- **Name the thing as the file spells it.** Quote the key, the entry name and
  the value the reader wrote, so that they can search the file for it. Keep
  the quoting the module already uses.
- **No "invalid", "illegal", "failed" or "error" on their own.** Say which
  rule the file breaks. No exclamation marks.
- **A message after a context prefix**, such as `Named expression 'x': …`,
  starts in lower case and continues the sentence the prefix began.
- **Change a message together with what quotes it.** A test that matches the
  text and a page that quotes the message change in the same commit, because
  the docs quote error messages whole.

## The gate

Before a page, a PR body or an issue is done, read it once against this
list. Each item points at the guide that owns it. Items 1 to 11 are read on
every prose line, item 12 on every sentence, and item 13 on every table.

1. Could a reader who has only the Google guide find a rule this text
   breaks? Fix it.
2. Does any inanimate subject say, read, hold, carry, own or name something?
   Rewrite with a flat verb, or give the sentence a real actor.
3. Does every "that", "this", "it" or "so" point at a noun or verb the text
   states? A pronoun after a negation ("builds nothing. Other tools do that")
   points at nothing. Name the thing.
4. Is the subject of each sentence a thing the reader can picture, and is its
   verb within a few words of it? "The alternative, which a framework that
   writes its math as code uses, is to check …" fails twice: the subject is an
   abstraction, and ten words sit between it and "is". Write "A framework that
   writes its math as code checks …". Use one verb for one action across the
   paragraph: not decide, answer and check for the same thing. A verb turned
   into a noun hides the actor the same way: "after the solve", "the
   attachment of data" and "the evaluation of a condition" are "after the
   solver runs", "when data is attached" and "when a tool evaluates the
   condition". A project word in the table below, such as advice or
   formulation, is not a fault.
5. Does each definition say what the thing is before what it is not, with at
   most one negation, and in nouns the page has already used? "A coordinate
   is absent when the model has no variable or no row there. It has no
   column and no value, and it is not a zero" is five holes and four nouns for
   two things. Write "An absent variable does not exist at that coordinate.
   Absent is different from zero, because zero is a value."
6. When a paragraph moves between situations, such as the file and the data,
   or load time and build time, does the sentence name the situation first?
   "With data attached, …", "Before any data is attached, …". An italic
   phrase is not a marker, and a place such as "in the file" is not a
   situation.
7. Does every term the reader might not know have a gloss and a link at first
   use?
8. Does every example end with a sentence that reads the result?
9. Is any sentence over 25 words, link text included, without being a list?
   Is any paragraph over six sentences, or about more than one subject? Five
   rules about five things are five paragraphs, a list, or a table. Does the
   paragraph open with the sentence that states its claim and close with the
   sentence that states what follows from it? A claim that arrives in the
   middle, or a paragraph that ends on a cross-reference or a detail, is read
   twice. The opening paragraph of a page is exempt, because item 10 sets its
   first sentence.
10. Does any sentence describe the text instead of the subject? "Two cases
    look alike and are treated differently", "this section covers" and "the
    point of this is" announce a sentence instead of being one. Delete the
    frame and keep the sentence it announced. An opening sentence says what the
    reader can do after the page, or states the claim the page supports. It
    is never an aphorism such as "a spec can state only what the language
    has words for", and never a question. A rule set off in a blockquote is
    the same aphorism with a frame around it; state the rule in a sentence
    that names the test it applies.
11. Is any claim stated twice on the page, or stated here and owned by another
    page? A paragraph that walks a table's rows or columns in prose is the
    table said twice. Keep the table. A clause that restates its own main
    clause is a sentence said twice: "decides every rule that it can decide
    from the file alone" is "decides" with its definition hung on the end.
12. Does the point of each sentence sit at its end? A reader weights the last
    words of a sentence, which Gopen and Swan call the stress position. "A
    `where:` on a variable leaves the variable absent, not zero, at every
    coordinate where the condition is false" ends on the condition, which the
    reader already holds. "Where its condition is false, a `where:` on a
    variable leaves the variable absent, not zero" ends on the point. A
    trailing qualifier, a link back to a known term or an aside after the
    point is the fault. A gloss parenthesis, "(a spec)", is the term's name
    and not a fault. Item 6 is a case of this rule: the situation opens the
    sentence because the reader holds it.
13. Do the table cells pass items 2, 7, 11 and 12, and the word lists? A cell
    that states a result is a full sentence with its actor: "a tool refuses
    the parameter if any row of its data is missing", not "is refused when
    the data is attached". A cell that names a thing is a fragment, and every
    cell in a column takes the same form. A cell the body restates in prose is
    the table said twice: keep one.

The sentence-length script below is an instrument for item 9, not a target.
Put its numbers in the PR's `<details>` when the PR changes prose.

````bash
pixi run python - docs/reference/language/absence.md <<'PY'
import re, sys

SKIP = ('#', '$$', '|', '>', '    ')
GENERATED = re.compile(r'<!-- [\w:-]+:(?:begin|end) -->')
ABBREV = re.compile(r'(?:\b[A-Za-z]|\d|\be\.g|\bi\.e|\betc|\bcf|\bFig|\bvs)\.$')


def blocks(path: str) -> list[str]:
    """Prose blocks: one per paragraph and one per list item, code stripped."""
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

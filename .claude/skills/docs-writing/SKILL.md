---
name: docs-writing
description: House rules for documentation pages in this project — what a page is for, how it is shaped, and how its examples and headings work. Use when writing a new documentation page or section, or when adding prose to an existing one, together with the prose-writing skill.
---

# Writing docs here

These are the rules a page has to meet. They apply to prose you write now and
to prose already on the page: a page that does not meet them is not finished,
whoever wrote it.

**Load [the prose-writing skill](../prose-writing/SKILL.md) first.** It sets
the reader, the voice, the sentences and the words, for pages, PRs and issues
alike. This skill adds what only a page needs.

## 1. Decide what the page is before writing a sentence

Two questions decide it, and they work on a paragraph as well as a page:

1. Does it inform **action** or **cognition**?
2. Does it serve **acquiring** a skill or **applying** one?

| Kind        | Informs   | Serves  | Answers                                               | Section · folder                                                 |
| ----------- | --------- | ------- | ----------------------------------------------------- | ---------------------------------------------------------------- |
| Tutorial    | action    | acquire | "Get me a first file that loads and prints"           | Tutorials · `docs/tutorials/`                                    |
| How-to      | action    | apply   | "I have this task"                                    | How-to guides · `docs/howto/`                                    |
| Reference   | cognition | apply   | "What exactly does X accept, and what does it print?" | Reference · `docs/reference/`, example pages in `docs/examples/` |
| Explanation | cognition | acquire | "Why is it like this?"                                | About · `docs/about/`                                            |

The nav and the tree are both arranged by kind, for someone who writes a
spec. A new page goes in the folder of its kind and under the nav section of
the same name. Each section opens with an `index.md` that lists its pages in
one line each; a new page adds its line there. The example pages sit at the end of the Reference section, after
the pages a reader looks things up in. A worked example is neither a tutorial
nor a how-to: it teaches no path and names no task, it shows that the language
says a spec.

The Development section, last in the nav, holds every page a spec writer does
not need, in three groups:

- **Building on mathspec** is for someone who writes a tool against `Spec`
  and `Program`: an engine such as specsolve, a renderer, a checker.
- **Contributing** is for someone who changes mathspec itself.
- **Proofs of concept** holds the notation page, which renders the typesetting
  test spec, and the PyPSA pages. The PyPSA pages stay in `docs/examples/`,
  where `tools/gallery.py` writes them.

A page in Development keeps the folder of its kind.

Each kind has one job, and one thing it must not do:

- **A tutorial is a lesson.** One path, every step shows a result, and the
  reader finishes with a file that loads and prints. It explains nothing and
  offers no choice: a choice is a how-to leaking in. Where a step needs a
  reason, one clause and a link to the explanation page carry it. The last
  section, before "Where to next", says what the reader has built.
- **A how-to is a recipe.** The title names the goal, the body is the steps,
  and the reader is assumed competent. It neither teaches nor explains: a
  term is linked to the reference, never defined; a rule is linked, never
  restated; a consequence is one sentence, never a section.
- **Reference describes, and only describes.** One consistent format, and a
  structure that mirrors what it describes: the language pages follow the
  file's keys, in the file's order, and the typeset page follows the three
  formats and their options. No rationale, no instruction. An example
  illustrates an entry and never turns into a recipe; a recipe is a link to
  the how-to.
- **Explanation is the one place for why.** Context, alternatives and opinion
  live here and nowhere else. An explanation page names the alternative it
  rejects and says why the choice is better here. It holds no table of keys,
  no checklist and no instruction; those link to the reference or the
  how-to.

**An example page is reference in its own form.** It answers "can the language
say my model, and what does the file mean?", and its shape is a witness rather
than a table: a paragraph of the page's own, then the file verbatim and the
math the typesetter prints from it. The block is written by `tools/gallery.py`
between `<!-- gallery:begin -->` and `<!-- gallery:end -->`; the paragraph is
the only prose on the page, and it says what the spec is and the one or two
things worth reading for, which the `description:` line in the file does not.
The PyPSA pages, in the Development section, add a generated block per rung,
holding the reference script and what PyPSA solved it to. Every example is a
file under `examples/`, loaded by the suite and compiled by the LaTeX gate,
and `tests/test_docs.py` holds each block to its generator byte for byte. The catalogue in
`docs/examples/index.md` is hand-written: one bullet per page in the Examples
section, saying why a reader would open it.

**The Python API is rendered from the docstrings.**
`docs/reference/api.md` holds one `:::` entry per name in `mathspec.__all__`,
for a spec writer. `docs/reference/program.md` renders `mathspec.program`,
for whoever builds on the program. mkdocstrings renders both from the
docstrings, so their prose is the docstring rules in `AGENTS.md`. No other
module gets a page: an internal module is read in the source.

Mixing kinds is the most common failure. Rationale inside a reference section
makes the rules unskimmable, and rules inside an explanation page make the
argument unreadable. Rationale about the code, its internals and its measured
numbers belongs in the PR, per `AGENTS.md`. Rationale about the language, its
shape and the alternatives it rejects belongs on an explanation page, where a
user can read it before relying on a rule.

Each kind has its own sentence patterns, from [Diátaxis](https://diataxis.fr):

| Kind        | Opens with                                                                            | Sentences                                                                                                                                        | Closes with                              |
| ----------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------- |
| Tutorial    | "In this tutorial you build …", and how long it takes                                 | "Make a file … Check it:", then the output, then one sentence that reads it. "If the output shows x, then …"                                     | "You have built …", then "Where to next" |
| How-to      | "This guide shows how to …", and what you need before                                 | "To get x, do y." "If you want w, write z." "The [reference](…) lists every option."                                                             | The result, checked                      |
| Reference   | What the thing is, in one sentence, then its shape                                    | Facts. "x accepts …", "x refuses …", "x must …". Never "to get x, do y".                                                                         | a "See also" admonition                  |
| Explanation | The decision, as one statement; or what the page covers, when it has several (see §2) | "Here x is better than y. The reason is …", "x is like w in z", "the rule exists because …", "what you write instead" with the reader as subject | What the reader can now judge            |

The language is documented here and only here. A page says what a file may
contain, what it means, what the loader refuses, and what the typesetter
prints from it. What a consumer does with a spec — the data it attaches, how it
solves, what it reads back — is that consumer's page, not this tree's
([what counts as language](../../../docs/about/what-counts-as-language.md)).
A rule about a consumer says only what the file guarantees it
([reading a spec and its program](../../../docs/reference/reading.md)).

Answer the two questions before starting. If a page needs two kinds, it is
two sections with two headings, or two pages.

## 2. Open with what the reader can do

The first sentence, above the first rule, says what the reader can do once
they have read the page. Do not restate the title. A page with one point
opens with that point, as a definition or a decision: "A dimension is a set
of labels that entries are indexed over", "mathspec numbers its releases
and its file format separately". A page with several points, which no one
sentence covers, opens with what it covers instead, as the pandas
documentation does ("This page describes every key a file accepts"). The
strain decides: a one-sentence claim that needs a metaphor, a second clause
or a word the body has not defined yet is the sign of several points. Never
open with a question or an aphorism. A coverage sentence is allowed at the
top of a page and nowhere else: "in this section we will" and "this page
holds" further down are frames.

The prose is the prose of the pandas documentation: a concept in a sentence
or two, then the example, then one sentence that reads the result. An
example is never left for the reader to interpret. A section that has a
sibling elsewhere ends with a `!!! info "See also"` admonition that links it. An aside that
would break the flow of a section goes in a `!!! note` or `!!! warning`
admonition, at most two per section.

Then the shape a reader needs, in this order:

1. **Shape** — the smallest thing they can write that works.
2. **Rules** — what is accepted, and what is refused.
3. **Rationale** — only where it changes what they write.

The subtlest rule gets the most support: a list, a worked example, a table.
The obvious rule gets one sentence.

## 3. Every rule carries an example, and the example is real

- **Show the input and its result side by side.** YAML next to the maths it
  renders, a call next to its output. Never in a later subsection.
- **Every generated block is checked; a hand-written fence is not.** The
  spec on an example page, the notation page, the operator table and the
  home spec come from a generator, and `tests/test_docs.py` holds them to
  it. `reading.md` is run by `tests/test_reading_page.py`, which checks every
  `expression  # value` line. The `NAME` production on the expressions page
  is compared to the parser's. A YAML fence anywhere else is read by nothing,
  so load it before committing: write it to a file and run
  `pixi run python -m mathspec check spec.yaml`. Write the fragment as a
  whole spec where the page allows it; a fragment that cannot stand alone is
  one the reader cannot run either.
- **Quote error messages whole.** mathspec suggests the rewrite at the end of
  each message, and a truncated quote drops exactly the half that teaches.
- **Prefer the smallest example that still shows the point.** A spec with two
  dimensions and one variable teaches; a realistic one hides the rule in
  scenery.
- **Show the refused form too**, where the refusal is the lesson, with the
  message it produces.

## 4. A rule about rows carries a figure

A section of a reference or explanation page that says what a construct does
to the rows of an entry carries a figure. That covers absence, `where:`,
`missing:`, `shift` and the other operators, a join or a sum through a
relation, `ordered`, and composition with `merge` or `override`. A tutorial or
a how-to links to the figure and draws none of its own.
`docs/static/absence-where-variable.svg` is the model; copy its structure.

- **Every entry is a table, one row per coordinate.** An absent coordinate has
  no row. A dashed rounded box with an italic note stands where the row would
  be: "no row for old: dispatch is absent". This is a table view, not a grid
  of dimensions.
- **A second dimension is a second key column.** Use one only where it
  changes the result, such as a per-entity `offset=` or the dimension a `sum`
  keeps. A figure holds at most two result panels to the right of its input;
  more go on a row below.
- **The figure uses the data of the section's example.** Where the page has no
  data, invent the smallest set and say so in the PR.
- **YAML appears once.** A figure that follows a YAML fence holds no YAML.
  A figure with no fence above it opens with the few keys it is about, and
  the key in question is in bold.
- **One mark, one meaning, on every page.**

  | Mark                                         | Means                                                                       |
  | -------------------------------------------- | --------------------------------------------------------------------------- |
  | vermilion `#D55E00` hatch                    | a row the condition removes, or has no data                                 |
  | dashed outline, no fill                      | absent: no row                                                              |
  | blue `#0072B2` tint                          | data the file is given: a parameter, a relation, a dimension, an input file |
  | orange `#E69F00` tint                        | a variable                                                                  |
  | bluish green `#009E73` tint                  | a constraint, an expression, an operator's result                           |
  | reddish purple `#CC79A7`, sky blue `#56B4E9` | the groups of a sum through a relation                                      |

  The hatch never highlights. A tint fills the header band at
  `fill-opacity="0.2"` and the body at `0.08`, under the text. Text, outlines
  and arrows stay `currentColor`, so the figure reads in light and dark mode.

- **No rule is stated in colour alone.** Each coloured table carries a text
  label for its kind, such as "a parameter" or "an expression". A legend lists
  the marks the figure uses, and no others.
- **An arrow meets its target at a right angle.** Draw it as a curve that ends
  in a short straight run, or as an elbow. A fan from one table to several is
  an elbow tree. The arrow carries a short label: the key or call, then what it
  does.
- **The words are the page's words**: a term, a condition, absent, left out.
- **The file** is `docs/static/<page>-<topic>.svg`. It opens with the SPDX
  header as an XML comment, then `<svg>` with `width`, `height`,
  `style="max-width: 100%; height: auto"`, `role="img"`, and a `<title>` and
  `<desc>` that `aria-labelledby` names. Every `id` takes a prefix of the
  figure's own, because one page holds several figures. Colours are
  attributes: a `<style>` element in an inline SVG styles the whole page. The
  file has no blank line, because a blank line ends the raw HTML block.
- **Embed it inline**, after the fence and before the sentence that reads the
  result, so `currentColor` follows the theme:

  ```markdown
  <figure class="diagram">
  --8<-- "docs/static/absence-where-variable.svg"
  </figure>
  ```

- **Look at it in both themes** before the page is done:

  ```bash
  rsvg-convert -w 1520 -b white x.svg -o light.png
  sed 's/currentColor/#ddd/g' x.svg | rsvg-convert -w 1520 -b '#1e2129' -o dark.png
  ```

  Text over the strongest tint keeps a contrast of 4.5:1 in both.

## 5. Headings are the table of contents

- **A heading takes the form of its kind.** On a how-to page, the title and
  every `##` are imperatives that name the task: "Check every spec in CI",
  "Choose between a dimension, a relation and a parameter". Not a gerund
  ("Checking every spec in CI") and not a noun ("CI checks"), which Diátaxis
  grades bad and very bad, because a reader searches for the task. On a
  tutorial page, a `##` names what the step adds: "The state of charge",
  "Closing the day on itself". On a reference page, a heading names the
  construct, in the order the file has it: "`dimensions`", "`one_of`". On an
  explanation page, a heading names the subject or the question: "The limits
  of the language", "What the language decides".
- **Elsewhere a heading names the subject, or the question the section answers.**
  "Quadratic expressions", "How a new construct enters". The test: a reader
  who types the subject into the search box lands on this heading.
- **A heading never states a conclusion.** A heading is read before the
  section, so it cannot depend on it. "Unknown keys", not "An unknown key is
  refused". "Solver capability", not "What a solver can take is a separate
  question". Put the claim in the first sentence, where the reader can act on
  it.
- **No second clause after a comma or a dash.** "Two states, and the difference
  between them" carries a heading and an aside. Keep the heading.
- **One `##` per idea.** A section that needs a paragraph of preamble before
  its first rule is two sections.

## 6. Bold is for terms and permissions

On a page, bold marks a term where the page defines it, and a short phrase
that changes what a sentence permits, as the prose-writing skill says. A page
has no bold lead-in on its list items, and bold is never a whole sentence.
Where a list must skim, make the first sentence of each item the claim:

```markdown
- Absence spreads through arithmetic. A sum with one absent term is absent.
```

not

```markdown
- **Arithmetic.** ...
```

## 7. Vocabulary

The prose-writing skill holds the word lists and the project words. On a page,
two more rules hold:

- **Gloss where the term is used**, explanation in the sentence and the term
  in parentheses, and link the reference page that owns it rather than
  redefine it. The eleven-rules table on the
  [language index](../../../docs/reference/language/index.md) says which page
  owns which rule; a second definition drifts.
- **Link the reference section at a construct's first mention** on the page.
  A construct links to its page under `docs/reference/language/`; a function,
  such as `to_spec` or `to_latex`, links to `docs/reference/typeset.md` or the
  API page.

## 8. A reference entry

An entry in `docs/reference/` has three parts, in this order.

1. **What it does to the data, verb first, arguments in plain words.** "Shifts
   array elements by a given offset along a single dimension". Not a metaphor
   ("reaches along an axis"), and not notation the reader must bind to the
   signature themselves (_t−n_).
2. **What it does not do.** "Only data is moved; coordinates stay in place".
   The sentence that stops a wrong assumption is worth more than any other in
   the entry, and it is the one most often missing.
3. **What each remaining argument is for**, at that level. "An additional
   `edge=` argument handles values shifted beyond the array bounds". The list
   of its values follows, or lives in the section that owns it.

## 9. What does not go on the page

- **History.** "Previously this used to…", "renamed from…" — that is git.
- **Argument on a tutorial, how-to or reference page.** The argument for a
  rule of the language goes on an explanation page; the argument for a change
  to the code goes in the PR.
- **A promise about the future.** "Will support…" ages into a lie.
- **Anything that duplicates another page.** One fact, one home; link instead.
  A second copy drifts silently. The README is pulled into `docs/index.md` as
  snippets, so a sentence that appears on both is edited once, in the README.
- **A rule of an engine.** How data is attached to a spec, how it is solved, or read back
  is a consumer's page. Here a consumer is named only for what the file
  guarantees it.
- **Generated content.** The spec and its math on every example page and the
  rung blocks on the PyPSA pages (`tools/gallery.py`), the table on
  `docs/reference/notation.md` (`tools/notation.py`), the operator table on
  `docs/reference/language/operators.md` (`tools/spec_math.py`), and the home
  spec on `docs/index.md` and in the README (`tools/home_math.py`) are
  written by a tool between `<!-- …:begin -->` and `<!-- …:end -->` markers.
  Change the generator, then read the diff. `tests/test_docs.py`'s
  `GENERATED` table is the list.

## 10. Mechanics

- **A list item with a second paragraph or a fence needs four spaces and a
  `<!-- prettier-ignore -->` line above the list.** Python-Markdown needs
  four spaces for the continuation, and prettier rewrites them to two, so
  without the ignore line the content renders outside the list (#87).
  `tests/test_docs.py` enforces this inside grid cards. Elsewhere, prefer
  one paragraph per item and put the fence after the list.

- **A new page needs a nav entry in `mkdocs.yml`.** The docs build is
  `--strict`, so a dead cross-link and a stale anchor fail it. A page with no
  nav entry does not fail the build — zensical validates links and leaves
  navigation alone — so `pixi run test` is what reports it, in
  `tests/test_docs.py`.
- **A new page carries the SPDX header** — `mathspec contributors`,
  `CC-BY-4.0` — in an HTML comment at the top, or as YAML comments inside the
  front matter where the page has one, as `docs/index.md` does. `reuse lint`
  is part of `pixi run lint`.
- **Inside `docs/`, link relatively; outside it, write the full GitHub URL.**
  A relative link above `docs/` renders in the repo and fails the strict
  build. Anchors follow GitHub's slug rules on the site too, so an anchor that
  works in the repo works on the site.
- **A card body is indented four spaces**, under `<!-- prettier-ignore -->`,
  or the card falls out of its list and `tests/test_docs.py` says so.
- **A generated block lands with its plumbing**: the page in
  `.prettierignore`, with a comment naming the tool, and the tool in
  `tests/test_docs.py`'s `GENERATED` table.
- **Write the version as a placeholder, never as a number.**
  `{{ mathspec.release }}` is the latest release and
  `{{ mathspec.language_version }}` the highest language version. An address
  of the schema takes the release tag, `v{{ mathspec.release }}`, never
  `main`. The macros plugin in `mkdocs.yml` renders them from
  `tools/macros.py`, fences included, and an unknown one fails the build.
- **Tables for what varies along one axis** — accepted keys, the operators,
  the formats. Prose for what has an order or a reason.

## 11. The structure gate

Before any sentence is checked, read the heading tree alone and answer these
five questions. Structure is fixed first, because moving a section moves
its sentences.

1. Does each section sit under the heading that names its subject? A
   section about refusals under "How a new construct enters" is misfiled.
2. Does the argument for a thing sit beside the thing? An explanation
   weighs the alternative where it introduces the subject, not three
   paragraphs later.
3. Is every section the page's own kind? A catalogue of operators inside
   an explanation is reference, and belongs on the language page it
   duplicates, with a link here.
4. Does a topic appear in one place? Two tables that say the same thing, or
   a section wedged between the two halves of another, are one topic split.
5. Does the page close as its kind closes? An explanation ends with what the
   reader can now judge, a tutorial with what they built, a reference with
   a "See also" admonition, a how-to with the result checked.

## 12. Gates

```bash
pixi run docs-build                                               # --strict, so a dead anchor is a failure
pixi run pytest tests/test_docs.py tests/test_reading_page.py -q  # the generated blocks, and the page that is run
pixi run lint                                                     # prettier, typos, reuse
```

`pixi run compile-tex` too when a file under `examples/` changed. Say which
gate ran and what was left unrun.

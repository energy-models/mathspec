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
| Tutorial    | action    | acquire | "Get me a first file that loads and prints"           | Tutorials · `docs/`                                              |
| How-to      | action    | apply   | "I have this task"                                    | How-to guides · `docs/howto/`                                    |
| Reference   | cognition | apply   | "What exactly does X accept, and what does it print?" | Reference · `docs/reference/`, example pages in `docs/examples/` |
| Explanation | cognition | acquire | "Why is it like this?"                                | About · `docs/about/`                                            |

The nav and the tree are both arranged by kind, for someone who writes a
spec. A new page goes in the folder of its kind and under the nav section of
the same name. The example pages sit at the end of the Reference section, after
the pages a reader looks things up in. A worked example is neither a tutorial
nor a how-to: it teaches no path and names no task, it shows that the language
says a spec.

The Development section, last in the nav, holds every page a spec writer does
not need, in three groups:

- **Building on mathspec** is for someone who writes a tool against `Spec`
  and `Program`: an engine such as specsolve, a renderer, a checker.
- **Contributing** is for someone who changes mathspec itself.
- **Proofs of concept** holds the notation page, which renders the typesetting
  test spec, the GEMS port and the PyPSA pages. The GEMS and PyPSA pages stay
  in `docs/examples/`, where `tools/gallery.py` writes them.

A page in Development keeps the folder of its kind.

Each kind has one job, and one thing it must not do:

- **A tutorial is a lesson.** One path, every step shows a result, and the
  reader finishes with a file that loads and prints. It explains nothing and
  offers no choice: a choice is a how-to leaking in.
- **A how-to is a recipe.** The title names the goal, the body is the steps,
  and the reader is assumed competent. It neither teaches nor explains.
- **Reference describes, and only describes.** One consistent format, and a
  structure that mirrors what it describes: the language pages follow the
  file's keys, the typeset page follows the three formats and their options.
  No rationale, no instruction.
- **Explanation is the one place for why.** Context, alternatives and opinion
  live here and nowhere else, within what `AGENTS.md` sends to the PR.

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
argument unreadable. Most rationale belongs in the PR, per `AGENTS.md`; what
survives into an explanation page is the part a user needs to make decisions.

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
they have read the page. Do not restate the title, and do not describe the
page: "in this section we will" and "this page holds" are frames.

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
- **Quote error messages whole.** This language's messages name the rewrite,
  and a truncated quote drops exactly the half that teaches.
- **Prefer the smallest example that still shows the point.** A spec with two
  dimensions and one variable teaches; a realistic one hides the rule in
  scenery.
- **Show the refused form too**, where the refusal is the lesson, with the
  message it produces.

## 4. Headings are the table of contents

- **A heading names the subject, or the question the section answers.**
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

## 5. Bold is for terms and permissions

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

## 6. Vocabulary

The prose-writing skill holds the word lists and the project words. On a page,
two more rules hold:

- **Gloss where the term is used**, and link the reference page that owns it
  rather than redefine it. The ten-rules table on the
  [language index](../../../docs/reference/language/index.md) says which page
  owns which rule; a second definition drifts.
- **Link the reference section at a construct's first mention** on the page.
  A construct links to its page under `docs/reference/language/`; a function,
  such as `to_spec` or `to_latex`, links to `docs/reference/typeset.md` or the
  API page.

## 7. A reference entry

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

## 8. What does not go on the page

- **History.** "Previously this used to…", "renamed from…" — that is git.
- **Argument for a settled decision.** That is the PR.
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

## 9. Mechanics

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
- **A diagram carries alt text**, and no rule is stated in colour alone.
- **Tables for what varies along one axis** — accepted keys, the operators,
  the formats. Prose for what has an order or a reason.

## 10. Gates

```bash
pixi run docs-build                                               # --strict, so a dead anchor is a failure
pixi run pytest tests/test_docs.py tests/test_reading_page.py -q  # the generated blocks, and the page that is run
pixi run lint                                                     # prettier, typos, reuse
```

`pixi run compile-tex` too when a file under `examples/` changed. Say which
gate ran and what was left unrun.

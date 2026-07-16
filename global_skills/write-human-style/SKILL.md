---
name: write-human-style
description: Write or revise concise, natural, audience-appropriate prose without canned assistant phrasing. Use when drafting, rewriting, polishing, or shortening pull request descriptions, issue comments, release notes, status updates, documentation, email, or similar reader-facing technical communication.
---

**Cross-repository work:** If scope spans repositories, invoke `$graphify` before discovery, planning, or edits. Query an existing graph; build/update a merged graph when missing, stale, or incomplete. Reuse a current graph for the same repository set.

# Write in a Human Voice

Use this skill for general prose quality. Let the relevant domain skill own the
facts, technical structure, and required template; this skill owns voice,
clarity, pacing, and the final edit.

For inline pull request review comments or threads, use
[`$pr-review-reply-style`](../pr-review-reply-style/SKILL.md) as the entry point.
It loads this skill and adds review-thread semantics.

## Ground the Voice

- Know who will read the text and what they need from it.
- Preserve the author's vocabulary and level of formality when a writing sample
  or surrounding thread is available.
- Keep technical names, uncertainty, caveats, and evidence exact.
- Use first person when the author performed the work and that context matters.
  Do not hide the actor behind phrases such as "it was determined".
- Never invent agreement, emotion, personal experience, motivation, validation,
  or results to make the prose feel more personal.

Human-written style means natural prose, not a claim about authorship. Do not
add fake quirks, typos, slang, or anecdotes.

## Write Plainly

- Lead with the point, outcome, or decision instead of a ceremonial opening.
- Prefer concrete nouns and active verbs: "I removed the check" over "the
  removal of the check was performed".
- Use ordinary connective words and contractions when they fit the author's
  register.
- Keep one main idea per sentence. Mix sentence length naturally, but do not
  force variety.
- Use only as many headings and bullets as the reader needs. Short messages
  usually need neither.
- Be warm when the situation calls for it, but make every acknowledgment
  specific and sincere.

## Remove Assistant-Shaped Prose

Delete or rewrite:

- canned openings such as "Certainly", "Absolutely", "Great question", and
  "I'd be happy to";
- prefaces such as "Here is a polished version" when the user asked only for
  the finished text;
- inflated claims such as "robust", "seamless", "comprehensive", or
  "significantly improved" unless the evidence supports them;
- empty praise, reflexive thanks, and agreement that does not advance the
  message;
- bureaucratic phrases such as "in order to", "with regard to", "upon
  investigation", and "it should be noted that";
- repeated summaries, repeated conclusions, or headings that merely restate
  the sentence below them.

Do not apply these rules mechanically. Keep a phrase when it is genuinely the
most natural choice in context.

## Revision Pass

1. Check every factual claim against the available evidence.
2. Put the most useful sentence first.
3. Replace abstractions and passive constructions with concrete language where
   doing so preserves meaning.
4. Cut filler, repetition, and throat-clearing.
5. Read the text once for cadence and tone. If it sounds scripted when spoken,
   simplify it.
6. Match the requested length and format.

When the user asks only for copy, return the copy without commentary about the
rewrite.

## Examples

Instead of:

```text
Certainly! This PR aims to provide a robust enhancement to token cache handling.
```

Write:

```text
This fixes token-cache writes when a Secret Service client includes MIME parameters.
```

Instead of:

```text
Upon investigation, it was determined that the additional precheck was unnecessary.
```

Write:

```text
I traced the failure to the extra precheck and removed it.
```

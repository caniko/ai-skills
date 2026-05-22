---
name: jd2cv
description: Create a job-description-adapted version of a generic CV/resume for tech lead, senior software engineer, senior backend/systems engineer, staff-leaning IC, or engineering lead applications. Use when Codex is asked to tailor, adapt, rewrite, optimize, target, or ATS-align a CV/resume from a specific job description while preserving factual accuracy and avoiding invented experience, metrics, credentials, or technologies.
---

# JD to CV

## Operating Standard

Never fabricate. Treat the generic CV, source profile, project files, links, and user-provided facts as the only evidence base. If a required fact is missing, mark it as a gap or ask for the source. Do not silently substitute a plausible technology, metric, title, employer, domain, date, location, credential, or business outcome.

Use this skill for application-specific CV variants, especially for senior software engineering and tech lead roles where evidence must show technical depth, ownership, leadership, business impact, and delivery judgment.

For current optimization heuristics, read `references/optimization-2026.md` when shaping the resume strategy or explaining tradeoffs.

## Required Inputs

Require these inputs before producing a final tailored CV:

- The generic CV source, preferably the editable source file rather than a rendered PDF.
- The complete job description or a faithful copy of it.
- Target language, geography, and output format when not obvious from the repo.

If the job description is missing, stop and request it. If the CV source is missing, search the workspace first; if still missing, stop and report the missing artifact, why it is required, the likely upstream source, and a validation command such as `rg --files -g '*cv*' -g '*resume*'`.

## Workflow

1. Discover the CV structure and build commands.
   - Read repository instructions, `README`, Makefile/flake/package files, and the active CV source.
   - Identify generated artifacts and avoid editing rendered outputs unless the repo expects that.

2. Extract the JD signal.
   - Capture exact role title, seniority, domain, location/work authorization, required stack, preferred stack, responsibilities, leadership expectations, and deal-breakers.
   - Group requirements into `must match`, `strong signal`, `nice to have`, and `cannot prove`.
   - Preserve exact JD terminology when truthful, including full names such as `Kubernetes` before abbreviations like `K8s`.

3. Map evidence.
   - Build a traceable map from each JD requirement to CV evidence: role, project, bullet, link, or source file.
   - Mark unsupported requirements explicitly. Do not add them to the CV as claims.
   - Prefer high-signal senior evidence: architecture decisions, production ownership, distributed systems, reliability, cross-functional delivery, mentoring, roadmap influence, incident handling, security, cost/performance work, and measurable business or user outcomes.

4. Choose the positioning.
   - Select the closest truthful target title or headline from the JD.
   - Make the first screen answer: "Why this candidate for this exact role?"
   - For tech lead roles, emphasize technical leadership without implying people-management responsibility unless proven.
   - For senior IC roles, emphasize hands-on depth, production systems, mentoring, and ownership.

5. Rewrite with constraints.
   - Keep bullets concrete: action, technical method, scope, and result.
   - Use metrics only when present in source evidence or provided by the user. If a denominator is unavailable, avoid naked percentage claims.
   - Replace generic phrasing with JD-relevant truthful specifics.
   - Remove or de-prioritize low-relevance content, but preserve chronology and dates.
   - Avoid keyword stuffing, exaggerated AI-generated tone, and laundry lists detached from experience.

6. Validate.
   - Build or compile the CV when the repo provides a command.
   - Check that the final document fits the expected page count and has no LaTeX/build errors.
   - Re-scan the tailored CV against the JD to ensure the strongest truthful matches are visible in the top summary, skills, and most relevant recent bullets.
   - Report any unsupported JD requirements that remain gaps.

## Senior Tech Lead Optimization Checklist

Use this checklist before finalizing:

- Role title or closest truthful equivalent appears near the top.
- Top 5-8 hard requirements from the JD appear in context, not only in skills.
- Skills are grouped by category and ordered by JD relevance.
- Recent roles carry the heaviest JD alignment.
- Leadership claims identify the mechanism: mentorship, technical direction, architecture ownership, unblock decisions, code review, delivery coordination, stakeholder communication, or hiring.
- Impact claims include scale, users, data volume, latency, reliability, revenue, cost, risk, compliance, or delivery speed when proven.
- Claims that sound surprising are backed by a concrete project, link, or source artifact.
- The document remains readable to a technical hiring manager after passing ATS matching.

## Output Expectations

When editing files, keep changes narrowly scoped to the tailored CV variant and any build wiring needed for it. Preserve reusable generic CV content unless the user asks to update the source profile.

In the final response, include:

- Files changed.
- Build/validation command and result.
- The positioning chosen for the JD.
- Unsupported or weakly supported JD requirements, if any.

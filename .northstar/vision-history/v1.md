# Does It Arabic? — Vision

## Problem
Server-side PDF, OG-image and chart libraries each do their own text layout and many break Arabic, Persian and Hebrew (disconnected letters, reversed words, misplaced numbers). Coding agents pick these libraries by default and repeat the same broken fixes. Nobody publishes a tested, machine-readable record of which library works.

## Product
An open, screenshot-backed test matrix: the same RTL invoice fixtures rendered by many real libraries, judged automatically against a Chromium/HarfBuzz reference, published as a static site, agent-readable files (matrix.json, llms.txt, skill file), a fixtures package and a check command / GitHub Action.

## Users
Full-stack developers at Arabic-market SaaS, fintech and e-commerce companies generating invoices and receipts; coding agents choosing a library; maintainers of rendering libraries who need reproducible RTL tests.

## Pillars
- Real renders, not opinions: every cell is a screenshot of real library output.
- Honest automated verdicts, labelled as machine-judged until a human reviews them.
- Agent-first distribution: matrix.json, llms.txt and a skill file.
- Reusable fixtures and a check command for your own pipeline.

## Out of scope for v1
Coding-agent benchmark runs, weekly history, Urdu/Nastaliq, publishing packages, hosted services, payments.

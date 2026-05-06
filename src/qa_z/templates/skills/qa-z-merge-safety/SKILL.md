---
name: qa-z-merge-safety
description: Make AI-generated code safer to merge by requiring QA contracts, checks, repair prompts, and verification evidence.
---

# QA-Z Merge Safety Skill

Use `qa-z guard` before claiming AI-generated code is safe to merge. Do not claim code is safe without evidence. Generate a repair prompt when checks fail, verify the repaired run, and report the merge verdict with artifact paths.

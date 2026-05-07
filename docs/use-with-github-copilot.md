# Use QA-Z With GitHub Copilot

Install the Copilot instruction template:

```bash
qa-z skill install copilot
```

Then require Copilot-assisted changes to include:

- a short change and risk summary
- `qa-z guard` evidence
- deep checks for risky surfaces
- repair prompts for failed checks
- a final merge verdict with artifact paths

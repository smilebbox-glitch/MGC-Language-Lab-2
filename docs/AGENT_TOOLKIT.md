# Codex and UI skills — pilot-safe setup

This repository includes three lightweight, project-scoped Agent Skills under .agents/skills. Codex can discover them from a local checkout of this branch; the changes do not install any executable software on the company's server.

Full upstream design tools are optional and require code/license review **on a separate development workstation**:
- https://github.com/pbakaus/impeccable
- https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- https://github.com/Nutlope/hallmark
- https://github.com/DietrichGebert/ponytail
- https://github.com/cathrynlavery/diagram-design

These skills help an agent with design and code review. They do not replace mobile/browser testing or the existing project test suite. Do not add Onyx, Scrapling/browser engines, REA or external telemetry to the pilot runtime without a scoped technical proposal.

The v6.0.31 pilot intentionally keeps the user-facing interface lightweight; design tasks must stay within that product contract.

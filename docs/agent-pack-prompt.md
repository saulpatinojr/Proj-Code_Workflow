# MASTER PROMPT — CREATE AN AGENT PACK FROM A ROLE

ROLE: [Enter the role here]

Create the complete Agent/Skill Pack for this role using the approved framework established in this conversation.

Reuse the framework, artifact structure, naming conventions, documentation depth, packaging, and validation standard. Author all role-specific content from scratch.

## 1. Derive the role requirements

Use the role, current conversation, and supplied reference files to establish:

- Mission, users, outcomes, scope, and non-goals
- Primary workflows and specialist capabilities
- Inputs, outputs, knowledge sources, and integrations
- Tools, permissions, dependencies, and operational constraints
- Security, privacy, responsible AI, failure handling, and escalation
- Examples, tests, acceptance criteria, and completion evidence

Fill meaningful capability gaps using current official documentation. Avoid peripheral Skills that do not materially support the role.

Do not ask me to repeat established information. Make reasonable assumptions and document them. Ask only when an unresolved decision would materially change the role or scope.

## 2. Preserve the canonical framework

Include:

- DESCRIPTION.md
- README.md
- AGENT-PACK-README.md
- PORTABLE_AGENT_SKILL_PACK_AUTHORING_PROMPT.md
- LICENSE
- apm.yml
- Uppercase VALIDATION_REPORT.md
- Canonical agents under .apm/agents/
- Canonical Skills under .apm/skills/
- docs/
- compatibility/
- instructions/
- prompts/
- examples/
- templates/
- hooks/
- tests/
- tooling/
- Generated targets for GitHub Copilot, Claude Code, OpenAI Codex, and Gemini CLI
- Distribution archives and SHA256 checksums

Retain canonical artifact categories. If one is genuinely inapplicable, explain why rather than silently omitting it.

Preserve the framework’s organizational pattern, but choose the number of Skills, specialists, prompts, examples, and templates according to the new role. Do not inherit another role’s counts.

## 3. Design one primary technology or role agent

Create one user-facing primary agent that can handle the role’s complete workflow.

Add optional specialist subagents only where separate expertise, context, permissions, or independent review provides concrete value. Do not create specialists merely to reproduce an organization chart.

Keep agent profiles thin. Place detailed procedures in focused Skills and shared contracts.

Primary and specialist profiles use each vendor’s documented agent directory. Do not invent a separate subagents folder.

Define specialist activation, assignment boundaries, handoff inputs, required evidence, and return format. The primary remains responsible for integration and completion.

## 4. Operationalize every Skill and hook

For each Skill or hook, define:

1. Purpose and activation conditions
2. Scope and exclusions
3. Required inputs
4. Dependencies and available tools
5. Expected workflow or behavior
6. Expected output
7. Validation requirements
8. Failure handling and escalation
9. Permissions and guardrails
10. Connection to agent instructions and workflows

Keep individual Skills useful when installed separately. Make pack-level prompts and specialists optional unless a real dependency requires them.

Hooks must perform useful, bounded checks. Clearly distinguish native vendor hooks from portable scripts or manual helpers.

## 5. Use accurate tools and permissions

Verify current official vendor Agent/Skill specifications before generating targets.

Use actual supported metadata and tool identifiers. Do not invent tool aliases, imply unavailable integrations, or claim that written instructions enforce security.

Apply least privilege and preserve existing user authorization within its scope. Require missing authority for consequential actions without repeatedly asking for approval already granted.

Do not install, publish, deploy, communicate externally, or change shared systems unless authorized.

## 6. Prevent content leakage

Previous packs are structural references only.

Do not carry forward unrelated personas, terminology, Skills, hooks, examples, business rules, integrations, or assumptions.

An element may recur only when independently relevant to the new role.

Create fresh canonical source rather than copying an entire previous pack and renaming it.

## 7. Produce the established downloads

Four primary downloads:

1. Full pack
2. Canonical Agent/Skill source
3. Reusable authoring prompt
4. Validation bundle

Secondary downloads:

- GitHub Copilot package
- Claude Code package
- OpenAI Codex package
- Gemini CLI package
- Individual validated skill.zip archives
- Bundle of individual Skill archives
- SHA256 checksums

Make the canonical source APM-friendly. Clearly distinguish a compatible source layout from any unverified APM CLI support.

## 8. Validate the integrated pack

Verify:

- Required artifacts and sections exist
- Content is specific to the requested role
- Skills, prompts, agents, hooks, and contracts reference existing files
- Installed vendor packages contain their required dependencies
- Tool permissions match responsibilities
- Metadata conforms to current vendor specifications
- Examples demonstrate documented workflows
- Tests cover critical behavior and failure conditions
- Scripts and hooks execute correctly within their supported environment
- No irrelevant prior-role content or unfinished placeholders remain
- Generated targets and archives match canonical source
- Archives are safe, complete, reproducible, and include the final validation report
- Individual Skill archives are valid
- Checksums match delivered archives

Correct discovered issues before delivery.

Distinguish structural checks, executable local tests, model behavior evaluations, and live integration evidence. Never describe an unexecuted check as passed.

## 9. Present the result

Save the complete pack in the current workspace.

Provide an ordered artifact catalog containing:

ARTIFACT NAME: PURPOSE: CONTENT:

Include the full transferable file contents in the catalog rather than flooding the chat with every file.

Finish with a concise delivery response linking the four primary downloads, vendor packages, artifact catalog, and uppercase validation report.

End with AGENT PACK VALIDATION SUMMARY covering:

- Role implemented
- Artifacts represented
- Skills and optional specialists
- Hooks and triggers
- Knowledge sources and integrations
- Permissions and guardrails
- Tests actually executed
- Genuine gaps, assumptions, and unverified behavior

SAME FRAMEWORK. SAME COMPLETENESS STANDARD. FRESH ROLE-SPECIFIC CONTENT.
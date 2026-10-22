---
type: Spec
title: Delta for [capability]
description: Spec delta for change [change-id]
status: draft
derived_from:
  - [change-id]
generated:
  by: agent:aidlc-memory
  at: [ISO-8601 with UTC offset]
---

# Delta for [capability]

Apply sections with `aidlc_memory.py archive-check` and `archive-apply`. A conflict blocks. Do not edit the living spec by hand to force a merge.

## ADDED Requirements

### Requirement: [New unique name]

The system SHALL [behavior].

#### Scenario: [Name]

- **GIVEN** [context]
- **WHEN** [action]
- **THEN** [outcome]

## MODIFIED Requirements

### Requirement: [Existing name]

The system SHALL [replacement text for the whole requirement].

#### Scenario: [Name]

- **GIVEN** [context]
- **WHEN** [action]
- **THEN** [outcome]

## REMOVED Requirements

### Requirement: [Existing name]

## RENAMED Requirements

Renames are not applied automatically. `archive-check` reports `rename_requires_human` and `archive-apply` stops.

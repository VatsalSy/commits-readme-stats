---
name: release-commits-readme-stats
description: Analyze commits since last tag, choose semantic bump (major/minor/patch), create a new tag, and publish GitHub release notes using release-notes-writer conventions.
---

# Release Commits Readme Stats

Release automation playbook for `commits-readme-stats` with semantic version tags:

- Tag format: `vMAJOR.MINOR.PATCH`
- Example progression:
  - `v4.0.0 -> v4.0.1 -> v4.1.0 -> v5.0.0`

Use this skill when the user asks to cut/publish a release for this repository.

## Required Companion Skill

Always invoke `$release-notes-writer` to draft the release notes body and section structure.

Important: this skill overrides versioning to full semver (`vMAJOR.MINOR.PATCH`) even if `$release-notes-writer` examples show `vMAJOR.MINOR`.

## Prerequisites

Run before any release operation:

```bash
git status --short --branch
git fetch --tags --prune
gh auth status
```

Rules:
- Working tree must be clean.
- Current branch should be `main` unless user explicitly requests another target.
- `gh` authentication must be valid.

## Step 1: Discover Last Tag and Change Set

```bash
LAST_TAG="$(git tag --list 'v*' --sort=-version:refname | head -n1)"
```

If no tag exists:
- Use `v1.0.0` as initial release unless user specifies otherwise.
- Build change context from full history.

If tag exists:

```bash
git log --oneline "$LAST_TAG"..HEAD
git log --no-merges --pretty=format:'%h %s' "$LAST_TAG"..HEAD
git diff --name-only "$LAST_TAG"..HEAD
git diff --stat "$LAST_TAG"..HEAD
```

If zero commits since last tag, stop and report "No release needed."

## Step 2: Decide Bump Type (Major/Minor/Patch)

Pick the highest required bump from commit messages and effective behavior changes.

### Major bump
Choose `major` when any of these are true:
- Commit follows conventional-commit breaking syntax (`type!:`) or contains `BREAKING CHANGE`.
- Backward-incompatible behavior in action inputs/outputs/public config.
- Required environment variables or defaults are removed/renamed incompatibly.

### Minor bump
Choose `minor` when:
- New backward-compatible feature is added (typically `feat:` commits).
- New optional capabilities or inputs are introduced without breaking existing users.

### Patch bump
Choose `patch` for:
- Fixes, refactors, dependency bumps, docs/tests/chore changes.
- Stability and correctness improvements without feature surface expansion.

## Step 3: Compute Next Version

Normalize the last tag to semver first:
- `v4.0` should be treated as `v4.0.0`.
- `v3.0.0` stays `v3.0.0`.

Bump logic:
- `major`: `X.Y.Z -> (X+1).0.0`
- `minor`: `X.Y.Z -> X.(Y+1).0`
- `patch`: `X.Y.Z -> X.Y.(Z+1)`

Candidate tag must not already exist locally or remotely.

## Step 4: Draft Release Notes (via release-notes-writer)

Use `$release-notes-writer` formatting and guidance to create notes:

- `## What's New` summary
- `### ✨ Features` (if any)
- `### 🔧 Improvements` (if any)
- `### 🐛 Bug Fixes` (if any)
- `### ⚠️ Breaking Changes` (major only)
- `**Full Changelog**: <previous-tag>...<new-tag>`

Write notes to a file:

```bash
NOTES_FILE="/tmp/commits-readme-stats-${NEW_TAG}-notes.md"
```

## Step 5: Confirm Before Git Operations

Present to the user:
- Last tag
- Commits since last tag
- Proposed bump rationale (`major|minor|patch`)
- Proposed new tag
- Draft release notes

Proceed only after explicit user approval.

## Step 6: Create Tag, Push, and Publish Release

```bash
git tag -a "$NEW_TAG" -m "Release $NEW_TAG"
git push origin "$NEW_TAG"
gh release create "$NEW_TAG" \
  --repo VatsalSy/commits-readme-stats \
  --target main \
  --title "GitHub Commit Stats $NEW_TAG" \
  --notes-file "$NOTES_FILE"
```

## Step 7: Post-Release Validation

Verify:

```bash
git show --no-patch "$NEW_TAG"
gh release view "$NEW_TAG" --repo VatsalSy/commits-readme-stats
```

Report:
- Final tag
- Release URL
- Number of commits included
- Any follow-up doc/version reference updates needed

## Error Recovery

| Error | Resolution |
|-------|------------|
| Tag exists | Compute next available tag and re-propose |
| Dirty working tree | Ask user to commit/stash, or stop |
| No commits since last tag | Skip release and report |
| gh unauthenticated | Run `gh auth login` |
| Push/release rejected | Check permissions/protection rules and retry with corrected target |


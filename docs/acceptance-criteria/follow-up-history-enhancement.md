# Acceptance Criteria: Follow-up History Enhancement

> **Source**: docs/prd/sales-follow-up-closure-deepening.md (Module: follow-up-history-enhancement)
> **Generated**: 2026-06-14
> **Functional Points**: 3
> **Scenarios**: 10 (Happy: 3 | Error: 2 | Boundary: 5)

---

## 1. Display Result Category and Reason Tags

### AC-01: History item shows category and reason tags
**Type**: Happy Path | **Priority**: P0

Given a follow-up record exists with `result_category="未接通"`, `reason="无人接听"`
When the user views the follow-up history on `/workbench/{lead-id}` or `/leads/{lead-id}`
Then the history item displays a tag "未接通" and a tag "无人接听"

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/lead-detail/__tests__/follow-up-history.test.tsx::test_ac01_shows_category_and_reason_tags

### AC-01-E1: Legacy follow-up without category shows fallback
**Type**: Error Case | **Priority**: P1

Given a legacy follow-up record exists with `result="未接通"` and no `result_category`
When the user views the follow-up history
Then the history item displays a muted tag "未接通 (legacy)"
And no empty category tag is shown

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/lead-detail/__tests__/follow-up-history.test.tsx::test_ac01_e1_legacy_fallback_without_category

### AC-01-B1: Empty notes do not render collapse control
**Type**: Boundary | **Priority**: P2

Given a follow-up record has `notes=""`
When the user views the history item
Then no "展开" button is rendered for notes

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/lead-detail/__tests__/follow-up-history.test.tsx::test_ac01_b1_empty_notes_no_expand

---

## 2. Highlight Overdue Next Action At

### AC-02: Overdue next_action_at is shown in red
**Type**: Happy Path | **Priority**: P0

Given a follow-up record has `next_action_at` earlier than current time
When the user views the follow-up history
Then the "下次跟进" time text is rendered in red (text-danger)

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/lead-detail/__tests__/follow-up-history.test.tsx::test_ac02_overdue_next_action_at_red

### AC-02-E1: Future next_action_at is not highlighted
**Type**: Error Case | **Priority**: P1

Given a follow-up record has `next_action_at` later than current time
When the user views the follow-up history
Then the "下次跟进" time text is rendered in normal muted color

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/lead-detail/__tests__/follow-up-history.test.tsx::test_ac02_e1_future_next_action_at_normal

### AC-02-B1: Missing next_action_at shows dash
**Type**: Boundary | **Priority**: P2

Given a follow-up record has `next_action_at=null`
When the user views the history item
Then the "下次跟进" row shows "-"

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/lead-detail/__tests__/follow-up-history.test.tsx::test_ac02_b1_missing_next_action_at_dash

---

## 3. Fold Notes Longer Than 60 Characters

### AC-03: Long notes are folded by default
**Type**: Happy Path | **Priority**: P0

Given a follow-up record has `notes` with 150 characters
When the user views the history item
Then only the first 60 characters are displayed
And an "展开" link is visible

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/lead-detail/__tests__/follow-up-history.test.tsx::test_ac03_long_notes_folded_by_default

### AC-03-E1: Clicking expand shows full notes
**Type**: Error Case | **Priority**: P1

Given a history item with folded notes
When the user clicks "展开"
Then the full note text is displayed
And the link text changes to "收起"

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/lead-detail/__tests__/follow-up-history.test.tsx::test_ac03_e1_click_expand_shows_full_notes

### AC-03-B1: Notes exactly 60 characters are not folded
**Type**: Boundary | **Priority**: P2

Given a follow-up record has `notes` with exactly 60 characters
When the user views the history item
Then the full note is displayed
And no "展开" link is shown

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/lead-detail/__tests__/follow-up-history.test.tsx::test_ac03_b1_exactly_sixty_not_folded

### AC-03-B2: Notes shorter than 60 characters are not folded
**Type**: Boundary | **Priority**: P2

Given a follow-up record has `notes` with 30 characters
When the user views the history item
Then the full note is displayed
And no "展开" link is shown

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/lead-detail/__tests__/follow-up-history.test.tsx::test_ac03_b2_shorter_than_sixty_not_folded

### AC-03-B3: Notes with multibyte CJK characters count correctly
**Type**: Boundary | **Priority**: P2

Given a follow-up record has `notes` with 40 Chinese characters
When the user views the history item
Then the full note is displayed (40 < 60)
And no "展开" link is shown

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/lead-detail/__tests__/follow-up-history.test.tsx::test_ac03_b3_cjk_characters_count_correctly

---

## Self-Check Report

| Check | Status | Notes |
|-------|--------|-------|
| Each functional point has happy path | ✅ | AC-01, AC-02, AC-03 |
| Write operations have error scenarios | N/A | 前端展示模块 |
| Boundary conditions covered | ✅ | AC-01-B1, AC-02-B1, AC-03-B1/B2/B3 |
| Role/permission scenarios covered | N/A | 前端展示模块 |
| State transition scenarios covered | N/A | 前端展示模块 |
| Idempotency considered | N/A | 前端展示模块 |
| Concurrency conflicts addressed | N/A | 前端展示模块 |
| Default value behavior specified | ✅ | AC-01-E1, AC-02-B1 |
| Data lifecycle clear (soft/hard delete) | N/A | 前端展示模块 |

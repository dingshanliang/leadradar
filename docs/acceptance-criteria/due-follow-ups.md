# Acceptance Criteria: Due Follow-ups

> **Source**: docs/prd/sales-follow-up-closure-deepening.md (Module: due-follow-ups)
> **Generated**: 2026-06-14
> **Functional Points**: 3
> **Scenarios**: 11 (Happy: 3 | Error: 4 | Boundary: 4)

---

## 1. Backend Returns Due Follow-ups Excluding Terminal Statuses

### AC-01: List only non-terminal due follow-ups
**Type**: Happy Path | **Priority**: P0
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_due_follow_ups.py::TestListDueFollowUps::test_ac01_list_only_non_terminal_due_follow_ups

Given `FollowUp` records exist with `next_action_at` in the past or next 7 days
And some associated leads have statuses `won`, `lost`, `invalid`, or `blocked`
When `GET /api/v1/follow-ups/due` is called
Then response status is 200
And the returned list excludes follow-ups whose lead status is terminal
And the list is sorted by `next_action_at` ascending

### AC-01-E1: Unauthorized request
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_due_follow_ups.py::TestListDueFollowUps::test_ac01_e1_unauthorized_request

Given the request does not include a valid JWT token
When `GET /api/v1/follow-ups/due` is called
Then response status is 401

### AC-01-B1: Empty list
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_due_follow_ups.py::TestListDueFollowUps::test_ac01_b1_empty_list

Given no follow-ups have `next_action_at` in the past or next 7 days
Or all due follow-ups belong to terminal-status leads
When `GET /api/v1/follow-ups/due` is called
Then response status is 200
And the returned list is empty

### AC-01-B2: Future follow-ups beyond 7 days are excluded
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_due_follow_ups.py::TestListDueFollowUps::test_ac01_b2_future_follow_ups_beyond_7_days_excluded

Given a follow-up has `next_action_at` 10 days in the future
When `GET /api/v1/follow-ups/due` is called
Then the follow-up is not included in the response

---

## 2. Sidebar Badge Shows Due Count

### AC-02: Badge appears when due follow-ups exist
**Type**: Happy Path | **Priority**: P0
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/layout/__tests__/sidebar.test.tsx::AC-02: displays a red badge with the due count

Given the current user has 3 due follow-ups
When the sidebar is rendered
Then a red badge with number "3" appears next to the lead pool icon or a new "到期跟进" nav item

### AC-02-E1: Badge hidden when count is zero
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/layout/__tests__/sidebar.test.tsx::AC-02-E1: hides the badge when the count is zero

Given the current user has 0 due follow-ups
When the sidebar is rendered
Then no badge is displayed

### AC-02-B1: Badge caps at 99+
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/layout/__tests__/sidebar.test.tsx::AC-02-B1: caps the badge at 99+ and shows exact count in tooltip

Given the current user has 150 due follow-ups
When the sidebar is rendered
Then the badge displays "99+"
And hovering the badge shows the exact count in a tooltip

### AC-02-B2: Badge updates after creating a follow-up with next_action_at in the past
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/components/layout/__tests__/sidebar.test.tsx::AC-02-B2: updates the badge when the count changes

Given the badge currently shows "2"
When the user submits a new follow-up with `next_action_at` set to 1 minute ago
Then the badge updates to "3" without requiring a full page reload

---

## 3. Due Follow-ups List Page

### AC-03: List page displays due follow-ups
**Type**: Happy Path | **Priority**: P0
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/(with-sidebar)/due-follow-ups/page.test.tsx::AC-03: renders due follow-ups sorted by next_action_at

Given the user navigates to `/due-follow-ups`
And the backend returns 3 due follow-ups
Then the page renders a list sorted by `next_action_at` ascending
And each row shows organization name, due time, last result, and a "进入工作台" button

### AC-03-E1: Empty state
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/(with-sidebar)/due-follow-ups/page.test.tsx::AC-03-E1: shows empty state when the list is empty

Given the backend returns an empty list
When the user navigates to `/due-follow-ups`
Then the page shows an empty state with text "暂无到期跟进"

### AC-03-E2: API error shows retry
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/(with-sidebar)/due-follow-ups/page.test.tsx::AC-03-E2: shows error state with retry button

Given the backend returns `500`
When the user navigates to `/due-follow-ups`
Then the page shows an error state with a "重试" button

### AC-03-B1: Clicking action navigates to workbench
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/(with-sidebar)/due-follow-ups/page.test.tsx::AC-03-B1: clicking 进入工作台 navigates to workbench

Given the user is on `/due-follow-ups`
When the user clicks "进入工作台" for lead `lead-id`
Then the browser navigates to `/workbench/{lead-id}`

---

## Self-Check Report

| Check | Status | Notes |
|-------|--------|-------|
| Each functional point has happy path | ✅ | AC-01, AC-02, AC-03 |
| Write operations have error scenarios | N/A | 本模块以读取/展示为主 |
| Boundary conditions covered | ✅ | AC-01-B1/B2, AC-02-B1/B2, AC-03-B1 |
| Role/permission scenarios covered | ✅ | AC-01-E1 覆盖未授权 |
| State transition scenarios covered | N/A | 本模块不修改状态 |
| Idempotency considered | N/A | 读取操作 |
| Concurrency conflicts addressed | N/A | 读取操作 |
| Default value behavior specified | N/A | 读取操作 |
| Data lifecycle clear (soft/hard delete) | N/A | 本模块不删除数据 |

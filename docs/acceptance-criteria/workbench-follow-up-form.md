# Acceptance Criteria: Workbench Follow-up Form

> **Source**: docs/prd/sales-follow-up-closure-deepening.md (Module: workbench-follow-up-form)
> **Generated**: 2026-06-14
> **Functional Points**: 3
> **Scenarios**: 11 (Happy: 3 | Error: 4 | Boundary: 4)

---

## 1. Display Next Action At Datetime Picker

### AC-01: Datetime picker is visible on workbench
**Type**: Happy Path | **Priority**: P0
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac01_datetime_picker_visible

Given the user is on `/workbench/{lead-id}`
And the page has finished loading lead detail
Then the follow-up form contains a labeled input "下次跟进时间"
And the input allows selecting both date and time (precision to hour)

### AC-01-E1: Submit is disabled when result is not selected
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac01_e1_submit_disabled_without_result

Given the user is on `/workbench/{lead-id}`
And the user has selected a next_action_at but has not selected a result category/reason
Then the "提交跟进" button is disabled
And the user cannot submit the form

### AC-01-B1: next_action_at defaults to suggestion from backend
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac01_b1_default_next_action_suggestion

Given the user is on `/workbench/{lead-id}`
And the backend meta endpoint returns a suggested next_action_at for the selected result category
When the user selects result category `未接通`
Then the "下次跟进时间" input is pre-filled with a datetime 2 hours after now

### AC-01-B2: User can clear next_action_at
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac01_b2_clear_next_action_at

Given the user is on `/workbench/{lead-id}`
And the "下次跟进时间" input has a value
When the user clears the input
Then the form submits successfully without next_action_at
And no due reminder is created for this follow-up

---

## 2. Two-Level Result Selection (Category → Reason)

### AC-02: Category select populates reason select
**Type**: Happy Path | **Priority**: P0
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac02_category_populates_reason_select

Given the user is on `/workbench/{lead-id}`
And `GET /api/v1/meta` returns call result dictionary with category `未接通` and reasons `["无人接听", "关机", "占线"]`
When the user selects category `未接通`
Then the "具体原因" select becomes enabled
And its options are `["无人接听", "关机", "占线"]`

### AC-02-E1: Reason select is disabled until category is chosen
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac02_e1_reason_disabled_until_category_chosen

Given the user is on `/workbench/{lead-id}`
And no category is selected
Then the "具体原因" select is disabled
And placeholder text reads "请先选择结果类别"

### AC-02-E2: Submit without reason shows validation error
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac02_e2_submit_without_reason_shows_error

Given the user is on `/workbench/{lead-id}`
And the user has selected category `未接通` but not a reason
When the user clicks "提交跟进"
Then the form does not submit
And a visible error message "请选择具体原因" is displayed

### AC-02-B1: Changing category resets reason
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac02_b1_changing_category_resets_reason

Given the user has selected category `未接通` and reason `无人接听`
When the user changes category to `接通有意向`
Then the reason select is cleared
And the user must select a new reason before submitting

---

## 3. Submit Form and Update UI

### AC-03: Submitting form creates follow-up and refreshes history
**Type**: Happy Path | **Priority**: P0
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac03_submit_creates_follow_up_refreshes_resets

Given the user is on `/workbench/{lead-id}`
And the user has selected channel `phone`, category `未接通`, reason `无人接听`, next_action_at in the future
When the user clicks "提交跟进"
Then `POST /api/v1/leads/{lead-id}/follow-ups` is called with the correct payload
And the follow-up history list refreshes
And the form resets to initial state
And the lead status badge updates to reflect the mapped status if changed

### AC-03-E1: API error shows error state
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac03_e1_api_error_preserves_values

Given the user is on `/workbench/{lead-id}`
And the backend returns `422` with detail "结果类别与原因不匹配"
When the form submission fails
Then an error message "结果类别与原因不匹配" is displayed
And the form values are preserved for correction

### AC-03-B1: Double-clicking submit does not create duplicate follow-ups
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac03_b1_double_click_does_not_duplicate

Given the user clicks "提交跟进" twice in rapid succession
Then only one `POST /api/v1/leads/{lead-id}/follow-ups` request is sent
And the submit button is disabled until the request completes

---

## Self-Check Report

| Check | Status | Notes |
|-------|--------|-------|
| Each functional point has happy path | ✅ | AC-01, AC-02, AC-03 |
| Write operations have error scenarios | ✅ | AC-01-E1, AC-02-E1/E2, AC-03-E1 |
| Boundary conditions covered | ✅ | AC-01-B1/B2, AC-02-B1, AC-03-B1 |
| Role/permission scenarios covered | N/A | MVP 不细分权限 |
| State transition scenarios covered | ✅ | AC-03 包含 lead status 更新 |
| Idempotency considered | ✅ | AC-03-B1 防止重复提交 |
| Concurrency conflicts addressed | N/A | 前端模块 |
| Default value behavior specified | ✅ | AC-01-B1 默认建议时间 |
| Data lifecycle clear (soft/hard delete) | N/A | 前端模块 |

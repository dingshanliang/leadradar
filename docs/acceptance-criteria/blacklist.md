# Acceptance Criteria: Blacklist

> **Source**: docs/prd/sales-follow-up-closure-deepening.md (Module: blacklist)
> **Generated**: 2026-06-14
> **Functional Points**: 4
> **Scenarios**: 14 (Happy: 4 | Error: 6 | Boundary: 4)

---

## 1. Auto-Block Lead on Invalid/Refuse Follow-up

### AC-01: Submitting invalid follow-up blocks the lead
**Type**: Happy Path | **Priority**: P0

Given a lead exists with id `lead-id` and belongs to organization `org-id`
And the request body contains `result_category="无效"`, `reason="不需要服务"`
When `POST /api/v1/leads/{lead-id}/follow-ups` is called
Then response status is 201
And the lead's `lead_status` is updated to `blocked`
And a `Blocklist` record is created with `organization_id=org-id` and `reason="不需要服务"`

**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_blacklist.py::TestAutoBlockOnInvalidFollowUp::test_ac01_submitting_invalid_follow_up_blocks_lead

### AC-01-E1: Lead already blocked
**Type**: Error Case | **Priority**: P1

Given a lead exists with id `lead-id` and is already `blocked`
And the organization `org-id` is already in `Blocklist`
When `POST /api/v1/leads/{lead-id}/follow-ups` is called with `result_category="无效"`
Then response status is 201
And no duplicate `Blocklist` record is created for the same organization

**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_blacklist.py::TestAutoBlockOnInvalidFollowUp::test_ac01_e1_lead_already_blocked_no_duplicate_blocklist

### AC-01-B1: Block only this lead without blocking organization
**Type**: Boundary | **Priority**: P2

Given a lead exists with id `lead-id` belonging to organization `org-id`
And the request body contains `result_category="无效"`, `reason="不需要服务"`, `block_organization=false`
When the follow-up is submitted
Then the lead status becomes `blocked`
And no `Blocklist` record is created for `org-id`

**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_blacklist.py::TestAutoBlockOnInvalidFollowUp::test_ac01_b1_block_only_lead_without_organization

### AC-01-B2: Block organization checkbox defaults to false
**Type**: Boundary | **Priority**: P2

Given the workbench form is rendered
Then the "同时屏蔽整个机构" checkbox is unchecked by default

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/workbench/[id]/__tests__/page.test.tsx::test_ac01_b2_block_organization_checkbox_defaults_unchecked

---

## 2. Blocklist CRUD API

### AC-02: List blocked organizations
**Type**: Happy Path | **Priority**: P0

Given the `Blocklist` table contains 2 records
When `GET /api/v1/blocklist` is called
Then response status is 200
And the response body contains a list of 2 blocklist entries with `organization_id`, `reason`, and `created_at`

**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_blacklist.py::TestBlocklistCrud::test_ac02_list_blocked_organizations

### AC-02-E1: Unauthorized request
**Type**: Error Case | **Priority**: P1

Given the request does not include a valid JWT token
When `GET /api/v1/blocklist` is called
Then response status is 401

**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_blacklist.py::TestBlocklistCrud::test_ac02_e1_unauthorized_request

### AC-03: Unblock an organization
**Type**: Happy Path | **Priority**: P0

Given organization `org-id` is in `Blocklist` with id `block-id`
When `DELETE /api/v1/blocklist/{block-id}` is called
Then response status is 204
And the `Blocklist` record is removed
And all leads belonging to `org-id` with status `blocked` are updated to status `new`

**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_blacklist.py::TestBlocklistCrud::test_ac03_unblock_organization

### AC-03-E1: Unblock non-existent record
**Type**: Error Case | **Priority**: P1

Given no blocklist record exists with id `00000000-0000-0000-0000-000000000000`
When `DELETE /api/v1/blocklist/00000000-0000-0000-0000-000000000000` is called
Then response status is 404

**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_blacklist.py::TestBlocklistCrud::test_ac03_e1_unblock_nonexistent_record

### AC-03-B1: Idempotent unblock
**Type**: Boundary | **Priority**: P2

Given organization `org-id` has already been unblocked
When `DELETE /api/v1/blocklist/{block-id}` is called again
Then response status is 404
And no error is thrown

**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_blacklist.py::TestBlocklistCrud::test_ac03_b1_idempotent_unblock

---

## 3. Lead Pool Excludes Blocked Leads by Default

### AC-04: Blocked leads hidden from lead pool
**Type**: Happy Path | **Priority**: P0

Given the lead pool contains 3 leads, one with status `blocked`
When `GET /api/v1/leads` is called without status filter
Then response status is 200
And the returned list contains only the 2 non-blocked leads

**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_blacklist.py::TestLeadPoolExcludesBlocked::test_ac04_blocked_leads_hidden_from_lead_pool

### AC-04-E1: Explicitly filter by blocked status shows blocked leads
**Type**: Error Case | **Priority**: P1

Given the lead pool contains 1 lead with status `blocked`
When `GET /api/v1/leads?status=blocked` is called
Then response status is 200
And the returned list contains the blocked lead

**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_blacklist.py::TestLeadPoolExcludesBlocked::test_ac04_e1_explicit_blocked_filter_shows_blocked

### AC-04-B1: Blocked leads excluded from dashboard stats
**Type**: Boundary | **Priority**: P2

Given there are 5 leads total, 1 blocked
When `GET /api/v1/stats` is called
Then `total` counts only the 4 non-blocked leads
And `invalid_rate` is calculated excluding blocked leads

**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_blacklist.py::TestLeadPoolExcludesBlocked::test_ac04_b1_blocked_leads_excluded_from_stats

---

## 4. Frontend Block/Unblock on Lead Detail Page

### AC-05: Block button visible for non-blocked lead
**Type**: Happy Path | **Priority**: P0

Given the user is on `/leads/{lead-id}`
And the lead status is not `blocked`
Then a "屏蔽" button is visible in the action area

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/(with-sidebar)/leads/[id]/__tests__/page.test.tsx::test_ac05_block_button_visible_for_non_blocked_lead

### AC-05-E1: Block button hidden for blocked lead
**Type**: Error Case | **Priority**: P1

Given the user is on `/leads/{lead-id}`
And the lead status is `blocked`
Then the "屏蔽" button is not visible
And an "解除屏蔽" button is visible instead

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/(with-sidebar)/leads/[id]/__tests__/page.test.tsx::test_ac05_e1_unblock_button_visible_for_blocked_lead

### AC-06: Clicking unblock restores lead status
**Type**: Happy Path | **Priority**: P0

Given the user is on `/leads/{lead-id}`
And the lead status is `blocked`
When the user clicks "解除屏蔽"
Then `DELETE /api/v1/blocklist/{block-id}` is called
And the page refreshes to show the lead status as `new`
And the "屏蔽" button reappears

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/(with-sidebar)/leads/[id]/__tests__/page.test.tsx::test_ac06_click_unblock_restores_lead_status

### AC-06-B1: Unblock triggers list refresh
**Type**: Boundary | **Priority**: P2

Given the user unblocks a lead on the detail page
When the operation succeeds
Then navigating back to the lead pool shows the unblocked lead in the default list

**Status**: ✅ PASS | 2026-06-14 | Test: web/src/app/(with-sidebar)/leads/[id]/__tests__/page.test.tsx::test_ac06_click_unblock_restores_lead_status

---

## Self-Check Report

| Check | Status | Notes |
|-------|--------|-------|
| Each functional point has happy path | ✅ | AC-01, AC-02, AC-03, AC-04, AC-05, AC-06 |
| Write operations have error scenarios | ✅ | AC-01-E1, AC-02-E1, AC-03-E1 |
| Boundary conditions covered | ✅ | AC-01-B1/B2, AC-03-B1, AC-04-B1, AC-06-B1 |
| Role/permission scenarios covered | ✅ | AC-02-E1 覆盖未授权访问 |
| State transition scenarios covered | ✅ | AC-03 覆盖 blocked → new |
| Idempotency considered | ✅ | AC-03-B1 |
| Concurrency conflicts addressed | N/A | 单次记录操作 |
| Default value behavior specified | ✅ | AC-01-B2 默认不屏蔽机构 |
| Data lifecycle clear (soft/hard delete) | ✅ | AC-03 硬删除 Blocklist 记录 |

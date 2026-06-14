# Acceptance Criteria: Follow-up Schema Extension

> **Source**: docs/prd/sales-follow-up-closure-deepening.md (Module: follow-up-schema-extension)
> **Generated**: 2026-06-14
> **Functional Points**: 3
> **Scenarios**: 13 (Happy: 4 | Error: 6 | Boundary: 3)

---

## 1. Create Follow-up with Next Action At

### AC-01: Submit follow-up with valid next_action_at
**Type**: Happy Path | **Priority**: P0
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestCreateFollowUpWithNextActionAt::test_create_follow_up_with_valid_next_action_at

Given a lead exists with id `lead-id`
And the request body contains `channel="phone"`, `result_category="未接通"`, `reason="无人接听"`, `notes="稍后再打"`, `next_action_at="2026-06-15T10:00:00+00:00"`
When `POST /api/v1/leads/{lead-id}/follow-ups` is called
Then response status is 201
And the returned `FollowUpOut` contains `next_action_at` equal to the provided value
And the stored `FollowUp.next_action_at` is set to the provided UTC datetime

### AC-01-E1: next_action_at is in the past
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestCreateFollowUpWithNextActionAt::test_create_follow_up_next_action_at_in_past

Given a lead exists with id `lead-id`
And the request body contains `next_action_at` earlier than current UTC time
When `POST /api/v1/leads/{lead-id}/follow-ups` is called
Then response status is 422
And response body contains `{"detail": "下次跟进时间必须晚于当前时间"}`

### AC-01-E2: Lead does not exist
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestCreateFollowUpWithNextActionAt::test_create_follow_up_lead_not_found

Given no lead exists with id `00000000-0000-0000-0000-000000000000`
When `POST /api/v1/leads/00000000-0000-0000-0000-000000000000/follow-ups` is called
Then response status is 404
And response body contains `{"detail": "Lead not found"}`

### AC-01-B1: next_action_at is omitted
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestCreateFollowUpWithNextActionAt::test_create_follow_up_without_next_action_at

Given a lead exists with id `lead-id`
And the request body does not contain `next_action_at`
When `POST /api/v1/leads/{lead-id}/follow-ups` is called
Then response status is 201
And the returned `FollowUpOut.next_action_at` is `null`

### AC-01-B2: next_action_at is explicitly set to null
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestCreateFollowUpWithNextActionAt::test_create_follow_up_null_next_action_at

Given a lead exists with id `lead-id`
And the request body contains `next_action_at: null`
When `POST /api/v1/leads/{lead-id}/follow-ups` is called
Then response status is 201
And the returned `FollowUpOut.next_action_at` is `null`

---

## 2. Structured Call Result (result_category + reason)

### AC-02: Submit follow-up with valid category and reason
**Type**: Happy Path | **Priority**: P0
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestStructuredCallResult::test_create_follow_up_with_category_and_reason

Given a lead exists with id `lead-id`
And `data/call_results.yml` defines category `未接通` with reasons `["无人接听", "关机", "占线"]`
And the request body contains `result_category="未接通"`, `reason="无人接听"`
When `POST /api/v1/leads/{lead-id}/follow-ups` is called
Then response status is 201
And the returned `FollowUpOut` contains `result_category="未接通"` and `reason="无人接听"`
And the stored `FollowUp.result` is `"未接通:无人接听"`

### AC-02-E1: reason is not in the allowed dictionary
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestStructuredCallResult::test_reason_not_in_allowed_dictionary

Given a lead exists with id `lead-id`
And the request body contains `result_category="未接通"`, `reason="不存在的原因"`
When `POST /api/v1/leads/{lead-id}/follow-ups` is called
Then response status is 422
And response body contains `{"detail": "Invalid follow-up reason"}`

### AC-02-E2: result_category and reason mismatch
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestStructuredCallResult::test_result_category_and_reason_mismatch

Given `data/call_results.yml` defines reason `"无人接听"` under category `未接通`, not under `接通有意向`
And the request body contains `result_category="接通有意向"`, `reason="无人接听"`
When `POST /api/v1/leads/{lead-id}/follow-ups` is called
Then response status is 422
And response body contains `{"detail": "结果类别与原因不匹配"}`

### AC-02-E3: reason is missing
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestStructuredCallResult::test_reason_missing

Given a lead exists with id `lead-id`
And the request body contains `result_category="未接通"` but no `reason`
When `POST /api/v1/leads/{lead-id}/follow-ups` is called
Then response status is 422
And response body contains `{"detail": "reason 字段必填"}`

### AC-02-B1: Legacy follow-ups without category/reason remain readable
**Type**: Boundary | **Priority**: P2
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestStructuredCallResult::test_legacy_follow_up_without_category_is_readable

Given a `FollowUp` record exists in the database with `result="未接通"` and no structured category/reason
When `GET /api/v1/leads/{lead-id}/follow-ups` is called
Then response status is 200
And the returned item contains `result="未接通"`, `result_category=null`, `reason=null`

---

## 3. Suggest Default Next Action At

### AC-03: API returns suggested next_action_at for known result
**Type**: Happy Path | **Priority**: P0
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestSuggestDefaultNextActionAt::test_suggestion_for_known_result

Given `data/follow_up_suggestions.yml` defines rule `未接通: 2h`
When `GET /api/v1/meta` is called (or a dedicated suggestion endpoint)
Then the response includes a suggestion mapping where result `"未接通"` maps to a datetime 2 hours after current UTC time

### AC-03-E1: Unknown result has no suggestion
**Type**: Error Case | **Priority**: P1
**Status**: ✅ PASS | 2026-06-14 | Test: tests/test_follow_up_schema_extension.py::TestSuggestDefaultNextActionAt::test_suggestion_for_unknown_result

Given `data/follow_up_suggestions.yml` does not define a rule for result `"未知结果"`
When the suggestion endpoint is queried for result `"未知结果"`
Then response status is 200
And the returned suggested `next_action_at` is `null`

---

## Self-Check Report

| Check | Status | Notes |
|-------|--------|-------|
| Each functional point has happy path | ✅ | AC-01, AC-02, AC-03 |
| Write operations have error scenarios | ✅ | AC-01-E1/E2, AC-02-E1/E2/E3 |
| Boundary conditions covered | ✅ | AC-01-B1/B2, AC-02-B1 |
| Role/permission scenarios covered | N/A | MVP 不细分权限 |
| State transition scenarios covered | N/A | 本模块不涉及状态机变更 |
| Idempotency considered | N/A | 创建操作允许重复提交 |
| Concurrency conflicts addressed | N/A | 单条记录创建，无并发冲突 |
| Default value behavior specified | ✅ | AC-01-B1/B2 覆盖 next_action_at 缺失/为空 |
| Data lifecycle clear (soft/hard delete) | N/A | 本模块不删除数据 |

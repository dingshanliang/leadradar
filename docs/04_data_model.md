# 04 数据模型

## 1. 核心实体

### Source

数据源定义。

字段：

- id
- name
- source_type
- base_url
- priority
- crawl_mode
- rate_limit
- enabled

### CrawlTask

采集任务。

字段：

- id
- source_id
- query
- status
- started_at
- finished_at
- error_message

### RawDocument

原始网页/公告/PDF 文本。

字段：

- id
- source_id
- url
- title
- published_at
- fetched_at
- raw_html
- extracted_text
- content_hash
- document_type
- parse_status

### ExtractionRun

LLM 抽取记录。

字段：

- id
- raw_document_id
- llm_provider
- model
- prompt_version
- raw_response
- parsed_json
- confidence
- status
- created_at

### Organization

机构/企业。

字段：

- id
- name
- normalized_name
- organization_type
- province
- city
- county
- industry
- official_website
- public_phone
- public_email
- credit_code

### Signal

预算/经营/资质信号。

字段：

- id
- raw_document_id
- organization_id
- signal_type
- title
- summary
- budget_amount
- expected_time
- published_at
- matched_keywords
- source_url
- evidence_text
- confidence

### Lead

可跟进销售线索。

字段：

- id
- organization_id
- primary_signal_id
- customer_type
- recommended_package
- budget_bucket
- lead_status
- owner
- created_at
- updated_at

### LeadScore

线索评分。

字段：

- id
- lead_id
- total_score
- grade
- budget_strength_score
- scenario_fit_score
- timing_score
- reachability_score
- leverage_score
- score_reason
- version

### Contact

公开业务联系信息。

字段：

- id
- organization_id
- name
- role
- phone
- email
- source_url
- is_public_business_contact
- do_not_contact

### FollowUp

跟进记录。

字段：

- id
- lead_id
- contact_id
- channel
- result
- notes
- next_action_at
- created_at

### Blocklist

拒绝联系或禁止联系。

字段：

- id
- organization_id
- contact_value_hash
- reason
- created_at

## 2. 状态枚举

### Lead status

```text
new
qualified
called
connected
diagnosis_scheduled
proposal_sent
won
lost
invalid
blocked
```

### Signal type

```text
procurement_intent
tender_notice
winning_notice
contract_notice
certification_registry
recruiting_signal
exhibition_signal
product_launch
packaging_upgrade
channel_partner
company_website
news_report
```

## 3. 去重策略

- RawDocument：url + content_hash
- Signal：organization + project_name + budget_amount + published_at
- Organization：normalized_name + province/city；有 credit_code 时优先 credit_code
- Contact：organization + phone/email hash

## 4. 隐私与审计字段

需要保留：

- source_url
- fetched_at
- evidence_text
- processing_basis：public_business_information / public_procurement_notice / registry
- do_not_contact
- deleted_at / redacted_at（后续）

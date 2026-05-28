from leadradar.models import (
    Blocklist,
    Contact,
    CrawlTask,
    CrawlTaskStatus,
    ExtractionRun,
    ExtractionRunStatus,
    FollowUp,
    Lead,
    LeadScore,
    LeadStatus,
    Organization,
    RawDocument,
    Signal,
    Source,
)


def test_all_models_importable():
    """Verify all models can be imported without circular dependency."""
    models = [
        Source,
        CrawlTask,
        ExtractionRun,
        RawDocument,
        Organization,
        Signal,
        Lead,
        LeadScore,
        Contact,
        FollowUp,
        Blocklist,
    ]
    for m in models:
        assert m is not None


def test_crawl_task_defaults():
    task = CrawlTask(source_id=None, query="区域品牌")
    assert task.status == CrawlTaskStatus.PENDING
    assert task.error_message is None


def test_extraction_run_defaults():
    from uuid import uuid4

    run = ExtractionRun(raw_document_id=uuid4(), llm_provider="mock", model="mock-v1")
    assert run.status == ExtractionRunStatus.PENDING
    assert run.prompt_version == "0.1"
    assert run.confidence == 0.0


def test_lead_status_enum():
    assert LeadStatus.NEW == "new"
    assert LeadStatus.BLOCKED == "blocked"


def test_crawl_task_status_lifecycle():
    task = CrawlTask(query="测试")
    assert task.status == CrawlTaskStatus.PENDING
    task.status = CrawlTaskStatus.RUNNING
    task.status = CrawlTaskStatus.COMPLETED
    assert task.status == CrawlTaskStatus.COMPLETED

# Prompt：实现采集器接口

请基于 docs/03_data_sources.md 和 docs/02_architecture.md 实现：

- src/leadradar/crawlers/base.py
- src/leadradar/crawlers/parser.py
- src/leadradar/crawlers/search_provider.py
- tests/test_crawler_parser.py

要求：

1. 定义 SearchProvider、FetchProvider、DocumentParser 接口。
2. 实现 MockSearchProvider 和 LocalFixtureFetchProvider，用本地 fixtures 测试。
3. 实现 HTML 正文抽取。
4. PDF 解析先预留接口，可以 TODO，但不能破坏流程。
5. 添加 URL hash 和 content hash。
6. 不要访问真实外网；不要绕过任何网站限制。

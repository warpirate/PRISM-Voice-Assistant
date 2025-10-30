# PersonalWebAgent Documentation

## Overview

**PersonalWebAgent** handles web-related operations including research, monitoring, and content management. Currently in **early implementation** stage with solid structure but limited integration.

## Capabilities

- `WEB_OPERATIONS`: Web research, monitoring, content saving

## Current Implementation Status

| Feature | Status | Utilization | Notes |
|---------|--------|-------------|-------|
| Research Planning | ✅ Complete | 10% | Structure ready |
| Website Monitoring | ✅ Complete | 5% | List management only |
| Content Saving | ✅ Complete | 5% | Tracking only |
| Web Search | ⚠️ Partial | 10% | Needs SystemControl integration |
| Actual Scraping | ❌ Not Implemented | 0% | Structure ready |
| **Overall** | **60%** | **10%** | **Needs Integration** |

## Architecture

### Class Structure

```python
class PersonalWebAgent(BaseAgent):
    monitored_sites: List[Dict[str, Any]]  # Websites being monitored
    saved_content: List[Dict[str, Any]]    # Saved articles/content
```

### Initialization

```python
async def initialize(self) -> bool:
    """
    Initializes web agent
    Currently minimal setup - ready for web scraping tools
    """
```

## Supported Operations

### 1. Research Topic

**Purpose**: Create structured research plan for a topic.

**Current State**: ✅ Planning structure complete, ⚠️ execution not implemented

**Usage**:
```python
response = await agent.execute("research Python tutorials", context)
```

**Process**:
1. Parses topic from input
2. Generates search queries
3. Lists sources to check
4. Returns research plan

**Response**:
```python
{
    'status': 'SUCCESS',
    'message': 'Research plan created for topic: Python tutorials',
    'data': {
        'topic': 'Python tutorials',
        'search_queries': [
            'Python tutorials overview',
            'Python tutorials best practices',
            'Python tutorials latest developments'
        ],
        'sources_to_check': [
            'Wikipedia',
            'Official documentation',
            'Recent articles',
            'Expert blogs'
        ],
        'timestamp': '2025-01-29T14:30:00'
    },
    'actions_taken': ['Created research plan for "Python tutorials"'],
    'suggestions': [
        'Use "search web for" to execute searches',
        'Save interesting content for later review'
    ]
}
```

**What's Missing**:
- Actual web scraping
- Content summarization
- Source credibility scoring
- Result aggregation

### 2. Monitor Website

**Purpose**: Add website to monitoring list for change detection.

**Current State**: ✅ List management complete, ❌ actual monitoring not implemented

**Usage**:
```python
response = await agent.execute("monitor https://example.com", context)
```

**Process**:
1. Extracts URL from input
2. Checks if already monitored
3. Adds to monitoring list
4. Returns confirmation

**Response**:
```python
{
    'status': 'SUCCESS',
    'message': 'Now monitoring website: https://example.com',
    'data': {
        'url': 'https://example.com',
        'added': '2025-01-29T14:30:00',
        'check_frequency': '1 hour',
        'last_check': None,
        'status': 'active'
    },
    'actions_taken': ['Added https://example.com to monitoring'],
    'suggestions': ['Set custom check frequency if needed']
}
```

**What's Missing**:
- Periodic checking mechanism
- Change detection algorithm
- Notification system
- Historical snapshots
- Diff visualization

### 3. Save Content

**Purpose**: Save content from URL for later review.

**Current State**: ✅ Tracking complete, ❌ actual saving not implemented

**Usage**:
```python
response = await agent.execute("save content from https://article.com", context)
```

**Process**:
1. Extracts URL from input
2. Records save request
3. Returns confirmation

**Response**:
```python
{
    'status': 'SUCCESS',
    'message': 'Content saved from: https://article.com',
    'data': {
        'url': 'https://article.com',
        'saved': '2025-01-29T14:30:00',
        'title': 'Content from https://article.com',
        'status': 'saved'
    },
    'actions_taken': ['Saved content from https://article.com'],
    'suggestions': ['Review saved content in your archive']
}
```

**What's Missing**:
- Actual content fetching
- HTML parsing and cleaning
- PDF generation
- Markdown conversion
- Metadata extraction
- Tag management

### 4. Web Search

**Purpose**: Perform web search and return results.

**Current State**: ⚠️ Structure ready, needs SystemControl integration

**Usage**:
```python
response = await agent.execute("search web for AI news", context)
```

**Process**:
1. Extracts query from input
2. Returns search structure
3. **Should integrate with SystemControl.web_search()**

**Response**:
```python
{
    'status': 'SUCCESS',
    'message': 'Web search initiated for: AI news',
    'data': {
        'query': 'AI news',
        'timestamp': '2025-01-29T14:30:00',
        'results_count': 0,
        'note': 'Integrate with SystemControl.web_search()'
    },
    'actions_taken': ['Searched for "AI news"'],
    'requires_followup': True,
    'metadata': {'integration_needed': 'SystemControl.web_search'}
}
```

**What's Needed**:
```python
# TODO: Integration code
from backend.system_control import SystemControl

async def _web_search(self, query: str, context: Optional[Dict] = None):
    system_control = SystemControl()
    results = await system_control.web_search(query)
    
    return AgentResponse.success(
        message=f"Found {len(results)} results for: {query}",
        agent_name=self.name,
        data={'results': results, 'query': query}
    )
```

## Helper Methods

### URL Extraction

```python
def _extract_url(self, task: str) -> Optional[str]:
    """Extract URL from task string using regex"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(url_pattern, task)
    return match.group(0) if match else None
```

### Topic Extraction

```python
def _extract_topic(self, task: str) -> str:
    """Extract research topic from task"""
    task_lower = task.lower()
    if 'research' in task_lower:
        topic = task_lower.split('research', 1)[1].strip()
        return topic.strip('"\'')
    return task
```

### Query Extraction

```python
def _extract_query(self, task: str) -> str:
    """Extract search query from task"""
    task_lower = task.lower()
    for prefix in ['search web for', 'search for', 'search']:
        if prefix in task_lower:
            query = task_lower.split(prefix, 1)[1].strip()
            return query.strip('"\'')
    return task
```

## Integration with PRISM

### Current Integration: **30%**

**What's Integrated**:
- ✅ Agent registration in coordinator
- ✅ Capability-based routing
- ✅ Intent parsing support
- ✅ Response handling

**What's Missing**:
- ❌ SystemControl.web_search() connection
- ❌ Actual web scraping implementation
- ❌ Content storage system
- ❌ Monitoring scheduler
- ❌ Notification system

### Execution Flow

```
1. User: "research Python tutorials"
        ↓
2. Coordinator parses intent
        ↓
3. Routes to PersonalWebAgent
        ↓
4. Agent creates research plan
        ↓
5. Returns structured plan
        ↓
6. User must manually execute searches (for now)
```

## Usage Statistics

### Current Utilization: **10%**

**Why So Low**:
- Most web operations go directly to SystemControl
- Agent not integrated with existing web search
- No actual scraping implemented
- Users don't know about research planning feature

**Usage Breakdown**:
- Research Planning: 10% (rarely used)
- Website Monitoring: 5% (experimental)
- Content Saving: 5% (not functional)
- Web Search: 10% (redirects to SystemControl)

## Strengths

✅ **Solid Foundation**
- Clean architecture
- Extensible design
- Clear separation of concerns

✅ **Well-Structured**
- Proper error handling
- Standardized responses
- Helper methods for parsing

✅ **Ready for Enhancement**
- Easy to add web scraping
- Monitoring list ready
- Content tracking in place

## Weaknesses

❌ **Limited Functionality**
- No actual web scraping
- No content fetching
- No monitoring execution
- No integration with existing systems

❌ **Low Utilization**
- Users bypass agent for web operations
- Features not discoverable
- No compelling use cases yet

❌ **Missing Critical Features**
- No HTML parsing
- No content storage
- No change detection
- No notification system

## Critical Improvements Needed

### Priority 1: SystemControl Integration

**Problem**: Web search goes directly to SystemControl, bypassing agent.

**Solution**:
```python
async def _web_search(self, query: str, context: Optional[Dict] = None):
    """Integrate with existing web search"""
    from backend.system_control import SystemControl
    
    system_control = SystemControl()
    results = await system_control.web_search(query)
    
    # Process and enhance results
    enhanced_results = []
    for result in results:
        enhanced_results.append({
            'title': result.get('title'),
            'url': result.get('url'),
            'snippet': result.get('snippet'),
            'relevance': self._calculate_relevance(result, query)
        })
    
    return AgentResponse.success(
        message=f"Found {len(enhanced_results)} results for: {query}",
        agent_name=self.name,
        data={
            'results': enhanced_results,
            'query': query,
            'total_results': len(results)
        },
        actions_taken=[f"Searched for '{query}'"],
        suggestions=self._generate_search_suggestions(query, enhanced_results)
    )
```

### Priority 2: Web Scraping Implementation

**Problem**: No actual content fetching.

**Solution**:
```python
async def _fetch_content(self, url: str) -> Dict[str, Any]:
    """Fetch and parse web content"""
    import aiohttp
    from bs4 import BeautifulSoup
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html = await response.text()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract main content
    content = {
        'title': soup.find('title').text if soup.find('title') else '',
        'text': soup.get_text(strip=True),
        'links': [a['href'] for a in soup.find_all('a', href=True)],
        'images': [img['src'] for img in soup.find_all('img', src=True)],
        'metadata': {
            'description': soup.find('meta', {'name': 'description'}),
            'keywords': soup.find('meta', {'name': 'keywords'}),
            'author': soup.find('meta', {'name': 'author'})
        }
    }
    
    return content
```

### Priority 3: Content Storage System

**Problem**: Saved content not actually stored.

**Solution**:
```python
class ContentStorage:
    """Persistent storage for saved web content"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)
        self.index_file = storage_dir / "index.json"
    
    async def save_content(self, url: str, content: Dict) -> str:
        """Save content and return content ID"""
        content_id = hashlib.md5(url.encode()).hexdigest()
        content_file = self.storage_dir / f"{content_id}.json"
        
        # Save content
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2)
        
        # Update index
        self._update_index(content_id, url, content)
        
        return content_id
    
    async def get_content(self, content_id: str) -> Optional[Dict]:
        """Retrieve saved content"""
        content_file = self.storage_dir / f"{content_id}.json"
        if content_file.exists():
            with open(content_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
```

### Priority 4: Website Monitoring

**Problem**: Monitoring list exists but no checking mechanism.

**Solution**:
```python
class WebsiteMonitor:
    """Background task for monitoring websites"""
    
    def __init__(self, agent: 'PersonalWebAgent'):
        self.agent = agent
        self.running = False
        self.check_interval = 3600  # 1 hour
    
    async def start(self):
        """Start monitoring loop"""
        self.running = True
        while self.running:
            for site in self.agent.monitored_sites:
                if site['status'] == 'active':
                    await self._check_site(site)
            await asyncio.sleep(self.check_interval)
    
    async def _check_site(self, site: Dict):
        """Check if website has changed"""
        url = site['url']
        
        # Fetch current content
        current_content = await self.agent._fetch_content(url)
        current_hash = hashlib.md5(
            current_content['text'].encode()
        ).hexdigest()
        
        # Compare with last check
        if site.get('last_hash') and site['last_hash'] != current_hash:
            # Website changed!
            await self._notify_change(site, current_content)
        
        # Update site record
        site['last_check'] = datetime.now().isoformat()
        site['last_hash'] = current_hash
```

## Recommended Implementation Plan

### Phase 1: Core Integration (1 week)

1. **Connect to SystemControl**
   - Integrate `web_search()` method
   - Add result enhancement
   - Generate smart suggestions

2. **Basic Web Scraping**
   - Add `aiohttp` and `BeautifulSoup4` dependencies
   - Implement `_fetch_content()` method
   - Add HTML parsing and cleaning

3. **Content Storage**
   - Create storage directory structure
   - Implement save/retrieve methods
   - Add content indexing

### Phase 2: Advanced Features (2 weeks)

1. **Website Monitoring**
   - Implement background monitoring task
   - Add change detection
   - Create notification system

2. **Research Execution**
   - Execute search queries automatically
   - Aggregate and summarize results
   - Generate research reports

3. **Content Management**
   - Add tagging system
   - Implement search within saved content
   - Add export to PDF/Markdown

### Phase 3: Intelligence (2-3 weeks)

1. **Smart Research**
   - Source credibility scoring
   - Automatic fact-checking
   - Citation generation

2. **Content Analysis**
   - Sentiment analysis
   - Key point extraction
   - Topic modeling

3. **Personalization**
   - Learn user interests
   - Suggest relevant content
   - Auto-categorize saved content

## Dependencies Needed

```python
# requirements.txt additions
aiohttp==3.9.1              # Async HTTP client
beautifulsoup4==4.12.3      # HTML parsing (already installed)
lxml==5.1.0                 # Fast XML/HTML parser
readability-lxml==0.8.1     # Extract main content
newspaper3k==0.2.8          # Article extraction
feedparser==6.0.11          # RSS feed parsing
```

## Testing Requirements

### Unit Tests

```python
# Test URL extraction
def test_extract_url():
    task = "monitor https://example.com for changes"
    url = agent._extract_url(task)
    assert url == "https://example.com"

# Test topic extraction
def test_extract_topic():
    task = "research Python tutorials"
    topic = agent._extract_topic(task)
    assert topic == "Python tutorials"

# Test monitoring list management
async def test_add_to_monitoring():
    response = await agent._monitor_website("https://test.com")
    assert response.is_success()
    assert len(agent.monitored_sites) == 1
```

### Integration Tests

```python
# Test web scraping
async def test_fetch_content():
    content = await agent._fetch_content("https://example.com")
    assert 'title' in content
    assert 'text' in content
    assert len(content['text']) > 0

# Test content storage
async def test_save_and_retrieve():
    content_id = await storage.save_content(url, content)
    retrieved = await storage.get_content(content_id)
    assert retrieved['title'] == content['title']

# Test monitoring
async def test_change_detection():
    # Add site to monitoring
    # Modify site content
    # Check if change detected
    # Verify notification sent
```

## Best Practices

### Using PersonalWebAgent

**DO**:
- ✅ Use for research planning
- ✅ Monitor important websites
- ✅ Save content for offline reading
- ✅ Integrate with SystemControl

**DON'T**:
- ❌ Expect actual scraping (not implemented yet)
- ❌ Rely on monitoring (not active yet)
- ❌ Assume content is saved (only tracked)

### Error Handling

```python
response = await agent.execute("research topic", context)

if response.is_success():
    plan = response.data
    # Execute research plan
else:
    logger.error(f"Research failed: {response.error}")
    # Fallback to manual search
```

## Conclusion

**PersonalWebAgent** has a solid foundation but is **significantly underutilized** at only **10%**. The architecture is sound, but critical features are missing.

**Current State**:
- 60% implementation (structure complete)
- 30% integration (routing works)
- 10% utilization (rarely used)

**Priority Actions**:
1. **Integrate with SystemControl** (1 day)
2. **Implement web scraping** (2-3 days)
3. **Add content storage** (2-3 days)
4. **Enable monitoring** (3-5 days)

**Potential Impact**:
- Research becomes automated
- Content management centralized
- Website monitoring active
- Utilization could reach 70-80%

The agent is **ready for enhancement** and could become a powerful tool for web-based workflows with focused development effort.

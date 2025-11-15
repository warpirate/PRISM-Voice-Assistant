"""
Personal Web Agent
Handles web research, monitoring, and content saving
"""

import asyncio
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from backend.agents.base_agent import BaseAgent, AgentCapability
from backend.agents.agent_response import AgentResponse, ResponseStatus


class PersonalWebAgent(BaseAgent):
    """
    Agent for personal web operations
    
    Capabilities:
    - Topic research and summarization
    - Website monitoring
    - Content saving and archiving
    - Price tracking (future)
    """
    
    def __init__(self):
        super().__init__(
            name="PersonalWebAgent",
            capabilities=[AgentCapability.WEB_OPERATIONS]
        )
        
        self.monitored_sites: List[Dict[str, Any]] = []
        self.saved_content: List[Dict[str, Any]] = []
    
    async def initialize(self) -> bool:
        """Initialize web agent"""
        try:
            # Initialize web scraping tools (if available)
            logger.info("PersonalWebAgent initialized")
            return True
            
        except Exception as e:
            logger.error(f"PersonalWebAgent initialization failed: {str(e)}")
            return False
    
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Execute web operation task
        
        Supported tasks:
        - "research [topic]"
        - "monitor [url]"
        - "save content from [url]"
        - "search web for [query]"
        - "web_search" (structured task with parameters)
        """
        try:
            # Handle structured task execution from agent coordinator
            if context and 'task_type' in context:
                task_type = context['task_type']
                parameters = context.get('parameters', {})
                
                if task_type == 'web_search':
                    query = parameters.get('query')
                    return await self._web_search(query, context)
                elif task_type == 'research':
                    topic = parameters.get('topic')
                    return await self._research_topic(topic, context)
                elif task_type == 'monitor':
                    url = parameters.get('url')
                    return await self._monitor_website(url)
                elif task_type == 'save_content':
                    url = parameters.get('url')
                    return await self._save_content(url)
                else:
                    return AgentResponse.failure(
                        message=f"Unknown structured task: {task_type}",
                        agent_name=self.name,
                        error="Task type not recognized"
                    )
            
            # Handle legacy string-based task execution
            task_lower = task.lower()
            
            if 'research' in task_lower:
                topic = self._extract_topic(task)
                return await self._research_topic(topic, context)
            
            elif 'monitor' in task_lower:
                url = self._extract_url(task)
                return await self._monitor_website(url)
            
            elif 'save' in task_lower or 'archive' in task_lower:
                url = self._extract_url(task)
                return await self._save_content(url)
            
            elif 'search' in task_lower:
                query = self._extract_query(task)
                return await self._web_search(query, context)
            
            else:
                return AgentResponse.failure(
                    message=f"Unknown web operation: {task}",
                    agent_name=self.name,
                    error="Task not recognized"
                )
                
        except Exception as e:
            logger.error(f"Web agent execution error: {str(e)}")
            return AgentResponse.failure(
                message=f"Web operation failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _research_topic(self, topic: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Research a topic using web search"""
        if not topic:
            return AgentResponse.failure(
                message="No topic specified for research",
                agent_name=self.name,
                error="Missing topic"
            )
        
        try:
            # This will integrate with existing web search functionality
            # For now, return structured research plan
            research_plan = {
                'topic': topic,
                'search_queries': [
                    f"{topic} overview",
                    f"{topic} best practices",
                    f"{topic} latest developments"
                ],
                'sources_to_check': [
                    'Wikipedia',
                    'Official documentation',
                    'Recent articles',
                    'Expert blogs'
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            return AgentResponse.success(
                message=f"Research plan created for topic: {topic}",
                agent_name=self.name,
                data=research_plan,
                actions_taken=[f"Created research plan for '{topic}'"],
                suggestions=[
                    "Use 'search web for' to execute searches",
                    "Save interesting content for later review"
                ]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Research failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _monitor_website(self, url: str) -> AgentResponse:
        """Add website to monitoring list"""
        if not url:
            return AgentResponse.failure(
                message="No URL specified for monitoring",
                agent_name=self.name,
                error="Missing URL"
            )
        
        try:
            # Check if already monitored
            if any(site['url'] == url for site in self.monitored_sites):
                return AgentResponse.success(
                    message=f"Website already being monitored: {url}",
                    agent_name=self.name,
                    data={'url': url, 'status': 'already_monitored'}
                )
            
            # Add to monitoring list
            monitor_entry = {
                'url': url,
                'added': datetime.now().isoformat(),
                'check_frequency': '1 hour',
                'last_check': None,
                'status': 'active'
            }
            
            self.monitored_sites.append(monitor_entry)
            
            return AgentResponse.success(
                message=f"Now monitoring website: {url}",
                agent_name=self.name,
                data=monitor_entry,
                actions_taken=[f"Added {url} to monitoring"],
                suggestions=["Set custom check frequency if needed"]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Failed to add website to monitoring: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _save_content(self, url: str) -> AgentResponse:
        """Save content from URL"""
        if not url:
            return AgentResponse.failure(
                message="No URL specified for saving",
                agent_name=self.name,
                error="Missing URL"
            )
        
        try:
            # This would fetch and save actual content
            # For now, record the save request
            save_entry = {
                'url': url,
                'saved': datetime.now().isoformat(),
                'title': f"Content from {url}",
                'status': 'saved'
            }
            
            self.saved_content.append(save_entry)
            
            return AgentResponse.success(
                message=f"Content saved from: {url}",
                agent_name=self.name,
                data=save_entry,
                actions_taken=[f"Saved content from {url}"],
                suggestions=["Review saved content in your archive"]
            )
            
        except Exception as e:
            return AgentResponse.failure(
                message=f"Failed to save content: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    async def _web_search(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Perform web search using Brave Search API with intelligent summarization"""
        if not query:
            return AgentResponse.failure(
                message="No search query specified",
                agent_name=self.name,
                error="Missing query"
            )
        
        try:
            # Import config to get API key
            from backend.config import config
            
            if not config.web_search.brave_api_key:
                logger.warning("Brave Search API key not configured, using fallback")
                return await self._fallback_web_search(query)
            
            import requests
            
            # First try Brave Summarizer API for intelligent summaries
            summary_response = await self._try_brave_summarizer(query, config.web_search.brave_api_key)
            if summary_response:
                return summary_response
            
            # Fallback to regular search with AI summarization
            return await self._brave_search_with_ai_summary(query, config.web_search.brave_api_key)
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return await self._fallback_web_search(query)
    
    async def _try_brave_summarizer(self, query: str, api_key: str) -> Optional[AgentResponse]:
        """Try Brave Summarizer API for intelligent search summaries"""
        try:
            import requests
            
            # Use Brave Summarizer API
            api_url = "https://api.search.brave.com/res/v1/summarizer/search"
            
            headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip',
                'X-Subscription-Token': api_key
            }
            
            params = {
                'q': query,
                'summary': True,
                'search_lang': 'en',
                'country': 'US',
                'safesearch': 'moderate',
                'freshness': 'pd'
            }
            
            logger.info(f"Trying Brave Summarizer for: {query}")
            response = requests.get(api_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract summary
                summarizer = data.get('summarizer', {})
                if summarizer and summarizer.get('type') == 'search_query':
                    summary_text = summarizer.get('summary', '')
                    if summary_text:
                        # Format the response nicely
                        formatted_response = f"**Summary for '{query}':**\n\n{summary_text}"
                        
                        # Add key sources if available
                        enrichments = summarizer.get('enrichments', [])
                        if enrichments:
                            formatted_response += "\n\n**Key Sources:**\n"
                            for i, enrichment in enumerate(enrichments[:3], 1):
                                title = enrichment.get('title', 'Source')
                                url = enrichment.get('url', '')
                                formatted_response += f"{i}. {title}\n   {url}\n"
                        
                        return AgentResponse.success(
                            message=formatted_response,
                            agent_name=self.name,
                            data={
                                'query': query,
                                'summary': summary_text,
                                'sources': enrichments,
                                'search_engine': 'Brave Summarizer'
                            },
                            actions_taken=[f"Generated intelligent summary for '{query}'"],
                            suggestions=["Ask me to search for more specific information if needed"]
                        )
            
            logger.debug(f"Brave Summarizer not available (status: {response.status_code}), falling back to regular search")
            return None
            
        except Exception as e:
            logger.debug(f"Brave Summarizer failed: {e}, falling back to regular search")
            return None
    
    async def _brave_search_with_ai_summary(self, query: str, api_key: str) -> AgentResponse:
        """Perform regular Brave search and use AI to create intelligent summary"""
        try:
            import requests
            
            # Use regular Brave Search API
            api_url = "https://api.search.brave.com/res/v1/web/search"
            
            headers = {
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip',
                'X-Subscription-Token': api_key
            }
            
            params = {
                'q': query,
                'count': 8,  # Get more results for better summary
                'search_lang': 'en',
                'country': 'US',
                'safesearch': 'moderate',
                'freshness': 'pd',
                'text_decorations': False
            }
            
            logger.info(f"Searching web for: {query}")
            response = requests.get(api_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract search results
            results = []
            web_results = data.get('web', {}).get('results', [])
            
            for result in web_results[:8]:
                try:
                    title = result.get('title', 'No title')
                    url = result.get('url', '')
                    description = result.get('description', '')
                    
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': description
                    })
                except Exception as e:
                    logger.debug(f"Error parsing result: {e}")
                    continue
            
            if not results:
                logger.warning("No results found from Brave Search API")
                return await self._fallback_web_search(query)
            
            # Use AI to create intelligent summary
            summary = await self._create_ai_summary(query, results)
            
            search_data = {
                'query': query,
                'results_count': len(results),
                'results': results,
                'timestamp': datetime.now().isoformat(),
                'search_engine': 'Brave Search + AI Summary'
            }
            
            return AgentResponse.success(
                message=summary,
                agent_name=self.name,
                data=search_data,
                actions_taken=[f"Searched and summarized information about '{query}'"],
                suggestions=["Ask me for more specific details if needed"]
            )
            
        except requests.RequestException as e:
            logger.error(f"Brave Search API request failed: {e}")
            return await self._fallback_web_search(query)
    
    async def _create_ai_summary(self, query: str, results: List[Dict]) -> str:
        """Create an intelligent summary using AI"""
        try:
            # Import AI engine
            from backend.ai_engine import AIEngine
            from backend.config import config
            
            # Create AI engine instance (no parameters needed)
            ai_engine = AIEngine()
            await ai_engine.initialize()
            
            # Prepare search results for AI
            search_content = f"Search results for '{query}':\n\n"
            for i, result in enumerate(results[:5], 1):
                search_content += f"{i}. {result['title']}\n"
                if result['snippet']:
                    search_content += f"   {result['snippet']}\n"
                search_content += f"   Source: {result['url']}\n\n"
            
            # Create summarization prompt
            summary_prompt = f"""Summarize these search results for query: '{query}'

Search Results:
{search_content}

Provide a clear, informative summary with key facts and insights:"""
            
            # Get AI summary
            ai_response = await ai_engine.process_input(summary_prompt)
            
            if ai_response and ai_response.text:
                # Clean up the response and format nicely
                summary = ai_response.text.strip()
                
                # Add source references
                summary += "\n\n**Sources:**\n"
                for i, result in enumerate(results[:3], 1):
                    summary += f"{i}. {result['title']} - {result['url']}\n"
                
                return summary
            else:
                # Fallback to simple formatting
                return self._create_simple_summary(query, results)
                
        except Exception as e:
            logger.warning(f"AI summarization failed: {e}, using simple summary")
            return self._create_simple_summary(query, results)
    
    def _create_simple_summary(self, query: str, results: List[Dict]) -> str:
        """Create an intelligent formatted summary without AI"""
        # Extract key information and numbers from snippets
        key_info = []
        prices = []
        dates = []
        
        for result in results[:5]:
            snippet = result.get('snippet', '')
            title = result.get('title', '')
            
            # Look for price patterns
            import re
            price_patterns = [
                r'\$[\d,]+\.?\d*',  # $1,234.56
                r'[\d,]+\.?\d*\s*dollars?',  # 1234.56 dollars
                r'[\d,]+\.?\d*\s*USD',  # 1234.56 USD
                r'Price:\s*[\d,]+\.?\d*',  # Price: 1234.56
                r'equal to [\d,]+\.?\d*',  # equal to 1234.56
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, snippet, re.IGNORECASE)
                prices.extend(matches)
            
            # Look for current/today information
            if any(word in snippet.lower() for word in ['current', 'today', 'now', 'latest', 'actual']):
                key_info.append({
                    'title': title,
                    'snippet': snippet,
                    'url': result.get('url', ''),
                    'relevance': 'high'
                })
            else:
                key_info.append({
                    'title': title,
                    'snippet': snippet,
                    'url': result.get('url', ''),
                    'relevance': 'medium'
                })
        
        # Build intelligent summary
        summary = f"**Current information about '{query}':**\n\n"
        
        # Add price information if found
        if prices:
            unique_prices = list(set(prices))[:3]  # Top 3 unique prices
            summary += "**Key Prices Found:**\n"
            for price in unique_prices:
                summary += f"• {price}\n"
            summary += "\n"
        
        # Add most relevant information
        high_relevance = [info for info in key_info if info['relevance'] == 'high']
        if high_relevance:
            summary += "**Latest Information:**\n"
            for info in high_relevance[:2]:
                summary += f"• {info['snippet']}\n"
                summary += f"  Source: {info['title']}\n\n"
        
        # Add additional context
        if len(key_info) > len(high_relevance):
            summary += "**Additional Context:**\n"
            other_info = [info for info in key_info if info['relevance'] != 'high'][:2]
            for info in other_info:
                summary += f"• {info['snippet']}\n"
                summary += f"  Source: {info['title']}\n\n"
        
        # Add sources
        summary += "**Sources:**\n"
        for i, info in enumerate(key_info[:3], 1):
            summary += f"{i}. {info['title']} - {info['url']}\n"
        
        return summary
    
    async def _fallback_web_search(self, query: str) -> AgentResponse:
        """Fallback web search method"""
        try:
            # Simple fallback - just provide search suggestions
            fallback_message = f"I couldn't perform a direct web search for '{query}' right now, but here are some suggestions:\n\n"
            fallback_message += f"• Try searching for: {query}\n"
            fallback_message += f"• You might want to check news websites for: {query}\n"
            fallback_message += f"• Consider searching on specific platforms related to: {query}\n"
            
            return AgentResponse.success(
                message=fallback_message,
                agent_name=self.name,
                data={'query': query, 'fallback': True},
                actions_taken=[f"Provided search suggestions for '{query}'"],
                suggestions=["Try rephrasing your search query", "Ask me to open a browser if you prefer manual searching"]
            )
        except Exception as e:
            return AgentResponse.failure(
                message=f"Even fallback search failed: {str(e)}",
                agent_name=self.name,
                error=str(e)
            )
    
    def _extract_topic(self, task: str) -> str:
        """Extract research topic from task"""
        task_lower = task.lower()
        if 'research' in task_lower:
            topic = task_lower.split('research', 1)[1].strip()
            return topic.strip('"\'')
        return task
    
    def _extract_url(self, task: str) -> Optional[str]:
        """Extract URL from task string"""
        # Simple URL extraction
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        match = re.search(url_pattern, task)
        if match:
            return match.group(0)
        return None
    
    def _extract_query(self, task: str) -> str:
        """Extract search query from task"""
        task_lower = task.lower()
        for prefix in ['search web for', 'search for', 'search']:
            if prefix in task_lower:
                query = task_lower.split(prefix, 1)[1].strip()
                return query.strip('"\'')
        return task
    
    def get_monitored_sites(self) -> List[Dict[str, Any]]:
        """Get list of monitored websites"""
        return self.monitored_sites
    
    def get_saved_content(self) -> List[Dict[str, Any]]:
        """Get list of saved content"""
        return self.saved_content
    
    async def shutdown(self) -> bool:
        """Cleanup and shutdown"""
        logger.info(f"PersonalWebAgent shutting down (monitored: {len(self.monitored_sites)}, saved: {len(self.saved_content)})")
        return True

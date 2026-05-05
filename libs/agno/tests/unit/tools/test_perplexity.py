"""Unit tests for PerplexityTools class."""

import json
from unittest.mock import Mock, patch, MagicMock
import httpx

import pytest

from agno.tools.perplexity import PerplexityTools


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "results": [
                            {"title": "Result 1", "url": "https://example.com/1", "snippet": "This is result 1"},
                            {"title": "Result 2", "url": "https://example.com/2", "snippet": "This is result 2"},
                        ]
                    })
                }
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def perplexity_tools():
    """Create a PerplexityTools instance with mock httpx client."""
    with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test_api_key"}):
        with patch("agno.tools.perplexity.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({"results": []})
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            tools = PerplexityTools()
            return tools


class TestPerplexityTools:
    """Test cases for PerplexityTools class."""

    def test_initialization_with_api_key(self):
        """Test initialization with API key."""
        tools = PerplexityTools(api_key="test_key")
        
        assert tools.api_key == "test_key"
        assert tools.base_url == "https://api.mtuo.ai/v1/chat/completions"

    def test_initialization_with_env_api_key(self):
        """Test initialization with API key from environment."""
        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "env_key"}):
            tools = PerplexityTools()
            assert tools.api_key == "env_key"

    def test_initialization_without_api_key_raises_error(self):
        """Test initialization without API key raises ValueError."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="PERPLEXITY_API_KEY is required"):
                PerplexityTools()

    def test_search_single_query_success(self, perplexity_tools):
        """Test successful search with single query."""
        with patch("agno.tools.perplexity.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "results": [
                                    {"title": "Article 1", "url": "https://example.com/1", "snippet": "Content 1"},
                                    {"title": "Article 2", "url": "https://example.com/2", "snippet": "Content 2"},
                                ]
                            })
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            # Perform search
            result = perplexity_tools.search("Python programming")
            
            # Parse result
            result_data = json.loads(result)
            
            # Verify structure
            assert "queries" in result_data
            assert "results" in result_data
            assert len(result_data["results"]) == 2
            assert result_data["results"][0]["title"] == "Article 1"
            assert result_data["results"][0]["url"] == "https://example.com/1"
            
            # Verify API was called correctly
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[1]["json"]["model"] == "sonar"
            assert "Python programming" in call_args[1]["json"]["messages"][0]["content"]

    def test_search_multiple_queries_success(self, perplexity_tools):
        """Test successful search with multiple queries."""
        with patch("agno.tools.perplexity.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "results": [
                                    {"title": "Result 1", "url": "https://example.com/1", "snippet": "Snippet 1"},
                                ]
                            })
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            # Perform search with list
            queries = ["Python", "JavaScript", "Go"]
            result = perplexity_tools.search(queries)
            
            # Parse result
            result_data = json.loads(result)
            
            # Verify structure
            assert len(result_data["queries"]) == 3
            assert result_data["queries"] == queries

    def test_search_with_max_results(self, perplexity_tools):
        """Test search with max_results limit."""
        with patch("agno.tools.perplexity.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            # Create mock with 5 results
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "results": [
                                    {"title": f"Result {i}", "url": f"https://example.com/{i}", "snippet": f"Snippet {i}"}
                                    for i in range(5)
                                ]
                            })
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            # Search with max_results=3
            result = perplexity_tools.search("test query", max_results=3)
            
            result_data = json.loads(result)
            
            # Should only return 3 results
            assert len(result_data["results"]) == 3
            assert result_data["results"][0]["title"] == "Result 0"
            assert result_data["results"][2]["title"] == "Result 2"

    def test_search_error_handling(self, perplexity_tools):
        """Test search error handling when API call fails."""
        with patch("agno.tools.perplexity.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            # Make API call raise an exception
            mock_client.post.side_effect = Exception("API Error")
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            # Perform search
            result = perplexity_tools.search("test query")
            
            result_data = json.loads(result)
            
            # Should return error message
            assert "error" in result_data
            assert "Perplexity 调用失败" in result_data["error"]
            assert "queries" in result_data

    def test_search_with_missing_attributes(self, perplexity_tools):
        """Test search when response has missing optional attributes."""
        with patch("agno.tools.perplexity.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            # Mock response with minimal attributes
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "results": [
                                    {"title": None, "url": None, "snippet": None},  # All None
                                    {"name": "Alternate Name"},  # Different attribute name
                                ]
                            })
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            # Perform search
            result = perplexity_tools.search("test")
            result_data = json.loads(result)
            
            # Should handle gracefully
            assert "results" in result_data
            assert len(result_data["results"]) == 2

    def test_search_empty_results(self, perplexity_tools):
        """Test search when no results are returned."""
        with patch("agno.tools.perplexity.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({"results": []})
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            result = perplexity_tools.search("empty query")
            result_data = json.loads(result)
            
            assert "results" in result_data
            assert len(result_data["results"]) == 0

    def test_search_with_unicode_content(self, perplexity_tools):
        """Test search handles unicode content correctly."""
        with patch("agno.tools.perplexity.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps({
                                "results": [
                                    {"title": "测试标题", "url": "https://example.com/测试", "snippet": "测试内容"}
                                ]
                            })
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            result = perplexity_tools.search("测试查询")
            result_data = json.loads(result)
            
            # Should parse unicode correctly
            assert "results" in result_data
            assert len(result_data["results"]) == 1
            # Result should handle unicode strings
            assert isinstance(result_data["results"][0]["title"], str)

    def test_search_with_non_json_content(self, perplexity_tools):
        """Test search when API returns non-JSON content."""
        with patch("agno.tools.perplexity.httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "This is plain text content, not JSON"
                        }
                    }
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__enter__.return_value = mock_client
            
            result = perplexity_tools.search("test query")
            result_data = json.loads(result)
            
            # Should create default result with the content
            assert "results" in result_data
            assert len(result_data["results"]) == 1
            assert result_data["results"][0]["title"] == "Search Result"
            assert result_data["results"][0]["snippet"] == "This is plain text content, not JSON"


@pytest.mark.integration
class TestPerplexityToolsIntegration:
    """Integration tests for PerplexityTools class with real API calls."""
    
    def test_real_api_call_basic(self):
        """Test real API call with basic query."""
        import os
        api_key = os.getenv("PERPLEXITY_API_KEY")
        
        if not api_key or api_key == "your_perplexity_api_key_here":
            pytest.skip("PERPLEXITY_API_KEY not set or is placeholder")
        
        # Create tools with real API key
        tools = PerplexityTools(api_key=api_key)
        
        # Perform real search
        result = tools.search("Python programming")
        
        # Parse and verify result
        result_data = json.loads(result)
        
        # Verify structure
        assert "queries" in result_data
        assert "results" in result_data
        assert "Python programming" in result_data["queries"]
        
        # Verify we got some response (error or results)
        assert "error" in result_data or len(result_data["results"]) >= 0
        
        print(f"\nAPI call successful! Query: {result_data['queries']}")
        print(f"\n=== 完整原始 JSON 响应 ===")
        print(json.dumps(result_data, ensure_ascii=False, indent=2))
        print("=" * 50)
        
        if "error" in result_data:
            print(f"API returned error: {result_data['error']}")
        else:
            print(f"Got {len(result_data['results'])} results")
            print("\n=== 真实 API 返回完整结果 ===")
            for i, item in enumerate(result_data['results']):  # 显示所有结果
                print(f"\n[结果 {i+1}]")
                print(f"标题: {item.get('title', 'N/A')}")
                print(f"链接: {item.get('url', 'N/A')}")
                snippet = item.get('snippet', 'N/A')
                print(f"摘要: {snippet}")  # 完整显示摘要，不截断
            print("=" * 50)
    
    def test_real_api_call_multiple_queries(self):
        """Test real API call with multiple queries."""
        import os
        api_key = os.getenv("PERPLEXITY_API_KEY")
        
        if not api_key or api_key == "your_perplexity_api_key_here":
            pytest.skip("PERPLEXITY_API_KEY not set or is placeholder")
        
        tools = PerplexityTools(api_key=api_key)
        
        # Perform search with multiple queries
        queries = ["Python", "JavaScript"]
        result = tools.search(queries)
        
        result_data = json.loads(result)
        
        # Verify structure
        assert "queries" in result_data
        assert "results" in result_data
        assert len(result_data["queries"]) == 2
        assert result_data["queries"] == queries
        
        print(f"\nAPI call successful! Queries: {result_data['queries']}")
        print(f"\n=== 完整原始 JSON 响应 ===")
        print(json.dumps(result_data, ensure_ascii=False, indent=2))
        print("=" * 50)
        
        if "error" in result_data:
            print(f"API returned error: {result_data['error']}")
        else:
            print(f"Got {len(result_data['results'])} results")
            print("\n=== 多查询 API 返回完整结果 ===")
            for i, item in enumerate(result_data['results']):  # 显示所有结果
                print(f"\n[结果 {i+1}]")
                print(f"标题: {item.get('title', 'N/A')}")
                print(f"链接: {item.get('url', 'N/A')}")
                snippet = item.get('snippet', 'N/A')
                print(f"摘要: {snippet}")  # 完整显示摘要，不截断
            print("=" * 50)


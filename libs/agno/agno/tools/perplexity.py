import os
import json
import time
import httpx
from typing import Any, List, Optional, Union

from agno.tools.toolkit import Toolkit
from agno.utils.log import log_info


class PerplexityTools(Toolkit):
    """
    Perplexity 检索工具。
    - 使用 OpenAI 兼容的 API 接口
    - 与 SupplierCommunicationTools 兼容：提供 search(query) -> str(JSON)
    - 支持传入单个字符串或字符串列表
    环境变量:
      - PERPLEXITY_API_KEY: API 密钥
    """

    def __init__(self, api_key: Optional[str] = None, **kwargs: Any):
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        self.base_url = os.getenv("PERPLEXITY_BASE_URL")
        
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY is required")

        tools: List[Any] = [self.search]
        super().__init__(name="perplexity", tools=tools, **kwargs)

    def search(self, query: Union[str, List[str]], max_results: Optional[int] = None) -> str:
        """
        使用 Perplexity 执行检索，返回 JSON 字符串。
        - query: 单条查询或查询列表
        - max_results: 可选，限制返回结果条数
        返回:
        - JSON 字符串，如:
          {
            "queries": [...],
            "results": [
              {"title": "...", "url": "...", "snippet": "..."},
              ...
            ]
          }
        """
        queries: List[str] = [query] if isinstance(query, str) else list(query)
        
        start_time = time.time()
        
        try:
            request_data = {
                "model": "sonar",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Search for: {', '.join(queries)}"
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            with httpx.Client() as client:
                response = client.post(
                    self.base_url,
                    json=request_data,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                resp_data = response.json()
                
        except Exception as e:
            elapsed_time = time.time() - start_time
            log_info(f"[Perplexity] 调用sonar耗时: {elapsed_time:.2f}秒 (失败)")
            return json.dumps({"error": f"Perplexity 调用失败: {e}", "queries": queries}, ensure_ascii=False)
        
        elapsed_time = time.time() - start_time
        log_info(f"[Perplexity] 调用sonar耗时: {elapsed_time:.2f}秒")

        try:
            content = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            try:
                parsed_content = json.loads(content)
                if isinstance(parsed_content, dict) and "results" in parsed_content:
                    results = parsed_content["results"]
                else:
                    results = [{"title": "Search Result", "url": "", "snippet": content}]
            except json.JSONDecodeError:
                results = [{"title": "Search Result", "url": "", "snippet": content}]
            
            if max_results is not None:
                results = results[:max_results]
                
        except Exception as e:
            results = [{"title": "Error", "url": "", "snippet": f"Failed to parse response: {e}"}]

        return json.dumps({"queries": queries, "results": results}, ensure_ascii=False, indent=2)
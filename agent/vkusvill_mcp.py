"""
Модуль для работы с MCP сервером ВкусВилл
"""
import requests
import json
from typing import Dict, List, Any, Optional


# Глобальное соединение
_client: Optional['_MCPClient'] = None


class _MCPClient:
    """Внутренний клиент MCP"""
    
    def __init__(self, base_url: str = "https://mcp001.vkusvill.ru/mcp"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session_id: Optional[str] = None
        self._request_id = 0
        self._connect()
    
    def _connect(self) -> None:
        """Инициализация соединения"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "vkusvill-mcp-client",
                    "version": "1.0"
                }
            }
        }
        
        response = self.session.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        if "error" in result:
            raise Exception(f"MCP Error: {result['error']}")
        
        self.session_id = response.headers.get('Mcp-Session-Id')
        if not self.session_id:
            raise Exception("No session ID received")
        
        # Отправляем уведомление об инициализации
        self.session.post(self.base_url, headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Mcp-Session-Id": self.session_id
        }, json={
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        })
    
    def _get_next_id(self) -> int:
        self._request_id += 1
        return self._request_id
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Вызов инструмента MCP"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Mcp-Session-Id": self.session_id
        }
        
        payload = {
            "jsonrpc": "2.0",
            "id": self._get_next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = self.session.post(self.base_url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        if "error" in result:
            raise Exception(f"MCP Error: {result['error']}")
        
        content = result.get("result", {}).get("content", [])
        if content and len(content) > 0:
            text = content[0].get("text", "{}")
            return json.loads(text)
        
        return {}
    
    def close(self) -> None:
        """Закрытие соединения"""
        self.session.close()


def _get_client() -> _MCPClient:
    """Получить или создать клиент MCP"""
    global _client
    if _client is None:
        _client = _MCPClient()
    return _client


def search_products(query: str, page: int = 1, sort: str = "popularity") -> Dict[str, Any]:
    """
    Поиск товаров по запросу
    
    Args:
        query: Поисковый запрос (1-255 символов)
        page: Номер страницы (по умолчанию 1)
        sort: Сортировка - "popularity", "rating", "price_asc", "price_desc"
    
    Returns:
        {
            "ok": bool,
            "data": {
                "meta": {"q": str, "limit": int, "total": int, "page": int, "pages": int, "has_more": bool},
                "items": [
                    {
                        "id": int,
                        "xml_id": int,
                        "name": str,
                        "description": str,
                        "price": {"current": int, "currency": str, "old": int|None, "discount_percent": float|None},
                        "unit": str,
                        "weight": {"value": float, "unit": str},
                        "rating": {"average": float, "count": int},
                        "url": str,
                        "images": [{"small": str, "medium": str, "large": str}],
                        "category": [{"id": int, "name": str, "slug": str, "url": str}]
                    }
                ]
            }
        }
    """
    client = _get_client()
    return client.call_tool("vkusvill_products_search", {
        "q": query,
        "page": page,
        "sort": sort
    })


def get_product_details(product_id: int) -> Dict[str, Any]:
    """
    Получение детальной информации о товаре (КБЖУ, состав, производитель)
    
    Args:
        product_id: ID товара
    
    Returns:
        {
            "ok": bool,
            "data": {
                # Все поля из search_products +
                "brand": str,
                "properties": [{"name": str, "value": str}]
                # properties: КБЖУ, Состав, Срок годности, Условия хранения, Изготовитель
            }
        }
    """
    client = _get_client()
    return client.call_tool("vkusvill_product_details", {
        "id": product_id
    })


def create_cart_link(products: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Создание ссылки на корзину с товарами
    
    Args:
        products: [{"xml_id": int, "q": float}]
                  xml_id - ID товара (из search_products)
                  q - количество (0.01-40)
                  Максимум 30 товаров
    
    Returns:
        {
            "ok": bool,
            "data": {"link": str}  # URL корзины на vkusvill.ru
        }
    
    Example:
        create_cart_link([
            {"xml_id": 36296, "q": 2},
            {"xml_id": 173, "q": 1}
        ])
    """
    client = _get_client()
    return client.call_tool("vkusvill_cart_link_create", {
        "products": products
    })


def close_connection() -> None:
    """
    Закрыть соединение с MCP сервером
    
    Вызывается автоматически при завершении программы.
    Можно вызвать вручную для явного закрытия.
    """
    global _client
    if _client is not None:
        _client.close()
        _client = None

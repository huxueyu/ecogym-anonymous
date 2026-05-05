"""Unit tests for SupplierCommunicationTools class."""

import json
from unittest.mock import Mock, patch, MagicMock

import pytest

from agno.tools.supplier import SupplierCommunicationTools


@pytest.fixture
def mock_perplexity_search():
    """Create a mock for PerplexityTools search method."""
    with patch("agno.tools.perplexity.PerplexityTools.search") as mock_search:
        mock_search.return_value = '{"results": ["Product A", "Product B"]}'
        yield mock_search


@pytest.fixture
def mock_duckduckgo_search():
    """Create a mock for DuckDuckGoTools search method."""
    with patch("agno.tools.duckduckgo.DuckDuckGoTools.search") as mock_search:
        mock_search.return_value = '{"results": ["Product A", "Product B"]}'
        yield mock_search


@pytest.fixture
def mock_openai_response():
    """Create a mock for OpenAI response."""
    mock_response = Mock()
    mock_response.content = "Thank you for your inquiry. We can supply the requested products."
    return mock_response


@pytest.fixture
def supplier_tools():
    """Create a SupplierCommunicationTools instance with mock dependencies."""
    with patch("agno.tools.supplier.PerplexityTools"):
        with patch("agno.tools.supplier.OpenAIChat") as mock_openai:
            # Mock the OpenAI response
            mock_response = Mock()
            mock_response.content = "Generated reply content"
            mock_openai_instance = Mock()
            mock_openai_instance.response.return_value = mock_response
            mock_openai.return_value = mock_openai_instance
            
            tools = SupplierCommunicationTools()
            # Replace the actual reply_model with our mock
            tools.reply_model = mock_openai_instance
            return tools


class TestSupplierCommunicationTools:
    """Test cases for SupplierCommunicationTools class."""

    def test_initialization(self):
        """Test initialization with default and custom parameters."""
        with patch("agno.tools.supplier.PerplexityTools"):
            with patch("agno.tools.supplier.OpenAIChat"):
                # Test default initialization
                tools = SupplierCommunicationTools()
                assert len(tools.orders) == 0

    def test_research_products_with_perplexity(self, supplier_tools):
        """Test researching products using Perplexity search engine."""
        # Mock the search tool
        with patch("agno.tools.supplier.PerplexityTools") as MockPerplexity:
            mock_search_tool = Mock()
            mock_search_tool.search.return_value = '{"results": ["Coke", "Pepsi", "Snickers"]}'
            MockPerplexity.return_value = mock_search_tool
            
            session_state = {}
            result = supplier_tools.research_products(session_state, "popular vending machine snacks")
            
            assert "Research results for" in result
            assert "popular vending machine snacks" in result
            mock_search_tool.search.assert_called_once_with("popular vending machine snacks")
            
            # Test session_state update
            assert "research_results" in session_state
            assert len(session_state["research_results"]) == 1
            assert session_state["research_results"][0]["query"] == "popular vending machine snacks"

    def test_generate_reply_calls_pplx_with_wholesaler_query(self, supplier_tools):
        """Ensure generate_reply constructs wholesaler query and calls PPLX.search with it."""
        with patch("agno.tools.supplier.PerplexityTools") as MockPerplexity:
            mock_search_tool = Mock()
            mock_search_tool.search.return_value = "Real data"
            MockPerplexity.return_value = mock_search_tool

            session_state = {}
            # Seed an incoming email to trigger reply
            supplier_tools.send_email(
                session_state,
                to="wholesaler@example.com",
                subject="Ask",
                body="What do you have?",
            )

            supplier_tools.generate_reply(session_state, email_id=0)

            # Verify that PerplexityTools.search was called with wholesaler name in query
            assert mock_search_tool.search.call_count == 1
            called_query = mock_search_tool.search.call_args[0][0]
            assert "wholesaler" in called_query
            assert "wholesaler" in called_query and "wholesaler" in called_query.lower()
            assert "wholesaler" in called_query and "wholesaler" in called_query.lower()

    def test_research_products_with_duckduckgo(self, supplier_tools):
        """Test researching products using DuckDuckGo search engine."""
        supplier_tools.search_engine = "duckduckgo"
        
        with patch("agno.tools.supplier.DuckDuckGoTools") as MockDDG:
            mock_search_tool = Mock()
            mock_search_tool.search.return_value = '{"results": ["Chips", "Candy"]}'
            MockDDG.return_value = mock_search_tool
            
            session_state = {}
            result = supplier_tools.research_products(session_state, "vending machine drinks")
            
            assert "Research results for" in result
            assert "vending machine drinks" in result
            mock_search_tool.search.assert_called_once()
            
            # Test session_state update
            assert "research_results" in session_state
            assert len(session_state["research_results"]) == 1

    def test_search_wholesalers(self, supplier_tools):
        """Test searching for wholesalers."""
        with patch("agno.tools.supplier.PerplexityTools") as MockPerplexity:
            mock_search_tool = Mock()
            mock_search_tool.search.return_value = "Wholesaler information"
            MockPerplexity.return_value = mock_search_tool
            
            session_state = {}
            result = supplier_tools.search_wholesalers(session_state, "New York", "soda")
            
            # Should return a list of wholesaler dicts
            assert isinstance(result, list)
            assert len(result) >= 0  # At least the mock data
            mock_search_tool.search.assert_called_once()
            
            # Test session_state update
            assert "wholesalers" in session_state
            assert "New York:soda" in session_state["wholesalers"]

    def test_read_emails_sorted_by_day(self, supplier_tools):
        """Test that read_emails returns emails sorted by day."""
        session_state = {"day": 0}
        supplier_tools.send_email(session_state, "a@example.com", "Day 0", "Body")
        
        session_state["day"] = 2
        supplier_tools.send_email(session_state, "b@example.com", "Day 2", "Body")
        
        session_state["day"] = 1
        supplier_tools.send_email(session_state, "c@example.com", "Day 1", "Body")
        
        emails = supplier_tools.read_emails(session_state)
        
        # 验证按天数排序
        assert len(emails) == 3
        assert emails[0]["day"] == 0
        assert emails[0]["to"] == "a@example.com"
        assert emails[1]["day"] == 1
        assert emails[1]["to"] == "c@example.com"
        assert emails[2]["day"] == 2
        assert emails[2]["to"] == "b@example.com"

    def test_send_email(self, supplier_tools):
        """Test sending an email."""
        # Initially no emails
        assert len(supplier_tools.emails) == 0
        
        session_state = {"day": 5}  # 设置当前天数
        # Send an email
        result = supplier_tools.send_email(
            session_state,
            to="wholesaler@example.com",
            subject="Inquiry about products",
            body="I would like to know more about your products."
        )
        
        # Check result
        assert "Email sent to" in result
        assert "wholesaler@example.com" in result
        
        # Check email was stored locally
        assert len(supplier_tools.emails) == 1
        email = supplier_tools.emails[0]
        assert email["to"] == "wholesaler@example.com"
        assert email["subject"] == "Inquiry about products"
        assert email["status"] == "sent"
        assert "timestamp" in email
        assert email["day"] == 5  # 验证 day 字段
        
        # Check email was stored in session_state
        assert "emails" in session_state
        assert len(session_state["emails"]) == 1
        assert session_state["emails"][0]["to"] == "wholesaler@example.com"
        assert session_state["emails"][0]["day"] == 5  # 验证 session_state 中的 day 字段

    def test_read_emails_empty(self, supplier_tools):
        """Test reading emails when inbox is empty."""
        session_state = {}
        emails = supplier_tools.read_emails(session_state)
        assert isinstance(emails, list)
        assert len(emails) == 0

    def test_read_emails_with_emails(self, supplier_tools):
        """Test reading emails when there are emails in the inbox."""
        session_state = {"day": 0}
        # Send some emails first
        supplier_tools.send_email(session_state, "seller1@example.com", "Subject 1", "Body 1")
        
        session_state["day"] = 2
        supplier_tools.send_email(session_state, "seller2@example.com", "Subject 2", "Body 2")
        
        # Read emails
        emails = supplier_tools.read_emails(session_state)
        
        assert len(emails) == 2
        # 验证按天数排序
        assert emails[0]["to"] == "seller1@example.com"
        assert emails[0]["day"] == 0
        assert emails[1]["to"] == "seller2@example.com"
        assert emails[1]["day"] == 2

    def test_generate_reply_invalid_email_id(self, supplier_tools):
        """Test generating reply with invalid email ID."""
        session_state = {}
        # No emails yet
        result = supplier_tools.generate_reply(session_state, email_id=0)
        assert "Invalid email ID" in result
        
        # Only one email, trying to access index beyond
        supplier_tools.send_email(session_state, "test@example.com", "Test", "Test")
        result = supplier_tools.generate_reply(session_state, email_id=10)
        assert "Invalid email ID" in result

    def test_generate_reply_success(self, supplier_tools):
        """Test generating a reply to an email."""
        # Mock search tool
        with patch("agno.tools.supplier.PerplexityTools") as MockPerplexity:
            mock_search_tool = Mock()
            mock_search_tool.search.return_value = "Real product data"
            MockPerplexity.return_value = mock_search_tool
            
            session_state = {"day": 3}
            # Send an initial email
            supplier_tools.send_email(
                session_state,
                to="wholesaler@example.com",
                subject="Product Inquiry",
                body="What products do you have?"
            )
            
            # Initially there is one email
            assert len(supplier_tools.emails) == 1
            assert len(session_state["emails"]) == 1
            
            # Generate reply
            result = supplier_tools.generate_reply(session_state, email_id=0)
            
            # Should have 2 emails now (original + reply)
            assert len(supplier_tools.emails) == 2
            assert len(session_state["emails"]) == 2
            
            # Check the reply was added
            reply = supplier_tools.emails[1]
            assert reply["subject"] == "Re: Product Inquiry"
            assert reply["from"] == "wholesaler@example.com"  # Sent by wholesaler
            assert reply["to"] == "agent@vending.com"  # Sent to agent
            assert reply["day"] == 4  # 验证次日回复

    def test_generate_reply_with_search_and_llm(self, supplier_tools):
        """Test that generate_reply uses search and LLM."""
        # Mock search tool
        with patch("agno.tools.supplier.PerplexityTools") as MockPerplexity:
            mock_search_tool = Mock()
            mock_search_tool.search.return_value = "Product data"
            MockPerplexity.return_value = mock_search_tool
            
            # Create a custom mock for the reply model
            mock_response = Mock()
            mock_response.content = "Thank you! We can supply those items."
            supplier_tools.reply_model.response.return_value = mock_response
            
            session_state = {}
            # Send email
            supplier_tools.send_email(session_state, "wholesaler@test.com", "Order", "I need items")
            
            # Generate reply
            result = supplier_tools.generate_reply(session_state, email_id=0)
            
            # Verify search was called
            mock_search_tool.search.assert_called_once()
            
            # Verify LLM was called
            supplier_tools.reply_model.response.assert_called_once()

    def test_process_order_invalid_email_id(self, supplier_tools):
        """Test processing order with invalid email ID."""
        session_state = {}
        # No emails
        result = supplier_tools.process_order(session_state, email_id=0, items=[{"name": "Coke", "quantity": 10}])
        assert "Invalid email ID" in result
        
        # Only one email, trying invalid ID
        supplier_tools.send_email(session_state, "test@example.com", "Test", "Test")
        result = supplier_tools.process_order(session_state, email_id=5, items=[{"name": "Coke", "quantity": 10}])
        assert "Invalid email ID" in result

    def test_process_order_success(self, supplier_tools):
        """Test successfully processing an order."""
        session_state = {"day": 2}
        # Create an inquiry email
        supplier_tools.send_email(
            session_state,
            to="wholesaler@example.com",
            subject="Order Request",
            body="I would like to order some products."
        )
        
        # Process order
        items = [{"name": "Coke", "quantity": 50}, {"name": "Snickers", "quantity": 30}]
        result = supplier_tools.process_order(session_state, email_id=0, items=items)
        
        # Check result
        assert "Order processed" in result
        
        # Check order was stored locally
        assert len(supplier_tools.orders) == 1
        order = supplier_tools.orders[0]
        assert order["items"] == items
        assert order["status"] == "processing"
        assert "delivery_time" in order
        assert order["created_day"] == 2  # 验证创建天数
        assert order["delivery_day"] == 5  # 验证交付天数（3天后）
        
        # Check order was stored in session_state
        assert "orders" in session_state
        assert len(session_state["orders"]) == 1
        assert session_state["orders"][0]["items"] == items
        
        # Check notification email was sent
        assert len(supplier_tools.emails) == 2  # Original + notification
        assert len(session_state["emails"]) == 2
        notification = supplier_tools.emails[1]
        assert notification["subject"] == "Order Confirmation"
        assert "Coke" in notification["body"]
        assert notification["status"] == "received"
        assert notification["day"] == 5  # 验证交付日期的通知邮件

    def test_process_order_with_multiple_items(self, supplier_tools):
        """Test processing order with multiple items."""
        session_state = {}
        supplier_tools.send_email(session_state, "seller@example.com", "Order", "I need products")
        
        items = [
            {"name": "Product A", "quantity": 10},
            {"name": "Product B", "quantity": 20},
            {"name": "Product C", "quantity": 15}
        ]
        
        result = supplier_tools.process_order(session_state, email_id=0, items=items)
        
        assert "Order processed" in result
        assert len(supplier_tools.orders) == 1
        assert len(supplier_tools.orders[0]["items"]) == 3
        assert len(session_state["orders"]) == 1
        assert len(session_state["orders"][0]["items"]) == 3

    def test_multiple_emails_chain(self, supplier_tools):
        """Test a chain of multiple emails and replies."""
        session_state = {}
        # Initial inquiry
        supplier_tools.send_email(session_state, "wholesaler@example.com", "Hello", "Hi there")
        assert len(supplier_tools.emails) == 1
        assert len(session_state["emails"]) == 1
        
        # Generate reply
        with patch("agno.tools.supplier.PerplexityTools") as MockPerplexity:
            mock_search = Mock()
            mock_search.search.return_value = "Data"
            MockPerplexity.return_value = mock_search
            
            supplier_tools.generate_reply(session_state, email_id=0)
            assert len(supplier_tools.emails) == 2
            assert len(session_state["emails"]) == 2
            
            # Process order
            items = [{"name": "Item", "quantity": 5}]
            supplier_tools.process_order(session_state, email_id=1, items=items)  # Process the reply email
            assert len(supplier_tools.emails) == 3
            assert len(session_state["emails"]) == 3
            assert len(supplier_tools.orders) == 1
            assert len(session_state["orders"]) == 1

    def test_search_wholesalers_returns_list(self, supplier_tools):
        """Test that search_wholesalers returns a list of dictionaries."""
        with patch("agno.tools.supplier.PerplexityTools") as MockPerplexity:
            mock_search = Mock()
            mock_search.search.return_value = "data"
            MockPerplexity.return_value = mock_search
            
            session_state = {}
            result = supplier_tools.search_wholesalers(session_state, "New York", "soda")
            
            # Should return a list
            assert isinstance(result, list)
            # Should contain dicts with specific keys
            for item in result:
                assert isinstance(item, dict)
                assert "name" in item
                assert "email" in item
                assert "products" in item
            
            # Test session_state update
            assert "wholesalers" in session_state
            assert "New York:soda" in session_state["wholesalers"]

    def test_read_emails_sorted_by_day(self, supplier_tools):
        """Test that read_emails returns emails sorted by day."""
        session_state = {"day": 0}
        supplier_tools.send_email(session_state, "a@example.com", "Day 0", "Body")
        
        session_state["day"] = 2
        supplier_tools.send_email(session_state, "b@example.com", "Day 2", "Body")
        
        session_state["day"] = 1
        supplier_tools.send_email(session_state, "c@example.com", "Day 1", "Body")
        
        emails = supplier_tools.read_emails(session_state)
        
        # 验证按天数排序
        assert len(emails) == 3
        assert emails[0]["day"] == 0
        assert emails[0]["to"] == "a@example.com"
        assert emails[1]["day"] == 1
        assert emails[1]["to"] == "c@example.com"
        assert emails[2]["day"] == 2
        assert emails[2]["to"] == "b@example.com"


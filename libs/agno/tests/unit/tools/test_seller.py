"""
Unit tests for libs.agno.agno.tools.seller
========================================

These tests verify all public methods exposed by the SalesTools (Agno Toolkit)
and the underlying SalesModel.

File location: libs/agno/tests/unit/tools/test_seller.py
"""

import pytest

from libs.agno.agno.tools.seller import SalesModel, SalesTools


@pytest.fixture
def sales_tools():
    """Create SalesTools instance with deterministic RNG."""
    model = SalesModel()
    return SalesTools(model)


@pytest.fixture
def session_state():
    """
    Create a reusable session_state for all tests.
    Simulates the business state that would be managed by the Agent.
    """
    return {
        "money": 100.0,
        "day": 0,
        "price_by_sku": {"cola": 2.0, "chips": 1.5},
        "qty_by_sku": {"cola": 10, "chips": 8},
        "category_by_sku": {"cola": "drink", "chips": "snack"},
        "wholesale_costs": {"cola": 1.2, "chips": 0.8},
        "daily_sales": [],
    }


def test_get_price(sales_tools, session_state):
    """Test getting price from session_state."""
    price = sales_tools.get_price(session_state, "cola")

    assert isinstance(price, float)
    assert price == session_state["price_by_sku"]["cola"]


def test_get_price_missing_product(sales_tools, session_state):
    """Test error handling when product not found."""
    result = sales_tools.get_price(session_state, "nonexistent")
    assert isinstance(result, str)
    assert "not found in price_by_sku" in result


def test_set_price(sales_tools, session_state):
    """Test setting price for a product."""
    # Set price for a new product
    result = sales_tools.set_price(session_state, "water", 1.75)
    
    assert isinstance(result, str)
    assert "Set price for 'water' to $1.75" in result
    assert session_state["price_by_sku"]["water"] == 1.75


def test_set_price_updates_existing(sales_tools, session_state):
    """Test updating an existing price."""
    original_price = session_state["price_by_sku"]["cola"]
    new_price = 2.50
    
    result = sales_tools.set_price(session_state, "cola", new_price)
    
    assert isinstance(result, str)
    assert f"Set price for 'cola' to ${new_price:.2f}" in result
    assert session_state["price_by_sku"]["cola"] == new_price
    assert session_state["price_by_sku"]["cola"] != original_price


def test_set_price_negative_raises_error(sales_tools, session_state):
    """Test that setting negative price raises ValueError."""
    with pytest.raises(ValueError, match="Price must be positive"):
        sales_tools.set_price(session_state, "cola", -1.0)


def test_set_price_zero_raises_error(sales_tools, session_state):
    """Test that setting zero price raises ValueError."""
    with pytest.raises(ValueError, match="Price must be positive"):
        sales_tools.set_price(session_state, "cola", 0.0)


def test_set_price_initializes_price_by_sku(sales_tools):
    """Test that set_price initializes price_by_sku if missing."""
    empty_state = {
        "money": 100.0,
        "day": 0,
        "qty_by_sku": {"cola": 10},
    }
    
    result = sales_tools.set_price(empty_state, "cola", 2.0)
    
    assert "price_by_sku" in empty_state
    assert empty_state["price_by_sku"]["cola"] == 2.0
    assert isinstance(result, str)


def test_get_demand_params(sales_tools, session_state):
    """Test getting demand parameters."""
    params = sales_tools.get_demand_params(session_state, "cola")

    assert isinstance(params, dict)
    assert "eps" in params
    assert "p_ref" in params
    assert "b_base" in params
    assert isinstance(params["eps"], float)
    assert isinstance(params["p_ref"], float)
    assert isinstance(params["b_base"], float)
    assert params["eps"] < 0  # elasticity should be negative


def test_simulate_day(sales_tools, session_state):
    """Test daily sales simulation with session_state updates."""
    initial_money = session_state["money"]
    initial_qty_cola = session_state["qty_by_sku"]["cola"]
    initial_qty_chips = session_state["qty_by_sku"]["chips"]
    
    sold = sales_tools.simulate_day(session_state)

    # Check sold quantities
    assert isinstance(sold, dict)
    assert "cola" in sold and "chips" in sold
    assert isinstance(sold["cola"], int)
    assert isinstance(sold["chips"], int)
    assert 0 <= sold["cola"] <= initial_qty_cola
    assert 0 <= sold["chips"] <= initial_qty_chips
    
    # Check inventory was updated
    assert session_state["qty_by_sku"]["cola"] == initial_qty_cola - sold["cola"]
    assert session_state["qty_by_sku"]["chips"] == initial_qty_chips - sold["chips"]
    
    # Check money was updated
    expected_revenue = (
        sold["cola"] * session_state["price_by_sku"]["cola"] +
        sold["chips"] * session_state["price_by_sku"]["chips"]
    )
    assert session_state["money"] == pytest.approx(initial_money + expected_revenue)
    
    # Check sales history was recorded
    assert len(session_state["daily_sales"]) == 1
    assert session_state["daily_sales"][0]["day"] == 0
    assert session_state["daily_sales"][0]["sold"] == sold


@pytest.mark.parametrize("objective", ["profit", "revenue", "sell_through"])
def test_recommend_price_variants(sales_tools, session_state, objective):
    """Test price recommendation with different objectives."""
    rec_price = sales_tools.recommend_price(
        session_state=session_state,
        product_name="cola",
        objective=objective,
        wholesale_cost=1.2,
    )

    assert isinstance(rec_price, float)
    assert rec_price > 0.0


def test_recommend_price_uses_session_wholesale_cost(sales_tools, session_state):
    """Test that recommend_price uses wholesale_cost from session_state when not provided."""
    rec_price = sales_tools.recommend_price(
        session_state=session_state,
        product_name="cola",
        objective="profit",
    )
    
    assert isinstance(rec_price, float)
    assert rec_price > 0.0


def test_recommend_prices_batch(sales_tools, session_state):
    """Test batch price recommendation."""
    recs = sales_tools.recommend_prices(
        session_state=session_state,
        product_names=["cola", "chips"],
        objective="profit",
    )

    assert isinstance(recs, dict)
    assert "cola" in recs and "chips" in recs
    assert all(isinstance(v, float) and v > 0 for v in recs.values())


def test_update_demand_params(sales_tools, session_state):
    """Test updating demand parameters based on sales observation."""
    # Simulate a day first
    sold = sales_tools.simulate_day(session_state)
    cola_sold = sold["cola"]
    
    # Advance day to simulate next observation
    session_state["day"] = 1

    # Update demand params
    updated = sales_tools.update_demand_params(
        session_state=session_state,
        product_name="cola",
        sold_qty=cola_sold,
    )

    assert isinstance(updated, dict)
    assert updated["product_name"] == "cola"
    assert "b_base" in updated and isinstance(updated["b_base"], float)

    # Ensure the model internal state reflects update
    params_after = sales_tools.get_demand_params(session_state, "cola")
    assert pytest.approx(params_after["b_base"], rel=1e-6) == pytest.approx(
        updated["b_base"], rel=1e-6
    )

def test_category_diversity_penalty_cap():
    """
    Verify that when the number of in-stock options in a category greatly exceeds
    the optimal threshold, the demand reduction is capped at 50% (default).
    """
    model = SalesModel()
    # Disable noise for deterministic ratio checks
    model.cfg.noise_std = 0.0
    tools = SalesTools(model)

    # Ensure parameters exist and set a large baseline to avoid rounding effects
    p = tools.get_demand_params({}, "cola")
    model._params["cola"].b_base = 1000.0  # type: ignore[attr-defined]

    # Helper to build session_state with k options in the same category
    def build_session_state(k: int) -> dict:
        price_by_sku = {"cola": 2.0}
        qty_by_sku = {"cola": 5000}
        category_by_sku = {"cola": "drink"}
        for i in range(k - 1):
            sku = f"filler{i}"
            price_by_sku[sku] = 1.0
            qty_by_sku[sku] = 10
            category_by_sku[sku] = "drink"
        return {
            "money": 0,
            "day": 0,
            "price_by_sku": price_by_sku,
            "qty_by_sku": qty_by_sku,
            "category_by_sku": category_by_sku,
            "daily_sales": [],
        }

    # k at optimal threshold (no penalty)
    state_opt = build_session_state(model.cfg.choice_optimal_options)
    sold_opt = tools.simulate_day(state_opt)["cola"]

    # k far beyond threshold -> penalty should cap at 50%
    state_many = build_session_state(60)
    sold_many = tools.simulate_day(state_many)["cola"]

    # Expect roughly 0.5x with small tolerance for rounding to int
    assert sold_opt > 0
    ratio = sold_many / sold_opt
    assert 0.48 <= ratio <= 0.52


def test_update_demand_params_adjust_eps_branch():
    """
    Enable adjust_eps and verify eps updates slightly and remains within bounds.
    """
    from libs.agno.agno.tools.seller import DemandConfig

    cfg = DemandConfig(adjust_eps=True, eps_alpha=0.02, seed=2025)
    model = SalesModel(config=cfg)
    tools = SalesTools(model)

    # Create session_state
    session_state = {
        "money": 100,
        "day": 5,
        "price_by_sku": {},
        "qty_by_sku": {},
        "category_by_sku": {},
        "daily_sales": [],
    }

    p = tools.get_demand_params(session_state, "cola")
    old_eps = p["eps"]

    # Set price in session_state to above reference
    session_state["price_by_sku"]["cola"] = p["p_ref"] * 1.2

    # Strong sales (2x baseline)
    strong_sales = int(model._params["cola"].b_base * 2)  # type: ignore[attr-defined]

    updated = tools.update_demand_params(session_state, product_name="cola", sold_qty=strong_sales)
    new_eps = model._params["cola"].eps  # type: ignore[attr-defined]

    # eps should have moved slightly and remain within configured bounds
    assert new_eps != old_eps
    lo, hi = cfg.eps_bounds
    assert lo <= new_eps <= hi

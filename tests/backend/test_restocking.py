"""Tests for the restocking recommendation and order endpoints."""
import main


def test_recommendations_respect_budget(client):
    data = client.get("/api/restocking/recommendations", params={"budget": 1000}).json()
    assert data["spent"] <= 1000
    assert data["remaining"] == round(1000 - data["spent"], 2)
    # Highest demand growth (WDG-001, +150 at 42.50) is ranked first
    assert data["items"][0]["item_sku"] == "WDG-001"


def test_recommendations_zero_budget_is_empty(client):
    assert client.get("/api/restocking/recommendations", params={"budget": 0}).json()["items"] == []


def test_recommendations_skip_decreasing_demand(client):
    data = client.get("/api/restocking/recommendations", params={"budget": 100000}).json()
    assert "MTR-304" not in {i["item_sku"] for i in data["items"]}


def test_negative_budget_rejected(client):
    assert client.get("/api/restocking/recommendations", params={"budget": -5}).status_code == 400


def test_submit_order_lead_time_is_longest_item(client):
    main.submitted_restock_orders.clear()
    items = client.get("/api/restocking/recommendations", params={"budget": 2000}).json()["items"]
    r = client.post("/api/restocking/orders", json={"budget": 2000, "items": items})
    assert r.status_code == 200
    order = r.json()
    assert order["lead_time_days"] == max(i["lead_time_days"] for i in items)
    assert client.get("/api/restocking/orders").json()[0]["order_number"] == order["order_number"]


def test_submit_order_over_budget_rejected(client):
    items = client.get("/api/restocking/recommendations", params={"budget": 2000}).json()["items"]
    assert client.post("/api/restocking/orders", json={"budget": 10, "items": items}).status_code == 400


def test_submit_empty_order_rejected(client):
    assert client.post("/api/restocking/orders", json={"budget": 100, "items": []}).status_code == 400

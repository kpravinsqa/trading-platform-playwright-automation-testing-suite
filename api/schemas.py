"""JSON schemas used for API contract validation."""

ORDER = {
    "type": "object",
    "required": ["id", "symbol", "side", "order_type", "quantity", "status", "created_at", "currency"],
    "properties": {
        "id": {"type": "integer"},
        "symbol": {"type": "string", "pattern": "^[A-Z]+$"},
        "side": {"enum": ["BUY", "SELL"]},
        "order_type": {"enum": ["MARKET", "LIMIT"]},
        "quantity": {"type": "integer", "minimum": 1},
        "limit_price": {"type": ["number", "null"]},
        "status": {"enum": ["PENDING", "FILLED", "CANCELLED"]},
        "commission": {"type": "number", "minimum": 0},
        "currency": {"const": "GBP"},
    },
}

ACCOUNT = {
    "type": "object",
    "required": ["currency", "cash", "invested", "total_value", "positions"],
    "properties": {
        "cash": {"type": "number"},
        "positions": {
            "type": "array",
            "items": {"type": "object", "required": ["symbol", "quantity", "avg_price", "market_value"]},
        },
    },
}

INSTRUMENT = {
    "type": "object",
    "required": ["symbol", "name", "exchange", "price", "status"],
    "properties": {"price": {"type": "number", "exclusiveMinimum": 0}, "status": {"enum": ["OPEN", "SUSPENDED"]}},
}

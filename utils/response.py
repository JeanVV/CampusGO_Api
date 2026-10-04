import json
from flask import jsonify

def success_response(data, message, http_code=200):
    return jsonify({
        "data": json.loads(json.dumps(data, default=lambda o: o.isoformat() if hasattr(o, "isoformat") else str(o))),
        "message": message,
        "status": True
    }), http_code

def error_response(message, http_code=400, data=None):
    return jsonify({
        "data": json.loads(json.dumps(data, default=lambda o: o.isoformat() if hasattr(o, "isoformat") else str(o))) if data is not None else None,
        "message": message,
        "status": False
    }), http_code
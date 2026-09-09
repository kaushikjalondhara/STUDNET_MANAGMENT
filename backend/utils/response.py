from flask import jsonify

def api_response(success=True, message="", data=None, status_code=200, errors=None):
    """Generates a standardized JSON response dictionary with HTTP status code."""
    payload = {
        'success': success,
        'message': message
    }
    if data is not None:
        payload['data'] = data
    if errors is not None:
        payload['errors'] = errors
        
    return jsonify(payload), status_code

def success_response(data=None, message="Operation completed successfully", status_code=200):
    """Shortcut helper for successful API responses."""
    return api_response(success=True, message=message, data=data, status_code=status_code)

def error_response(message="An error occurred", status_code=400, errors=None):
    """Shortcut helper for error API responses."""
    return api_response(success=False, message=message, data=None, status_code=status_code, errors=errors)

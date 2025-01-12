from datetime import datetime

from flask import jsonify


def apiResponse(error, code, data, msg):

    response = {
        "error": error,
        "data": data,
        "msg": msg,
        "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    return jsonify(response), code

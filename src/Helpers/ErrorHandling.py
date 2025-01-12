from src.Helpers.Response import apiResponse


class CustomError(Exception):
    def __init__(self, msg, code):
        self.msg = msg
        self.code = code

def handleCustomError(e):
    print(f"handle_custom_error: {e}")
    return apiResponse(True, e.code, None, f"Error: {e.msg}")


def handleValidationError(e):
    print(f"handle_validation_error: {e}")
    return apiResponse(True, 400, None, f"Validation Error: {e}")


# Handle global exceptions
def handleGenericError(e):
    print(f"handle_generic_error: {e}")
    return apiResponse(True, 500, None, f"Internal Server Error: {e}")

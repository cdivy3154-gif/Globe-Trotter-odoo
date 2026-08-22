class AppException(Exception):
    def __init__(self, detail: str, code: str = "APP_ERROR"):
        super().__init__(detail)
        self.detail = detail
        self.code = code

    def __str__(self) -> str:
        return f"[{self.code}] {self.detail}"


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", f"{resource.upper()}_NOT_FOUND")


class ForbiddenError(AppException):
    def __init__(self, detail: str = "Access denied"):
        super().__init__(detail, "FORBIDDEN")


class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail, "UNAUTHORIZED")


class ConflictError(AppException):
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(detail, "CONFLICT")


class ValidationError(AppException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(detail, "VALIDATION_ERROR")


class OverBudgetError(AppException):
    def __init__(self, detail: str = "Budget exceeded"):
        super().__init__(detail, "OVER_BUDGET")
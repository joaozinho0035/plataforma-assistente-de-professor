"""
Canal Educação v3.0 — Domain Exceptions.
Exceções tipadas para erros de domínio e regras de negócio.
"""


class DomainException(Exception):
    """Base para todas as exceções de domínio."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class EntityNotFoundException(DomainException):
    """Entidade não encontrada no banco de dados."""

    def __init__(self, entity: str, identifier: str):
        super().__init__(
            message=f"{entity} não encontrado(a): {identifier}",
            code="NOT_FOUND",
        )


class ConflictException(DomainException):
    """Conflito de dados (duplicidade, violação de unicidade)."""

    def __init__(self, message: str):
        super().__init__(message=message, code="CONFLICT")


class BusinessRuleViolation(DomainException):
    """Violação de uma regra de negócio do domínio."""

    def __init__(self, message: str):
        super().__init__(message=message, code="BUSINESS_RULE_VIOLATED")


class AuthenticationError(DomainException):
    """Credenciais inválidas ou token expirado."""

    def __init__(self, message: str = "Credenciais inválidas ou token expirado."):
        super().__init__(message=message, code="AUTHENTICATION_FAILED")


class AuthorizationError(DomainException):
    """Utilizador sem permissão para executar a ação."""

    def __init__(self, message: str = "Sem permissão para executar esta ação."):
        super().__init__(message=message, code="FORBIDDEN")


class InvalidInviteTokenError(DomainException):
    """Token de convite inválido ou expirado."""

    def __init__(self):
        super().__init__(
            message="Token de convite inválido ou expirado.",
            code="INVALID_INVITE_TOKEN",
        )


class DuplicateLessonError(DomainException):
    """Aula geminada detectada (P1/P2/P3 obrigatório)."""

    def __init__(self, nome_gerado: str):
        super().__init__(
            message=(
                f"Aula geminada detectada: '{nome_gerado}' já existe. "
                "Adicione o sufixo P1, P2 ou P3 ao conteúdo."
            ),
            code="DUPLICATE_LESSON",
        )

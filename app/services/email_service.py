import aiosmtplib
from email.message import EmailMessage
from app.core.config import get_settings

settings = get_settings()

async def send_invite_email(email: str, full_name: str, token: str):
    """
    Envia email de convite com link de confirmação conforme especificação 2.1.
    """
    # Verifica se as configurações de SMTP estão presentes
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"⚠️ SMTP não configurado no .env. Ignorando envio real.")
        print(f"🔗 Link de Confirmação para {email}: http://localhost:8000/confirm?token={token}")
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message["Subject"] = "Bem-vindo ao Canal Educação - Ative sua Conta"
    
    # O link deve apontar para a rota de confirmação definida no frontend/template
    # Usamos o primeiro origin do CORS ou localhost como fallback
    base_url = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:8000"
    confirm_url = f"{base_url}/confirm?token={token}"
    
    content = f"""
    Olá {full_name},
    
    Bem-vindo ao Canal Educação!
    
    Sua conta foi criada no sistema Canal Educação.
    
    Para começar a utilizar a plataforma, você precisa definir sua senha inicial
    através do link seguro abaixo:
    
    {confirm_url}
    
    Atenção: Este link é válido por {settings.INVITE_TOKEN_EXPIRE_HOURS} horas.
    
    Se você não solicitou este acesso, por favor ignore este e-mail.
    
    Atenciosamente,
    Equipe Canal Educação
    """
    message.set_content(content)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
        )
        print(f"✅ Email transacional enviado com sucesso para: {email}")
    except Exception as e:
        print(f"❌ Erro ao disparar email para {email}: {str(e)}")

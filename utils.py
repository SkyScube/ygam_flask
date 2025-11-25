import secrets
import string

def generate_cuid():
    """Génère un ID unique similaire à cuid de Prisma"""
    # Version simplifiée - tu peux utiliser la lib 'cuid' si tu veux
    return 'c' + ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(24))
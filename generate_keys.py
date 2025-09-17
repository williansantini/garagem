from pywebpush import generate_vapid_keys

# A função agora retorna um dicionário com as chaves
vapid_keys = generate_vapid_keys()

print("--- Chaves VAPID Geradas ---")
print(f"Chave Pública (VAPID_PUBLIC_KEY): {vapid_keys['public_key']}")
print(f"Chave Privada (VAPID_PRIVATE_KEY): {vapid_keys['private_key']}")
print("----------------------------")
print("Guarde estas chaves em segurança e configure-as como variáveis de ambiente.")
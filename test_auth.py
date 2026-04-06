from core.auth import hash_password, verify_password

password = "MonSuperMotDePasse123"
hashed = hash_password(password)

print(f"Mot de passe : {password}")
print(f"Hachage stocké : {hashed}") # Tu verras que c'est illisible !

is_correct = verify_password("MauvaisPass", hashed)
print(f"Test mauvais pass : {'✅' if not is_correct else '❌'}")

is_correct = verify_password(password, hashed)
print(f"Test bon pass : {'✅' if is_correct else '❌'}")
import instaloader

L = instaloader.Instaloader()

USERNAME = "instadanvideoyukla1"
PASSWORD = "Namangan0700"
SESSION_FILE = "insta_session"  # cookie fayl nomi

# Login qilish
L.login(USERNAME, PASSWORD)

# Sessiyani cookie faylga saqlash
L.save_session_to_file(SESSION_FILE)
print("Cookie fayl yaratildi!")

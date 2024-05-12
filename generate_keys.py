import pickle
from pathlib import Path
import streamlit_authenticator as stauth
import hashlib

names = ["Nikki Aung","Zenith Oo"]
usernames = ["Nikki", "Zenith"]
passwords = ["XXX", "XXX"]
special_key = "XXX"

hashed_passwords = stauth.Hasher(passwords).generate()
hashed_specialkey = hashlib.sha256(str(special_key).encode()).hexdigest()

file_path_pw = Path(__file__).parent / "hashed_pw.pkl"
with file_path_pw.open("wb") as file:
    pickle.dump(hashed_passwords, file)

file_path_sk = Path(__file__).parent / "hashed_sk.pkl"
with file_path_sk.open("wb") as file:
    pickle.dump(hashed_specialkey, file)


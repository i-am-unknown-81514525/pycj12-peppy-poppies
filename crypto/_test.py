from pathlib import Path

from key import export_key, generate_key_pair, import_private_key, import_public_key

if __name__ == "__main__":
    pri, pub = generate_key_pair()
    export_key(pri, Path("./crypto/keys") / "private.pem")
    pri_new = import_private_key(Path("./crypto/keys") / "private.pem")
    export_key(pub, Path("./crypto/keys") / "public.pem")
    pub_new = import_public_key(Path("./crypto/keys") / "public.pem")

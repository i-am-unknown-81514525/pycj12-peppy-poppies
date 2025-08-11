from pathlib import Path

from server.crypto.key import export_key, generate_key_pair, import_private_key, import_public_key

if __name__ == "__main__":
    pri, pub = generate_key_pair()
    export_key(pri, Path() / "pri.pem")
    pri_new = import_private_key(Path() / "pri.pem")
    export_key(pub, Path() / "pub.pem")
    pub_new = import_public_key(Path() / "pub.pem")

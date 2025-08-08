from pathlib import Path

from backend.crypto.key import _export_private_key, _import_private_key, generate_key_pair, _export_public_key, _import_public_key

if __name__ == "__main__":
    pri, pub = generate_key_pair()
    _export_private_key(pri, Path() / "pri.pem")
    pri_new = _import_private_key(Path() / "pri.pem")
    _export_public_key(pub, Path() / "pub.pem")
    pub_new = _import_public_key(Path() / "pub.pem")

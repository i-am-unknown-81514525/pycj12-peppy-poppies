from pathlib import Path


from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import (Encoding, PublicFormat, PrivateFormat, NoEncryption, load_pem_public_key, load_pem_private_key)

def generate_key_pair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key

def _import_public_key(pub_path: Path) -> Ed25519PublicKey:
    with open(pub_path, "rb") as fp:
        public_key = load_pem_public_key(fp.read())
    if not isinstance(public_key, Ed25519PublicKey):
        raise TypeError(f"The public key from {pub_path.as_posix()} is not Ed25519 public key")
    return public_key

def _import_private_key(pri_path: Path) -> Ed25519PrivateKey:
    with open(pri_path, "rb") as fp:
        private_key = load_pem_private_key(fp.read(), None)
    if not isinstance(private_key, Ed25519PrivateKey):
        raise TypeError(f"The public key from {pri_path.as_posix()} is not Ed25519 public key")
    return private_key

def _export_public_key(pub_key: Ed25519PublicKey ,pub_path: Path) -> None:
    with pub_path.open("wb") as fp:
        fp.write(pub_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo))

def _export_private_key(pri_key: Ed25519PrivateKey ,pri_path: Path) -> None:
    with pri_path.open("wb") as fp:
        fp.write(pri_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption()))

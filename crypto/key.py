from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
    load_pem_public_key,
)

type Ed25519Key = Ed25519PublicKey | Ed25519PrivateKey


def generate_key_pair() -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Generate a pair of Ed25519 private and public keys.

    Returns:
        tuple[Ed25519PrivateKey, Ed25519PublicKey]: The generated private and public key pair.

    """
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return private_key, public_key


def import_public_key(pub_path: Path) -> Ed25519PublicKey:
    """Import PEM formatted Ed25519 public key.

    Returns:
        Ed25519PublicKey: The imported Ed25519 public key.

    Raises:
        TypeError: If the key is not an Ed25519 public key.

    """
    with pub_path.open("rb") as fp:
        public_key = load_pem_public_key(fp.read())
    if not isinstance(public_key, Ed25519PublicKey):
        raise TypeError(f"The public key from {pub_path.as_posix()} is not Ed25519 public key")
    return public_key


def import_private_key(pri_path: Path) -> Ed25519PrivateKey:
    """Import PEM formatted Ed25519 private key.

    Returns:
        Ed25519PrivateKey: The imported Ed25519 private key.

    Raises:
        TypeError: If the key is not an Ed25519 private key.

    """
    with pri_path.open("rb") as fp:
        private_key = load_pem_private_key(fp.read(), None)
    if not isinstance(private_key, Ed25519PrivateKey):
        raise TypeError(f"The private key from {pri_path.as_posix()} is not Ed25519 private key")
    return private_key


def import_all(path: Path) -> tuple[Ed25519PrivateKey, Ed25519PublicKey]:
    """Import a pair of Ed25519 private and public keys from `path/pub.pem` and `path/pri.pem`.

    Returns:
        tuple[Ed25519PrivateKey, Ed25519PublicKey]: The imported private and public key pair.

    """
    return (
        import_private_key(path / "pri.pem"),
        import_public_key(path / "pub.pem"),
    )


def export_key(key: Ed25519Key, path: Path) -> None:
    """Export Ed25519 public/private key as PEM format to the given path."""
    with path.open("wb") as fp:
        fp.write(get_pem(key))


def export_all(path: Path, *, pub_key: Ed25519PublicKey, pri_key: Ed25519PrivateKey) -> None:
    """Export both public and private Ed25519 key in path/pub.pem and path/pri.pem respectively."""
    export_key(pub_key, path / "pub.pem")
    export_key(pri_key, path / "pri.pem")


def get_pem(key: Ed25519Key) -> bytes:
    """Get PEM formatted Ed25519 public/private key as bytes.

    Returns:
        bytes: PEM formatted key as bytes.

    Raises:
        ValueError: If the key is not an Ed25519PublicKey or Ed25519PrivateKey.

    """
    if isinstance(key, Ed25519PublicKey):
        return key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
    if isinstance(key, Ed25519PrivateKey):
        return key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    raise ValueError("The key must be either Ed25519PublicKey or Ed25519PrivateKey")

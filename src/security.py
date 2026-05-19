"""
security.py
팀원 A — 암호화 & 보안 엔진 (The Shield)

담당 함수:
  - hash_password()   : SHA-256 기반 비밀번호 해싱
  - encrypt_text()    : AES-256-CBC 기반 텍스트 암호화
  - decrypt_text()    : AES-256-CBC 기반 텍스트 복호화
"""

import hashlib
import os
import base64

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding


# ──────────────────────────────────────────────
# 내부 상수
# ──────────────────────────────────────────────
_BLOCK_SIZE = 128          # AES 블록 크기 (bits)
_IV_SIZE    = 16           # AES IV 크기  (bytes)
_KEY_SIZE   = 32           # AES-256 키 크기 (bytes)


# ──────────────────────────────────────────────
# 1. 비밀번호 해싱
# ──────────────────────────────────────────────
def hash_password(password: str) -> str:
    """
    사용자 비밀번호를 SHA-256으로 해시하여 반환한다.

    - 복원 불가능한 단방향 변환
    - 로그인 인증 시 입력값을 다시 해시해 비교하는 방식으로 사용

    Args:
        password (str): 사용자가 입력한 평문 비밀번호

    Returns:
        str: 64자리 16진수 SHA-256 다이제스트
    
    Example:
        >>> hashed = hash_password("mySecret123")
        >>> print(hashed)
        'a3f5...c9d2'   # 64자리 hex 문자열
    """
    if not isinstance(password, str) or not password:
        raise ValueError("비밀번호는 비어 있지 않은 문자열이어야 합니다.")

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ──────────────────────────────────────────────
# 내부 헬퍼: 키문자열 → AES 키 파생
# ──────────────────────────────────────────────
def _derive_key( keyString: str) -> bytes:
    """
    비밀번호 문자열을 SHA-256 해시로 변환해 32바이트 AES 키를 만든다.
    별도 솔트 없이 결정론적으로 동작하므로,
    같은 비밀번호는 항상 같은 키를 생성한다.
    """
    return hashlib.sha256( keyString.encode("utf-8")).digest()   # bytes, 32 bytes


# ──────────────────────────────────────────────
# 2. 텍스트 암호화
# ──────────────────────────────────────────────
def encrypt_text(plain_text: str, keyString: str) -> str:
    """
    평문 일기를 AES-256-CBC 방식으로 암호화한다.

    암호화 절차:
      1. AES 문자열 키
      2. 랜덤 16바이트 IV 생성
      3. PKCS7 패딩 후 AES-CBC 암호화
      4. (IV + 암호문)을 Base64로 인코딩해 문자열로 반환
         → 파일에 저장해도 텍스트 형태 유지

    Args:
        plain_text (str): 암호화할 원문 일기 내용
        keyString  (str): 암호화에 사용할 키문자열

    Returns:
        str: Base64 인코딩된 암호화 문자열 (IV 포함)

    Raises:
        ValueError: 입력이 비어 있을 때
    """
    if not plain_text:
        raise ValueError("암호화할 텍스트가 비어 있습니다.")
    if not keyString:
        raise ValueError("비밀번호가 비어 있습니다.")

    key = _derive_key(keyString)
    iv  = os.urandom(_IV_SIZE)          # 매 암호화마다 새 IV

    # PKCS7 패딩
    padder      = padding.PKCS7(_BLOCK_SIZE).padder()
    padded_data = padder.update(plain_text.encode("utf-8")) + padder.finalize()

    # AES-CBC 암호화
    cipher    = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    cipher_bytes = encryptor.update(padded_data) + encryptor.finalize()

    # IV + 암호문 → Base64 문자열
    encrypted_b64 = base64.b64encode(iv + cipher_bytes).decode("utf-8")
    return encrypted_b64


# ──────────────────────────────────────────────
# 3. 텍스트 복호화
# ──────────────────────────────────────────────
def decrypt_text(encrypted_text: str, keyString: str) -> str:
    """
    encrypt_text()로 암호화된 문자열을 복호화해 원문을 반환한다.

    복호화 절차:
      1. Base64 디코딩 → 앞 16바이트: IV, 나머지: 암호문
      2. AES 문자열키
      3. AES-CBC 복호화 후 PKCS7 패딩 제거

    Args:
        encrypted_text (str): encrypt_text()가 반환한 Base64 문자열
        keyString  (str): 암호화에 사용할 키문자열

    Returns:
        str: 복호화된 원문 텍스트

    Raises:
        ValueError: 비밀번호가 틀렸거나 데이터가 손상된 경우
    """
    if not encrypted_text:
        raise ValueError("복호화할 텍스트가 비어 있습니다.")
    if not keyString:
        raise ValueError("비밀번호가 비어 있습니다.")

    try:
        raw = base64.b64decode(encrypted_text.encode("utf-8"))
    except Exception:
        raise ValueError("암호화 데이터 형식이 올바르지 않습니다.")

    if len(raw) < _IV_SIZE:
        raise ValueError("암호화 데이터가 너무 짧습니다.")

    iv           = raw[:_IV_SIZE]
    cipher_bytes = raw[_IV_SIZE:]
    key          = _derive_key(keyString)

    try:
        cipher    = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plain = decryptor.update(cipher_bytes) + decryptor.finalize()

        # PKCS7 패딩 제거
        unpadder   = padding.PKCS7(_BLOCK_SIZE).unpadder()
        plain_bytes = unpadder.update(padded_plain) + unpadder.finalize()
    except Exception:
        raise ValueError("복호화 실패: 비밀번호가 틀렸거나 데이터가 손상되었습니다.")

    return plain_bytes.decode("utf-8")


# ──────────────────────────────────────────────
# 간단한 동작 확인 (직접 실행 시)
# ──────────────────────────────────────────────
if __name__ == "__main__":
    keyString = "파이썬123"
    pw   = "diary_secret_2024"
    text = "오늘은 정말 행복한 하루였다. 친구들과 영화를 보고 맛있는 것도 먹었다."

    print("=== 비밀번호 해싱 ===")
    hashed = hash_password(pw)
    print(f"  원본  : {pw}")
    print(f"  해시값: {hashed}")

    print("\n=== 암호화 키 출력 ===")
    print(f"  암호화 키     : {keyString}")

    print("\n=== 텍스트 암호화 ===")
    encrypted = encrypt_text(text, keyString)
    print(f"  원문     : {text}")
    print(f"  암호화 후: {encrypted}")

    print("\n=== 텍스트 복호화 ===")
    decrypted = decrypt_text(encrypted, keyString)
    print(f"  복호화 후: {decrypted}")
    print(f"  원문 일치: {text == decrypted}")

    print("\n=== 틀린 키 문자열로 복호화 시도 ===")
    try:
        decrypt_text(encrypted, "wrong_password")
    except ValueError as e:
        print(f"  오류 발생 (정상): {e}")
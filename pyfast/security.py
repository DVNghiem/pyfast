# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from base64 import b64encode, b64decode

import typing


class EDEngine(ABC):
    @abstractmethod
    def encrypt(self, data: str) -> str:
        raise NotImplementedError("Method not implemented")

    @abstractmethod
    def decrypt(self, data: str) -> str:
        raise NotImplementedError("Method not implemented")


class AESEngine(EDEngine):
    def __init__(self, secret_key: bytes, iv: bytes, padding_class: typing.Type) -> None:
        super().__init__()
        self.secret_key = secret_key
        self.iv = iv
        self.padding = padding_class(128)

    def encrypt(self, data: str) -> bytes:
        bytes_data = data.encode("utf-8")
        encryptor = Cipher(algorithms.AES(self.secret_key), modes.GCM(self.iv), backend=default_backend()).encryptor()
        padder = self.padding.padder()
        padded_data = padder.update(bytes_data) + padder.finalize()
        enctyped_data = encryptor.update(padded_data) + encryptor.finalize()
        tag = encryptor.tag
        return b64encode(tag + enctyped_data)

    def decrypt(self, data: bytes) -> str:
        data = b64decode(data)
        tag = data[:16]
        encrypted_data = data[16:]
        decryptor = Cipher(algorithms.AES(self.secret_key), modes.GCM(self.iv, tag), backend=default_backend()).decryptor()
        unpadder = self.padding.unpadder()
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()
        return unpadded_data.decode("utf-8")

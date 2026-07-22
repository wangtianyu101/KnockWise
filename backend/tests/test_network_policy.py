"""Tests for the default no-public-network policy."""
import socket

import pytest


def test_public_socket_connection_is_blocked():
    with socket.socket() as client:
        with pytest.raises(pytest.fail.Exception, match="external network is disabled"):
            client.connect(("203.0.113.1", 80))

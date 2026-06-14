"""The transport package exposes its public surface."""

import vgmdb_client.transport as transport


def test_public_symbols_are_exported() -> None:
    expected = {
        "SyncTransport",
        "AsyncTransport",
        "TransportConfig",
        "TransportError",
        "CloudflareChallengeError",
        "NotFoundError",
        "RateLimitedError",
        "TransientTransportError",
    }
    assert expected <= set(transport.__all__)
    for name in expected:
        assert getattr(transport, name) is not None


def test_clients_are_constructible_from_package_root() -> None:
    config = transport.TransportConfig(user_agent="UA/1.0")
    sync = transport.SyncTransport(config)
    async_transport = transport.AsyncTransport(config)
    assert isinstance(sync, transport.SyncTransport)
    assert isinstance(async_transport, transport.AsyncTransport)
    sync.close()

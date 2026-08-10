import hashlib
import hmac

from app.utils.signal_lane import SignalLaneRegistry


def _proof(secret, project, lane, app_id, instance_id, generation, server_nonce, client_nonce):
    material = "|".join([
        "ether-ratchet-v1",
        project,
        lane,
        app_id,
        instance_id,
        str(generation),
        server_nonce,
        client_nonce,
    ])
    return hmac.new(secret.encode(), material.encode(), hashlib.sha256).hexdigest()


def test_configured_lane_requires_fresh_proof_every_transition():
    registry = SignalLaneRegistry()
    secret = "test-secret"
    project = "circa_haus"
    lane = "circa_haus:app:device"
    app_id = "app"
    instance_id = "device"

    challenge = registry.handshake(
        project_slug=project,
        app_id=app_id,
        instance_id=instance_id,
        domain="example.test",
        lane_id=lane,
        signal_secret=secret,
        client_nonce=None,
        presented_proof=None,
    )
    assert challenge.accepted is False
    nonce0 = challenge.server_nonce
    generation0 = challenge.generation

    client_nonce = "client-1"
    proof = _proof(secret, project, lane, app_id, instance_id, generation0, nonce0, client_nonce)
    verified = registry.handshake(
        project_slug=project,
        app_id=app_id,
        instance_id=instance_id,
        domain="example.test",
        lane_id=lane,
        signal_secret=secret,
        client_nonce=client_nonce,
        presented_proof=proof,
    )
    assert verified.accepted is True
    assert verified.generation == generation0 + 1

    missing = registry.heartbeat(
        project_slug=project,
        lane_id=lane,
        app_id=app_id,
        instance_id=instance_id,
        status="ok",
        signal_secret=secret,
        client_nonce=None,
        presented_proof=None,
    )
    assert missing is not None
    assert missing.accepted is False

    next_client_nonce = "client-2"
    next_proof = _proof(
        secret,
        project,
        lane,
        app_id,
        instance_id,
        verified.generation,
        verified.server_nonce,
        next_client_nonce,
    )
    accepted = registry.heartbeat(
        project_slug=project,
        lane_id=lane,
        app_id=app_id,
        instance_id=instance_id,
        status="ok",
        signal_secret=secret,
        client_nonce=next_client_nonce,
        presented_proof=next_proof,
    )
    assert accepted is not None
    assert accepted.accepted is True


def test_replayed_proof_is_rejected_after_ratchet_advances():
    registry = SignalLaneRegistry()
    secret = "test-secret"
    project = "project"
    lane = "project:app:device"
    app_id = "app"
    instance_id = "device"

    first = registry.handshake(
        project_slug=project,
        app_id=app_id,
        instance_id=instance_id,
        domain=None,
        lane_id=lane,
        signal_secret=secret,
        client_nonce=None,
        presented_proof=None,
    )
    client_nonce = "nonce-a"
    proof = _proof(secret, project, lane, app_id, instance_id, first.generation, first.server_nonce, client_nonce)
    ok = registry.handshake(
        project_slug=project,
        app_id=app_id,
        instance_id=instance_id,
        domain=None,
        lane_id=lane,
        signal_secret=secret,
        client_nonce=client_nonce,
        presented_proof=proof,
    )
    assert ok.accepted is True

    replay = registry.heartbeat(
        project_slug=project,
        lane_id=lane,
        app_id=app_id,
        instance_id=instance_id,
        status="ok",
        signal_secret=secret,
        client_nonce=client_nonce,
        presented_proof=proof,
    )
    assert replay is not None
    assert replay.accepted is False

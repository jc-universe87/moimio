import asyncio, pytest
from app.core.pubsub import broker

@pytest.mark.asyncio
async def test_registration_topic_delivers():
    topic = "registration:11111111-1111-1111-1111-111111111111"
    async with broker.subscribe(topic) as queue:
        await broker.publish(topic, {"type": "registration_created", "participant_id": "p1", "status": "confirmed"})
        msg = await asyncio.wait_for(queue.get(), timeout=2)
        assert msg["type"] == "registration_created" and msg["participant_id"] == "p1"
    print("  registration pub/sub delivers")

@pytest.mark.asyncio
async def test_stream_endpoint_registered():
    from app.main import app
    paths = [r.path for r in app.routes]
    assert "/api/events/{event_id}/registration/stream" in paths, "registration stream not registered"
    print("  /registration/stream endpoint registered")

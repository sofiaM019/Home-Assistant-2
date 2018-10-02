"""Test config flow."""
from unittest.mock import patch


async def test_hassio_discovery_startup(hass, hassio_client,
                                        aioclient_mock):
    """Test startup and discovery after event."""
    aioclient_mock.get(
        "http://127.0.0.1/discovery", json={
            'result': 'ok', 'data': {'discovery': [
                {
                    "service": "mqtt", "uuid": "test",
                    "addon": "mosquitto", "config":
                    {
                        'broker': 'mock-broker',
                        'port': 1883,
                        'username': 'mock-user',
                        'password': 'mock-pass',
                        'protocol': '3.1.1'
                    }
                }
            ]}})
    aioclient_mock.get(
        "http://127.0.0.1/addons/mosquitto/info", json={
            'result': 'ok', 'data': {'name': "Mosquitto Test"}
        })

    with patch('homeassistant.components.mqtt.'
               'config_flow.FlowHandler.async_step_hassio') as mock_mqtt:
        await hass.async_start()

        assert aioclient_mock.call_count == 5
        assert mock_mqtt.called
        assert mock_mqtt.assert_called_with(input={
            'broker': 'mock-broker', 'port': 1883, 'username': 'mock-user',
            'password': 'mock-pass', 'protocol': '3.1.1'
        })

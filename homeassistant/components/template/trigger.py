"""Offer template automation rules."""
from collections.abc import Iterable
from datetime import timedelta
import logging
from typing import Any

import voluptuous as vol

from homeassistant import exceptions
from homeassistant.const import CONF_FOR, CONF_PLATFORM, CONF_VALUE_TEMPLATE
from homeassistant.core import CALLBACK_TYPE, HassJob, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv, template
from homeassistant.helpers.event import (
    EventStateChangedData,
    TrackTemplate,
    TrackTemplateResult,
    async_call_later,
    async_track_template_result,
)
from homeassistant.helpers.template import Template, result_as_boolean
from homeassistant.helpers.trigger import TriggerActionType, TriggerInfo
from homeassistant.helpers.typing import ConfigType, EventType

_LOGGER = logging.getLogger(__name__)

CONF_TO = "to"
CONF_FROM = "from"

MATCH_ALL = "*"

TRIGGER_SCHEMA = IF_ACTION_SCHEMA = cv.TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_PLATFORM): "template",
        vol.Required(CONF_VALUE_TEMPLATE): cv.template,
        vol.Optional(CONF_FOR): cv.positive_time_period_template,
        vol.Optional(CONF_TO): vol.Any(str, [str], None),
        vol.Optional(CONF_FROM): vol.Any(str, [str], None),
    }
)


def _process_match(parameter: str | Iterable[str] | None):
    if parameter is None or parameter == MATCH_ALL:
        return lambda _: True

    if isinstance(parameter, str) or not hasattr(parameter, "__iter__"):
        return lambda value: str(value) == parameter

    parameter_set = set(parameter)

    return lambda value: str(value) in parameter_set


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
    *,
    platform_type: str = "template",
) -> CALLBACK_TYPE:
    """Listen for state changes based on configuration."""
    trigger_data = trigger_info["trigger_data"]
    value_template: Template = config[CONF_VALUE_TEMPLATE]
    value_template.hass = hass
    time_delta = config.get(CONF_FOR)
    to_value = config.get(CONF_TO)
    from_value = config.get(CONF_FROM)
    template.attach(hass, time_delta)
    delay_cancel = None
    job = HassJob(action)
    armed = False

    if to_value is None and from_value is None:
        result_matches = result_as_boolean
        result_arms = lambda result: not result_as_boolean(result)
    else:
        result_matches = _process_match(to_value)
        result_arms = _process_match(from_value)

    # Arm at setup if the template is already false.
    try:
        if result_arms(value_template.async_render(trigger_info["variables"])):
            armed = True
    except exceptions.TemplateError as ex:
        _LOGGER.warning(
            "Error initializing 'template' trigger for '%s': %s",
            trigger_info["name"],
            ex,
        )

    @callback
    def template_listener(
        event: EventType[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        """Listen for state changes and calls action."""
        nonlocal delay_cancel, armed, result_matches
        result = updates.pop().result

        if isinstance(result, exceptions.TemplateError):
            _LOGGER.warning(
                "Error evaluating 'template' trigger for '%s': %s",
                trigger_info["name"],
                result,
            )
            return

        if delay_cancel:
            delay_cancel()
            delay_cancel = None

        was_armed = armed
        armed = result_arms(result)

        # Only fire if result matches criteria.
        if not result_matches(result):
            return

        # Only fire when previously armed.
        if not was_armed:
            return

        # Fire!
        entity_id = event and event.data["entity_id"]
        from_s = event and event.data["old_state"]
        to_s = event and event.data["new_state"]

        if entity_id is not None:
            description = f"{entity_id} via template"
        else:
            description = "time change or manual update via template"

        template_variables = {
            "platform": platform_type,
            "entity_id": entity_id,
            "from_state": from_s,
            "to_state": to_s,
        }
        trigger_variables = {
            **trigger_data,
            "for": time_delta,
            "description": description,
            "value": result,
        }

        @callback
        def call_action(*_: Any) -> None:
            """Call action with right context."""
            nonlocal trigger_variables
            hass.async_run_hass_job(
                job,
                {"trigger": {**template_variables, **trigger_variables}},
                (to_s.context if to_s else None),
            )

        if not time_delta:
            call_action()
            return

        try:
            period: timedelta = cv.positive_time_period(
                template.render_complex(time_delta, {"trigger": template_variables})
            )
        except (exceptions.TemplateError, vol.Invalid) as ex:
            _LOGGER.error(
                "Error rendering '%s' for template: %s", trigger_info["name"], ex
            )
            return

        trigger_variables["for"] = period

        delay_cancel = async_call_later(hass, period.total_seconds(), call_action)

    info = async_track_template_result(
        hass,
        [TrackTemplate(value_template, trigger_info["variables"])],
        template_listener,
    )
    unsub = info.async_remove

    @callback
    def async_remove():
        """Remove state listeners async."""
        unsub()
        if delay_cancel:
            delay_cancel()

    return async_remove

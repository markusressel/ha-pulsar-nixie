# Pulsar nixie clock for Home Assistant

A custom integration for the Pulsar nixie clock. It controls the settings of the clock's configuration page through
the same local HTTP API, without the cloud.

## Entities

| Entity                                                                                                  | Setting of the configuration page        |
|---------------------------------------------------------------------------------------------------------|------------------------------------------|
| Select: time zone, hour format                                                                          | Time settings                            |
| Button: sync time                                                                                       | Time settings: "Sync time"               |
| Select: date, temperature, pressure, show every, nixie effect, digit effect, dot mode                   | Settings                                 |
| Switch: hour beep, humidity                                                                             | Settings                                 |
| Number: temperature correction                                                                          | Settings                                 |
| Time: night from, night to                                                                              | Settings                                 |
| Light: LED backlight (on/off, day brightness, color, effects: static color, color change, rainbow, fade) | Led settings                             |
| Number: LED night brightness                                                                            | Led settings                             |
| Switch: timer, timer alarm; Number: timer hours, minutes, seconds                                       | Timer                                    |
| Switch: cathode protection; Select: its digit, value and period                                         | Service                                  |

Not included on purpose: the Wi-Fi settings (saving them restarts the clock, and a wrong value takes it off the
network) and the firmware upload.

Notes:

- The clock doesn't report changes by itself, so it is polled every 30 seconds.
- Saving the time zone or hour format also sets the clock to Home Assistant's current time, like the configuration
  page does with the browser's time.
- The LED light turns on again with the effect it had before it was turned off. Choosing a color switches to
  "Static color" unless the effect shows the color ("Static color", "Fade").

Tested with firmware `6c3sq-1.2.0`.

## Installation

With [HACS](https://hacs.xyz/): add this repository as a custom repository (type "Integration"), install
"Pulsar nixie clock" and restart Home Assistant. Without HACS, copy `custom_components/pulsar_nixie` into the
`custom_components` directory of your Home Assistant configuration.

Then add the integration under Settings > Devices & services, with the IP address or hostname of the clock.

## Development

```shell
uv sync --all-groups
uv run pytest
```

# MV Telescope Pi HAT: pin map (v1, 2026-10-31)

KiCad 10 project started from KiCad's official `RaspberryPi-HAT` template: HAT board outline, M2.5 holes and the
2x20 through-hole socket are already placed in the PCB. Since 2026-11-06 it is a hierarchical project with one
sheet file per owner (see the repo README):

- `mv-telescope-hat.kicad_sch`: root sheet map. Three blocks, and the wires between them are the agreed connections.
- `pi_header.kicad_sch` (Eeshan): J1, the 40-pin header. Its 17 hierarchical labels are the pin map below.
- `hat_signals.kicad_sch` (Ibrahim): the 74ACT244, driver terminals, limit-switch and encoder connectors. It starts
  with the 17 Pi labels on the left and the driver terminals J301/J302 on the right.
- `power.kicad_sch` (owner open): battery to DM542Ts, excluded from the board. It starts with the six driver-cable
  labels.

Checked 2026-10-31: the netlist was compared pin by pin against the Raspberry Pi 4 reduced schematic (J8) and
the BCM2711 datasheet (Table 94), with 0 mismatches. The template's optional ID EEPROM was removed, so pins 27/28
are no-connects.

Checked 2026-11-06 after the split (KiCad 10.0.7): ERC 0 errors and 92 warnings, all placeholders that clear as the
other sheets get drawn: 69 "label connected to only one pin" and 23 "unconnected wire endpoint". The PCB's J1
pads keep their net names (/ALT_PUL and so on), because the root-page labels name each net. DRC schematic parity
reports only J301/J302 "missing footprint": they're new and get a footprint when Ibrahim picks the terminal.

## Driver signals (Pi → 74ACT244 → DM542T, common anode)

| Net | GPIO (BCM) | Header pin | 74ACT244 in / out | Goes to | Note |
|---|---|---|---|---|---|
| ALT_PUL | GPIO12 | 32 | 1A1 (2) / 1Y1 (18) | ALT driver PUL− | hardware PWM0 |
| ALT_DIR | GPIO16 | 36 | 1A2 (4) / 1Y2 (16) | ALT driver DIR− | |
| ALT_ENA | GPIO5 | 29 | 1A3 (6) / 1Y3 (14) | ALT driver ENA− | boot pull is high |
| AZ_PUL | GPIO13 | 33 | 2A1 (11) / 2Y1 (9) | AZ driver PUL− | hardware PWM1 |
| AZ_DIR | GPIO26 | 37 | 2A2 (13) / 2Y2 (7) | AZ driver DIR− | |
| AZ_ENA | GPIO6 | 31 | 2A3 (15) / 2Y3 (5) | AZ driver ENA− | boot pull is high |
| BUF_OE_N | GPIO4 | 7 | 1OE (1) + 2OE (19) | 10k pull-up to +3V3 | boot pull is high |

- 244 VCC (20) = +5V from header pins 2/4, 100 nF to GND (10). Unused inputs 1A4 (8) and 2A4 (17) go to GND.
  TI: "All unused inputs of the device must be held at VCC or GND".
- +5V (the same rail as the 244) → PUL+, DIR+ and ENA+ on both drivers. Each driver's 1x4 is 5V / PUL− / DIR− / ENA−.
- Set each DM542T's logic-voltage selector to 5V. The V4.0 ships set to 24V (Amazon B06Y5VPSFN listing).
- Opto current is 7–16 mA per input (DM542T manual), so all six draw at most ~96 mA from the Pi's 5V.
  That is within the 244's 24 mA per output.

## Limit switches (we have them; type and count TBD)

| Net | GPIO | Pin |
|---|---|---|
| ALT_LIM_LOW (horizon end) | GPIO17 | 11 |
| ALT_LIM_HIGH (zenith end) | GPIO27 | 13 |
| AZ_LIM_CW | GPIO22 | 15 |
| AZ_LIM_CCW | GPIO23 | 16 |

Wire the NC contact between the net and GND. Add a 10k pull-up to +3V3 and 100 nF to GND. The pin reads LOW
normally and HIGH when the switch is hit or the wire breaks; software stops that axis. Only 3.3V is safe here,
because the Pi's GPIO is not 5V tolerant (Raspberry Pi docs).

## Encoders (none bought yet; spots only)

| Net | GPIO | Pin |
|---|---|---|
| ALT_ENC_A | GPIO24 | 18 |
| ALT_ENC_B | GPIO25 | 22 |
| AZ_ENC_A | GPIO20 | 38 |
| AZ_ENC_B | GPIO21 | 40 |

5V encoders need level shifting down to 3.3V before they reach the Pi.

## Software logic (common anode inverts it: GPIO LOW = optocoupler ON)

- **PUL**: idles HIGH. A step happens when the pin goes HIGH → LOW, because the manual says the opto's rising
  edge is active. Hold low ≥ 2.5 µs and high ≥ 2.5 µs (200 kHz max).
- **DIR**: set it ≥ 5 µs before the step edge. Which level means clockwise gets decided at the bench test.
- **ENA**: **HIGH = driver ON with holding torque**, the same as leaving ENA unwired ("Usually left UNCONNECTED
  (ENABLED)"). **LOW = driver OFF**, and the motor turns by hand. So "low = on" applies to the opto, not to the motor.
  ENA must be set ≥ 5 µs before DIR.
- **BUF_OE_N**: HIGH is the boot default (pulled up), which turns the 244 outputs off. The drivers see nothing,
  so they stay ON and holding, with no steps. At start, software sets PUL HIGH and sets ENA and DIR, then drives
  BUF_OE_N LOW. If the software dies and the pin floats, the pull-up turns the outputs off again.
- The driver drops to 50% current 0.4 s after the last pulse (DM542T manual, idle-current reduction).
- To be confirmed on the bench: ENA polarity on the V4.0. The only manual found is V2.0 (oyostepper),
  and its ENA wording is ambiguous.

## Left free on purpose (X on J1)

- Pins 27/28 (GPIO0/1): ID EEPROM only. The HAT spec says "if unused these pins must be left unconnected".
- GPIO2/3 (pins 3/5): I2C1, which has fixed 1.8k pull-ups on the Pi. Keep for a future sensor.
- GPIO14/15 (pins 8/10): UART, for a serial console or GPS.
- GPIO7–11 (pins 19/21/23/24/26): SPI0, if we ever use SPI absolute encoders.
- Spare: GPIO18 (pin 12) and GPIO19 (pin 35). One possible use is the DM542T V4.0 alarm outputs; check
  their spec first.

## Why these pins

- PUL is on GPIO12/13 because those are the two channels of hardware PWM0 (BCM2711 Table 94, ALT0). Either
  pigpio-style timed pulses or the PWM hardware can drive them.
- BUF_OE_N, ALT_ENA and AZ_ENA are on GPIO4/5/6, which BCM2711 pulls high at power-on. If someone ties OE to
  GND instead, both drivers still boot the same way: enabled and holding.
- No driver or switch signal uses a pin with another job we might want: I2C, UART, SPI0 or ID EEPROM.

Sources: DM542T manual V2.0 (oyostepper.com), STEPPERONLINE DM542T Amazon listing B06Y5VPSFN (V4.0 notes),
TI SN74ACT244 datasheet, BCM2711 ARM Peripherals (Table 94), Raspberry Pi 4 reduced schematics (J8),
raspberrypi/hats designguide.md, Raspberry Pi docs gpio-on-raspberry-pi.adoc.

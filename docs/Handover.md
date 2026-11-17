Here's a message you can pass on:

---

**Handoff: TCD1304 sensor stream over Ethernet/MQTT (optical-diameter-rs)**

**Network**
- The device (NUCLEO-G474RE + WIZ550io) is on a direct Ethernet cable, static IP `192.168.50.2/24`, no gateway.
- The PC's Ethernet port must be `192.168.50.1/24`.
- **Broker:** Mosquitto on the PC, port 1883, anonymous access, MQTT v5. The device connects with client ID `optical-diameter` and a 30 s keep-alive.
- **Starting it:** `mosquitto -c tools/mosquitto.conf -v`. It listens on `192.168.50.1` and `127.0.0.1`.
- **Order:** start the broker only after the cable is plugged in and the device is powered. macOS removes the IP while the link is down.

**Topics (all QoS 0)**

| Topic | Direction | Content |
|---|---|---|
| `optical-diameter/frame` | device → PC | binary frame, every 100 ms (≈ 10/s) |
| `optical-diameter/stats` | device → PC | JSON counters, every 1 s |
| `optical-diameter/exposure/set` | PC → device | exposure in µs as decimal text, e.g. `250` |

**Frame payload** (7422 bytes, all little-endian)

| Offset | Bytes | Field |
|---|---|---|
| 0 | 4 | magic `b"TCD2"` |
| 4 | 6 × u32 | counters, in order: frames, unpublished, implausible, late, overruns, starts |
| 28 | u32 | exposure of this frame in µs |
| 32 | u16 | output count (always 3694) |
| 34 | 3694 × u16 | raw 12-bit ADC codes, output D0 first |

Python decode: `struct.Struct("<7IH")` after the magic, then `np.frombuffer(payload, "<u2", offset=34)`. Reject the frame if the length isn't 7422, the magic is wrong, or count ≠ 3694.

**Interpreting the 3694 values (Toshiba TCD1304DG linear CCD)**
- **Index 0–15:** dummy outputs.
- **Index 16–28:** light-shielded, i.e. the dark reference.
- **Index 29–31:** dummy outputs.
- **Index 32–3679:** the 3648 real pixels S1–S3648, 8 µm pitch, 29.184 mm line.
- **Index 3680–3693:** dummy outputs.
- **Polarity:** lower code = brighter. Dark is about 3690 (≈ 2.93 V), saturated about 1810. ADC reference 3.25 V, 12-bit.
- **Saturation:** if all outputs, including the dark range, sit at about 1810, the sensor is overexposed. Room light already saturates it at 100 µs. Lower the exposure (about 20 µs in bright light).

**Stats JSON:** `{"frames":…,"unpublished":…,"implausible":…,"late":…,"overruns":…,"starts":…}`
- `unpublished` rising fast is normal: the sensor captures about 135 frames/s, more than the stream sends.
- `starts` counts capture (re)starts.
- `implausible` counts frames that failed the dark-reference check.

**Exposure control**
- The valid range is 10 µs to 1,000,000 µs. The firmware rejects (and logs) out-of-range or non-numeric values, and the capture keeps running.
- A valid value restarts the capture with the shortest valid frame period.
- The frame header's exposure field shows the value actually in effect, so read it from there rather than assuming the command was applied.
- The device accepts incoming MQTT packets only up to 256 bytes.

**Existing viewer:** `tools/mqtt_viewer.py --broker 192.168.50.1` (paho-mqtt 2.x, matplotlib, numpy). It subscribes in `on_connect` so reconnects keep working, plots the newest frame, and has an exposure text box. The format is also documented in `src/mqtt.rs`, and the topics are in `src/config.rs`.

---
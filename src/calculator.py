import math
import struct

FRAME_MAGIC = b"TCD2"
OUTPUT_COUNT = 3694
PIXEL_START = 32
PIXEL_COUNT = 3648
ADC_MAX = 4095
HEADER = struct.Struct("<7IH")
OUTPUTS = struct.Struct(f"<{OUTPUT_COUNT}H")
FRAME_DATA_OFFSET = len(FRAME_MAGIC) + HEADER.size
FRAME_LENGTH = FRAME_DATA_OFFSET + OUTPUTS.size


def _median(values: list[int]) -> float:
    middle = len(values) // 2
    if len(values) % 2:
        return float(values[middle])
    return (values[middle - 1] + values[middle]) / 2


def _otsu_threshold(pixels: tuple[int, ...]) -> int:
    """
    Compute the Otsu threshold for a histogram of pixel values.
    This threshold separates the pixels into two classes (bright and shadow) by maximizing
    the between-class variance."""
    histogram = [0] * (ADC_MAX + 1)
    for code in pixels:
        histogram[code] += 1

    total = len(pixels)
    total_sum = sum(level * count for level, count in enumerate(histogram))
    background_count = 0
    background_sum = 0
    best_threshold: int | None = None
    best_variance = -1.0

    for threshold, count in enumerate(histogram):
        background_count += count
        background_sum += threshold * count
        foreground_count = total - background_count
        if background_count == 0 or foreground_count == 0:
            continue

        background_mean = background_sum / background_count
        foreground_mean = (total_sum - background_sum) / foreground_count
        variance = (
            background_count
            * foreground_count
            * (background_mean - foreground_mean) ** 2
        )
        if variance > best_variance:
            best_variance = variance
            best_threshold = threshold

    if best_threshold is None:
        raise ValueError("Frame has no separable bright and shadow pixel levels.")
    return best_threshold


def _edge_position(
    x0: int,
    code0: int,
    x1: int,
    code1: int,
    threshold: float,
) -> float:
    return x0 + (threshold - code0) / (code1 - code0) * (x1 - x0)


def calculate_diameter(raw_payload: bytes | bytearray, mm_per_pixel: float) -> float:
    """Decode one TCD2 frame and return its calibrated shadow width in mm."""
    if (
        isinstance(mm_per_pixel, bool)
        or not isinstance(mm_per_pixel, (int, float))
        or not math.isfinite(mm_per_pixel)
        or mm_per_pixel <= 0
    ):
        raise ValueError(
            "'measurement.mm_per_pixel' must be a finite value greater than zero."
        )

    if len(raw_payload) != FRAME_LENGTH:
        raise ValueError(f"TCD2 frame must be {FRAME_LENGTH} bytes.")
    if not raw_payload.startswith(FRAME_MAGIC):
        raise ValueError("TCD2 frame has an invalid magic header.")

    output_count = HEADER.unpack_from(raw_payload, len(FRAME_MAGIC))[-1]
    if output_count != OUTPUT_COUNT:
        raise ValueError(f"TCD2 frame must contain {OUTPUT_COUNT} outputs.")

    outputs = OUTPUTS.unpack_from(raw_payload, FRAME_DATA_OFFSET)
    if any(code > ADC_MAX for code in outputs):
        raise ValueError(f"TCD2 frame contains an ADC code greater than {ADC_MAX}.")

    pixels = outputs[PIXEL_START : PIXEL_START + PIXEL_COUNT]
    split = _otsu_threshold(pixels)
    bright_pixels = sorted(code for code in pixels if code <= split)
    shadow_pixels = sorted(code for code in pixels if code > split)
    if not bright_pixels or not shadow_pixels:
        raise ValueError("Frame has no separable bright and shadow pixel levels.")

    bright_level = _median(bright_pixels)
    shadow_level = _median(shadow_pixels)
    if shadow_level <= bright_level:
        raise ValueError("Frame does not contain a darker filament shadow.")
    threshold = (bright_level + shadow_level) / 2

    shadow_runs: list[tuple[int, int]] = []
    run_start: int | None = None

    # Find contiguous runs of pixels above the threshold (the shadow).
    for index, code in enumerate(pixels):
        if code >= threshold:
            if run_start is None:
                run_start = index
        elif run_start is not None:
            shadow_runs.append((run_start, index - 1))
            run_start = None
            
    # close the last run if it extends to the end of the pixel array
    if run_start is not None:
        shadow_runs.append((run_start, len(pixels) - 1))

    if len(shadow_runs) != 1:
        raise ValueError("Frame must contain exactly one contiguous filament shadow.")

    start, end = shadow_runs[0]
    if start == 0 or end == len(pixels) - 1:
        raise ValueError("Filament shadow is clipped by the sensor edge.")

    left_edge = _edge_position(
        start - 1,
        pixels[start - 1],
        start,
        pixels[start],
        threshold,
    )
    right_edge = _edge_position(
        end,
        pixels[end],
        end + 1,
        pixels[end + 1],
        threshold,
    )
    width_pixels = right_edge - left_edge
    if not math.isfinite(width_pixels) or width_pixels <= 0:
        raise ValueError("Frame produced an invalid shadow width.")

    return width_pixels * mm_per_pixel

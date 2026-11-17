import struct
import unittest

from calculator import (
    FRAME_LENGTH,
    FRAME_MAGIC,
    HEADER,
    OUTPUT_COUNT,
    OUTPUTS,
    PIXEL_COUNT,
    PIXEL_START,
    calculate_diameter,
)


def make_frame(
    shadow_runs: tuple[tuple[int, int], ...] = ((100, 199),),
    *,
    background: int = 1800,
    shadow: int = 3600,
) -> bytes:
    outputs = [background] * OUTPUT_COUNT
    outputs[16:29] = [3690] * 13
    pixels = [background] * PIXEL_COUNT
    for start, end in shadow_runs:
        pixels[start : end + 1] = [shadow] * (end - start + 1)
    outputs[PIXEL_START : PIXEL_START + PIXEL_COUNT] = pixels
    header = HEADER.pack(1, 0, 0, 0, 0, 1, 100, OUTPUT_COUNT)
    return FRAME_MAGIC + header + OUTPUTS.pack(*outputs)


class CalculateDiameterTests(unittest.TestCase):
    def test_decodes_frame_and_returns_calibrated_diameter_in_mm(self):
        frame = make_frame()

        self.assertEqual(len(frame), FRAME_LENGTH)
        self.assertAlmostEqual(calculate_diameter(frame, 0.01), 1.0)

    def test_interpolates_edges_between_pixels(self):
        pixels = [1800] * PIXEL_COUNT
        pixels[100] = 2600
        pixels[101:200] = [3600] * 99
        pixels[200] = 2600
        outputs = [1800] * OUTPUT_COUNT
        outputs[16:29] = [3690] * 13
        outputs[PIXEL_START : PIXEL_START + PIXEL_COUNT] = pixels
        header = HEADER.pack(1, 0, 0, 0, 0, 1, 100, OUTPUT_COUNT)
        frame = FRAME_MAGIC + header + OUTPUTS.pack(*outputs)

        self.assertAlmostEqual(calculate_diameter(frame, 0.01), 0.998)

    def test_rejects_wrong_frame_length(self):
        with self.assertRaisesRegex(ValueError, "must be 7422 bytes"):
            calculate_diameter(b"short", 0.01)

    def test_rejects_wrong_magic(self):
        frame = b"BAD!" + make_frame()[len(FRAME_MAGIC) :]

        with self.assertRaisesRegex(ValueError, "invalid magic"):
            calculate_diameter(frame, 0.01)

    def test_rejects_incorrect_output_count(self):
        frame = bytearray(make_frame())
        struct.pack_into(
            "<H", frame, len(FRAME_MAGIC) + HEADER.size - 2, OUTPUT_COUNT - 1
        )

        with self.assertRaisesRegex(ValueError, "must contain 3694 outputs"):
            calculate_diameter(bytes(frame), 0.01)

    def test_rejects_adc_codes_outside_12_bit_range(self):
        outputs = list(
            OUTPUTS.unpack_from(make_frame(), len(FRAME_MAGIC) + HEADER.size)
        )
        outputs[PIXEL_START] = 4096
        header = HEADER.pack(1, 0, 0, 0, 0, 1, 100, OUTPUT_COUNT)
        frame = FRAME_MAGIC + header + OUTPUTS.pack(*outputs)

        with self.assertRaisesRegex(ValueError, "greater than 4095"):
            calculate_diameter(frame, 0.01)

    def test_rejects_frame_without_shadow_contrast(self):
        frame = make_frame(shadow_runs=(), background=1800, shadow=1800)

        with self.assertRaisesRegex(ValueError, "separable bright and shadow"):
            calculate_diameter(frame, 0.01)

    def test_rejects_multiple_shadow_regions(self):
        frame = make_frame(shadow_runs=((100, 199), (500, 599)))

        with self.assertRaisesRegex(ValueError, "exactly one contiguous"):
            calculate_diameter(frame, 0.01)

    def test_rejects_shadow_clipped_at_sensor_edge(self):
        frame = make_frame(shadow_runs=((0, 99),))

        with self.assertRaisesRegex(ValueError, "clipped"):
            calculate_diameter(frame, 0.01)

    def test_requires_positive_calibration(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            calculate_diameter(make_frame(), 0)


if __name__ == "__main__":
    unittest.main()

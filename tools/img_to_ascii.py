#!/usr/bin/env python3
"""
Convert an image to ASCII art.

Usage:
    python img_to_ascii.py <image_path> <output_path> [--width W] [--height H] [--invert]

The output is a text file with ASCII characters representing the image.
"""

import sys
import argparse
from PIL import Image


# Extended ASCII character ramp for more detail (70 levels)
ASCII_RAMP_DARK = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
ASCII_RAMP_LIGHT = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


def image_to_ascii(image_path, width=45, height=30, invert=False):
    """
    Convert an image file to ASCII art.

    Parameters
    ----------
    image_path : str
        Path to the source image.
    width : int
        Width of the ASCII output in characters.
    height : int
        Height of the ASCII output in lines.
    invert : bool
        If True, use light-on-dark mapping (bright pixels = dense chars).

    Returns
    -------
    str
        The ASCII art as a string.
    """
    img = Image.open(image_path)

    # Convert to grayscale
    img = img.convert('L')

    # Resize to target dimensions
    img = img.resize((width, height), Image.LANCZOS)

    ramp = ASCII_RAMP_LIGHT if invert else ASCII_RAMP_DARK

    # Map each pixel to an ASCII character
    lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            pixel = img.getpixel((x, y))
            # Map 0-255 to index in ramp
            idx = int(pixel / 256 * len(ramp))
            idx = min(idx, len(ramp) - 1)
            line += ramp[idx]
        lines.append(line)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Convert image to ASCII art")
    parser.add_argument("image", help="Path to input image")
    parser.add_argument("output", help="Path to output text file")
    parser.add_argument("--width", type=int, default=45, help="Width in characters")
    parser.add_argument("--height", type=int, default=30, help="Height in lines")
    parser.add_argument("--invert", action="store_true",
                        help="Invert brightness (bright pixels = dense characters)")

    args = parser.parse_args()

    ascii_art = image_to_ascii(args.image, args.width, args.height, args.invert)

    with open(args.output, 'w') as f:
        f.write(ascii_art)
        f.write("\n")

    print(f"Converted {args.image} → {args.output}")
    print(f"Dimensions: {args.width}×{args.height}")


if __name__ == "__main__":
    main()

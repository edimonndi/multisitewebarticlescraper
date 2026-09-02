import math
from PIL import Image, ImageDraw

def create_app_icon(output_ico="app_icon.ico", output_png="app_icon.png"):
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Background Rounded Rectangle with Gradient simulation
    # Deep slate-indigo gradient
    radius = 110
    for r in range(size // 2, 0, -2):
        # Draw radial glow in center
        pass

    # Base background card
    card_bounds = [24, 24, size - 24, size - 24]
    draw.rounded_rectangle(card_bounds, radius=radius, fill=(15, 23, 42, 255))

    # Inner subtle border / glow
    inner_bounds = [28, 28, size - 28, size - 28]
    draw.rounded_rectangle(inner_bounds, radius=radius - 4, outline=(59, 130, 246, 120), width=4)

    # 2. Glowing circular gradient backdrop behind book
    center_x, center_y = size // 2, size // 2 + 10
    for rad in range(160, 40, -10):
        alpha = int(35 * (1 - rad / 160))
        draw.ellipse(
            [center_x - rad, center_y - rad, center_x + rad, center_y + rad],
            fill=(37, 99, 235, alpha)
        )

    # 3. Modern Book / Pages
    # Left Page
    left_pts = [
        (100, 160),
        (240, 185),
        (240, 390),
        (100, 360)
    ]
    # Draw left page shadow
    draw.polygon([(p[0], p[1] + 8) for p in left_pts], fill=(10, 15, 30, 200))
    draw.polygon(left_pts, fill=(241, 245, 249, 255))

    # Right Page
    right_pts = [
        (272, 185),
        (412, 160),
        (412, 360),
        (272, 390)
    ]
    # Draw right page shadow
    draw.polygon([(p[0], p[1] + 8) for p in right_pts], fill=(10, 15, 30, 200))
    draw.polygon(right_pts, fill=(248, 250, 252, 255))

    # Spine highlight
    draw.polygon([(240, 185), (272, 185), (272, 390), (240, 390)], fill=(203, 213, 225, 255))

    # Text lines on left page
    line_col = (148, 163, 184, 255)
    for y in [220, 250, 280, 310, 340]:
        y_offset = int((y - 220) * 0.08)
        draw.rounded_rectangle([130, y - y_offset, 215, y + 6 - y_offset], radius=3, fill=line_col)

    # Text lines on right page
    for y in [220, 250, 280, 310, 340]:
        y_offset = int((y - 220) * 0.08)
        draw.rounded_rectangle([295, y + y_offset, 380, y + 6 + y_offset], radius=3, fill=line_col)

    # 4. Energy Lightning / Scraper Symbol in Vibrant Gold & Cyan
    bolt_pts = [
        (280, 70),
        (205, 230),
        (255, 230),
        (230, 350),
        (315, 190),
        (265, 190)
    ]
    # Bolt shadow
    draw.polygon([(p[0] + 4, p[1] + 6) for p in bolt_pts], fill=(15, 23, 42, 180))
    # Bolt glow
    for off in [4, 2]:
        draw.polygon(bolt_pts, fill=(251, 191, 36, 255), outline=(245, 158, 11, 255), width=off)
    # Bolt center
    draw.polygon(bolt_pts, fill=(254, 240, 138, 255))

    # Save PNG
    img.save(output_png, format="PNG")

    # Save multi-resolution ICO
    img.save(
        output_ico,
        format="ICO",
        sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    )
    print(f"Icons created successfully: {output_ico}, {output_png}")

if __name__ == "__main__":
    create_app_icon()
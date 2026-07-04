#!/usr/bin/env python3
"""Generate Coach Travel Istria breakout Facebook ad video."""

from __future__ import annotations

import math
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"
FRAMES_DIR = OUTPUT / "frames"

# Facebook mobile feed 4:5
W, H = 1080, 1350
FPS = 30
DURATION = 8.0
N_FRAMES = int(FPS * DURATION)

# Exact Facebook feed white
FB_WHITE = (255, 255, 255)
BRAND_GOLD = (200, 164, 90)
BRAND_GOLD_DARK = (168, 132, 62)
BRAND_NAVY = (26, 40, 68)
SKY_TOP = (72, 148, 210)
SKY_BOTTOM = (145, 198, 235)
SEA = (28, 118, 168)

SCENE_BOTTOM = 760
UI_STATS_Y = 842
UI_BUTTONS_Y = 918
UI_AD_TEXT_Y = 1048


@dataclass
class Assets:
    coach: Image.Image
    logo: Image.Image
    rovinj: Image.Image
    limfjord: Image.Image
    pineta: Image.Image


def load_assets() -> Assets:
    coach = Image.open(ASSETS / "coach-cutout.png").convert("RGBA")
    logo = Image.open(ASSETS / "logo.webp").convert("RGBA")
    rovinj = Image.open(ASSETS / "rovinj.jpg").convert("RGB")
    limfjord = Image.open(ASSETS / "limfjord.jpg").convert("RGB")
    pineta = Image.open(ASSETS / "pineta.jpg").convert("RGB")
    return Assets(coach=coach, logo=logo, rovinj=rovinj, limfjord=limfjord, pineta=pineta)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size)


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def ease_in_out_sine(t: float) -> float:
    return -(math.cos(math.pi * t) - 1) / 2


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def fit_cover(img: Image.Image, tw: int, th: int) -> Image.Image:
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return resized.crop((left, top, left + tw, top + th))


def fit_contain_rgba(img: Image.Image, tw: int, th: int) -> Image.Image:
    sw, sh = img.size
    scale = min(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    canvas.paste(resized, ((tw - nw) // 2, (th - nh) // 2), resized)
    return canvas


def build_istria_background(assets: Assets, zoom: float, pan_x: float) -> Image.Image:
    """Composite layered Istria scenery with cinematic color grade."""
    canvas = Image.new("RGB", (W, SCENE_BOTTOM))

    # Sky gradient fill for upper portion
    sky = Image.new("RGB", (W, SCENE_BOTTOM))
    draw = ImageDraw.Draw(sky)
    for y in range(SCENE_BOTTOM):
        t = y / SCENE_BOTTOM
        r = int(SKY_TOP[0] * (1 - t) + SKY_BOTTOM[0] * t)
        g = int(SKY_TOP[1] * (1 - t) + SKY_BOTTOM[1] * t)
        b = int(SKY_TOP[2] * (1 - t) + SKY_BOTTOM[2] * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    canvas = sky

    # Sea band
    sea_h = int(SCENE_BOTTOM * 0.42)
    sea_img = Image.new("RGB", (W, sea_h), SEA)
    sea_draw = ImageDraw.Draw(sea_img)
    for y in range(sea_h):
        t = y / sea_h
        c = (
            int(SEA[0] * (1 - t) + 18 * t),
            int(SEA[1] * (1 - t) + 92 * t),
            int(SEA[2] * (1 - t) + 132 * t),
        )
        sea_draw.line([(0, y), (W, y)], fill=c)
    canvas.paste(sea_img, (0, SCENE_BOTTOM - sea_h))

    # Rovinj hero – iconic harbor
    rov = fit_cover(assets.rovinj, int(W * 1.25 * zoom), int(SCENE_BOTTOM * 0.72 * zoom))
    rx = int((W - rov.width) // 2 + pan_x)
    ry = int(SCENE_BOTTOM * 0.08)
    temp = Image.new("RGBA", (W, SCENE_BOTTOM), (0, 0, 0, 0))
    temp.paste(rov, (rx, ry))
    temp = temp.filter(ImageFilter.GaussianBlur(radius=0.4))
    canvas.paste(temp.convert("RGB"), (0, 0), None)

    # Lim fjord accent left
    lim = fit_cover(assets.limfjord, int(W * 0.55 * zoom), int(SCENE_BOTTOM * 0.45 * zoom))
    lim = lim.filter(ImageFilter.GaussianBlur(radius=1.2))
    lim_layer = Image.new("RGBA", (W, SCENE_BOTTOM), (0, 0, 0, 0))
    lim_layer.paste(lim, (int(-W * 0.08 + pan_x * 0.4), int(SCENE_BOTTOM * 0.38)))
    lim_arr = np.array(lim_layer).astype(float)
    lim_arr[:, :, 3] *= 0.42
    lim_layer = Image.fromarray(lim_arr.astype(np.uint8), "RGBA")
    canvas = Image.alpha_composite(canvas.convert("RGBA"), lim_layer).convert("RGB")

    # Pineta coastal hint right
    pin = fit_cover(assets.pineta, int(W * 0.48 * zoom), int(SCENE_BOTTOM * 0.38 * zoom))
    pin = pin.filter(ImageFilter.GaussianBlur(radius=1.5))
    pin_layer = Image.new("RGBA", (W, SCENE_BOTTOM), (0, 0, 0, 0))
    pin_layer.paste(pin, (int(W * 0.58 + pan_x * 0.25), int(SCENE_BOTTOM * 0.48)))
    pin_arr = np.array(pin_layer).astype(float)
    pin_arr[:, :, 3] *= 0.35
    pin_layer = Image.fromarray(pin_arr.astype(np.uint8), "RGBA")
    canvas = Image.alpha_composite(canvas.convert("RGBA"), pin_layer).convert("RGB")

    # Warm Mediterranean grade
    arr = np.array(canvas).astype(float)
    arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.08 + 12, 0, 255)
    arr[:, :, 1] = np.clip(arr[:, :, 1] * 1.05 + 8, 0, 255)
    arr[:, :, 2] = np.clip(arr[:, :, 2] * 0.94 + 6, 0, 255)
    canvas = Image.fromarray(arr.astype(np.uint8), "RGB")

    # Bottom fade to white for breakout blend
    fade = Image.new("L", (W, SCENE_BOTTOM), 255)
    fade_draw = ImageDraw.Draw(fade)
    fade_start = int(SCENE_BOTTOM * 0.58)
    for y in range(fade_start, SCENE_BOTTOM):
        t = (y - fade_start) / (SCENE_BOTTOM - fade_start)
        alpha = int(255 * ease_in_out_sine(t))
        fade_draw.line([(0, y), (W, y)], fill=alpha)
    white = Image.new("RGB", (W, SCENE_BOTTOM), FB_WHITE)
    canvas = Image.composite(white, canvas, fade)

    # Subtle vignette
    vignette = Image.new("L", (W, SCENE_BOTTOM), 0)
    vd = ImageDraw.Draw(vignette)
    vd.ellipse([-W * 0.15, -SCENE_BOTTOM * 0.1, W * 1.15, SCENE_BOTTOM * 1.15], fill=180)
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=90))
    dark = Image.new("RGB", (W, SCENE_BOTTOM), (0, 0, 0))
    canvas = Image.composite(dark, canvas, vignette)

    return canvas


def draw_scene_text(base: Image.Image, t: float) -> Image.Image:
    img = base.copy()
    overlay = Image.new("RGBA", (W, SCENE_BOTTOM), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    alpha = int(255 * ease_out_cubic(min(max((t - 1.4) / 0.8, 0), 1)))
    if alpha <= 0:
        return img

    # Destination badge
    badge_w, badge_h = 420, 54
    bx, by = 48, 52
    draw.rounded_rectangle([bx, by, bx + badge_w, by + badge_h], radius=27, fill=(255, 255, 255, int(alpha * 0.92)))
    draw.text((bx + 22, by + 12), "🇭🇷  SMAAK VAN ISTRIË", fill=(*BRAND_NAVY, alpha), font=font(24, bold=True))

    # Main headline
    title_alpha = int(255 * ease_out_cubic(min(max((t - 1.8) / 0.9, 0), 1)))
    draw.text((48, 130), "10 dagen", fill=(255, 255, 255, title_alpha), font=font(74, bold=True))
    draw.text((48, 210), "Adriatische", fill=(255, 255, 255, title_alpha), font=font(74, bold=True))
    draw.text((48, 290), "Culinaire reis", fill=(*BRAND_GOLD, title_alpha), font=font(74, bold=True))

    # Price pill
    pill_alpha = int(255 * ease_out_cubic(min(max((t - 2.3) / 0.7, 0), 1)))
    px, py = 48, 392
    draw.rounded_rectangle([px, py, px + 360, py + 62], radius=31, fill=(*BRAND_GOLD, pill_alpha))
    draw.text((px + 24, py + 14), "Vanaf € 1.095 p.p.", fill=(255, 255, 255, pill_alpha), font=font(30, bold=True))

    # Route line
    route_alpha = int(220 * ease_out_cubic(min(max((t - 2.6) / 0.8, 0), 1)))
    draw.text((48, 478), "Rovinj · Limski Kanaal · Truffeljacht · Piran", fill=(255, 255, 255, route_alpha), font=font(22))

    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")


def draw_coach_shadow(base: Image.Image, coach_box: tuple[int, int, int, int], strength: float) -> Image.Image:
    x, y, cw, ch = coach_box
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sx, sy = x + int(cw * 0.08), y + ch - int(ch * 0.06)
    sw, sh = int(cw * 0.84), int(ch * 0.08)
    sd.ellipse([sx, sy, sx + sw, sy + sh], fill=(0, 0, 0, int(90 * strength)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=18))
    return Image.alpha_composite(base.convert("RGBA"), shadow).convert("RGB")


def paste_coach(base: Image.Image, coach: Image.Image, x: int, y: int) -> Image.Image:
    layer = base.convert("RGBA")
    layer.paste(coach, (x, y), coach)
    return layer.convert("RGB")


def draw_fake_facebook_ui(t: float) -> Image.Image:
    """Draw fake FB stats + action bar on white background."""
    ui = Image.new("RGBA", (W, H - SCENE_BOTTOM), FB_WHITE + (255,))
    draw = ImageDraw.Draw(ui)

    # Divider line
    draw.line([(0, 0), (W, 0)], fill=(220, 223, 226, 255), width=2)

    # Animated reaction count
    progress = ease_out_cubic(min(max((t - 2.8) / 1.2, 0), 1))
    reactions = int(lerp(0, 2847, progress))
    views = int(lerp(0, 12453, progress))
    stats_text = f"{reactions:,} reacties · {views:,} weergaves".replace(",", ".")
    draw.text((36, UI_STATS_Y - SCENE_BOTTOM + 8), stats_text, fill=(101, 103, 107, 255), font=font(26))

    # Reaction emoji bubbles
    bubble_x = W - 210
    bubble_y = UI_STATS_Y - SCENE_BOTTOM
    for i, color in enumerate([(24, 119, 242), (219, 68, 55), (247, 177, 37)]):
        draw.ellipse([bubble_x + i * 34, bubble_y, bubble_x + i * 34 + 30, bubble_y + 30], fill=color + (255,))

    draw.line([(0, UI_BUTTONS_Y - SCENE_BOTTOM - 12), (W, UI_BUTTONS_Y - SCENE_BOTTOM - 12)], fill=(220, 223, 226, 255), width=2)

    # Like / Comment / Send buttons
    labels = [("👍  Like", 120), ("💬  Comment", W // 2), ("➤  Send", W - 120)]
    for label, cx in labels:
        tw = draw.textlength(label, font=font(28, bold=True))
        draw.text((cx - tw / 2, UI_BUTTONS_Y - SCENE_BOTTOM), label, fill=(101, 103, 107, 255), font=font(28, bold=True))

    # Ad copy block
    ad_alpha = int(255 * ease_out_cubic(min(max((t - 3.2) / 0.9, 0), 1)))
    ay = UI_AD_TEXT_Y - SCENE_BOTTOM
    draw.text((36, ay), "Ontdek Istrië met Coach Travel", fill=(*BRAND_NAVY, ad_alpha), font=font(34, bold=True))
    draw.text((36, ay + 48), "Comfort Class touringcar · Halfpension · 7 nachten Vrsar", fill=(101, 103, 107, ad_alpha), font=font(24))
    draw.text((36, ay + 88), "coachtravel.nl  ·  Instappen = genieten", fill=(*BRAND_GOLD_DARK, ad_alpha), font=font(26, bold=True))

    # CTA button
    cta_alpha = ad_alpha
    cx, cy = W - 290, ay + 36
    draw.rounded_rectangle([cx, cy, cx + 250, cy + 64], radius=8, fill=(235, 238, 242, cta_alpha))
    tw = draw.textlength("Meer informatie", font=font(26, bold=True))
    draw.text((cx + (250 - tw) / 2, cy + 16), "Meer informatie", fill=(28, 30, 33, cta_alpha), font=font(26, bold=True))

    return ui


def draw_post_header() -> Image.Image:
    header = Image.new("RGBA", (W, 88), FB_WHITE + (255,))
    draw = ImageDraw.Draw(header)

    # Page avatar circle with brand gold
    draw.ellipse([28, 16, 84, 72], fill=BRAND_GOLD + (255,))
    draw.ellipse([38, 26, 74, 62], fill=FB_WHITE + (255,))
    draw.text((46, 34), "CT", fill=BRAND_GOLD_DARK + (255,), font=font(18, bold=True))

    draw.text((98, 22), "Coach Travel", fill=(28, 30, 33, 255), font=font(30, bold=True))
    draw.text((98, 54), "Gesponsord · 🌍", fill=(101, 103, 107, 255), font=font(22))

    draw.text((36, 118), "Stap in en proef Istrië — 10 dagen culinaire busreis", fill=(28, 30, 33, 255), font=font(26))
    return header


def render_frame(assets: Assets, frame_idx: int) -> Image.Image:
    t = frame_idx / FPS

    zoom = lerp(1.0, 1.08, ease_in_out_sine(min(t / DURATION, 1)))
    pan_x = lerp(0, -35, ease_in_out_sine(min(t / DURATION, 1)))

    canvas = Image.new("RGB", (W, H), FB_WHITE)
    scene = build_istria_background(assets, zoom, pan_x)
    canvas.paste(scene, (0, 0))

    # Coach animation: drive in + subtle idle float
    coach_target_w = int(W * 1.02)
    coach_scale = coach_target_w / assets.coach.width
    coach_h = int(assets.coach.height * coach_scale)
    coach = assets.coach.resize((coach_target_w, coach_h), Image.Resampling.LANCZOS)

    drive_progress = ease_out_cubic(min(max(t / 1.6, 0), 1))
    coach_x = int(lerp(-coach_target_w * 0.55, -int(W * 0.06), drive_progress))
    coach_y = int(SCENE_BOTTOM - coach_h * 0.58 + math.sin(t * 2.2) * 2.5)

    scene_with_text = draw_scene_text(scene, t)
    canvas.paste(scene_with_text, (0, 0))

    shadow_strength = ease_out_cubic(min(max(t / 1.2, 0), 1))
    frame = draw_coach_shadow(canvas, (coach_x, coach_y, coach_target_w, coach_h), shadow_strength)
    frame = paste_coach(frame, coach, coach_x, coach_y)

    # Fake FB UI below scene
    ui = draw_fake_facebook_ui(t)
    ui_full = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ui_full.paste(ui, (0, SCENE_BOTTOM))
    frame = Image.alpha_composite(frame.convert("RGBA"), ui_full).convert("RGB")

    # Re-paste coach front over UI buttons for breakout illusion
    breakout_mask = coach.crop((0, int(coach_h * 0.44), coach_target_w, coach_h))
    frame = paste_coach(
        frame,
        breakout_mask,
        coach_x,
        coach_y + int(coach_h * 0.44),
    )

    # Logo watermark top-right
    logo = fit_contain_rgba(assets.logo, 200, 90)
    logo_arr = np.array(logo).astype(float)
    logo_arr[:, :, 3] *= 0.95
    logo = Image.fromarray(logo_arr.astype(np.uint8), "RGBA")
    frame = Image.alpha_composite(frame.convert("RGBA"), Image.new("RGBA", (W, H), (0, 0, 0, 0)))
    frame.paste(logo, (W - 230, 24), logo)

    return frame.convert("RGB")


def encode_video() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT / "coach-travel-istrie-breakout.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(FRAMES_DIR / "frame_%05d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-movflags",
        "+faststart",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)
    print(f"Saved {out_path}")


def main() -> None:
    assets = load_assets()
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    for i in range(N_FRAMES):
        frame = render_frame(assets, i)
        frame.save(FRAMES_DIR / f"frame_{i:05d}.png", optimize=True)
        if i % 30 == 0:
            print(f"Rendered frame {i + 1}/{N_FRAMES}")

    encode_video()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate the final AWS architecture schematic for the dashboard project."""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "diagrams" / "final_aws_architecture.png"
OUT_HIGHRES = ROOT / "artifacts" / "diagrams" / "final_aws_architecture_highres.png"

WIDTH = 1800
HEIGHT = 1280
SCALE = 2

BG = "#f7f9fb"
INK = "#17212b"
MUTED = "#586474"
BORDER = "#cfd8e3"
LANE_BORDER = "#d8e2ee"

BLUE = "#1f6feb"
BLUE_LIGHT = "#e8f1ff"
GREEN = "#2f855a"
GREEN_LIGHT = "#e8f6ef"
AMBER = "#b7791f"
AMBER_LIGHT = "#fff7df"
PURPLE = "#6b46c1"
PURPLE_LIGHT = "#f0eaff"
GRAY_LIGHT = "#ffffff"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size * SCALE)
    return ImageFont.load_default()


TITLE = font(34, True)
SUBTITLE = font(18)
LANE_TITLE = font(22, True)
BOX_TITLE = font(18, True)
BOX_TEXT = font(15)
SMALL = font(13)
ICON_LABEL = font(11, True)


def s(value: int) -> int:
    return value * SCALE


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    max_width: int,
    fnt: ImageFont.FreeTypeFont,
    fill: str = INK,
    line_gap: int = 5,
) -> int:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        attempt = f"{current} {word}".strip()
        if draw.textbbox((0, 0), attempt, font=fnt)[2] <= s(max_width):
            current = attempt
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    x, y = xy
    for line in lines:
        draw.text((s(x), s(y)), line, font=fnt, fill=fill)
        line_height = draw.textbbox((0, 0), line, font=fnt)[3]
        y += int(line_height / SCALE) + line_gap
    return y


def draw_icon(
    draw: ImageDraw.ImageDraw,
    icon: str,
    x: int,
    y: int,
    color: str,
) -> None:
    """Draw small line icons without external icon dependencies."""
    stroke = s(3)
    if icon == "browser":
        draw.rounded_rectangle((s(x), s(y), s(x + 34), s(y + 28)), radius=s(5), outline=color, width=stroke)
        draw.line((s(x), s(y + 8), s(x + 34), s(y + 8)), fill=color, width=s(2))
        for i in range(3):
            draw.ellipse((s(x + 5 + i * 7), s(y + 3), s(x + 8 + i * 7), s(y + 6)), fill=color)
    elif icon == "server":
        for offset in (0, 14):
            draw.rounded_rectangle((s(x), s(y + offset), s(x + 36), s(y + offset + 11)), radius=s(3), outline=color, width=stroke)
            draw.ellipse((s(x + 6), s(y + offset + 4), s(x + 9), s(y + offset + 7)), fill=color)
            draw.line((s(x + 24), s(y + offset + 6), s(x + 31), s(y + offset + 6)), fill=color, width=s(2))
    elif icon == "proxy":
        draw.arc((s(x), s(y + 4), s(x + 22), s(y + 26)), 90, 270, fill=color, width=stroke)
        draw.arc((s(x + 14), s(y + 4), s(x + 36), s(y + 26)), -90, 90, fill=color, width=stroke)
        arrow(draw, (x + 7, y + 15), (x + 29, y + 15), color)
    elif icon == "api":
        draw.text((s(x), s(y - 4)), "{", font=BOX_TITLE, fill=color)
        draw.text((s(x + 24), s(y - 4)), "}", font=BOX_TITLE, fill=color)
        draw.line((s(x + 15), s(y + 8), s(x + 22), s(y + 21)), fill=color, width=stroke)
    elif icon == "files":
        draw.rectangle((s(x + 7), s(y + 2), s(x + 30), s(y + 30)), outline=color, width=stroke)
        draw.line((s(x + 13), s(y + 11), s(x + 25), s(y + 11)), fill=color, width=s(2))
        draw.line((s(x + 13), s(y + 18), s(x + 25), s(y + 18)), fill=color, width=s(2))
        draw.line((s(x + 13), s(y + 25), s(x + 22), s(y + 25)), fill=color, width=s(2))
    elif icon == "git":
        pts = [(x + 5, y + 15), (x + 18, y + 5), (x + 31, y + 15), (x + 18, y + 28)]
        draw.line([(s(px), s(py)) for px, py in pts + [pts[0]]], fill=color, width=stroke)
        draw.line((s(x + 18), s(y + 9), s(x + 18), s(y + 22)), fill=color, width=s(2))
        draw.ellipse((s(x + 14), s(y + 7), s(x + 22), s(y + 15)), outline=color, width=s(2))
        draw.ellipse((s(x + 14), s(y + 19), s(x + 22), s(y + 27)), outline=color, width=s(2))
    elif icon == "workflow":
        for dx, dy in ((0, 0), (24, 0), (12, 22)):
            draw.rounded_rectangle((s(x + dx), s(y + dy), s(x + dx + 13), s(y + dy + 13)), radius=s(3), outline=color, width=s(2))
        draw.line((s(x + 13), s(y + 7), s(x + 24), s(y + 7)), fill=color, width=s(2))
        draw.line((s(x + 7), s(y + 13), s(x + 15), s(y + 22)), fill=color, width=s(2))
        draw.line((s(x + 31), s(y + 13), s(x + 23), s(y + 22)), fill=color, width=s(2))
    elif icon == "lock":
        draw.rounded_rectangle((s(x + 5), s(y + 14), s(x + 31), s(y + 31)), radius=s(4), outline=color, width=stroke)
        draw.arc((s(x + 10), s(y + 1), s(x + 26), s(y + 22)), 180, 360, fill=color, width=stroke)
        draw.line((s(x + 10), s(y + 12), s(x + 10), s(y + 16)), fill=color, width=stroke)
        draw.line((s(x + 26), s(y + 12), s(x + 26), s(y + 16)), fill=color, width=stroke)
    elif icon == "terminal":
        draw.rounded_rectangle((s(x), s(y + 3), s(x + 36), s(y + 30)), radius=s(5), outline=color, width=stroke)
        draw.line((s(x + 7), s(y + 12), s(x + 13), s(y + 17)), fill=color, width=s(2))
        draw.line((s(x + 13), s(y + 17), s(x + 7), s(y + 22)), fill=color, width=s(2))
        draw.line((s(x + 18), s(y + 22), s(x + 29), s(y + 22)), fill=color, width=s(2))
    elif icon == "service":
        draw.ellipse((s(x + 5), s(y + 5), s(x + 31), s(y + 31)), outline=color, width=stroke)
        for angle_x, angle_y in ((18, 0), (18, 36), (0, 18), (36, 18)):
            draw.line((s(x + 18), s(y + 18), s(x + angle_x), s(y + angle_y)), fill=color, width=s(2))
    elif icon == "health":
        draw.line((s(x + 4), s(y + 18), s(x + 13), s(y + 18)), fill=color, width=stroke)
        draw.line((s(x + 13), s(y + 18), s(x + 17), s(y + 8)), fill=color, width=stroke)
        draw.line((s(x + 17), s(y + 8), s(x + 23), s(y + 28)), fill=color, width=stroke)
        draw.line((s(x + 23), s(y + 28), s(x + 27), s(y + 18)), fill=color, width=stroke)
        draw.line((s(x + 27), s(y + 18), s(x + 36), s(y + 18)), fill=color, width=stroke)
    elif icon == "cloudwatch":
        draw.arc((s(x + 2), s(y + 12), s(x + 20), s(y + 30)), 170, 350, fill=color, width=stroke)
        draw.arc((s(x + 12), s(y + 5), s(x + 30), s(y + 25)), 180, 360, fill=color, width=stroke)
        draw.arc((s(x + 20), s(y + 10), s(x + 38), s(y + 30)), 190, 350, fill=color, width=stroke)
        draw.line((s(x + 8), s(y + 30), s(x + 32), s(y + 30)), fill=color, width=stroke)
    elif icon == "alert":
        draw.polygon([(s(x + 18), s(y + 3)), (s(x + 34), s(y + 31)), (s(x + 2), s(y + 31))], outline=color)
        draw.line((s(x + 18), s(y + 11), s(x + 18), s(y + 22)), fill=color, width=stroke)
        draw.ellipse((s(x + 16), s(y + 26), s(x + 20), s(y + 30)), fill=color)
    elif icon == "boundary":
        draw.rounded_rectangle((s(x + 3), s(y + 5), s(x + 33), s(y + 29)), radius=s(8), outline=color, width=stroke)
        draw.line((s(x + 9), s(y + 17), s(x + 27), s(y + 17)), fill=color, width=s(2))
        draw.line((s(x + 18), s(y + 9), s(x + 18), s(y + 25)), fill=color, width=s(2))


def icon_badge(
    draw: ImageDraw.ImageDraw,
    icon: str,
    x: int,
    y: int,
    color: str,
    fill: str,
) -> None:
    draw.rounded_rectangle(
        (s(x), s(y), s(x + 58), s(y + 58)),
        radius=s(14),
        fill=fill,
        outline=color,
        width=s(2),
    )
    draw_icon(draw, icon, x + 11, y + 12, color)


def box(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    body: str,
    fill: str,
    accent: str,
    icon: str | None = None,
) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(
        (s(x1), s(y1), s(x2), s(y2)),
        radius=s(18),
        fill=fill,
        outline=accent,
        width=s(2),
    )
    draw.rounded_rectangle(
        (s(x1), s(y1), s(x2), s(y1 + 10)),
        radius=s(18),
        fill=accent,
    )
    if icon:
        icon_badge(draw, icon, x1 + 18, y1 + 28, accent, "#ffffff")
        text_x = x1 + 92
        text_width = x2 - x1 - 112
    else:
        text_x = x1 + 22
        text_width = x2 - x1 - 44
    body_y = draw_wrapped(draw, title, (text_x, y1 + 25), text_width, BOX_TITLE, INK, line_gap=2)
    draw_wrapped(draw, body, (text_x, body_y + 8), text_width, BOX_TEXT, MUTED)


def lane(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    title: str,
    subtitle: str,
    fill: str,
) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(
        (s(x1), s(y1), s(x2), s(y2)),
        radius=s(26),
        fill=fill,
        outline=LANE_BORDER,
        width=s(2),
    )
    draw.text((s(x1 + 28), s(y1 + 20)), title, font=LANE_TITLE, fill=INK)
    draw.text((s(x1 + 28), s(y1 + 50)), subtitle, font=SMALL, fill=MUTED)


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str = "#64748b",
) -> None:
    x1, y1 = start
    x2, y2 = end
    draw.line((s(x1), s(y1), s(x2), s(y2)), fill=color, width=s(4))
    size = 13
    if abs(x2 - x1) >= abs(y2 - y1):
        direction = 1 if x2 >= x1 else -1
        points = [
            (s(x2), s(y2)),
            (s(x2 - direction * size), s(y2 - size // 2)),
            (s(x2 - direction * size), s(y2 + size // 2)),
        ]
    else:
        direction = 1 if y2 >= y1 else -1
        points = [
            (s(x2), s(y2)),
            (s(x2 - size // 2), s(y2 - direction * size)),
            (s(x2 + size // 2), s(y2 - direction * size)),
        ]
    draw.polygon(points, fill=color)


def poly_arrow(
    draw: ImageDraw.ImageDraw,
    points: list[tuple[int, int]],
    color: str = "#64748b",
) -> None:
    for start, end in zip(points, points[1:]):
        draw.line((s(start[0]), s(start[1]), s(end[0]), s(end[1])), fill=color, width=s(4))
    arrow(draw, points[-2], points[-1], color)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (s(WIDTH), s(HEIGHT)), BG)
    draw = ImageDraw.Draw(img)

    draw.text((s(70), s(46)), "Durham Risk Intelligence Dashboard", font=TITLE, fill=INK)
    draw.text(
        (s(72), s(93)),
        "Final AWS architecture: Terraform managed EC2, Nginx reverse proxy, GitHub Actions OIDC + SSM deployment, Route 53, CloudWatch, and SNS monitoring",
        font=SUBTITLE,
        fill=MUTED,
    )

    lane(draw, (60, 145, 1740, 445), "Public Runtime", "Public traffic enters on port 80; FastAPI remains internal on localhost:8000.", BLUE_LIGHT)
    lane(draw, (60, 485, 1740, 800), "Deployment Automation", "GitHub Actions deploys through OIDC and AWS Systems Manager, not SSH.", GREEN_LIGHT)
    lane(draw, (60, 840, 1740, 1155), "Monitoring and Alerting", "EC2 metrics and public application health checks route alerts through SNS.", AMBER_LIGHT)

    runtime_y = 245
    runtime_boxes = [
        ((95, runtime_y, 335, runtime_y + 145), "User Browser", "Dashboard users access the public EC2 URL over HTTP.", BLUE_LIGHT, BLUE, "browser"),
        ((390, runtime_y, 650, runtime_y + 145), "EC2 Host", "Public IP: 54.242.183.123. HTTP traffic enters on port 80.", GRAY_LIGHT, BLUE, "server"),
        ((705, runtime_y, 965, runtime_y + 145), "Nginx", "Public reverse proxy forwards requests to the local app runtime.", GRAY_LIGHT, BLUE, "proxy"),
        ((1020, runtime_y, 1295, runtime_y + 145), "FastAPI", "Dashboard app runs on localhost port 8000 through systemd.", GRAY_LIGHT, BLUE, "api"),
        ((1350, runtime_y, 1695, runtime_y + 145), "App Files + Data", "Routes, templates, static files, GeoJSON layers, and local data.", GRAY_LIGHT, BLUE, "files"),
    ]
    for item in runtime_boxes:
        box(draw, *item)
    for start_x, end_x in [(335, 390), (650, 705), (965, 1020), (1295, 1350)]:
        arrow(draw, (start_x + 8, runtime_y + 72), (end_x - 8, runtime_y + 72), BLUE)

    deploy_y = 585
    deploy_boxes = [
        ((95, deploy_y, 320, deploy_y + 145), "Push to main", "Developer pushes code to the GitHub repository.", GREEN_LIGHT, GREEN, "git"),
        ((365, deploy_y, 600, deploy_y + 145), "GitHub Actions", "Starts on push or manual dispatch.", GRAY_LIGHT, GREEN, "workflow"),
        ((645, deploy_y, 875, deploy_y + 145), "OIDC + IAM", "Assumes AWS role without stored keys.", GRAY_LIGHT, GREEN, "lock"),
        ((920, deploy_y, 1145, deploy_y + 145), "AWS SSM", "Runs deploy command without SSH.", GRAY_LIGHT, GREEN, "terminal"),
        ((1190, deploy_y, 1435, deploy_y + 145), "EC2 Deploy", "Pulls code and checks requirements.", GRAY_LIGHT, GREEN, "server"),
        ((1480, deploy_y, 1695, deploy_y + 145), "Restart App", "Restarts systemd and checks /health.", GRAY_LIGHT, GREEN, "service"),
    ]
    for item in deploy_boxes:
        box(draw, *item)
    for start_x, end_x in [(320, 365), (600, 645), (875, 920), (1145, 1190), (1435, 1480)]:
        arrow(draw, (start_x + 8, deploy_y + 72), (end_x - 8, deploy_y + 72), GREEN)

    mon_y = 945
    monitoring_boxes = [
        ((95, mon_y, 390, mon_y + 145), "Route 53 Health Check", "HTTP check of public /health on port 80.", AMBER_LIGHT, AMBER, "health"),
        ((455, mon_y, 820, mon_y + 145), "CloudWatch Alarms", "HealthCheckStatus, EC2 CPU, and EC2 status checks.", GRAY_LIGHT, AMBER, "cloudwatch"),
        ((885, mon_y, 1180, mon_y + 145), "SNS Alerts", "Email alert path for monitoring events.", GRAY_LIGHT, AMBER, "alert"),
        ((1245, mon_y, 1695, mon_y + 145), "Security Note", "Public app: port 80 via Nginx. Internal FastAPI: port 8000.", PURPLE_LIGHT, PURPLE, "boundary"),
    ]
    for item in monitoring_boxes:
        box(draw, *item)
    arrow(draw, (390 + 8, mon_y + 72), (455 - 8, mon_y + 72), AMBER)
    arrow(draw, (820 + 8, mon_y + 72), (885 - 8, mon_y + 72), AMBER)
    for x in range(1190, 1235, 10):
        draw.line((s(x), s(mon_y + 72), s(x + 5), s(mon_y + 72)), fill=PURPLE, width=s(2))

    footer = (
        "Current instance: i-0998e40b915d53346  |  Service: durham-risk-dashboard.service  |  "
        "Deploy path: /home/ec2-user/durham-aws-risk-dashboard"
    )
    draw.text((s(72), s(1180)), footer, font=SMALL, fill=MUTED)
    draw.text(
        (s(72), s(1210)),
        "Current architecture excludes ALB, Target Group, Auto Scaling Group, Launch Template, and Custom AMI.",
        font=SMALL,
        fill=MUTED,
    )

    img.save(OUT_HIGHRES)
    img = img.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    img.save(OUT)
    print(OUT)
    print(OUT_HIGHRES)


if __name__ == "__main__":
    main()

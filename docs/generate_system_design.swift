import AppKit

let canvasWidth: CGFloat = 1800
let canvasHeight: CGFloat = 1120

struct BoxStyle {
    let fill: NSColor
    let stroke: NSColor
}

struct DiagramBox {
    let x: CGFloat
    let y: CGFloat
    let width: CGFloat
    let height: CGFloat
    let style: BoxStyle
    let title: String
    let lines: [String]
}

func color(_ hex: UInt32, alpha: CGFloat = 1.0) -> NSColor {
    NSColor(
        calibratedRed: CGFloat((hex >> 16) & 0xff) / 255.0,
        green: CGFloat((hex >> 8) & 0xff) / 255.0,
        blue: CGFloat(hex & 0xff) / 255.0,
        alpha: alpha
    )
}

func rect(_ x: CGFloat, _ y: CGFloat, _ width: CGFloat, _ height: CGFloat) -> NSRect {
    NSRect(x: x, y: canvasHeight - y - height, width: width, height: height)
}

func point(_ x: CGFloat, _ y: CGFloat) -> NSPoint {
    NSPoint(x: x, y: canvasHeight - y)
}

func drawText(_ text: String, x: CGFloat, y: CGFloat, font: NSFont, color: NSColor) {
    let attributes: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: color,
    ]
    let size = text.size(withAttributes: attributes)
    let drawRect = NSRect(x: x, y: canvasHeight - y - size.height, width: size.width + 4, height: size.height + 4)
    text.draw(in: drawRect, withAttributes: attributes)
}

func drawParagraph(_ text: String, x: CGFloat, y: CGFloat, width: CGFloat, font: NSFont, color: NSColor, lineHeight: CGFloat = 22) {
    let style = NSMutableParagraphStyle()
    style.lineBreakMode = .byWordWrapping
    style.minimumLineHeight = lineHeight
    style.maximumLineHeight = lineHeight
    let attributes: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: color,
        .paragraphStyle: style,
    ]
    let attributed = NSAttributedString(string: text, attributes: attributes)
    attributed.draw(with: rect(x, y, width, lineHeight * 3.0), options: [.usesLineFragmentOrigin, .usesFontLeading])
}

func drawRoundedBox(_ box: DiagramBox) {
    let path = NSBezierPath(roundedRect: rect(box.x, box.y, box.width, box.height), xRadius: 22, yRadius: 22)
    box.style.fill.setFill()
    path.fill()
    box.style.stroke.setStroke()
    path.lineWidth = 2
    path.stroke()

    drawText(box.title, x: box.x + 26, y: box.y + 26, font: .boldSystemFont(ofSize: 22), color: color(0x1f2f50))
    for (index, line) in box.lines.enumerated() {
        drawParagraph(
            line,
            x: box.x + 26,
            y: box.y + 64 + CGFloat(index) * 28,
            width: box.width - 52,
            font: .systemFont(ofSize: 17, weight: .regular),
            color: color(0x31415f),
            lineHeight: 22
        )
    }
}

func drawZone(title: String, x: CGFloat, y: CGFloat, width: CGFloat, height: CGFloat) {
    let zonePath = NSBezierPath(roundedRect: rect(x, y, width, height), xRadius: 26, yRadius: 26)
    color(0xf7f9fc).setFill()
    zonePath.fill()
    color(0xd8dfeb).setStroke()
    zonePath.lineWidth = 2
    zonePath.stroke()
    drawText(title, x: x + 18, y: y + 16, font: .boldSystemFont(ofSize: 20), color: color(0x1f2f50))
}

func drawArrow(from start: (CGFloat, CGFloat), to end: (CGFloat, CGFloat), dashed: Bool = false) {
    let path = NSBezierPath()
    if dashed {
        let pattern: [CGFloat] = [10, 8]
        path.setLineDash(pattern, count: pattern.count, phase: 0)
    }
    path.lineWidth = dashed ? 2.5 : 3
    color(dashed ? 0x7b879d : 0x44506b).setStroke()
    path.move(to: point(start.0, start.1))
    path.line(to: point(end.0, end.1))
    path.stroke()

    let angle = atan2(end.1 - start.1, end.0 - start.0)
    let arrowLength: CGFloat = 16
    let arrowWidth: CGFloat = 8
    let tip = point(end.0, end.1)
    let left = point(
        end.0 - arrowLength * cos(angle) + arrowWidth * sin(angle),
        end.1 - arrowLength * sin(angle) - arrowWidth * cos(angle)
    )
    let right = point(
        end.0 - arrowLength * cos(angle) - arrowWidth * sin(angle),
        end.1 - arrowLength * sin(angle) + arrowWidth * cos(angle)
    )

    let arrowHead = NSBezierPath()
    arrowHead.move(to: tip)
    arrowHead.line(to: left)
    arrowHead.line(to: right)
    arrowHead.close()
    color(dashed ? 0x7b879d : 0x44506b).setFill()
    arrowHead.fill()
}

func drawLabel(_ text: String, x: CGFloat, y: CGFloat) {
    drawText(text, x: x, y: y, font: .systemFont(ofSize: 16, weight: .regular), color: color(0x4b5b78))
}

let bitmap = NSBitmapImageRep(
    bitmapDataPlanes: nil,
    pixelsWide: Int(canvasWidth),
    pixelsHigh: Int(canvasHeight),
    bitsPerSample: 8,
    samplesPerPixel: 4,
    hasAlpha: true,
    isPlanar: false,
    colorSpaceName: .deviceRGB,
    bytesPerRow: 0,
    bitsPerPixel: 0
)!

NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: bitmap)

color(0xf3f6fb).setFill()
rect(0, 0, canvasWidth, canvasHeight).fill()

drawText("Medical AI Workflow Demo: System Design", x: 86, y: 22, font: .boldSystemFont(ofSize: 40), color: color(0x14213d))
drawParagraph(
    "Implementation-based view derived from the current FastAPI, Celery, React, PostgreSQL, Redis, and Keycloak code paths.",
    x: 80,
    y: 64,
    width: 1160,
    font: .systemFont(ofSize: 18),
    color: color(0x44506b)
)

let notePath = NSBezierPath(roundedRect: rect(1131.5902, 39.5, 456, 55.5), xRadius: 14, yRadius: 14)
    color(0xffffff, alpha: 0.82).setFill()
notePath.fill()
drawText("Public-safe: synthetic data, fake entities, demo-only auth seed", x: 1151.5902, y: 60.44971, font: .systemFont(ofSize: 15), color: color(0x44506b))

drawZone(title: "CLIENT AND IDENTITY", x: 60, y: 150, width: 1680, height: 250)
drawZone(title: "APPLICATION AND JOB EXECUTION", x: 60, y: 430, width: 1680, height: 300)
drawZone(title: "DATA AND SHARED ETL LAYER", x: 60, y: 760, width: 1680, height: 300)

let gold = BoxStyle(fill: color(0xfff8e8), stroke: color(0xf0c35f))
let blue = BoxStyle(fill: color(0xebf2ff), stroke: color(0x80aaff))
let green = BoxStyle(fill: color(0xecfdf3), stroke: color(0x84d8a8))
let red = BoxStyle(fill: color(0xfff1ef), stroke: color(0xf3a29a))
let neutral = BoxStyle(fill: color(0xffffff), stroke: color(0xb7c3d8))

let boxes = [
    DiagramBox(
        x: 100, y: 210, width: 300, height: 175, style: gold,
        title: "User Browser",
        lines: [
            "Operator signs in,",
            "watches metrics,",
            "triggers ETL runs, and",
            "saves views.",
        ]
    ),
    DiagramBox(
        x: 560, y: 205, width: 420, height: 180, style: blue,
        title: "React + Vite Frontend",
        lines: [
            "`frontend/src/App.jsx`",
            "Bootstraps Keycloak auth and polls data.",
            "Calls `/api/me`, `/api/overview`,",
            "`/api/jobs`, and `/api/views`.",
        ]
    ),
    DiagramBox(
        x: 1240, y: 205, width: 360, height: 180, style: green,
        title: "Keycloak Identity Provider",
        lines: [
            "Realm import under `keycloak/`",
            "Issues OIDC tokens and realm roles",
            "used by the API for `admin` authorization.",
        ]
    ),
    DiagramBox(
        x: 150, y: 510, width: 470, height: 190, style: blue,
        title: "FastAPI Backend",
        lines: [
            "`backend/app/main.py` + `security.py`",
            "Validates bearer tokens and upserts app users.",
            "Reads analytics, persists saved views,",
            "and queues ETL refresh jobs.",
        ]
    ),
    DiagramBox(
        x: 800, y: 545, width: 230, height: 135, style: red,
        title: "Redis",
        lines: [
            "Celery broker and",
            "result backend.",
        ]
    ),
    DiagramBox(
        x: 1160, y: 495, width: 460, height: 200, style: gold,
        title: "Celery Worker",
        lines: [
            "`backend/app/tasks.py`",
            "Marks pipeline runs running, succeeded, or failed.",
            "Invokes the ETL snapshot loader and writes",
            "status or errors back into Postgres.",
        ]
    ),
    DiagramBox(
        x: 120, y: 845, width: 380, height: 175, style: gold,
        title: "Shared ETL Package",
        lines: [
            "`src/medical_ai_demo/`",
            "Synthetic generators build raw telemetry.",
            "Transforms produce analytics tables.",
            "Reporting writes a markdown summary.",
        ]
    ),
    DiagramBox(
        x: 747.27906, y: 820, width: 600, height: 210, style: green,
        title: "PostgreSQL",
        lines: [
            "One database with three logical areas:",
            "`raw.*` synthetic source events",
            "`analytics.*` dimensions, facts, and metrics",
            "`app.*` users, pipeline runs, and saved views",
        ]
    ),
    DiagramBox(
        x: 1495, y: 850, width: 230, height: 143, style: neutral,
        title: "Report Output",
        lines: [
            "Generated markdown",
            "summary artifact.",
        ]
    ),
]

for box in boxes {
    drawRoundedBox(box)
}

drawParagraph(
    "The worker truncates and reloads raw/analytics snapshot tables on each ETL run.",
    x: 783.9443,
    y: 993.3901,
    width: 540,
    font: .systemFont(ofSize: 15),
    color: color(0x44506b),
    lineHeight: 20
)

drawArrow(from: (400, 290), to: (560, 290))
drawLabel("UI interaction", x: 424.5733, y: 266)

drawArrow(from: (980, 260), to: (1240, 260))
drawArrow(from: (1240, 325), to: (980, 325))
drawLabel("OIDC login", x: 1064.7695, y: 237.09033)
drawLabel("JWT tokens", x: 1067.9102, y: 303.83984)

drawArrow(from: (700, 385), to: (330, 510))
drawLabel("Bearer-authenticated API calls", x: 632.42065, y: 405.5)

drawArrow(from: (1320, 385), to: (390, 510), dashed: true)
drawLabel("Discovery + JWKS fetch for token validation", x: 1186, y: 405.5)

drawArrow(from: (620, 610), to: (800, 610))
drawLabel("Queue ETL job", x: 656.4805, y: 584.1499)

drawArrow(from: (1030, 610), to: (1160, 610))
drawLabel("Dispatch task", x: 1046.9805, y: 585.5)

drawArrow(from: (1250, 695), to: (500, 845))
drawLabel("Run snapshot ETL", x: 1080.8175, y: 735.5)

drawArrow(from: (590, 670), to: (980, 820))
drawLabel("Read analytics and persist app state", x: 484.28796, y: 735.5)

drawArrow(from: (500, 930), to: (746.5, 930))
drawLabel("Load raw + analytics", x: 550.09766, y: 904.9489)

drawArrow(from: (1347.279, 919.2847), to: (1495.2, 919.2847))
drawLabel("Write summary", x: 1366.3633, y: 895.0101)

NSGraphicsContext.restoreGraphicsState()

let outputURL = URL(fileURLWithPath: "docs/assets/system-design.png")
if let pngData = bitmap.representation(using: .png, properties: [:]) {
    try pngData.write(to: outputURL)
    print("Wrote \(outputURL.path)")
} else {
    fputs("Failed to encode PNG\n", stderr)
    exit(1)
}

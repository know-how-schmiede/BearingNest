"""Render the shared contour geometry for documentation."""
from pathlib import Path
import sys

ADDIN = Path(__file__).resolve().parents[1] / 'Fusion-Add-In' / 'BearingNest'
sys.path.insert(0, str(ADDIN))
from contour_geometry import contour


def render(path):
    segments = contour()
    scale, cx, cy = 17, 290, 295

    def xy(point):
        return f'{cx + scale * point[0]:.4f},{cy - scale * point[1]:.4f}'

    commands = [f'M {xy(segments[0].start)}']
    for segment in segments:
        if segment.radius:
            radius = scale * segment.radius
            commands.append(f'A {radius} {radius} 0 0 {int(segment.clockwise)} {xy(segment.end)}')
        else:
            commands.append(f'L {xy(segment.end)}')
    commands.append('Z')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="640" viewBox="0 0 1100 640">
<rect width="1100" height="640" fill="#f7fafc"/>
<g font-family="Arial,sans-serif" fill="#142b3b">
<text x="30" y="38" font-size="25" font-weight="bold">BearingNest — rounded contour proposal A</text>
<text x="30" y="66" font-size="16">Top view · dimensions in mm · review prototype, not released geometry</text>
<path d="{' '.join(commands)}" fill="#b8e6df" stroke="#142b3b" stroke-width="2"/>
<circle cx="{cx}" cy="{cy}" r="{10.95 * scale}" fill="none" stroke="#688393" stroke-dasharray="6 5"/>
<path d="M 65 {cy} H 515 M {cx} 70 V 520" stroke="#8da4af" stroke-dasharray="4 6"/>
<path d="M {cx-10.95*scale} 540 H {cx+10.95*scale} M {cx-10.95*scale} 530 V 550 M {cx+10.95*scale} 530 V 550" stroke="#142b3b"/>
<text x="185" y="570" font-size="18">Contact diameter 21.90</text>
<text x="570" y="130" font-size="21" font-weight="bold">Dimension set</text>
<text x="570" y="170" font-size="18">Example bearing D = 22.00; correction = −0.10</text>
<text x="570" y="207" font-size="18">5 contact lands; pitch = 72°; land angle = 30°</text>
<text x="570" y="244" font-size="18">Radial relief depth = 1.20</text>
<text x="570" y="281" font-size="18">Both transition fillets R = 0.40</text>
<text x="570" y="318" font-size="18">Maximum contour diameter = 24.30</text>
<text x="570" y="365" font-size="18">Each flank: inner fillet → radial wall → outer fillet.</text>
<text x="570" y="400" font-size="18">All joins are tangent. Contact lands stay at 21.90.</text>
<text x="570" y="450" font-size="18" font-weight="bold">Construction confirmed by owner</text>
<text x="570" y="485" font-size="17">Flank shape confirmed; transition width is derived.</text>
<text x="570" y="520" font-size="17">Axial extent: full seat depth (below lead-in).</text>
<text x="30" y="615" font-size="15">Illustrative dimensions only; no verified bearing record or calibrated print fit is implied.</text>
</g></svg>'''
    Path(path).write_text(svg, encoding='utf-8')


if __name__ == '__main__':
    render(Path(__file__).resolve().parents[1] / 'images/contour-proposal.svg')

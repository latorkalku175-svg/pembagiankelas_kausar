"""Generate PWA icons from the GuruKelas logo (graduation cap / segitiga ungu)."""
import subprocess, sys

# SVG content matching the navbar logo - graduation cap style
def make_svg(size):
    # Padding so icon doesn't clip
    pad = size * 0.1
    inner = size - pad * 2
    
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <!-- Background circle -->
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6C5CE7"/>
      <stop offset="100%" style="stop-color:#4A3CB8"/>
    </linearGradient>
  </defs>
  <rect width="{size}" height="{size}" rx="{size*0.22}" fill="url(#bg)"/>
  <!-- Graduation cap icon scaled to fit -->
  <g transform="translate({pad},{pad}) scale({inner/24})">
    <path d="M12 3 1.5 8.25 12 13.5l9.5-5.25L12 3Z" fill="white"/>
    <path d="M5.25 11.25v4.5c0 .7 2.84 2.75 6.75 2.75s6.75-2.05 6.75-2.75v-4.5" 
          stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <path d="M21.5 8.25v6" stroke="white" stroke-width="1.6" stroke-linecap="round" fill="none"/>
  </g>
</svg>'''

for size in [192, 512]:
    svg = make_svg(size)
    fname = f"/home/claude/gurukelas_django_kausar/static/icons/icon-{size}x{size}.svg"
    with open(fname, 'w') as f:
        f.write(svg)
    print(f"Created {fname}")

# Also create a maskable version (same but fills more space)
def make_svg_maskable(size):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6C5CE7"/>
      <stop offset="100%" style="stop-color:#4A3CB8"/>
    </linearGradient>
  </defs>
  <rect width="{size}" height="{size}" fill="url(#bg)"/>
  <g transform="translate({size*0.12},{size*0.12}) scale({size*0.76/24})">
    <path d="M12 3 1.5 8.25 12 13.5l9.5-5.25L12 3Z" fill="white"/>
    <path d="M5.25 11.25v4.5c0 .7 2.84 2.75 6.75 2.75s6.75-2.05 6.75-2.75v-4.5" 
          stroke="white" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <path d="M21.5 8.25v6" stroke="white" stroke-width="1.6" stroke-linecap="round" fill="none"/>
  </g>
</svg>'''

svg = make_svg_maskable(512)
with open("/home/claude/gurukelas_django_kausar/static/icons/icon-512x512-maskable.svg", 'w') as f:
    f.write(svg)
print("Created maskable icon")

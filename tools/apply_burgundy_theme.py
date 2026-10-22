import os
import re

STYLES_CSS = r"C:\Claude Work\camoroles\static\styles.css"
with open(STYLES_CSS, "r", encoding="utf-8") as f:
    css = f.read()

# 1. Update :root variables to Apple Burgundy & Vintage Warm White with subtle yellowishness
root_old = """:root {
  /* Clean Executive Canvas with Navy Blue Foundation */
  --bg:             #F8FAFC; /* Crisp slate white canvas */
  --bg-subtle:      #F1F5F9; /* Subtle cool tone */
  --surface:        #FFFFFF; /* Pure white surface */
  --surface-card:   #FFFFFF;
  --surface-hover:  #F8FAFC;
  --surface-sunken: #E2E8F0;

  /* Hairlines & Borders */
  --line:           #E2E8F0; /* Clean border */
  --line-strong:    #CBD5E1;
  --line-subtle:    rgba(15, 23, 42, 0.06);

  /* Ink & Typography */
  --ink:            #0F172A; /* Deep Navy Ink */
  --ink-secondary:  #1E293B;
  --muted:          #64748B; /* Cool slate muted */
  --dim:            #94A3B8;

  /* Executive Navy Blue Accents (Replacing Warm Orange / Amber) */
  --navy:           #1E3A8A; /* Classic Executive Navy */
  --navy-accent:    #2563EB; /* Vibrant Navy Blue */
  --navy-hover:     #1D4ED8;
  --navy-soft:      rgba(37, 99, 235, 0.08);
  --navy-border:    rgba(37, 99, 235, 0.22);

  --terracotta:     #1E40AF; /* Primary Navy Action */
  --terracotta-hover: #1E3A8A;
  --terracotta-soft:  rgba(30, 64, 175, 0.09);
  --emerald:        #0D9488; /* Sophisticated Teal for verified badge */
  --gold:           #2563EB; /* Replaced orange with Navy Blue */
  --gold-subtle:    rgba(37, 99, 235, 0.08);
  --gold-border:    rgba(37, 99, 235, 0.24);
  --blue-soft:      #2563EB;

  /* Shadows & Depth */
  --paper-shadow:   0 1px 3px rgba(15, 23, 42, 0.04), 0 4px 14px rgba(15, 23, 42, 0.03);
  --card-shadow:    0 1px 2px rgba(15, 23, 42, 0.04);
  --search-shadow:  0 2px 10px rgba(30, 64, 175, 0.08), 0 1px 3px rgba(15, 23, 42, 0.05);
  --sunken-shadow:  inset 0 1px 3px rgba(15, 23, 42, 0.06);

  --slider-pct:     100%;
}"""

root_new = """:root {
  /* Vintage Warm White Canvas with Subtle Organic Yellowishness / Ivory Paper Tone */
  --bg:             #FAF6EE; /* Vintage warm white with subtle yellowishness */
  --bg-subtle:      #F3ECE0; /* Warm vintage linen / deeper paper tone */
  --surface:        #FFFEFB; /* Crisp elevated vintage warm white surface */
  --surface-card:   #FFFEFB;
  --surface-hover:  #F6F0E4;
  --surface-sunken: #EFE7D8; /* Warm sunken inputs & sliders */

  /* Hairlines & Borders */
  --line:           #E7DECB; /* Delicate vintage paper border */
  --line-strong:    #D6CABE;
  --line-subtle:    rgba(112, 26, 43, 0.06);

  /* Ink & Typography */
  --ink:            #231418; /* Deep espresso noir with rich burgundy undertone */
  --ink-secondary:  #3B242A;
  --muted:          #7A6268; /* Warm antique rose-taupe */
  --dim:            #A08B91;

  /* Apple Mobile Deep Burgundy & Cabernet Accents */
  --navy:           #701A2B; /* Apple Mobile Deep Velvet Burgundy */
  --navy-accent:    #8E2239; /* Luminous Burgundy Accent */
  --navy-hover:     #541220; /* Deep Velvet Wine Hover */
  --navy-soft:      rgba(112, 26, 43, 0.08);
  --navy-border:    rgba(112, 26, 43, 0.22);

  --terracotta:     #701A2B; /* Primary Burgundy Action */
  --terracotta-hover: #541220;
  --terracotta-soft:  rgba(112, 26, 43, 0.08);
  --emerald:        #1E6B52; /* Sophisticated deep sage/forest for verified live status */
  --gold:           #8E2239; /* Apple Mobile Burgundy */
  --gold-subtle:    rgba(142, 34, 57, 0.08);
  --gold-border:    rgba(142, 34, 57, 0.25);
  --blue-soft:      #8E2239;

  /* Shadows & Depth */
  --paper-shadow:   0 1px 3px rgba(35, 20, 24, 0.04), 0 4px 14px rgba(35, 20, 24, 0.03);
  --card-shadow:    0 1px 2px rgba(35, 20, 24, 0.04);
  --search-shadow:  0 2px 14px rgba(112, 26, 43, 0.12), 0 1px 3px rgba(35, 20, 24, 0.05);
  --sunken-shadow:  inset 0 1px 3px rgba(35, 20, 24, 0.06);

  --slider-pct:     100%;
}"""

if root_old in css:
    css = css.replace(root_old, root_new)
    print("Replaced :root variables successfully")
else:
    print("Warning: root_old not found directly")

# 2. Update [data-theme="dark"]
dark_old = """/* Deep Midnight Navy Slate Dark Mode */
[data-theme="dark"] {
  --bg:             #0B0F19; /* Deep Midnight Navy Canvas */
  --bg-subtle:      #111827; /* Dark navy slate */
  --surface:        #151D2E; /* Elevated dark navy surface */
  --surface-card:   #151D2E;
  --surface-hover:  #1E293B;
  --surface-sunken: #090D16;

  --line:           #1E293B; /* Refined navy slate border */
  --line-strong:    #334155;
  --line-subtle:    rgba(255, 255, 255, 0.06);

  --ink:            #F8FAFC; /* Crisp bright white ink */
  --ink-secondary:  #E2E8F0;
  --muted:          #94A3B8; /* Refined cool stone */
  --dim:            #64748B;

  --navy:           #3B82F6;
  --navy-accent:    #60A5FA;
  --navy-hover:     #2563EB;
  --navy-soft:      rgba(59, 130, 246, 0.14);
  --navy-border:    rgba(59, 130, 246, 0.32);

  --terracotta:     #2563EB; /* Vibrant Navy Blue */
  --terracotta-hover: #3B82F6;
  --terracotta-soft:  rgba(37, 99, 235, 0.16);
  --emerald:        #14B8A6;
  --gold:           #3B82F6; /* Replaced orange with electric navy */
  --gold-subtle:    rgba(59, 130, 246, 0.12);
  --gold-border:    rgba(59, 130, 246, 0.32);
  --blue-soft:      #60A5FA;

  --paper-shadow:   0 2px 8px rgba(0, 0, 0, 0.5), 0 8px 24px rgba(0, 0, 0, 0.4);
  --card-shadow:    0 1px 3px rgba(0, 0, 0, 0.45);
  --search-shadow:  0 4px 20px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(59, 130, 246, 0.25);
  --sunken-shadow:  inset 0 1px 4px rgba(0, 0, 0, 0.7);
}"""

dark_new = """/* Deep Noir Cabernet & Illuminated Apple Burgundy Dark Mode */
[data-theme="dark"] {
  --bg:             #12090C; /* Deepest Noir Burgundy Canvas */
  --bg-subtle:      #190F13; /* Dark velvet wine slate */
  --surface:        #201419; /* Elevated dark burgundy surface */
  --surface-card:   #201419;
  --surface-hover:  #2A1B22;
  --surface-sunken: #0E0608;

  --line:           #341F27; /* Refined dark wine border */
  --line-strong:    #4A2E39;
  --line-subtle:    rgba(255, 255, 255, 0.06);

  --ink:            #FAF6EE; /* Vintage warm white ink */
  --ink-secondary:  #F0E8DC;
  --muted:          #A8939B; /* Warm vintage dusty rose */
  --dim:            #735F66;

  --navy:           #E05A76; /* Illuminated Apple mobile burgundy/rose */
  --navy-accent:    #EC6F8A;
  --navy-hover:     #D44A67;
  --navy-soft:      rgba(224, 90, 118, 0.16);
  --navy-border:    rgba(224, 90, 118, 0.32);

  --terracotta:     #E05A76; /* Vibrant Apple Mobile Burgundy */
  --terracotta-hover: #EC6F8A;
  --terracotta-soft:  rgba(224, 90, 118, 0.16);
  --emerald:        #2DD4BF;
  --gold:           #E05A76;
  --gold-subtle:    rgba(224, 90, 118, 0.12);
  --gold-border:    rgba(224, 90, 118, 0.32);
  --blue-soft:      #EC6F8A;

  --paper-shadow:   0 2px 8px rgba(0, 0, 0, 0.5), 0 8px 24px rgba(0, 0, 0, 0.4);
  --card-shadow:    0 1px 3px rgba(0, 0, 0, 0.45);
  --search-shadow:  0 4px 20px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(224, 90, 118, 0.28);
  --sunken-shadow:  inset 0 1px 4px rgba(0, 0, 0, 0.7);
}"""

if dark_old in css:
    css = css.replace(dark_old, dark_new)
    print("Replaced dark mode variables successfully")
else:
    print("Warning: dark_old not found directly")

# 3. Replace residual hardcoded rgba(197, 160, 89, ...) with burgundy glow
css = css.replace("rgba(197, 160, 89, 0.3)", "rgba(112, 26, 43, 0.25)")
css = css.replace("rgba(197, 160, 89, 0.45)", "rgba(112, 26, 43, 0.40)")
css = css.replace("rgba(197, 160, 89, 0.2)", "rgba(112, 26, 43, 0.20)")
css = css.replace("rgba(197, 160, 89, 0.25)", "rgba(112, 26, 43, 0.22)")
css = css.replace("rgba(197, 160, 89, 0.4)", "rgba(112, 26, 43, 0.35)")

# 4. Update button text color for crisp vintage contrast
btn_rule_old = """[data-theme="dark"] .btn-apply-link,
[data-theme="dark"] .modal-direct-apply-btn,
[data-theme="dark"] .btn-search-go {
  color: #FFFFFF !important;
  font-weight: 700;
}"""

btn_rule_new = """.btn-apply-link,
.modal-direct-apply-btn,
.btn-search-go {
  background: var(--terracotta);
  color: #FFFDF8 !important;
  font-weight: 700;
}"""

if btn_rule_old in css:
    css = css.replace(btn_rule_old, btn_rule_new)
    print("Updated button text rules successfully")

with open(STYLES_CSS, "w", encoding="utf-8") as f:
    f.write(css)

# Update web/styles.css
WEB_STYLES = r"C:\Claude Work\camoroles\web\styles.css"
with open(WEB_STYLES, "w", encoding="utf-8") as f:
    f.write(css)

print("styles.css updated with Apple Burgundy & Vintage Warm White")

# 5. Update app.js monogram palette to harmonize with Apple Burgundy
APP_JS = r"C:\Claude Work\camoroles\static\app.js"
with open(APP_JS, "r", encoding="utf-8") as f:
    app_js = f.read()

palette_old = """  const palette = [
    '#1E3A8A', '#1E40AF', '#1D4ED8', '#0F766E', '#047857',
    '#312E81', '#3730A3', '#4338CA', '#0369A1', '#0E7490',
    '#334155', '#1F2937', '#111827', '#1E293B', '#2563EB'
  ];"""

palette_new = """  const palette = [
    '#701A2B', '#852035', '#5E1424', '#7D1E32', '#8E2239',
    '#1E6B52', '#2A4365', '#4A2A51', '#3B242A', '#8C2B41',
    '#2E2226', '#631B2B', '#1D3557', '#501524', '#791C2F'
  ];"""

if palette_old in app_js:
    app_js = app_js.replace(palette_old, palette_new)
    with open(APP_JS, "w", encoding="utf-8") as f:
        f.write(app_js)
    WEB_APP_JS = r"C:\Claude Work\camoroles\web\app.js"
    with open(WEB_APP_JS, "w", encoding="utf-8") as f:
        f.write(app_js)
    print("Updated monogram palette in app.js successfully")
else:
    print("Note: palette_old was not matched verbatim in app.js")

print("Theme update complete.")

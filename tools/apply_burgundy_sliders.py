import os

STYLES_FILE = r"C:\Claude Work\camoroles\static\styles.css"
with open(STYLES_FILE, "r", encoding="utf-8") as f:
    css = f.read()

slider_old = """/* Custom Tactile Experience Slider (Paperneat Style) */
.slider-box {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 12px 14px;
  box-shadow: var(--card-shadow);
}

.slider-header-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 10px;
}

.slider-readout {
  font-size: 12px;
  font-weight: 700;
  color: var(--terracotta);
}

input[type=range].tactile-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--terracotta) 0%, var(--terracotta) var(--slider-pct, 100%), var(--surface-sunken) var(--slider-pct, 100%));
  outline: none;
  margin: 0;
  cursor: pointer;
  border: 1px solid var(--line);
  box-shadow: var(--sunken-shadow);
}

input[type=range].tactile-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--surface);
  border: 2px solid var(--terracotta);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  transition: transform 0.1s ease;
}

input[type=range].tactile-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

input[type=range].tactile-slider::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--surface);
  border: 2px solid var(--terracotta);
  cursor: pointer;
}

.slider-presets-row {
  display: flex;
  gap: 5px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.preset-pill-btn {
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 5px;
  background: var(--bg-subtle);
  border: 1px solid var(--line);
  color: var(--muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.preset-pill-btn:hover {
  color: var(--ink);
  background: var(--surface-hover);
}

.preset-pill-btn.active {
  background: var(--terracotta-soft);
  border-color: var(--terracotta);
  color: var(--terracotta);
  font-weight: 600;
}"""

slider_new = """/* Custom Tactile Experience Slider — Apple Burgundy Edition */
.slider-box {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 13px 15px;
  box-shadow: var(--card-shadow);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.slider-box:hover {
  border-color: var(--navy-border);
  box-shadow: 0 2px 8px rgba(112, 26, 43, 0.08);
}

.slider-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.slider-readout {
  font-size: 11.5px;
  font-weight: 700;
  color: var(--terracotta);
  background: var(--terracotta-soft);
  border: 1px solid var(--navy-border);
  padding: 2.5px 9px;
  border-radius: 6px;
  letter-spacing: 0.02em;
}

input[type=range].tactile-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 7px;
  border-radius: 999px;
  background: linear-gradient(90deg, #8E2239 0%, #701A2B var(--slider-pct, 100%), var(--surface-sunken) var(--slider-pct, 100%));
  outline: none;
  margin: 6px 0;
  cursor: pointer;
  border: 1px solid var(--line);
  box-shadow: var(--sunken-shadow);
  transition: all 0.15s ease;
}

[data-theme="dark"] input[type=range].tactile-slider {
  background: linear-gradient(90deg, #D44A67 0%, #E05A76 var(--slider-pct, 100%), var(--surface-sunken) var(--slider-pct, 100%));
}

/* Apple Burgundy Jewel Thumb */
input[type=range].tactile-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #701A2B;
  border: 2.5px solid #FFFDF8;
  box-shadow: 0 2px 6px rgba(112, 26, 43, 0.45), 0 0 0 1px rgba(112, 26, 43, 0.25);
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background-color 0.15s ease;
}

[data-theme="dark"] input[type=range].tactile-slider::-webkit-slider-thumb {
  background: #E05A76;
  border: 2.5px solid #12090C;
  box-shadow: 0 2px 8px rgba(224, 90, 118, 0.55), 0 0 0 1px rgba(224, 90, 118, 0.35);
}

input[type=range].tactile-slider::-webkit-slider-thumb:hover {
  transform: scale(1.22);
  box-shadow: 0 0 14px rgba(112, 26, 43, 0.65), 0 2px 8px rgba(0, 0, 0, 0.2);
}

[data-theme="dark"] input[type=range].tactile-slider::-webkit-slider-thumb:hover {
  transform: scale(1.22);
  box-shadow: 0 0 16px rgba(224, 90, 118, 0.75);
}

input[type=range].tactile-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #701A2B;
  border: 2.5px solid #FFFDF8;
  box-shadow: 0 2px 6px rgba(112, 26, 43, 0.45);
  cursor: pointer;
  transition: transform 0.15s ease;
}

[data-theme="dark"] input[type=range].tactile-slider::-moz-range-thumb {
  background: #E05A76;
  border: 2.5px solid #12090C;
  box-shadow: 0 2px 8px rgba(224, 90, 118, 0.55);
}

input[type=range].tactile-slider::-moz-range-thumb:hover {
  transform: scale(1.22);
}

.slider-presets-row {
  display: flex;
  gap: 6px;
  margin-top: 11px;
  flex-wrap: wrap;
}

.preset-pill-btn {
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 6px;
  background: var(--bg-subtle);
  border: 1px solid var(--line);
  color: var(--muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.preset-pill-btn:hover {
  color: var(--ink);
  background: var(--surface-hover);
  border-color: var(--line-strong);
}

.preset-pill-btn.active {
  background: #701A2B;
  border-color: #701A2B;
  color: #FFFDF8 !important;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(112, 26, 43, 0.3);
}

[data-theme="dark"] .preset-pill-btn.active {
  background: #E05A76;
  border-color: #E05A76;
  color: #12090C !important;
  box-shadow: 0 2px 8px rgba(224, 90, 118, 0.35);
}"""

if slider_old in css:
    css = css.replace(slider_old, slider_new)
    print("Replaced slider block successfully")
else:
    print("Warning: slider_old not found verbatim")

# Also add subtle Apple Burgundy scrollbars
scrollbar_rule = """
/* Subtle Apple Burgundy Scrollbars */
::-webkit-scrollbar {
  width: 7px;
  height: 7px;
}
::-webkit-scrollbar-track {
  background: var(--bg);
}
::-webkit-scrollbar-thumb {
  background: rgba(112, 26, 43, 0.25);
  border-radius: 999px;
  border: 1.5px solid var(--bg);
}
::-webkit-scrollbar-thumb:hover {
  background: var(--terracotta);
}
[data-theme="dark"] ::-webkit-scrollbar-thumb {
  background: rgba(224, 90, 118, 0.3);
  border-color: var(--bg);
}
[data-theme="dark"] ::-webkit-scrollbar-thumb:hover {
  background: #E05A76;
}
"""

if "/* Subtle Apple Burgundy Scrollbars */" not in css:
    css += scrollbar_rule
    print("Added scrollbar rule successfully")

with open(STYLES_FILE, "w", encoding="utf-8") as f:
    f.write(css)

WEB_STYLES = r"C:\Claude Work\camoroles\web\styles.css"
with open(WEB_STYLES, "w", encoding="utf-8") as f:
    f.write(css)

print("Sliders and scrollbars successfully updated to Apple Burgundy.")

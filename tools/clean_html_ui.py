import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove hero editorial heading and subtitle above search bar
html = re.sub(r'<h1 class="hero-editorial-title">.*?</h1>\s*<p class="hero-editorial-subtitle">.*?</p>', '', html, flags=re.DOTALL)

# 2. Mode buttons - remove emojis and keep text clean
html = html.replace('<span>✨ AI Recruiter Chat</span>', '<span>AI Recruiter</span>')
html = html.replace('<span>⌨️ Manual Search</span>', '<span>Manual Search</span>')
html = html.replace('<span>★ Saved</span>', '<span>Saved</span>')
html = html.replace('Talk with AI Recruiter like ChatGPT or drop your CV...', 'Ask AI Recruiter or drop CV to match verified roles...')

# 3. Clean Emojis in Sort Options
html = html.replace('>⚡ Highest Match %<', '>Highest Match %<')
html = html.replace('>⏱️ Most Recent<', '>Most Recent<')
html = html.replace('>💰 Top Compensation<', '>Top Compensation<')

# 4. Clean Emojis in Filter buttons across sidebar and drawer
emoji_replacements = [
    ('🤖 Robotics & Autonomy', 'Robotics & Autonomy'),
    ('⚡ Distributed Systems & Backend', 'Distributed Systems & Backend'),
    ('⚡ Distributed Systems', 'Distributed Systems'),
    ('🚀 SpaceTech & Satellites', 'SpaceTech & Satellites'),
    ('🚀 SpaceTech', 'SpaceTech'),
    ('🔋 ClimateTech & Clean Energy', 'ClimateTech & Clean Energy'),
    ('🔋 ClimateTech', 'ClimateTech'),
    ('🧬 BioTech & Genomics', 'BioTech & Genomics'),
    ('🧬 BioTech', 'BioTech'),
    ('🦾 Hardware & Silicon', 'Hardware & Silicon'),
    ('🛡️ Defense & Cyber Systems', 'Defense & Cyber Systems'),
    ('🛡️ Defense & Cyber', 'Defense & Cyber'),
    ('🎮 Game Development', 'Game Development'),
    ('🎮 Game Dev', 'Game Dev'),
    ('🎨 Product & UI/UX Design', 'Product & UI/UX Design'),
    ('🎨 Product Design', 'Product Design'),
    ('📊 Business & Finance', 'Business & Finance'),
    ('👥 HR & Talent Acquisition', 'HR & Talent Acquisition'),
    ('👥 HR & Talent', 'HR & Talent'),
    ('⚡ Electrical & Electronics', 'Electrical & Electronics'),
    ('🏗️ Civil & Structural', 'Civil & Structural'),
    ('☁️ Cloud & DevOps', 'Cloud & DevOps'),
    ('💻 Frontend & Fullstack', 'Frontend & Fullstack'),
    ('💻 Frontend & Web', 'Frontend & Web'),
    ('🌍 Worldwide Remote', 'Worldwide Remote'),
    ('🇦🇪 UAE & Dubai Hub', 'UAE & Dubai Hub'),
    ('🇮🇳 India (Blr / Hyd)', 'India (Blr / Hyd)'),
    ('🤖 Senior AI/LLM Systems (Remote/Seattle)', 'Senior AI/LLM Systems (Remote/Seattle)'),
    ('⚡ Distributed Systems ($200k+)', 'Distributed Systems ($200k+)'),
    ('🇮🇳 Top Openings in India (Blr / Hyd)', 'Top Openings in India (Blr / Hyd)'),
    ('🚗 Robotics & Autonomy (C++)', 'Robotics & Autonomy (C++)')
]

for old, new in emoji_replacements:
    html = html.replace(old, new)

# 5. Clean up initial chat greeting to executive tone
old_msg = '''          <div class="chat-messages-container" id="hero-chat-messages">
            <div class="chat-msg agent-msg">
              <div class="msg-avatar">AI</div>
              <div class="msg-bubble">
                <p>Welcome! I'm your AI Recruiter. Ask me anything like you do in ChatGPT—for instance: <em>"Senior backend in Go or Rust paying $180k+ remote"</em>, <em>"Game dev roles in Unreal Engine"</em>, or <em>"Top AI openings in India or Dubai"</em>. You can also upload your CV above for instant ranking!</p>
              </div>
            </div>
          </div>'''

new_msg = '''          <div class="chat-messages-container" id="hero-chat-messages">
            <div class="chat-msg agent-msg">
              <div class="msg-avatar">Recruiter</div>
              <div class="msg-bubble">
                <p>Camouroles Executive Recruiter active across 7,400+ verified requisitions. Specify your target technical stack, domain, or seniority to review qualified opportunities, or attach your CV for automated evaluation.</p>
              </div>
            </div>
          </div>'''
html = html.replace(old_msg, new_msg)

html = html.replace('placeholder="Ask AI: e.g. SpaceTech roles, Tesla autopilot, or mid-level frontend..."',
                    'placeholder="Specify role, technical domain, or company (e.g. Distributed Systems, NVIDIA, Robotics C++)..."')

# 6. Ensure any remaining stray emojis in index.html are removed
# Remove rocket, brain, sparkles, lightning, etc.
html = re.sub(r'[\U0001f300-\U0001f9ff]|[\u2600-\u26ff]|[\u2700-\u27bf]', '', html)
# Restore standard close cross ✕ if stripped
html = html.replace('class="job-modal-close-btn"></button>', 'class="job-modal-close-btn">&times;</button>')
html = html.replace('class="search-clear-action" id="hero-search-clear" onclick="clearSearchInput()"></button>', 'class="search-clear-action" id="hero-search-clear" onclick="clearSearchInput()">&times;</button>')
html = html.replace('class="search-clear-action" onclick="clearSearchInput()"></button>', 'class="search-clear-action" onclick="clearSearchInput()">&times;</button>')

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

with open('web/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Updated static/index.html and web/index.html successfully.')

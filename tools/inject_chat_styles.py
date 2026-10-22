chat_cards_css = '''
/* Inline AI Recruiter Direct Webpage Control & Job Cards */
.chat-inline-job-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 10px;
  width: 100%;
}
.chat-inline-job-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-left: 3px solid var(--gold);
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  cursor: pointer;
  transition: all 0.16s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.chat-inline-job-card:hover {
  border-color: var(--gold);
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(112, 26, 43, 0.1);
}
.chat-inline-job-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.chat-inline-job-company {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--muted);
}
.chat-inline-comp-name {
  color: var(--ink);
  font-weight: 700;
}
.chat-inline-match-badge {
  font-size: 11px;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--gold);
  color: #FFFFFF;
  letter-spacing: 0.02em;
  white-space: nowrap;
}
.chat-inline-job-title {
  font-size: 13.5px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1.3;
}
.chat-inline-job-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--muted);
}
.chat-inline-job-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px dashed var(--line);
}
.chat-inline-apply-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--gold);
  color: #FFFFFF !important;
  font-size: 11px;
  font-weight: 700;
  border-radius: 6px;
  text-decoration: none;
  transition: opacity 0.15s ease;
}
.chat-inline-apply-btn:hover {
  opacity: 0.9;
}
.chat-inline-view-btn {
  background: transparent;
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  cursor: pointer;
}
.chat-inline-view-btn:hover {
  color: var(--ink);
  border-color: var(--ink);
}
.chat-inline-cv-prompt {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.chat-inline-upload-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 9px 16px;
  background: var(--gold);
  color: #FFFFFF;
  border: none;
  border-radius: 8px;
  font-size: 12.5px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 2px 8px rgba(112, 26, 43, 0.2);
}
.chat-inline-upload-btn:hover {
  opacity: 0.92;
  transform: translateY(-1px);
}
.chat-inline-cv-hint {
  font-size: 11px;
  color: var(--muted);
  font-style: italic;
}
.chat-inline-feed-jump {
  margin-top: 8px;
  width: 100%;
}
.chat-jump-feed-btn {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg);
  border: 1px solid var(--gold);
  border-radius: 8px;
  color: var(--gold);
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.15s ease;
}
.chat-jump-feed-btn:hover {
  background: var(--gold);
  color: #FFFFFF;
}
'''

for path in ["static/styles.css", "web/styles.css"]:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if ".chat-inline-job-list" not in content:
        needle = "/* ==========================================================================\n   DEDICATED PROFILE PAGE VIEW STYLES"
        if needle not in content:
            needle = "/* ==========================================================================\r\n   DEDICATED PROFILE PAGE VIEW STYLES"
        
        if needle in content:
            content = content.replace(needle, chat_cards_css + "\n" + needle, 1)
        else:
            content += "\n" + chat_cards_css
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Added inline chat cards CSS to {path}")
    else:
        print(f"Already in {path}")

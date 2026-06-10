import os

langs = {
    'ES': {
        'dir': 'Distribucion_ES',
        'html_file': 'Documentacion/Manual_Oficial_Charm.html',
        'msg_md': "\n> [!IMPORTANT]\n> **REGLA DE ORO:** Para que Chask Swarm pueda comunicarse contigo por Telegram, Discord, Meet Charm, Slack, etc., debes tener el cursor dentro de la conversación Charm del proyecto Charm en Charm.\n",
        'msg_html': '<div style="background: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin-bottom: 20px; color: #991b1b; font-weight: bold;">⚠️ IMPORTANTE: Para que Chask Swarm pueda comunicarse contigo por Telegram, Discord, Meet Charm, Slack, etc., debes tener el cursor dentro de la conversación Charm del proyecto Charm en Charm.</div>'
    },
    'EN': {
        'dir': 'Distribucion_EN',
        'html_file': 'Official_Charm_Manual.html',
        'msg_md': "\n> [!IMPORTANT]\n> **GOLDEN RULE:** For Chask Swarm to communicate with you via Telegram, Discord, Meet Charm, Slack, etc., you must keep your cursor inside the Charm conversation of the Charm project in Charm.\n",
        'msg_html': '<div style="background: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin-bottom: 20px; color: #991b1b; font-weight: bold;">⚠️ IMPORTANT: For Chask Swarm to communicate with you via Telegram, Discord, Meet Charm, Slack, etc., you must keep your cursor inside the Charm conversation of the Charm project in Charm.</div>'
    },
    'PT': {
        'dir': 'Distribucion_PT',
        'html_file': 'Official_Charm_Manual.html',
        'msg_md': "\n> [!IMPORTANT]\n> **REGRA DE OURO:** Para que o Chask Swarm se comunique com você pelo Telegram, Discord, Meet Charm, Slack, etc., você deve manter o cursor dentro da conversa Charm do projeto Charm no Charm.\n",
        'msg_html': '<div style="background: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin-bottom: 20px; color: #991b1b; font-weight: bold;">⚠️ IMPORTANTE: Para que o Chask Swarm se comunique com você pelo Telegram, Discord, Meet Charm, Slack, etc., você deve manter o cursor dentro da conversa Charm do projeto Charm no Charm.</div>'
    },
    'ZH': {
        'dir': 'Distribucion_ZH',
        'html_file': 'Official_Charm_Manual.html',
        'msg_md': "\n> [!IMPORTANT]\n> **黄金法则：** 为了让 Chask Swarm 能够通过 Telegram、Discord、Meet Charm、Slack 等与您通信，您必须将光标保持在 Charm 中 Charm 项目的 Charm 对话内。\n",
        'msg_html': '<div style="background: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin-bottom: 20px; color: #991b1b; font-weight: bold;">⚠️ 重要提示：为了让 Chask Swarm 能够通过 Telegram、Discord、Meet Charm、Slack 等与您通信，您必须将光标保持在 Charm 中 Charm 项目的 Charm 对话内。</div>'
    },
    'RU': {
        'dir': 'Distribucion_RU',
        'html_file': 'Official_Charm_Manual.html',
        'msg_md': "\n> [!IMPORTANT]\n> **ЗОЛОТОЕ ПРАВИЛО:** Чтобы Chask Swarm мог общаться с вами через Telegram, Discord, Meet Charm, Slack и т.д., вы должны держать курсор внутри беседы Charm проекта Charm в Charm.\n",
        'msg_html': '<div style="background: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin-bottom: 20px; color: #991b1b; font-weight: bold;">⚠️ ВАЖНО: Чтобы Chask Swarm мог общаться с вами через Telegram, Discord, Meet Charm, Slack и т.д., вы должны держать курсор внутри беседы Charm проекта Charm в Charm.</div>'
    }
}

base_dir = "C:\\Users\\fnora\\Desktop"

for lang, data in langs.items():
    print(f"Processing {lang}...")
    repo_path = os.path.join(base_dir, data['dir'])
    
    # 1. Update README.md
    readme_path = os.path.join(repo_path, 'Documentacion', 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Insert after the first heading if not already present
        if data['msg_md'].strip() not in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('# '):
                    lines.insert(i+1, data['msg_md'])
                    break
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
    
    # 2. Update HTML Manual
    html_path = os.path.join(repo_path, data['html_file'])
    if not os.path.exists(html_path) and lang == 'ES':
        # ES could be Official_Charm_Manual.html or Manual_Oficial_Charm.html
        html_path = os.path.join(repo_path, 'Official_Charm_Manual.html')
        
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if data['msg_html'].strip() not in content:
            # Replace the old warning if it exists, otherwise insert after <body>
            # The old warning was: "Para que todo funcione a la perfección deben dejar en Charm el cursor sobre el cuadro de texto de la conversación Chask del proyecto Chask."
            # It's easier to just insert our block after <div class="container">
            if '<div class="container">' in content:
                content = content.replace('<div class="container">', '<div class="container">\n' + data['msg_html'])
            elif '<body>' in content:
                content = content.replace('<body>', '<body>\n' + data['msg_html'])
                
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)

print("Update complete.")

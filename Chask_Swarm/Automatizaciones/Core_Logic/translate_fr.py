import os
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='auto', target='fr')

def translate_text(text):
    if not text.strip(): return text
    try:
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

# Translate HTML
html_path = r"C:\Users\fnora\Desktop\Distribucion_FR\Official_Charm_Manual.html"
if os.path.exists(html_path):
    print("Translating HTML...")
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'li', 'td', 'th', 'b', 'strong', 'i', 'em', 'span', 'a', 'div']):
        if tag.string and tag.string.strip():
            # Translate only the direct string content
            original = tag.string.strip()
            # Ignore purely numeric or punctuation strings
            if len(original) > 1 and any(c.isalpha() for c in original):
                translated = translate_text(original)
                if translated:
                    tag.string.replace_with(translated)

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
        
# Translate BAT files
bat_files = [
    r"C:\Users\fnora\Desktop\Distribucion_FR\Install.bat",
    r"C:\Users\fnora\Desktop\Distribucion_FR\Start.bat",
    r"C:\Users\fnora\Desktop\Distribucion_FR\Stop_Swarm.bat",
    r"C:\Users\fnora\Desktop\Distribucion_FR\recovery.bat",
    r"C:\Users\fnora\Desktop\Distribucion_FR\Start_Chask_Hive.bat"
]

for bat_path in bat_files:
    if os.path.exists(bat_path):
        print(f"Translating {bat_path}...")
        with open(bat_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            if line.strip().lower().startswith('echo '):
                prefix = line[:line.lower().index('echo ') + 5]
                text = line[len(prefix):].strip()
                # Skip variable outputs or empty strings or set statements inside echo
                if text and not text.startswith('Set ') and not text.startswith('WScript') and not text.startswith('If ') and not text.startswith('cscript '):
                    translated = translate_text(text)
                    if translated:
                        new_lines.append(prefix + translated + "\n")
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
# Translate README.md
readme_path = r"C:\Users\fnora\Desktop\Distribucion_FR\README.md"
if os.path.exists(readme_path):
    print("Translating README.md...")
    with open(readme_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if line.strip() and not line.startswith('```') and not line.startswith('<'):
            # Basic block translation
            translated = translate_text(line.strip())
            if translated:
                new_lines.append(translated + "\n")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

print("Translation complete!")

import os
import glob

def process_dir(d):
    for f in glob.glob(d + '/*.html'):
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        content = content.replace('href="leave.html"', 'href="leave.html?v=2"')
        content = content.replace('href="notices.html"', 'href="notices.html?v=2"')
        content = content.replace('href="notifications.html"', 'href="notifications.html?v=2"')
        content = content.replace('href="leaves.html"', 'href="leaves.html?v=2"')
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)

process_dir('frontend/student')
process_dir('frontend/teacher')
print('Done cache busting links')

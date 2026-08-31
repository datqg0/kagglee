"""Clean bundler for kag_agent."""
import os
import re

modules = [
    'constants.py',
    'models.py',
    'access.py',
    'routing.py',
    'profile.py',
    'world.py',
    'market.py',
    'shop_solver.py',
    'economy.py',
    'tasks.py',
    'assignment.py',
    'orders.py',
    'validator.py',
    'entrypoint.py'
]

header = '''"""Standalone submission v3 for Kaggriculture Competition."""
from __future__ import annotations
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
'''

parts = [header]

for mod in modules:
    path = os.path.join('temp_sub_v3', 'kag_agent', mod)
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove try-except import blocks
    content = re.sub(r'try:\s+from \.?\w+ import [^\n]+\nexcept [^\n]+:\s+from \w+ import [^\n]+', '', content)
    # Remove single imports
    content = re.sub(r'from \.?\w+ import [^\n]+', '', content)
    # Remove _cur / _parent sys.path manipulation blocks
    content = re.sub(r'_cur = [^\n]+', '', content)
    content = re.sub(r'if _cur not in sys\.path:\s+sys\.path\.insert[^\n]+', '', content)
    content = re.sub(r'_parent = [^\n]+', '', content)
    content = re.sub(r'if _parent not in sys\.path:\s+sys\.path\.insert[^\n]+', '', content)
    content = re.sub(r'from __future__ import annotations', '', content)
    
    parts.append(f'\n# ==================== MODULE: {mod} ====================\n')
    parts.append(content)

final_code = '\n'.join(parts)
# Clean up duplicate empty lines
final_code = re.sub(r'\n{3,}', '\n\n', final_code)

with open('submission_v3_standalone.py', 'w', encoding='utf-8') as f:
    f.write(final_code)

print('Successfully generated submission_v3_standalone.py, length:', len(final_code))

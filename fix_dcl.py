c = open('railway_file_server.py', 'r', encoding='utf-8').read()

# Find the DOMContentLoaded block and add loadCloudDataProjects() call
old_dcl_end = "loadCloudDataProjects()}});"
new_dcl_end = "loadCloudDataProjects()\n}})}});"

# Actually, let's look at the actual code
import re
dcl_matches = list(re.finditer(r"DOMContentLoaded',function\(\).*?\}\}\);", c, re.DOTALL))
print(f'Found {len(dcl_matches)} DOMContentLoaded blocks')
for i, m in enumerate(dcl_matches):
    print(f'  #{i}: len={len(m.group())} at {m.start()}')
    ctx = m.group()
    print(f'    ends with: {repr(ctx[-50:])}')

# The problem: after addEventListener calls, there should be loadCloudDataProjects()
# Fix: replace the block with one that has the call
if dcl_matches:
    old = dcl_matches[0].group()
    # Find where the last close of if(sel) is
    # The end should be: ...addEventListener(...); loadCloudDataProjects()}});
    # Currently it's: ...loadCloudDataProjects()}});
    # But loadCloudDataProjects is called inside change handler, not at DCL level
    
    # Actually, looking at my code again:
    # domContentLoaded',function(){var sel=document.getElementById('cdpSelect');
    #   if(sel){
    #     sel.addEventListener('change',function(){...loadCloudDataProjects()...})
    #     ...more listeners...
    #   }
    # })
    # The loadCloudDataProjects IS called inside change handler. Not at DCL level.
    
    # Fix: add loadCloudDataProjects() call right before the closing of the if(sel) block
    # Find where if(sel){...} ends and add call
    old_fixed = old.replace(
        "document.getElementById('cdQueryType').addEventListener('change',function(){var pid=sel.value;if(pid)loadCloudDataList(pid,1)});loadCloudDataProjects()}});",
        "document.getElementById('cdQueryType').addEventListener('change',function(){var pid=sel.value;if(pid)loadCloudDataList(pid,1)});loadCloudDataProjects()\n}})}});"
    )
    # Actually the fix is simpler: replace the entire block
    # Current: ...loadCloudDataProjects()}}); 
    # Want: loadCloudDataProjects() called in the outer scope, not inner
    
    # The current code: after addEventListener calls, has: loadCloudDataProjects() then }}) then })
    # The loadCloudDataProjects() is inside the change handler
    # Fix: put loadCloudDataProjects() at the DCL scope level
    
    # Let me see exactly what's before this
    print()
    print('BEFORE fix:')
    print(old[:100])
    print('...')
    print(old[-120:])
    
    # Create corrected version
    new_dcl = old.replace(
        "loadCloudDataProjects()",
        ""
    ).replace(
        "if(pid)loadCloudDataList(pid,1)});loadCloudDataProjects()",
        "if(pid)loadCloudDataList(pid,1)});loadCloudDataProjects()\nloadCloudDataProjects()"
    )
    
    # Hmm that's hacky. Better: just add loadCloudDataProjects() before the closing }}) of the DCL
    # Find: })}); and add loadCloudDataProjects() before it
    new_dcl = old.replace(
        "}});",
        "loadCloudDataProjects(); }}});"
    )
    
    c = c.replace(old, new_dcl)
    print('Fixed DCL block')
    print()
    # Verify
    new_idx = c.find('DOMContentLoaded')
    new_dcl_block = c[new_idx:c.find('}});', new_idx)+5]
    print('AFTER fix:', new_dcl_block[-60:])

open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('OK size:', len(c))

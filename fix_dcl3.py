c = open('railway_file_server.py', 'r', encoding='utf-8').read()

# Find DOMContentLoaded block
dcl_idx = c.find('DOMContentLoaded')
next_dcl_close = c.find('}});', dcl_idx)
if next_dcl_close < 0: next_dcl_close = c.find('}})', dcl_idx)
print(f'DCL at {dcl_idx}, close at {next_dcl_close}')

# Extract the block
dcl_block = c[dcl_idx:next_dcl_close + 5]
print(f'DCL block length: {len(dcl_block)}')
print(f'DCL block: {dcl_block[:150]}')
print(f'...')
print(f'DCL block end: {repr(dcl_block[-100:])}')

# Replace block with corrected version
# The fix: move loadCloudDataProjects() from inside change handler to outside
# Current has: loadCloudDataList(pid,1)loadCloudDataProjects(); }}}
# Want: loadCloudDataList(pid,1)}}); ... loadCloudDataProjects()

# Find the problematic part
if 'loadCloudDataList(pid,1)loadCloudDataProjects()' in dcl_block:
    old_fragment = 'loadCloudDataList(pid,1)loadCloudDataProjects()'
    new_fragment = 'loadCloudDataList(pid,1)'
    
    new_dcl = dcl_block.replace(old_fragment, new_fragment)
    # Now add loadCloudDataProjects() at the right level
    # Find where to insert: after all addEventListener but before the closing })});
    add_pos = new_dcl.rfind('}});')
    # Count braces to find outer level
    if add_pos >= 0:
        # Insert before this close
        new_dcl = new_dcl[:add_pos] + 'loadCloudDataProjects()\n' + new_dcl[add_pos:]
    
    c = c[:dcl_idx] + new_dcl + c[next_dcl_close + 5:]
    print('Fixed DCL')
else:
    print('Pattern not found, checking exact...')
    # Find the exact end
    end_marker = 'loadCloudDataList(pid,1)'
    pos = dcl_block.find(end_marker)
    if pos >= 0:
        print(f'Found at {pos}: {repr(dcl_block[pos:pos+100])}')
    
    # Check what's at the very end
    print(f'Full end: {repr(dcl_block[-200:])}')

open('railway_file_server.py', 'w', encoding='utf-8').write(c)
import py_compile
py_compile.compile('railway_file_server.py', doraise=True)
print('OK')

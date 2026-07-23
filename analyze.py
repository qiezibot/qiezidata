# -*- coding: utf-8 -*-
import sys
c = open(r'C:\Users\lfy20\AppData\Local\Temp\full_utf8.py', 'r', encoding='utf-8').read()

# Find _ADMIN template
adm = c.find('_ADMIN =')
end_adm = c.find('"""', adm + 10)
print('_ADMIN starts at:', adm)
print('_ADMIN ends at:', end_adm)
print('_ADMIN length:', end_adm - adm)

# Show the JS/HTML after the user table section
# Find where the JS functions are in _ADMIN
adm_content = c[adm:end_adm]

# Find page-apidocs section then the script block
apidocs_start = adm_content.find('page-apidocs')
print('\npage-apidocs starts at offset:', apidocs_start)

# Find last script block
last_script = adm_content.rfind('<script>')
print('last <script> at offset:', last_script)
last_close = adm_content.rfind('</script>')
print('last </script> at offset:', last_close)

# Print the content between apidocs and last script
print('\n=== Content between apidocs and last </script> ===')
print(adm_content[apidocs_start:last_close+9][:5000])

# Print the last 2000 chars before </body>
body_end = adm_content.rfind('</body>')
print('\n=== Last 2000 chars before </body> ===')
print(adm_content[body_end-2000:body_end])

import base64

with open('E:/openclaw压缩包及启动教程/u-claw/portable/data/.openclaw/workspace/cover_small_b64.txt') as f:
    b64 = f.read()

# Create a simple JS file that sets sessionStorage in chunks
# Each chunk is a line: sessionStorage.setItem('b64_0', '...first chars...')
chunk_size = 3000
chunks = [b64[i:i+chunk_size] for i in range(0, len(b64), chunk_size)]

with open('C:/Users/lfy20/Downloads/set_b64.html', 'w') as f:
    f.write('<html><body><script>\n')
    for i, c in enumerate(chunks):
        escaped = c.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
        f.write(f"sessionStorage.setItem('b64_{i}','{escaped}');\n")
    f.write("var all='';for(var i=0;i<" + str(len(chunks)) + ";i++){all+=sessionStorage.getItem('b64_'+i);}\n")
    f.write("window.__b64=all;document.body.textContent='done: '+all.length;\n")
    f.write('</script></body></html>\n')
print(f'HTML file created with {len(chunks)} chunks')

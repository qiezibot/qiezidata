c=open('railway_file_server.py','r',encoding='utf-8').read()
sw = c.find('switchPage')
ccall = c.find('initCloudData()', sw, sw+300)
print('Local:', ccall >= 0)
if not ccall:
    print('Found:', repr(c[sw:sw+300]))

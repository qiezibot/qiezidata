import sys
path = sys.argv[1]
with open(path, 'rb') as f:
    h = f.read(44)
    if h[:4] == b'RIFF':
        print("WAV file")
    elif h[:2] in (b'\xff\xfb', b'\xff\xf3'):
        print("MP3 file")
    elif h[:4] == b'\x66\x4c\x61\x43':
        print("FLAC file")
    elif h[:3] == b'\x23\x21':
        print("SILK (from QQ voice)")
        print("First bytes:", h[:16].hex())
    else:
        print("Unknown format")
        print("First 16 bytes:", h[:16].hex())
    f.seek(0)
    data = f.read()
    print(f"Size: {len(data)} bytes ({len(data)/1024:.1f}KB)")

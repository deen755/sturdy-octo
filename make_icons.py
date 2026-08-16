import struct, zlib

def make_png(w, h, path):
    raw = b'\x00' + b'\x00\x00\xff' * w
    raw = b''.join([raw for _ in range(h)])
    compressed = zlib.compress(raw)
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    idat = compressed
    def chunk(tp, data):
        return struct.pack('>I', len(data)) + tp + data + struct.pack('>I', zlib.crc32(tp + data) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(png)

make_png(192, 192, 'static/icons/icon-192.png')
make_png(512, 512, 'static/icons/icon-512.png')

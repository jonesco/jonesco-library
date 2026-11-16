# Pull 'sfnt' resources out of a Mac resource fork into plain .ttf files. Usage: sfnt_extract.py <file> <outdir>  (prints out paths)
import struct, sys, os, hashlib
def sfnts(p):
    d = open(p + "/..namedfork/rsrc", "rb").read()
    do, mo, dl, ml = struct.unpack(">IIII", d[:16]); tl = mo + struct.unpack(">H", d[mo+24:mo+26])[0]
    n = struct.unpack(">H", d[tl:tl+2])[0] + 1
    for i in range(n):
        o = tl + 2 + i * 8
        if d[o:o+4] != b"sfnt": continue
        cnt = struct.unpack(">H", d[o+4:o+6])[0] + 1; ro = tl + struct.unpack(">H", d[o+6:o+8])[0]
        for j in range(cnt):
            r = ro + j * 12; off = struct.unpack(">I", b"\0" + d[r+5:r+8])[0]
            ln = struct.unpack(">I", d[do+off:do+off+4])[0]
            yield d[do+off+4:do+off+4+ln]
if __name__ == "__main__":
    p, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
    for k, b in enumerate(sfnts(p)):
        f = os.path.join(out, hashlib.md5(p.encode()).hexdigest()[:8] + "_%d.ttf" % k); open(f, "wb").write(b); print(f)

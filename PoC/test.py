import struct

filename = "live/live_acquisition_ui.bin"

# Baca seluruh isi file sebagai unsigned short (2 byte per data)
with open(filename, "rb") as f:
    data = f.read()
    # 'H' = unsigned short, 'len(data)//2' = jumlah data 16-bit
    values = struct.unpack("<{}H".format(len(data)//2), data)

print(values)
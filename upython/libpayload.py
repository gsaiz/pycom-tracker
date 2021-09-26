import struct

__author__ = 'Guillem Saiz Pascual'


def pack(list_lan_scans, max_n=10):
    if len(list_lan_scans) > max_n:
        list_lan_scans = list_lan_scans[:max_n]

    n_of_lans = struct.pack(
        # Number of networks, unsigned int
        'B',
        len(list_lan_scans),
    )
    packed = [n_of_lans,]
    for wlan_scan in list_lan_scans:
        args = [int(oct, 16) for oct in wlan_scan['macAddress'].lower().split(':')]
        args.append(wlan_scan['signalStrength'])
        args.append(wlan_scan['channel'])
        p = struct.pack(
            (
                # Big endian
                '>'
                # Wlan scan for 1 network:
                # 6 Bytes, unisnged char, MAC
                '6B'
                # 1 Byte, signed char, Signal strength, in dBm, from 0 to -100
                'b'
                # 1 Byte, channel, unsigned char
                'B'
            ),
            *args,
        )
        packed.append(p)
    
    return b''.join(packed)


def unpack(_bytes):
    n_of_networks, = struct.unpack(
        # Number of networks, unsigned int
        'B',
        _bytes[:1]
    )
    _bytes = _bytes[1:]
    size_wlan_scan = 8
    wlan_scans = []
    for ind in range(n_of_networks):
        *macAddress, signalStrength, channel  = struct.unpack(
            (
                # Big endian
                '>'
                # Wlan scan for 1 network:
                # 6 Bytes, unsigned char, MAC
                '6B'
                # 1 Byte, signed char, Signal strength, in dBm, from 0 to -100
                'b'
                # 1 Byte, channel, unsigned char
                'B'
            ),
            _bytes[ind*size_wlan_scan:(ind+1)*size_wlan_scan],
        )
        wlan_scan = {
            'macAddress': ':'.join([hex(oct)[2:].zfill(2) for oct in macAddress]),
            'signalStrength': signalStrength,
            'channel': channel,

        }

        wlan_scans.append(wlan_scan)

    return wlan_scans


def test_pack_unpack_1():
    # Test with 1
    wlan_scans = [
        {
            'macAddress': 'aa:dd:44:11:66:ff',
            'signalStrength': -23,
            'channel': 11,
        },
    ]

    packed = pack(wlan_scans)
    print('length pack: {}'.format(len(packed)))
    print('packed: {}'.format(packed))

    unpacked = unpack(packed)
    print('unpacked: {}'.format(unpacked))

    assert unpacked == wlan_scans


def test_pack_unpack_many():
    # Test with many
    wlan_scans = [
        {
            'macAddress': 'aa:bb:dd:bb:ff:00',
            'signalStrength': -23,
            'channel': 11,
        },
        {
            'macAddress': '22:23:24:25:af:b2',
            'signalStrength': -99,
            'channel': 2,
        },
        {
            'macAddress': '00:01:20:55:77:39',
            'signalStrength': -10,
            'channel': 19,
        },
    ]

    packed = pack(wlan_scans)
    print('length pack: {}'.format(len(packed)))
    print('packed: {}'.format(packed))

    unpacked = unpack(packed)
    print('unpacked: {}'.format(unpacked))

    assert unpacked == wlan_scans


if __name__ == '__main__':
    test_pack_unpack_1()
    test_pack_unpack_many()
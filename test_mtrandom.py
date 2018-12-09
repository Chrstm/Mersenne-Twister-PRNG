from mtrandom import MTRandom
import random


def check(seed):
    r = MTRandom(seed)
    s = random.Random(seed)
    assert r.getstate() == s.getstate()[1]
    for i in range(313):
        assert r.random() == s.random()
    for i in range(1, 64):
        assert r.getrandbits(i) == s.getrandbits(i)


print("Testing ...")
gendata = random.Random()
check(gendata)

for i in range(-16, 16):
    check(i)
    check(i / 10)

for i in range(1, 32):
    # int
    check(gendata.getrandbits(i))
    check(-gendata.getrandbits(i))

    # bytes, str
    s = gendata.getrandbits(i * 8).to_bytes(i, 'big')
    check(s)
    # check(bytearray(s))  # TypeError: unhashable type: 'bytearray', WHY?
    check(s.decode('Latin1'))

    # other object
    check(gendata.random())
    check((gendata.getrandbits(32) for _ in range(i)))

print("OK!")

from random import Random as _Random
from hashlib import sha512 as _sha512
from os import urandom as _urandom, getpid as _getpid
from time import time as _time, monotonic as _monotonic
from struct import pack as _pack, unpack as _unpack

N = 624
M = 397
MATRIX_A = 0x9908b0df
UPPER_MASK = 0x80000000
LOWER_MASK = 0x7fffffff


class MTRandom:
    """Mersenne Twister random number generator
    pure python implementation of random in python
    refer to cpython/Lib/random.py & cpython/Modules/_randommodule.c

    """
    def __init__(self, s=None):
        self.index = 0
        self.state = [0] * N
        self.seed(s)

    def seed(self, a=None, version=2):
        if version == 1 and isinstance(a, (str, bytes)):
            x = ord(a[0]) << 7 if a else 0
            for c in a:
                x = ((1000003 * x) ^ ord(c)) & 0xFFFFFFFFFFFFFFFF
            x ^= len(a)
            a = -2 if x == -1 else x

        if version == 2 and isinstance(a, (str, bytes, bytearray)):
            if isinstance(a, str):
                a = a.encode()
            a += _sha512(a).digest()
            a = int.from_bytes(a, 'big')

        self.random_seed(a)

    def get_random_inst(self):
        """Return a random.Random instance."""
        r = _Random()
        r.setstate((3, self.getstate(), None))
        return r

    def random(self):
        """Return a float ranged in [0, 1)."""
        return self.random_random()

    def getstate(self):
        """Return a tuple contain state vector"""
        return tuple(self.state + [self.index])

    def setstate(self, state):
        self.random_setstate(state)

    def getrandbits(self, k):
        """Return an int with k random bits"""
        return self.random_getrandbits(k)

# -------------------- methods from _randommodule.c  -------------------

    def genrand_int32(self):
        mt = self.state

        if self.index >= N:
            self.index = 0
            mag01 = (0, MATRIX_A)
            for i in range(N - M):
                y = (mt[i] & UPPER_MASK) | (mt[i + 1] & LOWER_MASK)
                mt[i] = mt[i + M] ^ (y >> 1) ^ mag01[y & 1]
            for i in range(N - M, N - 1):
                y = (mt[i] & UPPER_MASK) | (mt[i + 1] & LOWER_MASK)
                mt[i] = mt[i - (N - M)] ^ (y >> 1) ^ mag01[y & 1]
            y = (mt[-1] & UPPER_MASK) | (mt[0] & LOWER_MASK)
            mt[-1] = mt[M - 1] ^ (y >> 1) ^ mag01[y & 1]

        y = mt[self.index]
        y ^= y >> 11
        y ^= (y << 7) & 0x9d2c5680
        y ^= (y << 15) & 0xefc60000
        y ^= (y >> 18)
        self.index += 1
        return y

    def random_random(self):
        a = self.genrand_int32() >> 5
        b = self.genrand_int32() >> 6
        return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0)

    def init_genrand(self, s):
        mt = self.state
        mt[0] = s
        for i in range(1, N):
            mt[i] = (1812433253 * (mt[i - 1] ^ (mt[i - 1] >> 30)) + i) & 0xffffffff
        self.index = N

    def init_by_array(self, init_key, key_length):
        mt = self.state
        self.init_genrand(19650218)
        i, j = 1, 0
        for k in range(max(N, key_length), 0, -1):
            mt[i] = ((mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1664525)) + init_key[j] + j) & 0xffffffff
            i += 1
            j += 1
            if i >= N:
                mt[0] = mt[N - 1]
                i = 1
            if j >= key_length:
                j = 0
        for k in range(N - 1, 0, -1):
            mt[i] = ((mt[i] ^ ((mt[i - 1] ^ (mt[i - 1] >> 30)) * 1566083941)) - i) & 0xffffffff
            i += 1
            if i >= N:
                mt[0] = mt[N - 1]
                i = 1
        mt[0] = 0x80000000

    def random_seed_urandom(self):
        key = _urandom(N * 4)  # _PyOS_URandomNonblock
        key = [int.from_bytes(key[i * 4: i * 4 + 4], 'little') for i in range(N)]
        self.init_by_array(key, len(key))

    def random_seed_time_pid(self):
        key = []
        now = int(round(_time() * 10 ** 9))  # _PyTime_GetSystemClock
        key.append(now & 0xffffffff)
        key.append(now >> 32)
        key.append(_getpid())
        now = int(round(_monotonic() * 10 ** 9))  # _PyTime_GetMonotonicClock
        key.append(now & 0xffffffff)
        key.append(now >> 32)
        self.init_by_array(key, len(key))

    def random_seed(self, arg):
        if not arg:
            try:
                self.random_seed_urandom()
            except Exception:
                self.random_seed_time_pid()

        if isinstance(arg, int):
            arg = abs(arg)
        else:
            arg = hash(arg)
            arg = _unpack('N', _pack('n', arg))[0]  # PyLong_FromSize_t

        key = []  # _PyLong_AsByteArray
        while arg:
            key.append(arg & 0xffffffff)
            arg >>= 32
        if not key:
            key = [0]
        self.init_by_array(key, len(key))

    def random_setstate(self, state):
        if not isinstance(state, tuple):
            raise TypeError('state vector must be a tuple')
        if len(state) != N + 1:
            raise ValueError('state vector is the wrong size')
        if state[-1] < 0 or state[-1] > N:
            raise ValueError('invalid state')
        mt = self.state
        for i in range(N):
            mt[i] = state[i]
        self.index = state[-1]

    def random_getrandbits(self, k):
        if k <= 0:
            raise ValueError('number of bits must be greater than zero')
        if k <= 32:
            return self.genrand_int32() >> (32 - k)
        wordbytes = b''.join(self.genrand_int32().to_bytes(4, 'little') for _ in range(k // 32))
        k %= 32
        if k:
            r = self.genrand_int32() >> (32 - k)
            wordbytes += r.to_bytes((k + 7) // 8, 'little')
        return int.from_bytes(wordbytes, 'little')

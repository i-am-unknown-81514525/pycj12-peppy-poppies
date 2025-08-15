from sympy import prime

def find_xth_prime_sqrt(x):
    if x == 1:
        return 2
    primes_found = 1
    num = 3
    while True:
        if all(num % i != 0 for i in range(3, int(num**0.5) + 1, 2)):
            primes_found += 1
            if primes_found == x:
                return num
        num += 2

def find_xth_prime_sympy(x):
    return prime(x)

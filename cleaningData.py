import json
import numpy as np
import random
import itertools

max_guessed_set_size = 5

enumeration_set = [12, 14, 34, 50, 69, 75, 76, 88]
try_count = 0
try_residue_count = 0

for size in np.arange(1, max_guessed_set_size + 1):

    for guess_I1 in itertools.combinations(enumeration_set, size):
        # print(guess_I1)

        try_count += 1
        try_residue_count += 1

        guess_x = {k: 1 for k in guess_I1}
        print(guess_x)
        guess_I2 = {v: 0 for v in np.setdiff1d(enumeration_set, guess_x)}
        print(guess_I2)
        # for k in guess_I2:
        #     guess_x[k] = 0
print(try_count)
# print(alpha_delta)

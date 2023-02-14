import time
from pathlib import Path
from statistics import pvariance, fmean
from typing import Tuple, List, Union

import numpy as np
import pandas as pd
import getch

ROOT = Path(__file__).parent.resolve()
ETALON_DATASET = ROOT / 'etalons.csv'

DEFAULT_TIMES_AUTH = 5
t_r = {0.05: {5: 2.5706, 6: 2.4469, 7: 2.3646, 8: 2.306, 9: 2.2622}}


def enter_word(word: str) -> Tuple[str, List[float]]:
    time_intervals = []
    input_string = ""

    ind = 1
    char = getch.getche()
    while True:
        input_string += char

        if ind == len(word):
            break

        start_time = time.perf_counter()
        char = getch.getche()
        end_time = time.perf_counter()

        elapsed_time = end_time - start_time
        time_intervals.append(elapsed_time)

        ind += 1

    if input_string != word:
        print(f"\nERROR: {input_string} isn't equal {word}. So try again...")
        return enter_word(word)

    return input_string, time_intervals


def get_statistics(arr: List[float]) -> Tuple[float, float]:
    M = fmean(arr)
    S = pvariance(arr)
    return M, S


def compare_authentication_with_etalons(
        etalons: pd.DataFrame, val: Tuple[float, float], n_intervals: int, t: float
) -> Tuple[int, bool]:
    M, S = val

    S_ = (etalons['S'] + S) * (n_intervals - 1) / (2 * n_intervals - 1)
    t_p_ = np.abs(etalons['M'] - M) / np.sqrt(S_ * 2 / n_intervals)

    r: int = (t_p_ < t).sum()
    P = r / etalons.shape[0]

    return r, P >= 0.9


def get_df_with_stats(
        word_etalon: str, n_times: int = 5, validation: bool = False, **kwargs
) -> Union[pd.DataFrame, Tuple[int, int]]:
    r, n_authenticated = 0, 0
    d = {'key': [], 'M': [], 'S': []}

    for i in range(n_times):
        print(f'\n[{i + 1}] Enter etalon: ', end='')

        word, times = enter_word(word_etalon)
        M, S = get_statistics(times)

        if validation:
            r_, is_authenticated = compare_authentication_with_etalons(val=(M, S), **kwargs)

            r += r_
            n_authenticated += int(is_authenticated)
        else:
            d['key'].append(word)
            d['M'].append(M)
            d['S'].append(S)

    if validation:
        return r, n_authenticated

    return pd.DataFrame(d)


def create_etalon():
    etalon_word = input("Create etalon word (len between 6 and 10): ").strip()

    if len(etalon_word) not in range(6, 11):
        print(f'ERROR: The length of {etalon_word} must be in range [6, 10]!!')
        return create_etalon()

    N = int(input("Enter number of etalons: ").strip())

    df = get_df_with_stats(etalon_word, N)
    df.to_csv(ETALON_DATASET, index=False)

    print("Etalons created successfully")


def validate():
    df_etalon = pd.read_csv(ETALON_DATASET)
    etalon_key_word = df_etalon['key'][0]
    n_intervals = len(etalon_key_word) - 1

    key_word = input("Enter your key word: ").strip()
    if key_word != etalon_key_word:
        print(f'ERROR: {key_word} is wrong!')
        return validate()

    alpha = float(input(f"Enter alpha for t_r {list(t_r.keys())}: ").strip())
    if alpha not in t_r.keys():
        print(f'ERROR: alpha {alpha} doesnt exist!')
        return validate()

    r, n_auth = get_df_with_stats(
        etalon_key_word,
        n_times=DEFAULT_TIMES_AUTH,
        validation=True,
        etalons=df_etalon,
        t=t_r[alpha][n_intervals],
        n_intervals=n_intervals
    )

    k_e = df_etalon.shape[0] * DEFAULT_TIMES_AUTH
    P = r / k_e
    N1 = (DEFAULT_TIMES_AUTH - n_auth) / DEFAULT_TIMES_AUTH

    print(f'\n\nP={P}')
    print(f'N1={N1}')

    if P >= 0.9:
        print("====> Validation successful\n")
    else:
        print("====> Validation failed\n")


def main():
    flag = 'y'

    while True:
        option = input("Enter '1' to create etalons, '2' to validate or 'q' to quit: ").strip()
        if option == '1':
            if ETALON_DATASET.exists():
                flag = input("Enter 'y' if you want to overwrite etalons.csv, otherwise 'n': ").strip()
            if flag == 'y':
                create_etalon()
        elif option == '2':
            if ETALON_DATASET.exists():
                validate()
            else:
                print('etalon dataset doesnt exist')
        elif option == 'q':
            break
        else:
            print(f"Invalid option: {option}")


if __name__ == '__main__':
    main()

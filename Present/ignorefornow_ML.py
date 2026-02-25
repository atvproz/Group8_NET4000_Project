import numpy as np
import random

def get_delay(h1):
    """Run ping, return delay in ms as float"""
    result = h1.cmd('ping -c 3 -W 1 10.0.0.2')
    for line in result.split('\n'):
        if 'avg' in line:  # "rtt min/avg/max/mdev = 0.1/0.2/0.3"
            try:
                avg = float(line.split('/')[4])
                return avg
            except:
                pass
    return 50.0  # Default if ping fails

def train_delay_model(net):
    print("Training...")
    h1 = net.get('h1')
    X, y = [], []

    for trial in range(100):
        bw_mock = random.uniform(5, 50)
        delay = get_delay(h1)
        X.append([bw_mock, 4])
        y.append(delay)
        if trial % 25 == 0:
            print(f"Trial {trial}, delay={delay:.1f}ms")

    X, y = np.array(X), np.array(y)
    A = np.c_[X, np.ones(len(X))]
    coeffs, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    rmse = np.sqrt(np.mean((X @ coeffs[:2] + coeffs[2] - y)**2))
    print(f"Done! RMSE={rmse:.1f}ms")
    return coeffs

def test_model(coeffs):
    print("\nPredictions:")
    for bw in [50, 25, 10]:
        d = np.array([bw, 4]) @ coeffs[:2] + coeffs[2]
        print(f"  BW {bw}Mbps -> {d:.1f}ms predicted")

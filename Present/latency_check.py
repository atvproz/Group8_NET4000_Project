def latency_check(net, label, src='h1', dst='10.0.0.2', count=20):
    result = net.get(src).cmd(f'ping -c {count} -W 1 {dst}')
    avg, loss = None, 100.0
    for line in result.split('\n'):
        if 'avg' in line:
            try: avg = float(line.split('/')[4])
            except: pass
        if 'packet loss' in line:
            try: loss = float(line.split('%')[0].split()[-1])
            except: pass
    adj = ((1 - loss/100) * (avg or 1000)) + (loss/100 * 1000)
    print(f"\n{label} | Raw: {f'{avg:.3f}ms' if avg else 'N/A'} | Loss: {loss:.1f}% | Adjusted: {adj:.3f}ms")
    return {'label': label, 'raw': avg, 'loss': loss, 'adj': adj}
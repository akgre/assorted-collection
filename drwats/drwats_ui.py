import numpy as np
from scipy import signal
from scipy.signal.windows import hann
import matplotlib.pyplot as plt

# Define filter parameters
fs = 44100.0  # Sample rate, Hz
fcuts = [3000.0, 8000.0]  # Cutoff frequencies, Hz
b = signal.firwin(101, fcuts, pass_zero=False, fs=fs)
w, H = signal.freqz(b)

# Apply averaging
win = hann(51)
H_smooth = np.convolve(np.abs(H), win, mode='same') / sum(win)

# Plot frequency response
fig, ax = plt.subplots()
ax.plot(w/(2*np.pi)*fs, 20*np.log10(H_smooth)-3)
ax.set(xlabel='Frequency (Hz)', ylabel='Gain (dB)',
       title='Bandpass filter frequency response')
ax.grid()
plt.show()

# Print data points to console
x_values = list(w/(2*np.pi)*fs)
y_values = list(20*np.log10(H_smooth)-3)
print(';'.join(map(str, x_values)))
print(';'.join(map(str, y_values)))

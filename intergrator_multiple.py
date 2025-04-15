import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from scipy.integrate import cumulative_trapezoid, cumulative_simpson

class IntegrationComparator:
    def __init__(self, file_path, fs=50, cutoff=3.0):
        self.fs = fs
        self.dt = 1/fs
        self.cutoff = cutoff
        
        # Load raw data (already in m/s²)
        df = pd.read_csv(file_path, on_bad_lines='skip', engine='python')
        self.acc_raw = df[['acc_x', 'acc_y', 'acc_z']].dropna().astype(float)
        self.t = np.arange(len(self.acc_raw)) * self.dt
        
        # Create filtered version
        self.acc_filtered = self.apply_filter(self.acc_raw)

    def apply_filter(self, data):
        """Create filtered copy of acceleration data"""
        b, a = butter(4, self.cutoff/(0.5*self.fs), btype='low')
        filtered = pd.DataFrame(
            filtfilt(b, a, data, axis=0),
            columns=data.columns,
            index=data.index
        )
        return filtered

    def integrate(self, method='trapz', use_filter=False):
        """Integrate using specified method with raw or filtered data"""
        acc_data = self.acc_filtered if use_filter else self.acc_raw
        methods = {
            'trapz': lambda x: cumulative_trapezoid(x, dx=self.dt, initial=0),
            'simpson': cumulative_simpson,
            'rk4': self.rk4_integration
        }
        
        integrator = methods[method]
        results = {}
        
        for axis in acc_data.columns:
            # First integration (acceleration to velocity)
            acc_vals = acc_data[axis].values
            velocity = integrator(acc_vals) if method != 'simpson' else \
                      cumulative_simpson(acc_vals, dx=self.dt, initial=0)
            
            # Second integration (velocity to position)
            position = integrator(velocity) if method != 'simpson' else \
                      cumulative_simpson(velocity, dx=self.dt, initial=0)
            
            results[axis] = {
                'velocity': velocity,
                'position': position
            }
        
        return results

    def rk4_integration(self, data):
        """Runge-Kutta 4th order integration"""
        n = len(data)
        integrated = np.zeros(n)
        for i in range(1, n):
            h = self.dt
            k1 = data[i-1]
            k2 = data[i-1] + h*k1/2
            k3 = data[i-1] + h*k2/2
            k4 = data[i-1] + h*k3
            integrated[i] = integrated[i-1] + (h/6)*(k1 + 2*k2 + 2*k3 + k4)
        return integrated

    def compare_methods(self, methods=['trapz', 'simpson', 'rk4']):
        """Compare integration methods with/without filtering"""
        metrics = []
        fig, axs = plt.subplots(len(methods), 2, figsize=(15, 5*len(methods)))
        
        for row, method in enumerate(methods):
            # Get both raw and filtered results
            raw_results = self.integrate(method, use_filter=False)
            filt_results = self.integrate(method, use_filter=True)
            
            # Calculate drift metrics (last 10% of trajectory)
            window = int(len(self.t) * 0.1)
            for col, (results, label) in enumerate(zip(
                [raw_results, filt_results],
                ['Raw', 'Filtered']
            )):
                pos = results['acc_x']['position']
                drift = np.mean(np.abs(pos[-window:]))
                metrics.append({
                    'Method': method,
                    'Type': label,
                    'Drift': drift
                })
                
                # Plot positions
                ax = axs[row, col] if len(methods) > 1 else axs[col]
                for axis in ['acc_x', 'acc_y', 'acc_z']:
                    ax.plot(self.t, results[axis]['position'], label=axis)
                ax.set_title(f'{method.upper()} - {label} Data')
                ax.set_ylabel('Position (m)')
                ax.legend()
                if row == len(methods)-1:
                    ax.set_xlabel('Time (s)')

        plt.tight_layout()
        plt.show()
        
        # Display metrics
        metrics_df = pd.DataFrame(metrics)
        print("\nIntegration Drift Metrics (Mean Absolute Error - Last 10%):")
        print(metrics_df.pivot(index='Method', columns='Type', values='Drift'))
        return metrics_df

# ================= Usage Example =================
if __name__ == "__main__":
    comparator = IntegrationComparator('tskin_log_20250415_180510.csv', fs=50, cutoff=2.0)
    
    # Compare integration methods with both raw and filtered data
    metrics = comparator.compare_methods()
    
    # Optional: Plot raw vs filtered acceleration
    fig, axs = plt.subplots(3, 1, figsize=(12, 8))
    for idx, axis in enumerate(['acc_x', 'acc_y', 'acc_z']):
        axs[idx].plot(comparator.t, comparator.acc_raw[axis], label='Raw')
        axs[idx].plot(comparator.t, comparator.acc_filtered[axis], label='Filtered')
        axs[idx].set_title(f'{axis.upper()} Acceleration Comparison')
        axs[idx].legend()
    plt.tight_layout()
    plt.show()
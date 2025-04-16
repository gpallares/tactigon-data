import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, detrend
from scipy.integrate import cumulative_trapezoid, cumulative_simpson
from sklearn.metrics import mean_squared_error

class AccXIntegrationComparator:
    def __init__(self, file_path, fs=50, cutoff=3.0):
        self.fs = fs
        self.dt = 1/fs
        self.cutoff = cutoff
        
        # Load data and process acc_x
        df = pd.read_csv(file_path, on_bad_lines='skip', engine='python')
        self.acc_raw = df['acc_x'].dropna().values.astype(float)
        self.t = np.arange(len(self.acc_raw)) * self.dt
        
        # Create filtered version
        self.acc_filtered = self.apply_filter(self.acc_raw)
        
        # Calculate theoretical displacement (ground truth)
        self.theoretical_displacement = self.calculate_theoretical_displacement()

    def apply_filter(self, data):
        """Apply low-pass filter to acc_x"""
        b, a = butter(4, self.cutoff/(0.5*self.fs), btype='low')
        return filtfilt(b, a, data)

    def calculate_theoretical_displacement(self):
        """Calculate expected displacement from synthetic signal parameters"""
        t = self.t
        displacement = np.zeros_like(t)
        
        # Phase 1: Sine wave integration (0-3s)
        mask = t <= 3.0
        displacement[mask] = -0.25 * np.sin(2*np.pi*1*t[mask])  # Double integral of sin(t)
        
        # Phase 2: Constant acceleration (3-6s)
        mask = (t > 3.0) & (t <= 6.0)
        t_phase = t[mask] - 3.0
        displacement[mask] = 0.5 * 1.5 * t_phase**2 + 0.25  # 0.5*a*t² + continuity
        
        # Phase 3: Linear acceleration (6-10s)
        mask = t > 6.0
        t_phase = t[mask] - 6.0
        # Integral of linear acceleration a(t) = 1.5 + (4-1.5)/4 * t
        displacement[mask] = (0.5*1.5*t_phase**2 +
                             (0.5*(4-1.5)/(4*3)*t_phase**3) +
                             0.5*1.5*3**2 + 0.25 ) # Continuity
        
        return displacement

    def integrate(self, method='trapz', use_filter=False):
        """Integrate acc_x using specified method"""
        acc_data = self.acc_filtered if use_filter else self.acc_raw
        
        methods = {
            'trapz': lambda x: cumulative_trapezoid(x, dx=self.dt, initial=0),
            'simpson': lambda x: cumulative_simpson(x, dx=self.dt, initial=0),
            'rk4': self.rk4_integration
        }
        
        integrator = methods[method]
        
        # First integration (velocity)
        velocity = integrator(acc_data)
        
        # Second integration (displacement)
        displacement = integrator(velocity)
        
        return displacement

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

    def compare_methods(self):
        """Compare integration methods with error metrics"""
        methods = ['trapz', 'simpson', 'rk4']
        fig, axs = plt.subplots(len(methods), 2, figsize=(15, 5*len(methods)))
        
        metrics = []
        
        for row, method in enumerate(methods):
            # Calculate both raw and filtered displacements
            raw_disp = self.integrate(method, use_filter=False)
            filt_disp = self.integrate(method, use_filter=True)
            
            # Calculate metrics
            window = int(len(self.t) * 0.1)
            for col, (disp, label) in enumerate(zip([raw_disp, filt_disp], ['Raw', 'Filtered'])):
                # Drift metric
                drift = np.mean(np.abs(disp[-window:]))
                # drift = np.mean(np.abs(estimated_position[-window:] - theoretical_displacement[-window:]))

                # RMSE against theoretical
                rmse = np.sqrt(mean_squared_error(self.theoretical_displacement, disp))
                
                metrics.append({
                    'Method': method,
                    'Type': label,
                    'Drift': drift,
                    'RMSE': rmse
                })
                
                # Plotting
                ax = axs[row, col]
                ax.plot(self.t, disp, label='Estimated')
                ax.plot(self.t, self.theoretical_displacement, '--', label='Theoretical')
                ax.set_title(f'{method.upper()} - {label} Data\nDrift: {drift:.2f}m, RMSE: {rmse:.2f}m')
                ax.set_ylabel('Displacement (m)')
                ax.legend()
                if row == len(methods)-1:
                    ax.set_xlabel('Time (s)')

        plt.tight_layout()
        plt.grid()
        plt.show()
        
        # Display metrics
        metrics_df = pd.DataFrame(metrics)
        print("\nIntegration Performance Metrics:")
        print(metrics_df.pivot(index='Method', columns='Type', values=['Drift', 'RMSE']))
        return metrics_df

# ================= Usage =================
if __name__ == "__main__":
    comparator = AccXIntegrationComparator('modified_data.csv', fs=50, cutoff=2.0)
    metrics = comparator.compare_methods()
    
    # Plot acceleration comparison
    plt.figure(figsize=(12, 4))
    plt.plot(comparator.t, comparator.acc_raw, label='Raw Acceleration')
    plt.plot(comparator.t, comparator.acc_filtered, label='Filtered Acceleration')
    plt.title('Acceleration X Comparison')
    plt.xlabel('Time (s)')
    plt.ylabel('Acceleration (m/s²)')
    plt.legend()
    plt.grid()
    plt.show()
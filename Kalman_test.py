import numpy as np
from scipy.linalg import block_diag
from pyquaternion import Quaternion  # For quaternion operations

class SensorFusionEKF:
    def __init__(self, Q, R, P0):
        """
        Initialize the EKF for IMU + vision fusion
        
        Args:
            Q: Process noise covariance matrix
            R: Measurement noise covariance matrix
            P0: Initial state covariance matrix
        """
        # State vector: [px, py, pz, vx, vy, vz, qx, qy, qz, qw, b_ax, b_ay, b_az, b_gx, b_gy, b_gz]
        # 16 elements: position(3), velocity(3), orientation(4), accel bias(3), gyro bias(3)
        self.state_dim = 16
        self.state = np.zeros(self.state_dim)
        self.state[9] = 1.0  # Initialize quaternion (w=1)
        
        self.covariance = P0  # State covariance matrix
        self.process_noise = Q
        self.measurement_noise = R
        
        # Gravity vector in world frame (assume z-up)
        self.gravity = np.array([0, 0, -9.81])
        
        # For calibration
        self.calibration_buffer = []
        self.calibration_samples_needed = 100  # Adjust based on your needs
        
    def predict(self, imu_data, dt):
        """
        Prediction step using IMU data
        
        Args:
            imu_data: Dictionary containing:
                - 'accel': raw accelerometer reading (3x1)
                - 'gyro': raw gyroscope reading (3x1)
                - 'timestamp': measurement timestamp
            dt: Time step since last prediction
        """
        # Extract current state
        position = self.state[0:3]
        velocity = self.state[3:6]
        quaternion = Quaternion(self.state[6:10])
        accel_bias = self.state[10:13]
        gyro_bias = self.state[13:16]
        
        # Apply bias correction to IMU measurements
        corrected_accel = imu_data['accel'] - accel_bias
        corrected_gyro = imu_data['gyro'] - gyro_bias
        
        # Rotate acceleration to world frame and subtract gravity
        accel_world = quaternion.rotate(corrected_accel) + self.gravity
        
        # State prediction
        new_position = position + velocity * dt + 0.5 * accel_world * dt**2
        new_velocity = velocity + accel_world * dt
        
        # Orientation prediction using gyro data
        rotation_vector = corrected_gyro * dt
        rotation_magnitude = np.linalg.norm(rotation_vector)
        
        if rotation_magnitude > 1e-12:  # Avoid division by zero
            delta_q = Quaternion(axis=rotation_vector/rotation_magnitude, 
                               angle=rotation_magnitude)
            new_quaternion = quaternion * delta_q
        else:
            new_quaternion = quaternion
        
        # Update state
        self.state[0:3] = new_position
        self.state[3:6] = new_velocity
        self.state[6:10] = new_quaternion.elements
        
        # Compute Jacobian (F) of the motion model
        F = self._compute_jacobian_F(quaternion, corrected_accel, dt)
        
        # Predict covariance
        self.covariance = F @ self.covariance @ F.T + self.process_noise
        
    def update(self, vision_pose):
        """
        Update step using vision pose
        
        Args:
            vision_pose: Dictionary containing:
                - 'position': camera position estimate (3x1)
                - 'orientation': camera orientation as quaternion (4x1)
                - 'timestamp': measurement timestamp
        """
        # Extract vision measurements
        z = np.concatenate([vision_pose['position'], vision_pose['orientation']])
        
        # Measurement model: we directly observe position and orientation
        H = np.zeros((7, self.state_dim))
        H[0:3, 0:3] = np.eye(3)  # Position observation
        H[3:7, 6:10] = np.eye(4)  # Orientation observation
        
        # Predicted measurement
        z_pred = np.concatenate([self.state[0:3], self.state[6:10]])
        
        # Measurement residual
        y = z - z_pred
        
        # Handle quaternion difference properly
        state_quat = Quaternion(self.state[6:10])
        meas_quat = Quaternion(vision_pose['orientation'])
        quat_diff = meas_quat * state_quat.inverse
        
        # Convert quaternion difference to axis-angle for the residual
        if quat_diff.real < 0:
            quat_diff = -quat_diff  # Ensure positive real part
            
        angle = 2 * np.arccos(min(max(quat_diff.real, -1), 1))  # Clamp to valid range
        axis = quat_diff.axis if angle > 1e-6 else np.array([1, 0, 0])
        
        y[3:6] = axis * angle  # Use axis-angle representation for orientation residual
        y = y[:6]  # Drop the scalar part of the quaternion residual
        
        # Adjust H for the axis-angle representation
        H = H[:6, :]  # Now 6x16
        
        # Kalman gain calculation
        S = H @ self.covariance @ H.T + self.measurement_noise[:6, :6]
        K = self.covariance @ H.T @ np.linalg.inv(S)
        
        # State update
        self.state = self.state + K @ y
        
        # Normalize quaternion
        self.state[6:10] = Quaternion(self.state[6:10]).normalised.elements
        
        # Covariance update (Joseph form for numerical stability)
        I_KH = np.eye(self.state_dim) - K @ H
        self.covariance = I_KH @ self.covariance @ I_KH.T + K @ self.measurement_noise[:6, :6] @ K.T
        
    def _compute_jacobian_F(self, quaternion, corrected_accel, dt):
        """
        Compute the Jacobian of the motion model
        """
        F = np.eye(self.state_dim)
        
        # Position depends on velocity
        F[0:3, 3:6] = np.eye(3) * dt
        
        # Velocity depends on orientation (through acceleration)
        # Get the Jacobian of rotated acceleration w.r.t. quaternion
        accel_skew = np.array([
            [0, -corrected_accel[2], corrected_accel[1]],
            [corrected_accel[2], 0, -corrected_accel[0]],
            [-corrected_accel[1], corrected_accel[0], 0]
        ])
        
        # Quaternion to rotation matrix derivative
        q = quaternion.elements
        qx, qy, qz, qw = q
        G = np.array([
            [ qw, -qz,  qy],
            [ qz,  qw, -qx],
            [-qy,  qx,  qw],
            [-qx, -qy, -qz]
        ])
        
        dR_dq = 2 * G @ accel_skew
        F[3:6, 6:10] = dR_dq * dt
        
        # Velocity depends on acceleration bias
        F[3:6, 10:13] = -quaternion.rotation_matrix * dt
        
        # Orientation depends on gyro bias
        F[6:10, 13:16] = -0.5 * dt * np.array([
            [ qw, -qz,  qy],
            [ qz,  qw, -qx],
            [-qy,  qx,  qw],
            [-qx, -qy, -qz]
        ])
        
        return F
    
    def start_calibration(self):
        """Start collecting data for calibration"""
        self.calibration_buffer = []
        
    def add_calibration_data(self, imu_data, vision_pose):
        """Add data point to calibration buffer"""
        self.calibration_buffer.append({
            'imu': imu_data,
            'vision': vision_pose,
            'timestamp': imu_data['timestamp']
        })
        
    def run_calibration(self):
        """Estimate IMU biases from collected calibration data"""
        if len(self.calibration_buffer) < self.calibration_samples_needed:
            raise ValueError("Not enough calibration data")
            
        # Calculate average difference between IMU and vision data
        accel_errors = []
        gyro_errors = []
        
        for data in self.calibration_buffer:
            # For stationary calibration, expected gyro is zero and accel should measure gravity
            expected_accel = -Quaternion(data['vision']['orientation']).inverse.rotate(self.gravity)
            accel_errors.append(data['imu']['accel'] - expected_accel)
            
            # Expected gyro is zero when stationary
            gyro_errors.append(data['imu']['gyro'])
            
        # Compute average biases
        avg_accel_bias = np.mean(accel_errors, axis=0)
        avg_gyro_bias = np.mean(gyro_errors, axis=0)
        
        # Update the state with new bias estimates
        self.state[10:13] = avg_accel_bias
        self.state[13:16] = avg_gyro_bias
        
        # Reset calibration buffer
        self.calibration_buffer = []
        
        return {
            'accel_bias': avg_accel_bias,
            'gyro_bias': avg_gyro_bias
        }
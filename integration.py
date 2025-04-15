import scipy.integrate as spi

time = [0, 1, 2, 3, 4, 5]
acceleration = [0, 1, 2, 3, 4, 5]
velocity = spi.cumulative_trapezoid(acceleration, time, initial=0)
print(velocity)
position = spi.cumulative_trapezoid(velocity, time, initial=0)
print(position)
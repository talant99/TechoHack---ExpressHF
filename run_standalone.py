import numpy as np
import matplotlib.pyplot as plt
from ExpressFrac.Runner import Runner


express_solver = Runner("./input.json")
result = express_solver.solve()

print("Front right:", result.front_location)
print("Max mean width:", np.max(result.width))

fig_1, (ax_1, ax_2) = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))

ax_1.cla()
ax_2.cla()
ax_1.plot(result.mesh.xc, result.width)
ax_2.plot(result.mesh.xc, result.pressure)

# e_prime = express_solver.solver.reservoir_prop.e_prime
# toughness = express_solver.solver.reservoir_prop.toughness
# H = express_solver.solver.reservoir_prop.pay_zone_height
# flowrate = express_solver.solver.pumping_schedule.flowrate
# total_time = express_solver.solver.pumping_schedule.time_end
#
# w_k = toughness * np.sqrt(np.pi * H) / e_prime
# l_k = e_prime * flowrate * total_time / (np.sqrt(4 * np.pi) * toughness * np.power(H, 3 / 2))
# ax_1.axhline(y=w_k, linestyle="--", color="k")
# ax_1.axvline(x=l_k, linestyle="--", color="k")

ax_1.set_ylim([0, 0.0185])
ax_2.set_ylim([0, 2e6])

plt.show()

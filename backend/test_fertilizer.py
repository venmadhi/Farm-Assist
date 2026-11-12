from app.ml.fertilizer_agent import fertilizer_agent

print("Case 1: Rubber (N=30, P=15, K=35, pH=5.2)")
res1 = fertilizer_agent.calculate_fertilizer("rubber", 30, 15, 35, 5.2, temperature=30, humidity=80)
print(f"N: {res1['n_status']}, P: {res1['p_status']}, K: {res1['k_status']}")
tips1 = res1['sustainability_tips']
print("Tips:", tips1)

print("\nCase 2: Banana (N=65, P=40, K=50, pH=5.4)")
res2 = fertilizer_agent.calculate_fertilizer("banana", 65, 40, 50, 5.4, temperature=30, humidity=80)
print(f"N: {res2['n_status']}, P: {res2['p_status']}, K: {res2['k_status']}")
tips2 = res2['sustainability_tips']
print("Tips:", tips2)
print("Fertilizer:", res2['fertilizer_schedule'][1]['fertilizer_name'])

import math

def haversine_km(a, b):
    R = 6371.0
    lat1, lon1 = math.radians(a["lat"]), math.radians(a["lon"])
    lat2, lon2 = math.radians(b["lat"]), math.radians(b["lon"])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(h))

def _fallback(stops):
    if not stops:
        return [], 0.0
    remaining = stops[1:].copy()
    route = [stops[0]]
    while remaining:
        last = route[-1]
        nxt = min(remaining, key=lambda s: haversine_km(last, s))
        route.append(nxt)
        remaining.remove(nxt)
    distance = sum(haversine_km(route[i], route[i+1]) for i in range(len(route)-1))
    return route, distance

def optimize_route(stops, vehicle_capacity_kg=1000):
    raw = [s.model_dump() if hasattr(s, "model_dump") else s for s in stops]
    if len(raw) <= 1:
        return {
            "ordered_stops": raw,
            "total_distance_km": 0,
            "estimated_minutes": 0,
            "estimated_fuel_cost": 0,
            "method": "No routing needed",
        }

    # Try OR-Tools for a real routing solver.
    try:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2

        n = len(raw)
        matrix = [[round(haversine_km(raw[i], raw[j]) * 1000) for j in range(n)] for i in range(n)]
        manager = pywrapcp.RoutingIndexManager(n, 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_cb(from_index, to_index):
            return matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

        transit = routing.RegisterTransitCallback(distance_cb)
        routing.SetArcCostEvaluatorOfAllVehicles(transit)
        params = pywrapcp.DefaultRoutingSearchParameters()
        params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        solution = routing.SolveWithParameters(params)

        if solution:
            ordered = []
            index = routing.Start(0)
            while not routing.IsEnd(index):
                ordered.append(raw[manager.IndexToNode(index)])
                index = solution.Value(routing.NextVar(index))
            ordered.append(raw[manager.IndexToNode(index)])
            distance = sum(haversine_km(ordered[i], ordered[i+1]) for i in range(len(ordered)-1))
            return {
                "ordered_stops": ordered,
                "total_distance_km": round(distance, 2),
                "estimated_minutes": int(round(distance / 30 * 60)),
                "estimated_fuel_cost": round(distance / 12 * 100, 2),
                "method": "Google OR-Tools",
            }
    except Exception:
        pass

    ordered, distance = _fallback(raw)
    return {
        "ordered_stops": ordered,
        "total_distance_km": round(distance, 2),
        "estimated_minutes": int(round(distance / 30 * 60)),
        "estimated_fuel_cost": round(distance / 12 * 100, 2),
        "method": "Nearest-neighbour fallback",
    }

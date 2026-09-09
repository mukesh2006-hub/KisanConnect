import math


def haversine_km(a, b):
    R = 6371.0
    lat1, lon1 = math.radians(a["lat"]), math.radians(a["lon"])
    lat2, lon2 = math.radians(b["lat"]), math.radians(b["lon"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(h))


def _fallback(stops, vehicle_capacity_kg):
    """Capacity-aware nearest-neighbour fallback."""

    if not stops:
        return [], 0.0

    remaining = stops[1:].copy()
    route = [stops[0]]
    current_load = 0.0

    # Apply pickup/delivery at the first stop.
    current_load += stops[0].get("pickup_kg", 0)
    current_load -= stops[0].get("delivery_kg", 0)

    if current_load < 0 or current_load > vehicle_capacity_kg:
        raise ValueError("Vehicle capacity is not sufficient for the starting stop.")

    while remaining:
        last = route[-1]
        feasible = []

        for stop in remaining:
            new_load = (
                current_load
                + stop.get("pickup_kg", 0)
                - stop.get("delivery_kg", 0)
            )

            if 0 <= new_load <= vehicle_capacity_kg:
                feasible.append((stop, new_load))

        if not feasible:
            raise ValueError(
                "No feasible route found for the given vehicle capacity."
            )

        nxt, new_load = min(
            feasible,
            key=lambda item: haversine_km(last, item[0]),
        )

        route.append(nxt)
        remaining.remove(nxt)
        current_load = new_load

    distance = sum(
        haversine_km(route[i], route[i + 1])
        for i in range(len(route) - 1)
    )

    return route, distance


def optimize_route(stops, vehicle_capacity_kg=1000):
    raw = [
        s.model_dump() if hasattr(s, "model_dump") else s
        for s in stops
    ]

    if vehicle_capacity_kg <= 0:
        raise ValueError("Vehicle capacity must be greater than zero.")

    if len(raw) <= 1:
        return {
            "ordered_stops": raw,
            "total_distance_km": 0,
            "estimated_minutes": 0,
            "estimated_fuel_cost": 0,
            "method": "No routing needed",
        }

    # Validate individual stop loads.
    for stop in raw:
        pickup = stop.get("pickup_kg", 0)
        delivery = stop.get("delivery_kg", 0)

        if pickup < 0 or delivery < 0:
            raise ValueError("Pickup and delivery quantities cannot be negative.")

        if pickup > vehicle_capacity_kg:
            raise ValueError(
                f"Pickup at {stop['name']} exceeds vehicle capacity."
            )

    # Try Google OR-Tools first.
    try:
        from ortools.constraint_solver import (
            pywrapcp,
            routing_enums_pb2,
        )

        n = len(raw)

        matrix = [
            [
                round(haversine_km(raw[i], raw[j]) * 1000)
                for j in range(n)
            ]
            for i in range(n)
        ]

        manager = pywrapcp.RoutingIndexManager(n, 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        # Distance callback.
        def distance_cb(from_index, to_index):
            return matrix[
                manager.IndexToNode(from_index)
            ][
                manager.IndexToNode(to_index)
            ]

        transit = routing.RegisterTransitCallback(distance_cb)
        routing.SetArcCostEvaluatorOfAllVehicles(transit)

        # Load callback.
        # Pickup adds weight; delivery removes weight.
        def load_cb(from_index):
            node = manager.IndexToNode(from_index)
            stop = raw[node]

            return int(
                round(
                    stop.get("pickup_kg", 0)
                    - stop.get("delivery_kg", 0)
                )
            )

        load_callback = routing.RegisterUnaryTransitCallback(load_cb)

        # Add vehicle capacity constraint.
        routing.AddDimensionWithVehicleCapacity(
            load_callback,
            0,  # No extra capacity allowed.
            [int(round(vehicle_capacity_kg))],
            True,  # Vehicle starts empty.
            "Load",
        )

        params = pywrapcp.DefaultRoutingSearchParameters()

        params.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        solution = routing.SolveWithParameters(params)

        if solution:
            ordered = []

            index = routing.Start(0)

            while not routing.IsEnd(index):
                ordered.append(raw[manager.IndexToNode(index)])
                index = solution.Value(routing.NextVar(index))

            # Add final depot.
            ordered.append(raw[manager.IndexToNode(index)])

            distance = sum(
                haversine_km(
                    ordered[i],
                    ordered[i + 1],
                )
                for i in range(len(ordered) - 1)
            )

            return {
                "ordered_stops": ordered,
                "total_distance_km": round(distance, 2),
                "estimated_minutes": int(round(distance / 30 * 60)),
                "estimated_fuel_cost": round(distance / 12 * 100, 2),
                "method": "Google OR-Tools + Capacity",
            }

    except ValueError:
        raise

    except Exception:
        pass

    # Capacity-aware fallback.
    ordered, distance = _fallback(
        raw,
        vehicle_capacity_kg,
    )

    return {
        "ordered_stops": ordered,
        "total_distance_km": round(distance, 2),
        "estimated_minutes": int(round(distance / 30 * 60)),
        "estimated_fuel_cost": round(distance / 12 * 100, 2),
        "method": "Nearest-neighbour + Capacity fallback",
    }